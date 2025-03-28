"""
Sales specialist agent implementation
"""
import logging
from typing import Dict, Any, List, Optional

# Import from our common imports module
from .common_imports import function_tool, RunContextWrapper
from .base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

class SalesAgent(BaseAgent):
    """
    Agent specialized in sales data analysis and insights
    """
    def __init__(self, data_manager):
        """
        Initialize the sales agent
        
        Args:
            data_manager: Data manager instance
        """
        description = "A specialized agent for sales data analysis and forecasting"
        instructions = """
        You are a sales specialist agent for a company's decision-making system.
        Your role is to analyze sales data and provide insights to help higher management make informed decisions.
        
        Key responsibilities:
        - Track revenue and sales performance metrics
        - Analyze customer purchase patterns
        - Monitor sales team performance
        - Generate sales forecasts
        - Identify opportunities for revenue growth
        
        You have access to sales data that is updated daily. Use this data to provide accurate, 
        data-driven insights and recommendations. When answering questions, always cite relevant data 
        points to support your conclusions.
        
        If you cannot answer a question with the data available, or if the question falls outside 
        your sales expertise, indicate that the question should be redirected to another agent.
        """
        
        # Create tools specific to sales agent
        tools = [
            self._get_sales_metrics,
            self._analyze_sales_performance,
            self._forecast_sales
        ]
        
        super().__init__("Sales Agent", data_manager, description, instructions, tools)
    
    @function_tool(
        name_override="get_sales_metrics",
        description_override="Get sales metrics from the latest data."
    )
    async def _get_sales_metrics(
        self, 
        context: RunContextWrapper[AgentContext], 
        metric_name: str = None,
        time_period: str = "current"  # Options: current, last_month, last_quarter, ytd
    ) -> Dict[str, Any]:
        """
        Get sales metrics from the latest data
        
        Args:
            context: Agent context wrapper
            metric_name: Optional specific metric name to retrieve
            time_period: Time period for the metrics
            
        Returns:
            Dictionary containing the requested sales metrics
        """
        try:
            sales_data = self.data_manager.get_sales_data()
            
            # Filter by time period if needed
            if time_period != "current" and "periods" in sales_data:
                if time_period in sales_data["periods"]:
                    sales_data = sales_data["periods"][time_period]
                else:
                    return {"error": f"Time period '{time_period}' not found in sales data"}
            
            if metric_name:
                if metric_name in sales_data:
                    return {metric_name: sales_data[metric_name]}
                else:
                    return {"error": f"Metric '{metric_name}' not found in sales data"}
            
            # Return all metrics if no specific one requested
            return sales_data
        except Exception as e:
            logger.error(f"Error getting sales metrics: {str(e)}")
            return {"error": str(e)}
    
    @function_tool(
        name_override="analyze_sales_performance",
        description_override="Analyze sales performance across different dimensions."
    )
    async def _analyze_sales_performance(
        self, 
        context: RunContextWrapper[AgentContext], 
        dimension: str = "overall",  # Options: overall, by_product, by_region, by_rep
        time_period: str = "current"
    ) -> Dict[str, Any]:
        """
        Analyze sales performance across different dimensions
        
        Args:
            context: Agent context wrapper
            dimension: Dimension to analyze performance
            time_period: Time period for analysis
            
        Returns:
            Dictionary containing sales performance analysis
        """
        try:
            sales_data = self.data_manager.get_sales_data()
            
            # Filter by time period if needed
            if time_period != "current" and "periods" in sales_data:
                if time_period in sales_data["periods"]:
                    sales_data = sales_data["periods"][time_period]
                else:
                    return {"error": f"Time period '{time_period}' not found in sales data"}
            
            # Analyze based on dimension
            if dimension == "overall":
                return {
                    "total_revenue": sales_data.get("total_revenue", 0),
                    "total_units": sales_data.get("total_units", 0),
                    "average_deal_size": sales_data.get("avg_deal_size", 0),
                    "conversion_rate": sales_data.get("conversion_rate", 0)
                }
            elif dimension == "by_product" and "products" in sales_data:
                return {"product_performance": sales_data["products"]}
            elif dimension == "by_region" and "regions" in sales_data:
                return {"regional_performance": sales_data["regions"]}
            elif dimension == "by_rep" and "sales_reps" in sales_data:
                return {"rep_performance": sales_data["sales_reps"]}
            else:
                return {"error": f"Analysis dimension '{dimension}' not available"}
        except Exception as e:
            logger.error(f"Error analyzing sales performance: {str(e)}")
            return {"error": str(e)}
    
    @function_tool(
        name_override="forecast_sales",
        description_override="Generate sales forecasts based on historical data."
    )
    async def _forecast_sales(
        self, 
        context: RunContextWrapper[AgentContext], 
        forecast_period: str = "next_quarter",  # Options: next_month, next_quarter, next_year
        product_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate sales forecasts based on historical data
        
        Args:
            context: Agent context wrapper
            forecast_period: Period to forecast
            product_id: Optional specific product ID
            
        Returns:
            Dictionary containing sales forecasts
        """
        try:
            sales_data = self.data_manager.get_sales_data()
            
            # Check if forecast data exists
            if "forecasts" not in sales_data:
                return {"error": "No forecast data available"}
            
            forecasts = sales_data["forecasts"]
            
            # Filter by period
            if forecast_period not in forecasts:
                return {"error": f"Forecast period '{forecast_period}' not available"}
                
            period_forecast = forecasts[forecast_period]
            
            # Filter by product if specified
            if product_id:
                if "by_product" in period_forecast and product_id in period_forecast["by_product"]:
                    return {"product_forecast": period_forecast["by_product"][product_id]}
                else:
                    return {"error": f"Forecast for product '{product_id}' not available"}
            
            return {"forecast": period_forecast}
        except Exception as e:
            logger.error(f"Error generating sales forecast: {str(e)}")
            return {"error": str(e)}