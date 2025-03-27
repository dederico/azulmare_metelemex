"""
Adapter for using OpenAI Assistants API instead of Agents SDK
"""
import asyncio
import json
import time
import logging
import inspect
from typing import Dict, Any, List, Optional, Callable, TypeVar, Generic, Union, Type

from openai import OpenAI
from pydantic import BaseModel

import config

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class RunContextWrapper(Generic[T]):
    """
    Context wrapper to mimic the Agent SDK RunContextWrapper
    """
    def __init__(self, context: Optional[BaseModel] = None):
        self.context = context

# Make RunContextWrapper properly support subscriptable notation
# This is a hack to make type hints work
RunContextWrapper.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)

class AssistantAdapter:
    """
    Adapter for using OpenAI's Assistants API instead of Agents SDK
    """
    def __init__(self):
        self.openai = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
        self.temperature = config.AGENT_TEMPERATURE
        self.last_completion_ts = 0
        self.last_completion_context: Optional[RunContextWrapper[T]] = None
        self.max_tokens = config.AGENT_MAX_TOKENS
        self.current_completion_id: Optional[str] = None
        self.completion_history: List[str] = []
        self.completion_cache: Dict[str, Dict[str, Any]] = {}
        self.prompt_prefix = config.RECOMMENDED_PROMPT_PREFIX
    async def run(self, function_name: str, args: Dict[str, Any], context: Optional[RunContextWrapper[T]] = None) -> Dict[str, Any]:
        """
        Run a function using OpenAI's Assistants API
        
        Args:
            function_name: Name of the function to run
            args: Arguments to pass to the function
            context: Optional context to pass to the function
        
        Returns:
            Result of the function
        """
        if time.time() - self.last_completion_ts < config.AGENT_COMPLETION_RATE_LIMIT:
            logger.info("Rate limit exceeded, waiting before making another completion")
            await asyncio.sleep(config.AGENT_COMPLETION_RATE_LIMIT - (time.time() - self.last_completion_ts))
        
        self.last_completion_ts = time.time()
        self.last_completion_context = context
        
        function = self.get_function(function_name)

        if function is None:
            raise ValueError(f"Function '{function_name}' not found")
        if not callable(function):
            raise TypeError(f"Function '{function_name}' is not callable")
        
        input = self.get_input_for_function(function, args, context)
        output = await self.make_completion(input)
        result = self.parse_output(function, output)
        self.completion_cache[self.current_completion_id] = result
        self.completion_history.append(self.current_completion_id)
    
        return result
    

class AdapterRunner:
    """
    Runner for the adapter
    """
    def __init__(self, adapter: AssistantAdapter):
        self.adapter = adapter
        self.completion_cache = adapter.completion_cache
        self.completion_history = adapter.completion_history
        self.current_completion_id = None
        self.current_completion_function: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
        self.current_completion_args: Optional[Dict[str, Any]] = None
        self.current_completion_context: Optional[RunContextWrapper[T]] = None
        self.prompt_prefix = adapter.prompt_prefix
        self.max_tokens = adapter.max_tokens
        self.current_completion_id = None
        self.completion_history = []
        self.completion_cache = {}
        self.current_completion_function = None
        self.current_completion_args = None
    
    async def run(self, function_name: str, args: Dict[str, Any], context: Optional[RunContextWrapper[T]] = None) -> Dict[str, Any]:
        """
        Run a function using the adapter's runner
        
        Args:
            function_name: Name of the function to run
            args: Arguments to pass to the function
            context: Optional context to pass to the function
        
        Returns:
            Result of the function
        """
        self.current_completion_id = str(time.time())
        self.current_completion_function = self.adapter.get_function(function_name)
        self.current_completion_args = args
        self.current_completion_context = context
    
    class MessageItem(BaseModel):
        content: str
        role: str
        type: str
        created_at: float = time.time()
        id: Optional[str] = None
        parent_id: Optional[str] = None
        model: str = "text-davinci-003"
        temperature: float = 0.7
        max_tokens: int = 200
        stop: Optional[List[str]] = None
        stream: bool = False
    
    async def complete(self) -> Dict[str, Any]:
        """
        Complete the current function using the adapter
        
        Returns:
            Computed result of the function
        """
        if self.current_completion_function is None:
            raise ValueError("No function to complete")
        if self.current_completion_args is None:
            raise ValueError("No arguments provided for the function")
        
        input_items = [
            self.MessageItem(
                content=f"{self.prompt_prefix} {self.current_completion_function.__name__}({', '.join(f'{key}={value}' for key, value in self.current_completion_args.items())})",
                role="user",
                type="input",
            )
        ]
        if self.current_completion_context is not None:
            input_items.append(self.MessageItem(
                content=json.dumps(self.current_completion_context.dict()),
                role="assistant",
                type="context",
            ))

            # Add cached completion for the context
            if self.current_completion_id in self.completion_cache:
                input_items.append(self.MessageItem(
                    content=json.dumps(self.completion_cache[self.current_completion_id]),
                    role="assistant",
                    type="output",
                ))
                input_items[-1].parent_id = input_items[-2].id
                input_items[-1].id = str(time.time())
                input_items[-2].stop = ["output"]
                input_items[-2].stream = True
                input_items[-1].model = "text-davinci-003"
                input_items[-1].temperature = 0.7
                input_items[-1].max_tokens = self.max_tokens
                input_items[-1].stop = ["output"]
                input_items[-1].stream = True
            
            # Add completion history
            for completion_id in self.completion_history:
                if completion_id in self.completion_cache:
                    input_items.append(self.MessageItem(
                        content=json.dumps(self.completion_cache[completion_id]),
                        role="assistant",
                        type="output",
                    ))
                    input_items[-1].parent_id = input_items[-2].id
                    input_items[-1].id = str(time.time())
                    input_items[-2].stop = ["output"]
                    input_items[-2].stream = True
                    input_items[-1].model = "text-davinci-003"
                    input_items[-1].temperature = 0.7
                    input_items[-1].max_tokens = self.max_tokens
                    input_items[-1].stop = ["output"]
                    input_items[-1].stream = True

                    