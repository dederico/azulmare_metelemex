"""
Triage agent implementation to coordinate between specialized agents
"""
import logging
from typing import Dict, Any, List
import uuid

# Import from common_imports with simpler approach
from .common_imports import function_tool, RunContextWrapper, USING_OFFICIAL_SDK
from .base_agent import BaseAgent, AgentContext
# These imports are only used for type hints, actual instances are passed in register_specialized_agents
from .marketing_agent import MarketingAgent
from .sales_agent import SalesAgent
from .logistics_agent import LogisticsAgent
from .collection_agent import CollectionAgent

logger = logging.getLogger(__name__)

class TriageAgent(BaseAgent):
    """
    Agent responsible for routing queries to specialized agents
    """
    def __init__(self, data_manager):
        """
        Initialize the triage agent
        
        Args:
            data_manager: Data manager instance
        """
        description = "A triage agent that delegates requests to specialized agents"
        instructions = """
        You are a triage agent for a company's decision-making system designed for higher management.
        Your role is to analyze incoming queries and direct them to the most appropriate specialized agent.
        
        You have access to these specialized agents:
        1. Marketing Agent - For marketing data analysis, campaign performance, and ROI
        2. Sales Agent - For sales performance, forecasting, and customer purchase analysis
        3. Logistics Agent - For inventory, shipping, and supply chain analysis
        4. Collection Agent - For accounts receivable, payment trends, and risk assessment
        
        When you receive a query:
        1. Determine which specialized agent is best equipped to handle it
        2. Send the query to that agent using the appropriate hand-off
        3. If a query spans multiple domains, break it down and route each part to the appropriate agent
        4. If you're unsure which agent to route to, use your analysis tool to determine the best match
        
        Try to be decisive and efficient in your routing. The goal is to get the query to the right expert
        as quickly as possible to provide higher management with accurate insights.
        """
        
        # Create tools specific to triage agent
        tools = [
            self._analyze_query_domain,
            self._get_system_status
        ]
        
        super().__init__("Triage Agent", data_manager, description, instructions, tools)
        
        # Track specialized agents
        self.specialized_agents = {}
    
    def register_specialized_agents(self, agents: Dict[str, BaseAgent]):
        """
        Register specialized agents with the triage agent
        
        Args:
            agents: Dictionary of specialized agents
        """
        self.specialized_agents = agents
        
        # Create handoffs to specialized agents
        handoffs = []
        for agent in agents.values():
            handoffs.append(agent.agent)
        
        # Update agent with handoffs
        self.agent.handoffs = handoffs
        
        # Register this triage agent with all specialized agents
        for agent in agents.values():
            agent.agent.handoffs.append(self.agent)
    
    @function_tool(
        name_override="analyze_query_domain",
        description_override="Analyze which domain a query belongs to."
    )
    async def _analyze_query_domain(
        self, 
        context: RunContextWrapper[AgentContext], 
        query: str
    ) -> Dict[str, Any]:
        """
        Analyze which domain a query belongs to
        
        Args:
            context: Agent context wrapper
            query: The user query to analyze
            
        Returns:
            Dictionary containing domain analysis
        """
        domains = {
            "marketing": 0,
            "sales": 0,
            "logistics": 0,
            "collection": 0
        }
        
        # Marketing keywords
        marketing_keywords = [
            "marketing", "campaign", "brand", "advertising", "promotion", 
            "market share", "customer acquisition", "social media", "digital marketing",
            "campaign performance", "marketing roi", "conversion rate"
        ]
        
        # Sales keywords
        sales_keywords = [
            "sales", "revenue", "quota", "pipeline", "deal", "customer", 
            "sales rep", "forecast", "opportunity", "close rate", "win rate",
            "sales performance", "upsell", "cross-sell"
        ]
        
        # Logistics keywords
        logistics_keywords = [
            "logistics", "shipping", "delivery", "inventory", "warehouse", 
            "supply chain", "stock", "fulfillment", "supplier", "distribution",
            "backorder", "lead time", "transportation"
        ]
        
        # Collection keywords
        collection_keywords = [
            "collection", "receivable", "payment", "invoice", "due", 
            "aging", "overdue", "cash flow", "debt", "credit",
            "accounts receivable", "past due", "outstanding balance"
        ]
        
        # Analyze query for keywords
        query_lower = query.lower()
        
        for keyword in marketing_keywords:
            if keyword in query_lower:
                domains["marketing"] += 1
                
        for keyword in sales_keywords:
            if keyword in query_lower:
                domains["sales"] += 1
                
        for keyword in logistics_keywords:
            if keyword in query_lower:
                domains["logistics"] += 1
                
        for keyword in collection_keywords:
            if keyword in query_lower:
                domains["collection"] += 1
        
        # Determine primary domain
        primary_domain = max(domains, key=domains.get)
        primary_score = domains[primary_domain]
        
        # Check if there's a clear winner
        is_clear_match = True
        secondary_domains = []
        
        for domain, score in domains.items():
            if domain != primary_domain and score > 0:
                secondary_domains.append(domain)
                if score == primary_score:
                    is_clear_match = False
        
        return {
            "primary_domain": primary_domain if primary_score > 0 else "unknown",
            "is_clear_match": is_clear_match,
            "domain_scores": domains,
            "secondary_domains": secondary_domains
        }
    
    @function_tool(
        name_override="get_system_status",
        description_override="Get the status of all specialized agents and data freshness."
    )
    async def _get_system_status(self, context) -> Dict[str, Any]:
        """
        Get the status of all specialized agents and data freshness
        
        Args:
            context: Agent context wrapper
            
        Returns:
            Dictionary containing system status information
        """
        status = {
            "agents": {},
            "data_freshness": {}
        }
        
        # Get agent status
        for name, agent in self.specialized_agents.items():
            status["agents"][name] = {
                "name": agent.name,
                "available": True
            }
        
        # Get data freshness
        data_types = ["marketing", "sales", "logistics", "collection"]
        for data_type in data_types:
            data_method = f"get_{data_type}_data"
            if hasattr(self.data_manager, data_method):
                data = getattr(self.data_manager, data_method)()
                if data and "last_updated" in data:
                    status["data_freshness"][data_type] = data["last_updated"]
                else:
                    status["data_freshness"][data_type] = "unknown"
        
        return status
    
    async def process_query(self, query: str) -> str:
        """
        Process a query through the triage system
        
        Args:
            query: The user query
            
        Returns:
            The response from the appropriate agent
        """
        # Create a unique conversation ID
        conversation_id = uuid.uuid4().hex[:16]
        
        # Initialize context
        context = AgentContext(user_query=query)
        
        try:
            # Just use the base class's process_query method
            return await super().process_query(query, context)
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"An error occurred while processing your query: {str(e)}"