"""
Direct implementation using OpenAI API to create assistants
"""
import logging
import asyncio
import json
import os
from typing import List, Dict, Any, Optional, Callable

from openai import OpenAI
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAIClientSingleton:
    """Singleton class to manage the OpenAI client instance"""
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the OpenAI client instance, creating it if needed"""
        if cls._instance is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            logger.info("Initializing OpenAI client")
            cls._instance = OpenAI(api_key=api_key)
        
        return cls._instance

class AgentContext(BaseModel):
    """Context for maintaining state during agent interactions"""
    user_query: str = ""
    processed_data: Dict[str, Any] = {}
    conversation_history: List[Dict[str, str]] = []

class DirectAgent:
    """
    Simple agent implementation using OpenAI Assistants API directly
    """
    def __init__(
        self,
        name: str,
        instructions: str,
        tools: List[Callable] = None,
        model: str = "gpt-4o"
    ):
        """
        Initialize the agent
        
        Args:
            name: Agent name
            instructions: Agent instructions
            tools: List of tool functions
            model: Model to use
        """
        self.name = name
        self.instructions = instructions
        self.tools = tools or []
        self.model = model
        
        # Get the OpenAI client
        self.client = OpenAIClientSingleton.get_instance()
        
        logger.info(f"Using model: {model}")
        
        # Format tools for OpenAI API
        openai_tools = self._format_tools()
        
        # Create the Assistant
        try:
            self.assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=openai_tools,
                model=model
            )
            logger.info(f"Created assistant {name} with ID {self.assistant.id}")
        except Exception as e:
            logger.error(f"Error creating assistant: {str(e)}")
            raise
        
        # Map function names to actual functions
        self.function_map = {func.__name__: func for func in self.tools}
    
    def _format_tools(self) -> List[Dict[str, Any]]:
        """Format tools for the OpenAI API"""
        formatted_tools = []
        
        for func in self.tools:
            # Get function name and docstring
            name = func.__name__
            description = func.__doc__ or f"Function {name}"
            
            # Get function parameters
            import inspect
            sig = inspect.signature(func)
            
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param in sig.parameters.items():
                # Skip self parameter
                if param_name == "self":
                    continue
                
                # Determine parameter type
                param_type = "string"  # Default type
                annotation = param.annotation
                if annotation == int:
                    param_type = "number"
                elif annotation == float:
                    param_type = "number"
                elif annotation == bool:
                    param_type = "boolean"
                
                # Add parameter details
                parameters["properties"][param_name] = {
                    "type": param_type,
                    "description": f"Parameter: {param_name}"
                }
                
                # Add to required list if it has no default value
                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)
            
            # Add tool definition
            tool = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            }
            
            formatted_tools.append(tool)
        
        return formatted_tools
    
    async def process_query(self, query: str) -> str:
        """
        Process a user query
        
        Args:
            query: User query string
            
        Returns:
            Response from the assistant
        """
        # Create a thread
        thread = self.client.beta.threads.create()
        
        # Add a message to the thread
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )
        
        # Run the assistant
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant.id
        )
        
        # Wait for the run to complete or require action
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                break
            
            # Handle tool calls if needed
            if run_status.status == "requires_action":
                tool_outputs = []
                
                for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                    tool_call_id = tool_call.id
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Call the appropriate function
                    if function_name in self.function_map:
                        try:
                            result = self.function_map[function_name](**function_args)
                            # Convert to string if necessary
                            if not isinstance(result, str):
                                result = json.dumps(result)
                                
                            tool_outputs.append({
                                "tool_call_id": tool_call_id,
                                "output": result
                            })
                        except Exception as e:
                            logger.error(f"Error calling tool {function_name}: {e}")
                            tool_outputs.append({
                                "tool_call_id": tool_call_id,
                                "output": f"Error: {str(e)}"
                            })
                    else:
                        tool_outputs.append({
                            "tool_call_id": tool_call_id,
                            "output": f"Error: Function {function_name} not found"
                        })
                
                # Submit tool outputs
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            
            elif run_status.status in ["failed", "cancelled", "expired"]:
                return f"Error: Run {run.id} ended with status {run_status.status}"
            
            # Wait a bit before checking again
            await asyncio.sleep(0.5)
        
        # Get messages from the thread
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Extract the assistant's response
        response = ""
        for message in messages.data:
            if message.role == "assistant":
                for content_item in message.content:
                    if content_item.type == "text":
                        response += content_item.text.value + "\n"
        
        return response.strip()

# Decorator for function tools
def function_tool(func):
    """
    Simple decorator to mark a function as a tool
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    return func