"""
Common imports for all agents to avoid circular dependencies and import errors.
This centralizes all import logic related to the Agents SDK.
"""
import logging
import sys
import os
from typing import Any, Dict, List, Optional, TypeVar, Generic

# Add the project root to sys.path to ensure imports work
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set up a logger
logger = logging.getLogger(__name__)

# Flag to track which implementation is being used
USING_OFFICIAL_SDK = False
RECOMMENDED_PROMPT_PREFIX = "You are a helpful assistant that answers questions based on your expertise."

# Attempt to import the official SDK
try:
    logger.info("Attempting to import official OpenAI Agents SDK")
    # Import from the official agents package
    from agents.sdk_imports import (
        Agent, HandoffOutputItem, ItemHelpers, MessageOutputItem,
        RunContextWrapper, Runner, ToolCallItem, ToolCallOutputItem,
        function_tool, handoff, trace, RECOMMENDED_PROMPT_PREFIX
    )
    USING_OFFICIAL_SDK = True
    logger.info("Successfully imported official OpenAI Agents SDK")
except ImportError as e:
    logger.info(f"Official OpenAI Agents SDK import failed: {e}")
    # Create placeholder functions and classes for compatibility
    # These will be replaced by actual implementations from the adapter
    
    class Agent:
        """Placeholder Agent class until the adapter is loaded"""
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("Agent SDK not loaded and adapter not yet available")
    
    class RunContextWrapper:
        """Placeholder RunContextWrapper class"""
        pass
    
    class Runner:
        """Placeholder Runner class"""
        @staticmethod
        def run(*args, **kwargs):
            raise NotImplementedError("Agent SDK not loaded and adapter not yet available")
    
    class ItemHelpers:
        """Placeholder ItemHelpers class"""
        pass
    
    class MessageOutputItem:
        """Placeholder MessageOutputItem class"""
        pass
    
    class HandoffOutputItem:
        """Placeholder HandoffOutputItem class"""
        pass
    
    class ToolCallItem:
        """Placeholder ToolCallItem class"""
        pass
    
    class ToolCallOutputItem:
        """Placeholder ToolCallOutputItem class"""
        pass
    
    def function_tool(**kwargs):
        """Placeholder function_tool decorator"""
        def decorator(func):
            return func
        return decorator
    
    def handoff(agent, on_handoff=None):
        """Placeholder handoff function"""
        return agent
    
    def trace(name, group_id=None):
        """Placeholder trace function"""
        class TraceDummy:
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        
        return TraceDummy()

# Export all the necessary components
__all__ = [
    'Agent',
    'HandoffOutputItem',
    'ItemHelpers',
    'MessageOutputItem',
    'RunContextWrapper',
    'Runner',
    'ToolCallItem',
    'ToolCallOutputItem',
    'function_tool',
    'handoff',
    'trace',
    'RECOMMENDED_PROMPT_PREFIX',
    'USING_OFFICIAL_SDK'
]

# We'll load the adapter later if needed, to avoid circular imports
def load_adapter():
    """Load the OpenAI adapter if the official SDK is not available"""
    global Agent, RunContextWrapper, Runner, ItemHelpers, function_tool, USING_OFFICIAL_SDK
    
    if not USING_OFFICIAL_SDK:
        try:
            logger.info("Attempting to load OpenAI adapter")
            # We need to use a relative import with the project root in sys.path
            from utils.openai_adapter import (
                AssistantAdapter as Agent,
                RunContextWrapper,
                AdapterRunner as Runner,
                MessageItem as ItemHelpers,
                function_tool
            )
            logger.info("Successfully loaded OpenAI adapter")
        except ImportError as e:
            logger.error(f"Failed to load OpenAI adapter: {e}")
            raise ImportError(f"Both OpenAI Agents SDK and adapter failed to load: {e}")