"""
Marketing specialist agent implementation
"""
import logging
from typing import Dict, Any

# Import from our common imports module
from .common_imports import function_tool, RunContextWrapper
from .base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

class MarketingAgent(BaseAgent):
    """
    Agent specialized in marketing data analysis and insights
    """
    def __init__(self, data_manager):
        """
        Initialize the marketing agent
        
        Args:
            data_manager: Data manager instance
        """
        description = "A specialized agent for marketing data analysis and insights"
        instructions = """
        You are a marketing specialist agent for a company's decision-making system.
        Your role is to analyze marketing data and provide insights to help higher management make informed decisions.
        
        Key responsibilities:
        - Analyze marketing campaign performance
        - Track customer acquisition costs
        - Monitor brand awareness metrics
        - Evaluate marketing ROI
        - Identify market trends and opportunities
        
        You have access to marketing data that is updated daily. Use this data to provide accurate, 
        data-driven insights and recommendations. When answering questions, always cite relevant data 
        points to support your conclusions.
        
        If you cannot answer a question with the data available, or if the question falls outside 
        your marketing expertise, indicate that the question should be redirected to another agent.
        """
        
        # Create tools specific to marketing agent
        tools = [
            self._get_marketing_metrics,
            self._analyze_campaign_performance,
            self._calculate_marketing_roi
        ]
        
        super().__init__("Marketing Agent", data_manager, description, instructions, tools)
    
    @function_tool(
        name_override="get_marketing_metrics",
        description_override="Get marketing metrics from the latest data."
    )
    async def _get_marketing_metrics(self, context: RunContextWrapper[AgentContext], metric_name: str = None) -> Dict[str, Any]:
        """
        Get marketing metrics from the latest data
        
        Args:
            context: Agent context wrapper
            metric_name: Optional specific metric name to retrieve
            
        Returns:
            Dictionary containing the requested marketing metrics
        """
        try:
            marketing_data = self.data_manager.get_marketing_data()
            
            if metric_name:
                if metric_name in marketing_data:
                    return {metric_name: marketing_data[metric_name]}
                else:
                    return {"error": f"Metric '{metric_name}' not found in marketing data"}
            
            # Return all metrics if no specific one requested
            return marketing_data
        except Exception as e:
            logger.error(f"Error analyzing campaign performance: {str(e)}")
            return {"error": str(e)}
    
    @function_tool(
        name_override="calculate_marketing_roi",
        description_override="Calculate return on investment for marketing activities."
    )
    async def _calculate_marketing_roi(
        self, 
        context: RunContextWrapper[AgentContext], 
        campaign_id: str = None,
        period: str = "all"  # e.g., "last_month", "q1", "all"
    ) -> Dict[str, Any]:
        """
        Calculate marketing ROI for specific campaigns or periods
        
        Args:
            context: Agent context wrapper
            campaign_id: Optional specific campaign ID
            period: Time period for calculation
            
        Returns:
            Dictionary containing ROI calculations
        """
        try:
            marketing_data = self.data_manager.get_marketing_data()
            
            # Check if campaigns data exists
            if 'campaigns' not in marketing_data:
                return {"error": "No campaign data available for ROI calculation"}
            
            campaigns = marketing_data['campaigns']
            
            # Filter by campaign ID if specified
            if campaign_id:
                campaigns = [c for c in campaigns if c.get('id') == campaign_id]
                if not campaigns:
                    return {"error": f"Campaign with ID '{campaign_id}' not found"}
            
            # Calculate ROI for each campaign
            roi_results = []
            for campaign in campaigns:
                cost = campaign.get('cost', 0)
                revenue = campaign.get('revenue', 0)
                
                if cost == 0:
                    roi = 0
                else:
                    roi = ((revenue - cost) / cost) * 100
                
                roi_results.append({
                    "campaign_id": campaign.get('id'),
                    "campaign_name": campaign.get('name'),
                    "cost": cost,
                    "revenue": revenue,
                    "roi": round(roi, 2),
                    "roi_percent": f"{round(roi, 2)}%"
                })
            
            return {"roi_analysis": roi_results}
        except Exception as e:
            logger.error(f"Error calculating marketing ROI: {str(e)}")
            return {"error": str(e)}

    @function_tool(
        name_override="analyze_campaign_performance",
        description_override="Analyze the performance of marketing campaigns."
    )
    async def _analyze_campaign_performance(
        self, 
        context: RunContextWrapper[AgentContext], 
        campaign_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyze the performance of marketing campaigns
        
        Args:
            context: Agent context wrapper
            campaign_id: Optional specific campaign ID to analyze
            
        Returns:
            Dictionary containing campaign performance analysis
        """
        try:
            marketing_data = self.data_manager.get_marketing_data()
            
            # Check if campaigns data exists
            if 'campaigns' not in marketing_data:
                return {"error": "No campaign data available"}
            
            campaigns = marketing_data['campaigns']
            
            if campaign_id:
                # Find specific campaign
                campaign = next((c for c in campaigns if c.get('id') == campaign_id), None)
                if campaign:
                    return {"campaign": campaign}
                else:
                    return {"error": f"Campaign with ID '{campaign_id}' not found"}
            
            # Analyze all campaigns if no specific ID requested
            return {"campaigns": campaigns}
        except Exception as e:
            logger.error(f"Error analyzing campaign performance: {str(e)}")
            return {"error": str(e)}