"""
Logistics specialist agent implementation
"""
import logging
from typing import Dict, Any, List, Optional

# Import from our common imports module
from .common_imports import function_tool, RunContextWrapper
from .base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)

class LogisticsAgent(BaseAgent):
    """
    Agent specialized in logistics and supply chain analysis
    """
    def __init__(self, data_manager):
        """
        Initialize the logistics agent
        
        Args:
            data_manager: Data manager instance
        """
        description = "A specialized agent for logistics and supply chain analysis"
        instructions = """
        You are a logistics specialist agent for a company's decision-making system.
        Your role is to analyze supply chain and logistics data to help higher management make informed decisions.
        
        Key responsibilities:
        - Monitor inventory levels and warehouse capacity
        - Track shipping and delivery performance
        - Analyze supply chain efficiency
        - Identify bottlenecks in the logistics process
        - Recommend improvements for logistics operations
        
        You have access to logistics data that is updated daily. Use this data to provide accurate, 
        data-driven insights and recommendations. When answering questions, always cite relevant data 
        points to support your conclusions.
        
        If you cannot answer a question with the data available, or if the question falls outside 
        your logistics expertise, indicate that the question should be redirected to another agent.
        """
        
        # Create tools specific to logistics agent
        tools = [
            self._get_inventory_status,
            self._analyze_shipping_performance,
            self._evaluate_supply_chain
        ]
        
        super().__init__("Logistics Agent", data_manager, description, instructions, tools)
    
    @function_tool(
        name_override="get_inventory_status",
        description_override="Get current inventory status and warehouse capacity."
    )
    async def _get_inventory_status(
        self, 
        context: RunContextWrapper[AgentContext], 
        product_id: str = None,
        warehouse_id: str = None
    ) -> Dict[str, Any]:
        """
        Get current inventory status
        
        Args:
            context: Agent context wrapper
            product_id: Optional specific product ID
            warehouse_id: Optional specific warehouse ID
            
        Returns:
            Dictionary containing inventory status
        """
        try:
            logistics_data = self.data_manager.get_logistics_data()
            
            # Check if inventory data exists
            if "inventory" not in logistics_data:
                return {"error": "No inventory data available"}
            
            inventory_data = logistics_data["inventory"]
            
            # Filter by product if specified
            if product_id:
                product_inventory = [item for item in inventory_data if item.get("product_id") == product_id]
                if not product_inventory:
                    return {"error": f"No inventory data for product '{product_id}'"}
                return {"product_inventory": product_inventory}
            
            # Filter by warehouse if specified
            if warehouse_id:
                warehouse_inventory = [item for item in inventory_data if item.get("warehouse_id") == warehouse_id]
                if not warehouse_inventory:
                    return {"error": f"No inventory data for warehouse '{warehouse_id}'"}
                return {"warehouse_inventory": warehouse_inventory}
            
            # Get warehouse capacity information
            warehouses = logistics_data.get("warehouses", [])
            
            # Return overall inventory status
            return {
                "total_inventory": len(inventory_data),
                "warehouses": warehouses,
                "inventory_summary": self._calculate_inventory_summary(inventory_data)
            }
        except Exception as e:
            logger.error(f"Error getting inventory status: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_inventory_summary(self, inventory_data: List[Dict]) -> Dict[str, Any]:
        """Helper method to calculate inventory summary statistics"""
        total_units = sum(item.get("quantity", 0) for item in inventory_data)
        total_value = sum(item.get("quantity", 0) * item.get("unit_cost", 0) for item in inventory_data)
        low_stock_items = [item for item in inventory_data if item.get("status") == "low"]
        out_of_stock_items = [item for item in inventory_data if item.get("status") == "out_of_stock"]
        
        return {
            "total_units": total_units,
            "total_value": total_value,
            "low_stock_count": len(low_stock_items),
            "out_of_stock_count": len(out_of_stock_items)
        }
    
    @function_tool(
        name_override="analyze_shipping_performance",
        description_override="Analyze shipping and delivery performance metrics."
    )
    async def _analyze_shipping_performance(
        self, 
        context: RunContextWrapper[AgentContext], 
        carrier_id: str = None,
        time_period: str = "current"  # Options: current, last_month, last_quarter
    ) -> Dict[str, Any]:
        """
        Analyze shipping and delivery performance
        
        Args:
            context: Agent context wrapper
            carrier_id: Optional specific carrier ID
            time_period: Time period for analysis
            
        Returns:
            Dictionary containing shipping performance analysis
        """
        try:
            logistics_data = self.data_manager.get_logistics_data()
            
            # Check if shipping data exists
            if "shipping" not in logistics_data:
                return {"error": "No shipping data available"}
            
            shipping_data = logistics_data["shipping"]
            
            # Filter by time period if needed
            if time_period != "current" and "periods" in shipping_data:
                if time_period in shipping_data["periods"]:
                    shipping_data = shipping_data["periods"][time_period]
                else:
                    return {"error": f"Time period '{time_period}' not found in shipping data"}
            
            # Filter by carrier if specified
            if carrier_id:
                carrier_data = [item for item in shipping_data.get("carriers", []) if item.get("carrier_id") == carrier_id]
                if not carrier_data:
                    return {"error": f"No shipping data for carrier '{carrier_id}'"}
                return {"carrier_performance": carrier_data[0]}
            
            # Calculate overall metrics
            on_time_deliveries = shipping_data.get("on_time_deliveries", 0)
            total_deliveries = shipping_data.get("total_deliveries", 0)
            average_delivery_time = shipping_data.get("average_delivery_time", 0)
            
            on_time_percentage = 0
            if total_deliveries > 0:
                on_time_percentage = (on_time_deliveries / total_deliveries) * 100
            
            return {
                "total_deliveries": total_deliveries,
                "on_time_deliveries": on_time_deliveries,
                "on_time_percentage": round(on_time_percentage, 2),
                "average_delivery_time": average_delivery_time,
                "carriers": shipping_data.get("carriers", [])
            }
        except Exception as e:
            logger.error(f"Error analyzing shipping performance: {str(e)}")
            return {"error": str(e)}
    
    @function_tool(
        name_override="evaluate_supply_chain",
        description_override="Evaluate supply chain efficiency and identify bottlenecks."
    )
    async def _evaluate_supply_chain(
        self, 
        context: RunContextWrapper[AgentContext],
        aspect: str = "overall"  # Options: overall, lead_times, costs, suppliers
    ) -> Dict[str, Any]:
        """
        Evaluate supply chain efficiency and identify bottlenecks
        
        Args:
            context: Agent context wrapper
            aspect: Specific aspect of the supply chain to evaluate
            
        Returns:
            Dictionary containing supply chain evaluation
        """
        try:
            logistics_data = self.data_manager.get_logistics_data()
            
            # Check if supply chain data exists
            if "supply_chain" not in logistics_data:
                return {"error": "No supply chain data available"}
            
            supply_chain_data = logistics_data["supply_chain"]
            
            # Evaluate based on specified aspect
            if aspect == "overall":
                return {
                    "efficiency_score": supply_chain_data.get("efficiency_score", 0),
                    "bottlenecks": supply_chain_data.get("bottlenecks", []),
                    "improvement_areas": supply_chain_data.get("improvement_areas", [])
                }
            elif aspect == "lead_times" and "lead_times" in supply_chain_data:
                return {"lead_times": supply_chain_data["lead_times"]}
            elif aspect == "costs" and "costs" in supply_chain_data:
                return {"costs": supply_chain_data["costs"]}
            elif aspect == "suppliers" and "suppliers" in supply_chain_data:
                return {"suppliers": supply_chain_data["suppliers"]}
            else:
                return {"error": f"Supply chain aspect '{aspect}' not available"}
        except Exception as e:
            logger.error(f"Error evaluating supply chain: {str(e)}")
            return {"error": str(e)}