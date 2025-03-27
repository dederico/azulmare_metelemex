"""
Direct imports from the OpenAI Agents SDK.
Separated to avoid circular imports issues.
"""
import logging

logger = logging.getLogger(__name__)

try:
    # Try to import from the pure agents package first
    from agents import (
        Agent, HandoffOutputItem, ItemHelpers, MessageOutputItem,
        RunContextWrapper, Runner, ToolCallItem, ToolCallOutputItem,
        function_tool, handoff, trace
    )
    
    try:
        from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
    except ImportError:
        logger.warning("Could not import RECOMMENDED_PROMPT_PREFIX from agents.extensions.handoff_prompt")
        RECOMMENDED_PROMPT_PREFIX = "You are a helpful assistant that answers questions based on your expertise."
    
    logger.info("Successfully imported from agents package")
except ImportError:
    # Try openai_agents as an alternative
    try:
        from openai_agents import (
            Agent, HandoffOutputItem, ItemHelpers, MessageOutputItem,
            RunContextWrapper, Runner, ToolCallItem, ToolCallOutputItem,
            function_tool, handoff, trace
        )
        
        try:
            from openai_agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
        except ImportError:
            logger.warning("Could not import RECOMMENDED_PROMPT_PREFIX from openai_agents.extensions.handoff_prompt")
            RECOMMENDED_PROMPT_PREFIX = "You are a helpful assistant that answers questions based on your expertise."
        
        logger.info("Successfully imported from openai_agents package")
    except ImportError:
        # Let the error propagate to be handled by common_imports.py
        logger.error("Failed to import from both agents and openai_agents packages")
        raise