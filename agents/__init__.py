"""
Agents package initialization
"""
# This file purposely avoids importing from other modules to prevent circular imports

# Define the public API
__all__ = [
    'get_agent_classes'
]

# Function to get all agent classes without causing circular imports
def get_agent_classes():
    """Get all agent classes to avoid circular imports"""
    # Imports are done inside the function to avoid circular imports
    from .base_agent import BaseAgent, AgentContext
    from .marketing_agent import MarketingAgent
    from .sales_agent import SalesAgent
    from .logistics_agent import LogisticsAgent
    from .collection_agent import CollectionAgent
    from .triage_agent import TriageAgent, create_triage_agent
    
    return {
        'BaseAgent': BaseAgent,
        'AgentContext': AgentContext,
        'MarketingAgent': MarketingAgent,
        'SalesAgent': SalesAgent,
        'LogisticsAgent': LogisticsAgent,
        'CollectionAgent': CollectionAgent,
        'TriageAgent': TriageAgent,
        'create_triage_agent': create_triage_agent
    }