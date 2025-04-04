"""
Sales specialist agent implementation
"""
import logging
from typing import Dict, Any, List, Optional

# Import from our common imports module
from .common_imports import function_tool, RunContextWrapper
from .base_agent import BaseAgent, AgentContext
import pandas as pd
from datetime import datetime, timedelta


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
            self._forecast_sales,
            self._calculate_average_ticket,
            self._analyze_top_sellers,
            self._calculate_conversion_rate,
            self._analyze_customer_retention,
            self._analyze_sales_channels,
            self._analyze_sales_cycle,
            self.get_sales_data
        ]
        
        super().__init__("Sales Agent", data_manager, description, instructions, tools)
        self.sales_df = None

    def _load_and_prepare_data(self):
        if self.sales_df is None:
            sales_data = self.data_manager.get_sales_data()
            print(f"DEBUG: Raw sales data type: {type(sales_data)}")
            print(f"DEBUG: Raw sales data keys: {sales_data.keys() if isinstance(sales_data, dict) else 'Not a dict'}")
            if isinstance(sales_data, dict) and 'raw_data' in sales_data:
                self.sales_df = pd.DataFrame(sales_data)
            else:
                print("ERROR: Expected sales_data to be a dictionary with 'raw_data' key")
                self.sales_df = pd.DataFrame()

            print(f"DEBUG: sales_df columns: {self.sales_df.columns}")
            print(f"DEBUG: sales_df shape: {self.sales_df.shape}")

            if 'FECHA' in self.sales_df.columns:
                self.sales_df['FECHA'] = pd.to_datetime(self.sales_df['FECHA'], errors='coerce')
            if 'IMPORTE_TOTAL' in self.sales_df.columns:
                self.sales_df['IMPORTE_TOTAL'] = self.sales_df['IMPORTE_TOTAL'].astype(float)
    @function_tool(
        name_override="get_sales_metrics",
        description_override="Get sales metrics from the latest data."
    )
    async def _get_sales_metrics(
        self, 
        context: RunContextWrapper[AgentContext], 
        metric_name: str = None) -> str:
        """
        Get sales metrics from the latest data
        
        Args:
            context: Agent context wrapper
            metric_name: Optional specific metric name to retrieve
            
        Returns:
            Dictionary containing the requested sales metrics
        """
        try:
            result = self.data_manager.get_sales_data()

            if metric_name:
                if metric_name in result:
                    return {metric_name: result[metric_name]}
                else:
                    return {"error": f"Metric '{metric_name}' not found in sales data"}
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
        dimension: str = "overall",  # Options: overall, by_product, by_customer, by_region, by_rep
        top_n: int = 5
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
            
            if dimension == "overall":
                return {
                    "total_revenue": sales_data['total_revenue'],
                    "total_units": sales_data['total_units'],
                    "avg_deal_size": sales_data['avg_deal_size'],
                    "total_sales": sales_data['total_sales']
                }
            elif dimension in ["by_product", "by_customer", "by_region", "by_rep"]:
                data = sales_data[dimension]
                sorted_data = sorted(data, key=lambda x: x['revenue'], reverse=True)
                return {
                    "top_performers": sorted_data[:top_n],
                    "total_count": len(data)
                }
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
        
    @function_tool(
    name_override="calculate_average_ticket",
    description_override="Calculate the average ticket value of customers."
    )
    async def _calculate_average_ticket(self, context: RunContextWrapper[AgentContext]) -> Dict[str, Any]:
        self._load_and_prepare_data()
        avg_ticket = self.sales_df['IMPORTE_TOTAL'].mean()
        return {"average_ticket": avg_ticket}
    
    @function_tool(
        name_override="analyze_top_sellers",
        description_override="Analyze top-performing sellers and their performance."
    )
    async def _analyze_top_sellers(self, context: RunContextWrapper[AgentContext], top_n: int = 5) -> Dict[str, Any]:
        try:
            print("DEBUG: Entering _analyze_top_sellers function")
            sales_data = self.data_manager.get_sales_data()
            print(f"DEBUG: Sales data keys: {sales_data.keys()}")

            if 'raw_data' in sales_data and isinstance(sales_data['raw_data'], list):
                # Assuming raw_data is a list of dictionaries
                df = pd.DataFrame(sales_data['raw_data'])
                print(f"DEBUG: Raw data columns: {df.columns}")
                if 'NOMBRE_ASESOR' in df.columns and 'IMPORTE_TOTAL' in df.columns:
                    top_sellers = df.groupby('NOMBRE_ASESOR')['IMPORTE_TOTAL'].sum().nlargest(top_n)
                    return {"top_sellers": top_sellers.to_dict()}
                else:
                    # If the expected columns are not present, check for alternatives
                    seller_column = next((col for col in df.columns if 'ASESOR' in col.upper() or 'VENDEDOR' in col.upper()), None)
                    amount_column = next((col for col in df.columns if 'IMPORTE' in col.upper() or 'VENTA' in col.upper()), None)
                    
                    if seller_column and amount_column:
                        top_sellers = df.groupby(seller_column)[amount_column].sum().nlargest(top_n)
                        return {"top_sellers": top_sellers.to_dict()}
                    else:
                        return {"error": "No se encontraron columnas adecuadas para analizar los mejores vendedores"}
            elif 'aggregations' in sales_data and 'by_rep' in sales_data['aggregations']:
                print(f"DEBUG: Aggregation keys: {sales_data['aggregations'].keys()}")
                # If there's already an aggregation by rep, use it
                top_sellers = pd.Series(sales_data['aggregations']['by_rep']).nlargest(top_n)
                return {"top_sellers": top_sellers.to_dict()}
            else:
                return {"error": "No se encontraron datos adecuados para analizar los mejores vendedores"}
        except Exception as e:
            logger.error(f"Error analyzing top sellers: {str(e)}")
            return {"error": str(e)}
    
    @function_tool(
        name_override="analyze_customer_retention",
        description_override="Analyze customer retention rate and lifetime value."
    )
    async def _analyze_customer_retention(self, context: RunContextWrapper[AgentContext]) -> Dict[str, Any]:
        self._load_and_prepare_data()
        # This is a simplified version and would need more sophisticated logic in a real scenario
        repeat_customers = self.sales_df['CLIENTE'].value_counts()
        retention_rate = (repeat_customers > 1).sum() / len(repeat_customers) * 100
        return {"retention_rate": retention_rate}
    
    @function_tool(
        name_override="analyze_sales_channels",
        description_override="Analyze the performance of different sales channels."
    )
    async def _analyze_sales_channels(self, context: RunContextWrapper[AgentContext]) -> Dict[str, Any]:
        self._load_and_prepare_data()
        channel_performance = self.sales_df.groupby('VENDEDOR')['IMPORTE_TOTAL'].sum().sort_values(ascending=False)
        return {"channel_performance": channel_performance.to_dict()}
    
        if "total de ventas" in question.lower():
            print("DEBUG: Fetching total sales metrics")
            result = await self._get_sales_metrics(context)
            print(f"DEBUG: Received sales metrics: {result}")
            return f"El total de ventas es {result.get('total_revenue', 'N/A'):.2f}."
        elif "ticket promedio" in question.lower():
            print("DEBUG: Calculating average ticket")
            result = await self._calculate_average_ticket(context)
            print(f"DEBUG: Received average ticket: {result}")
            return f"El ticket promedio de nuestros clientes es {result.get('average_ticket', 'N/A'):.2f}."
        elif any(keyword in question.lower() for keyword in ["mejores vendedores", "top vendedores", "vendedores destacados"]):
            print("DEBUG: Analyzing top sellers")
            result = await self._analyze_top_sellers(context)
            print(f"DEBUG: Received top sellers data: {result}")
            if "error" in result:
                print(f"DEBUG: Error in _analyze_top_sellers: {result['error']}")
                return f"Lo siento, no pude obtener información sobre los mejores vendedores: {result['error']}"
            top_sellers = result.get('top_sellers', {})
            if not top_sellers:
                print("DEBUG: No top sellers data found")
                return "Lo siento, no pude obtener información sobre los mejores vendedores."
            response = "Los mejores vendedores son:\n"
            for seller, sales in top_sellers.items():
                response += f"- {seller}: {sales:.2f}\n"
            return response
        elif "tasa de retención" in question.lower():
            logger.info("Analyzing customer retention")
            result = await self._analyze_customer_retention(context)
            logger.info(f"Received retention rate: {result}")
            return f"La tasa de retención de clientes es {result.get('retention_rate', 'N/A'):.2f}%."
        elif "canales de venta" in question.lower():
            logger.info("Analyzing sales channels")
            result = await self._analyze_sales_channels(context)
            logger.info(f"Received channel performance data: {result}")
            channel_performance = result.get('channel_performance', {})
            if not channel_performance:
                return "Lo siento, no pude obtener información sobre los canales de venta."
            response = "El rendimiento de los canales de venta es:\n"
            for channel, sales in channel_performance.items():
                response += f"- {channel}: {sales:.2f}\n"
            return response
        else:
            print(f"DEBUG: Unable to answer question: {question}")
            return "Lo siento, no puedo responder a esa pregunta con la información disponible."