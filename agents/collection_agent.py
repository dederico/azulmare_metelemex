"""
Collection specialist agent implementation
"""
import logging
from typing import Dict, Any, List, Optional

# Import from our common imports module
from .common_imports import function_tool, RunContextWrapper
from .base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

class CollectionAgent(BaseAgent):
    """
    Agent specialized in accounts receivable and collections analysis
    """
    def __init__(self, data_manager):
        """
        Initialize the collection agent
        
        Args:
            data_manager: Data manager instance
        """
        description = "A specialized agent for accounts receivable and collections analysis"
        instructions = """
        You are a collections specialist agent for a company's decision-making system.
        Your role is to analyze accounts receivable and collections data to help higher management make informed decisions.
        
        Key responsibilities:
        - Monitor accounts receivable aging
        - Track collection efficiency
        - Analyze payment trends
        - Identify high-risk accounts
        - Recommend strategies to improve cash flow
        
        You have access to collections data that is updated daily. Use this data to provide accurate, 
        data-driven insights and recommendations. When answering questions, always cite relevant data 
        points to support your conclusions.
        
        If you cannot answer a question with the data available, or if the question falls outside 
        your collections expertise, indicate that the question should be redirected to another agent.
        """
        
        # Create tools specific to collection agent
        tools = [
            self._get_accounts_receivable_status,
            self._analyze_payment_trends,
            self._identify_high_risk_accounts
        ]
        
        super().__init__("Collection Agent", data_manager, description, instructions, tools)
    
    @function_tool(
        name_override="get_accounts_receivable_status",
        description_override="Get current accounts receivable status and aging."
    )
    async def _get_accounts_receivable_status(
        self, 
        context: RunContextWrapper[AgentContext], 
        customer_id: str = None,
        aging_bucket: str = None  # Options: current, 1_30, 31_60, 61_90, over_90
    ) -> Dict[str, Any]:
        """
        Get current accounts receivable status
        
        Args:
            context: Agent context wrapper
            customer_id: Optional specific customer ID
            aging_bucket: Optional specific aging bucket
            
        Returns:
            Dictionary containing AR status
        """
        try:
            collection_data = self.data_manager.get_collection_data()
            
            # Check if AR data exists
            if "accounts_receivable" not in collection_data:
                return {"error": "No accounts receivable data available"}
            
            ar_data = collection_data["accounts_receivable"]
            
            # Filter by customer if specified
            if customer_id:
                customer_ar = [item for item in ar_data.get("invoices", []) if item.get("customer_id") == customer_id]
                if not customer_ar:
                    return {"error": f"No accounts receivable data for customer '{customer_id}'"}
                
                total_due = sum(item.get("amount_due", 0) for item in customer_ar)
                return {
                    "customer_id": customer_id,
                    "total_due": total_due,
                    "invoices": customer_ar
                }
            
            # Filter by aging bucket if specified
            if aging_bucket:
                if aging_bucket not in ar_data.get("aging", {}):
                    return {"error": f"Aging bucket '{aging_bucket}' not found"}
                
                return {"aging": {aging_bucket: ar_data["aging"][aging_bucket]}}
            
            # Return overall AR status
            return {
                "total_ar": ar_data.get("total_ar", 0),
                "aging": ar_data.get("aging", {}),
                "average_days_outstanding": ar_data.get("average_days_outstanding", 0),
                "total_overdue": ar_data.get("total_overdue", 0)
            }
        except Exception as e:
            logger.error(f"Error getting accounts receivable status: {str(e)}")
            return {"error": str(e)}
    
    @function_tool(
        name_override="analyze_payment_trends",
        description_override="Analyze payment trends and collection efficiency."
    )
    async def _analyze_payment_trends(
        self, 
        context: RunContextWrapper[AgentContext], 
        time_period: str = "current",  # Options: current, last_month, last_quarter, ytd
        customer_segment: str = None  # Optional customer segment
    ) -> Dict[str, Any]:
        """
        Analyze payment trends and collection efficiency
        
        Args:
            context: Agent context wrapper
            time_period: Time period for analysis
            customer_segment: Optional customer segment
            
        Returns:
            Dictionary containing payment trend analysis
        """
        try:
            collection_data = self.data_manager.get_collection_data()
            
            # Check if payment trends data exists
            if "payment_trends" not in collection_data:
                return {"error": "No payment trends data available"}
            
            trends_data = collection_data["payment_trends"]
            
            # Filter by time period if needed
            if time_period != "current" and "periods" in trends_data:
                if time_period in trends_data["periods"]:
                    trends_data = trends_data["periods"][time_period]
                else:
                    return {"error": f"Time period '{time_period}' not found in payment trends data"}
            
            # Filter by customer segment if specified
            if customer_segment and "segments" in trends_data:
                if customer_segment not in trends_data["segments"]:
                    return {"error": f"Customer segment '{customer_segment}' not found"}
                
                return {"segment_trends": trends_data["segments"][customer_segment]}
            
            # Return overall payment trends
            return {
                "collection_efficiency": trends_data.get("collection_efficiency", 0),
                "average_days_to_pay": trends_data.get("average_days_to_pay", 0),
                "payment_methods": trends_data.get("payment_methods", {}),
                "trend_by_month": trends_data.get("trend_by_month", [])
            }
        except Exception as e:
            logger.error(f"Error analyzing payment trends: {str(e)}")
            return {"error": str(e)}
    
    @function_tool(
        name_override="identify_high_risk_accounts",
        description_override="Identify high-risk accounts based on payment history."
    )
    async def _identify_high_risk_accounts(
        self, 
        context: RunContextWrapper[AgentContext],
        risk_level: str = "high"  # Options: high, medium, all
    ) -> Dict[str, Any]:
        """
        Identify high-risk accounts based on payment history
        
        Args:
            context: Agent context wrapper
            risk_level: Risk level to filter accounts
            
        Returns:
            Dictionary containing high-risk accounts
        """
        try:
            collection_data = self.data_manager.get_collection_data()
            
            # Check if risk assessment data exists
            if "risk_assessment" not in collection_data:
                return {"error": "No risk assessment data available"}
            
            risk_data = collection_data["risk_assessment"]
            
            # Filter accounts by risk level
            if risk_level == "all":
                return {
                    "high_risk": risk_data.get("high_risk", []),
                    "medium_risk": risk_data.get("medium_risk", []),
                    "low_risk": risk_data.get("low_risk", [])
                }
            elif risk_level in ["high", "medium", "low"]:
                risk_key = f"{risk_level}_risk"
                if risk_key not in risk_data:
                    return {"error": f"No {risk_level} risk data available"}
                    
                return {risk_key: risk_data[risk_key]}
            else:
                return {"error": f"Invalid risk level: {risk_level}"}
        except Exception as e:
            logger.error(f"Error identifying high-risk accounts: {str(e)}")
            return {"error": str(e)}