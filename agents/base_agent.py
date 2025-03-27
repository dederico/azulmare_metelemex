"""
Base agent class for all specialized agents
"""
from __future__ import annotations

import logging
import sys
import os
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)

# Import common components
from .common_imports import (
    Agent, RunContextWrapper, Runner, ItemHelpers, 
    function_tool, RECOMMENDED_PROMPT_PREFIX, USING_OFFICIAL_SDK,
    MessageOutputItem, load_adapter, handoff
)

# Load the adapter if we're not using the official SDK
if not USING_OFFICIAL_SDK:
    load_adapter()

class AgentContext(BaseModel):
    """
    Base context for all agents
    """
    user_query: str = ""
    processed_data: Dict[str, Any] = {}
    conversation_history: List[Dict[str, str]] = []

class BaseAgent:
    """
    Base class for all specialized agents
    """
    def __init__(self, name: str, data_manager, description: str, instructions: str, tools: List = None):
        """
        Initialize the base agent
        
        Args:
            name: Name of the agent
            data_manager: Data manager instance
            description: Short description of the agent
            instructions: Detailed instructions for the agent
            tools: List of tools available to the agent
        """
        self.name = name
        self.data_manager = data_manager
        self.description = description
        self.instructions = instructions
        self.tools = tools or []
        
        # Create the actual agent instance
        self.agent = Agent[AgentContext](
            name=name,
            handoff_description=description,
            instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n{instructions}",
            tools=self.tools
        )
        
        # List to store handoffs
        self.handoffs = []
        
    def add_handoff(self, target_agent, on_handoff=None):
        """
        Add a handoff to another agent
        
        Args:
            target_agent: The agent to hand off to
            on_handoff: Optional function to call on handoff
        """
        if USING_OFFICIAL_SDK:
            if on_handoff:
                self.handoffs.append(handoff(agent=target_agent.agent, on_handoff=on_handoff))
            else:
                self.handoffs.append(target_agent.agent)
        else:
            # Simplified handoff for adapter
            self.handoffs.append(target_agent.agent)
    
    def update_agent_with_handoffs(self):
        """Update the agent with all handoffs"""
        self.agent.handoffs = self.handoffs
    
    async def process_query(self, query: str, context: Optional[AgentContext] = None) -> str:
        """
        Process a query through this agent
        
        Args:
            query: The user query
            context: Optional context for the agent
            
        Returns:
            The response from the agent
        """
        if context is None:
            context = AgentContext(user_query=query)
        
        input_items = [{"content": query, "role": "user"}]
        
        try:
            result = await Runner.run(self.agent, input_items, context=context)
            
            # Get the response text
            response = ""
            if USING_OFFICIAL_SDK:
                for new_item in result.new_items:
                    if isinstance(new_item, MessageOutputItem):
                        response += f"{ItemHelpers.text_message_output(new_item)}\n"
            else:
                for new_item in result.get("new_items", []):
                    response += f"{new_item.get('content', '')}\n"
            
            return response.strip()
        except Exception as e:
            logger.error(f"Error processing query with {self.name}: {str(e)}")
            return f"Error processing query: {str(e)}"