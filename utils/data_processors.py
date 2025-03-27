"""
Data processing utilities
"""
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

def process_marketing_data(data: Union[Dict[str, Any], str, bytes]) -> Dict[str, Any]:
    """
    Process marketing data from source format to internal format
    
    Args:
        data: Raw marketing data (JSON, CSV, or Excel)
        
    Returns:
        Processed marketing data dictionary
    """
    try:
        # If data is already a dictionary, return it
        if isinstance(data, dict):
            return data
        
        # Convert to string if bytes
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        # If data is CSV string
        if isinstance(data, str) and ',' in data:
            df = pd.read_csv(pd.StringIO(data))
            return _convert_marketing_df_to_dict(df)
        
        # If data is Excel content
        try:
            df = pd.read_excel(data)
            return _convert_marketing_df_to_dict(df)
        except Exception:
            logger.warning("Failed to parse data as Excel")
        
        # Default fallback
        return {"error": "Unsupported data format for marketing data"}
    except Exception as e:
        logger.error(f"Error processing marketing data: {str(e)}")
        return {"error": str(e)}

def _convert_marketing_df_to_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Convert marketing DataFrame to dictionary
    
    Args:
        df: Marketing data DataFrame
        
    Returns:
        Dictionary format of marketing data
    """
    result = {}
    
    # Check if DataFrame has expected columns
    if 'campaign_id' in df.columns and 'campaign_name' in df.columns:
        # Process campaign data
        campaigns = []
        for _, row in df.iterrows():
            campaign = {col: row[col] for col in df.columns if pd.notna(row[col])}
            campaigns.append(campaign)
        
        result['campaigns'] = campaigns
    
    # Check for other marketing metrics
    metrics_columns = [
        'total_marketing_spend', 'customer_acquisition_cost', 
        'brand_awareness_score', 'conversion_rate'
    ]
    
    for col in metrics_columns:
        if col in df.columns:
            # Get the first non-NaN value for each metric
            value = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            if value is not None:
                result[col] = value
    
    # Process channel performance if available
    channel_columns = ['channel', 'spend', 'roi', 'engagement_rate']
    if all(col in df.columns for col in channel_columns[:2]):
        channels = {}
        channel_df = df[['channel'] + [c for c in channel_columns[1:] if c in df.columns]].dropna(subset=['channel'])
        
        for _, row in channel_df.iterrows():
            channel_name = row['channel']
            channels[channel_name] = {col: row[col] for col in channel_columns[1:] if col in df.columns and pd.notna(row[col])}
        
        if channels:
            result['channel_performance'] = channels
    
    return result

def process_sales_data(data: Union[Dict[str, Any], str, bytes]) -> Dict[str, Any]:
    """
    Process sales data from source format to internal format
    
    Args:
        data: Raw sales data (JSON, CSV, or Excel)
        
    Returns:
        Processed sales data dictionary
    """
    try:
        # If data is already a dictionary, return it
        if isinstance(data, dict):
            return data
        
        # Convert to string if bytes
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        # If data is CSV string
        if isinstance(data, str) and ',' in data:
            df = pd.read_csv(pd.StringIO(data))
            return _convert_sales_df_to_dict(df)
        
        # If data is Excel content
        try:
            df = pd.read_excel(data)
            return _convert_sales_df_to_dict(df)
        except Exception:
            logger.warning("Failed to parse data as Excel")
        
        # Default fallback
        return {"error": "Unsupported data format for sales data"}
    except Exception as e:
        logger.error(f"Error processing sales data: {str(e)}")
        return {"error": str(e)}

def _convert_sales_df_to_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Convert sales DataFrame to dictionary
    
    Args:
        df: Sales data DataFrame
        
    Returns:
        Dictionary format of sales data
    """
    result = {}
    
    # Check for product data
    if 'product_id' in df.columns and 'product_name' in df.columns:
        products = []
        product_columns = ['product_id', 'product_name', 'revenue', 'units', 'growth']
        
        for _, row in df.iterrows():
            product = {col: row[col] for col in product_columns if col in df.columns and pd.notna(row[col])}
            if product:
                products.append(product)
        
        if products:
            result['products'] = products
    
    # Check for region data
    if 'region_id' in df.columns and 'region_name' in df.columns:
        regions = []
        region_columns = ['region_id', 'region_name', 'revenue', 'growth']
        
        for _, row in df.iterrows():
            region = {col: row[col] for col in region_columns if col in df.columns and pd.notna(row[col])}
            if region:
                regions.append(region)
        
        if regions:
            result['regions'] = regions
    
    # Check for sales rep data
    if 'rep_id' in df.columns and 'rep_name' in df.columns:
        reps = []
        rep_columns = ['rep_id', 'rep_name', 'revenue', 'deals_closed', 'quota_attainment']
        
        for _, row in df.iterrows():
            rep = {col: row[col] for col in rep_columns if col in df.columns and pd.notna(row[col])}
            if rep:
                reps.append(rep)
        
        if reps:
            result['sales_reps'] = reps
    
    # Check for forecast data
    if 'forecast_period' in df.columns and 'revenue_forecast' in df.columns:
        forecasts = {}
        forecast_df = df[['forecast_period', 'revenue_forecast', 'growth_percentage']].dropna(subset=['forecast_period'])
        
        for _, row in forecast_df.iterrows():
            period = row['forecast_period']
            forecasts[period] = {
                'revenue_forecast': row['revenue_forecast'],
                'growth_percentage': row.get('growth_percentage', 0)
            }
        
        if forecasts:
            result['forecasts'] = forecasts
    
    # Check for overall metrics
    metrics_columns = [
        'total_revenue', 'total_units', 'avg_deal_size', 
        'conversion_rate', 'sales_cycle_days'
    ]
    
    for col in metrics_columns:
        if col in df.columns:
            # Get the first non-NaN value for each metric
            value = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
            if value is not None:
                result[col] = value
    
    return result

def process_logistics_data(data: Union[Dict[str, Any], str, bytes]) -> Dict[str, Any]:
    """
    Process logistics data from source format to internal format
    
    Args:
        data: Raw logistics data (JSON, CSV, or Excel)
        
    Returns:
        Processed logistics data dictionary
    """
    try:
        # If data is already a dictionary, return it
        if isinstance(data, dict):
            return data
        
        # Convert to string if bytes
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        # If data is CSV string
        if isinstance(data, str) and ',' in data:
            df = pd.read_csv(pd.StringIO(data))
            return _convert_logistics_df_to_dict(df)
        
        # If data is Excel content
        try:
            df = pd.read_excel(data)
            return _convert_logistics_df_to_dict(df)
        except Exception:
            logger.warning("Failed to parse data as Excel")
        
        # Default fallback
        return {"error": "Unsupported data format for logistics data"}
    except Exception as e:
        logger.error(f"Error processing logistics data: {str(e)}")
        return {"error": str(e)}

def _convert_logistics_df_to_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Convert logistics DataFrame to dictionary
    
    Args:
        df: Logistics data DataFrame
        
    Returns:
        Dictionary format of logistics data
    """
    result = {}
    
    # Check for inventory data
    if 'product_id' in df.columns and 'warehouse_id' in df.columns and 'quantity' in df.columns:
        inventory = []
        inventory_columns = [
            'product_id', 'product_name', 'warehouse_id', 
            'quantity', 'unit_cost', 'status'
        ]
        
        for _, row in df.iterrows():
            item = {col: row[col] for col in inventory_columns if col in df.columns and pd.notna(row[col])}
            if item:
                inventory.append(item)
        
        if inventory:
            result['inventory'] = inventory
    
    # Check for warehouse data
    if 'warehouse_id' in df.columns and 'capacity' in df.columns:
        warehouses = []
        warehouse_columns = [
            'warehouse_id', 'name', 'location', 
            'capacity', 'utilization'
        ]
        
        for _, row in df.iterrows():
            warehouse = {col: row[col] for col in warehouse_columns if col in df.columns and pd.notna(row[col])}
            if warehouse:
                warehouses.append(warehouse)
        
        if warehouses:
            result['warehouses'] = warehouses
    
    # Check for shipping data
    if 'carrier_id' in df.columns and 'deliveries' in df.columns:
        carriers = []
        carrier_columns = [
            'carrier_id', 'name', 'deliveries', 
            'on_time_percentage', 'average_cost'
        ]
        
        for _, row in df.iterrows():
            carrier = {col: row[col] for col in carrier_columns if col in df.columns and pd.notna(row[col])}
            if carrier:
                carriers.append(carrier)
        
        if carriers:
            result['shipping'] = {
                'carriers': carriers
            }
            
            # Add overall shipping metrics if available
            shipping_metrics = [
                'total_deliveries', 'on_time_deliveries', 'average_delivery_time'
            ]
            
            for metric in shipping_metrics:
                if metric in df.columns:
                    value = df[metric].dropna().iloc[0] if not df[metric].dropna().empty else None
                    if value is not None:
                        result['shipping'][metric] = value
    
    # Check for supply chain data
    supply_chain_columns = ['efficiency_score', 'bottleneck', 'improvement_area']
    if any(col in df.columns for col in supply_chain_columns):
        supply_chain = {}
        
        # Add efficiency score if available
        if 'efficiency_score' in df.columns:
            value = df['efficiency_score'].dropna().iloc[0] if not df['efficiency_score'].dropna().empty else None
            if value is not None:
                supply_chain['efficiency_score'] = value
        
        # Add bottlenecks if available
        if 'bottleneck' in df.columns:
            bottlenecks = df['bottleneck'].dropna().tolist()
            if bottlenecks:
                supply_chain['bottlenecks'] = bottlenecks
        
        # Add improvement areas if available
        if 'improvement_area' in df.columns:
            areas = df['improvement_area'].dropna().tolist()
            if areas:
                supply_chain['improvement_areas'] = areas
        
        # Add lead times if available
        if 'product_id' in df.columns and 'lead_time' in df.columns:
            lead_times = {}
            lead_time_df = df[['product_id', 'lead_time']].dropna()
            
            for _, row in lead_time_df.iterrows():
                lead_times[row['product_id']] = row['lead_time']
            
            if lead_times:
                supply_chain['lead_times'] = lead_times
        
        # Add costs if available
        cost_columns = ['cost_category', 'cost_amount']
        if all(col in df.columns for col in cost_columns):
            costs = {}
            cost_df = df[cost_columns].dropna()
            
            for _, row in cost_df.iterrows():
                costs[row['cost_category']] = row['cost_amount']
            
            if costs:
                supply_chain['costs'] = costs
        
        # Add suppliers if available
        if 'supplier_id' in df.columns and 'supplier_name' in df.columns:
            suppliers = []
            supplier_columns = [
                'supplier_id', 'supplier_name', 'reliability_score', 
                'lead_time', 'cost_index'
            ]
            
            for _, row in df.iterrows():
                supplier = {}
                for col in supplier_columns:
                    if col in df.columns and pd.notna(row[col]):
                        # Rename columns to remove 'supplier_' prefix
                        new_key = col.replace('supplier_', '')
                        supplier[new_key] = row[col]
                
                if supplier:
                    suppliers.append(supplier)
            
            if suppliers:
                supply_chain['suppliers'] = suppliers
        
        if supply_chain:
            result['supply_chain'] = supply_chain
    
    return result

def process_collection_data(data: Union[Dict[str, Any], str, bytes]) -> Dict[str, Any]:
    """
    Process collection data from source format to internal format
    
    Args:
        data: Raw collection data (JSON, CSV, or Excel)
        
    Returns:
        Processed collection data dictionary
    """
    try:
        # If data is already a dictionary, return it
        if isinstance(data, dict):
            return data
        
        # Convert to string if bytes
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        # If data is CSV string
        if isinstance(data, str) and ',' in data:
            df = pd.read_csv(pd.StringIO(data))
            return _convert_collection_df_to_dict(df)
        
        # If data is Excel content
        try:
            df = pd.read_excel(data)
            return _convert_collection_df_to_dict(df)
        except Exception:
            logger.warning("Failed to parse data as Excel")
        
        # Default fallback
        return {"error": "Unsupported data format for collection data"}
    except Exception as e:
        logger.error(f"Error processing collection data: {str(e)}")
        return {"error": str(e)}

def _convert_collection_df_to_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Convert collection DataFrame to dictionary
    
    Args:
        df: Collection data DataFrame
        
    Returns:
        Dictionary format of collection data
    """
    result = {}
    
    # Check for invoice data
    if 'invoice_id' in df.columns and 'customer_id' in df.columns and 'amount_due' in df.columns:
        invoices = []
        invoice_columns = [
            'invoice_id', 'customer_id', 'customer_name', 
            'amount_due', 'due_date', 'days_outstanding', 'status'
        ]
        
        for _, row in df.iterrows():
            invoice = {col: row[col] for col in invoice_columns if col in df.columns and pd.notna(row[col])}
            if invoice:
                invoices.append(invoice)
        
        if invoices:
            result['accounts_receivable'] = {
                'invoices': invoices
            }
            
            # Calculate aging buckets
            if 'days_outstanding' in df.columns and 'amount_due' in df.columns:
                current = df[df['days_outstanding'] <= 0]['amount_due'].sum()
                days_1_30 = df[(df['days_outstanding'] > 0) & (df['days_outstanding'] <= 30)]['amount_due'].sum()
                days_31_60 = df[(df['days_outstanding'] > 30) & (df['days_outstanding'] <= 60)]['amount_due'].sum()
                days_61_90 = df[(df['days_outstanding'] > 60) & (df['days_outstanding'] <= 90)]['amount_due'].sum()
                over_90 = df[df['days_outstanding'] > 90]['amount_due'].sum()
                
                result['accounts_receivable']['aging'] = {
                    'current': current,
                    '1_30': days_1_30,
                    '31_60': days_31_60,
                    '61_90': days_61_90,
                    'over_90': over_90
                }
                
                # Add total AR and overdue
                total_ar = df['amount_due'].sum()
                total_overdue = df[df['days_outstanding'] > 0]['amount_due'].sum()
                
                result['accounts_receivable']['total_ar'] = total_ar
                result['accounts_receivable']['total_overdue'] = total_overdue
                
                # Calculate average days outstanding
                if not df.empty:
                    avg_days = df['days_outstanding'].mean()
                    result['accounts_receivable']['average_days_outstanding'] = round(avg_days, 1)
    
    # Check for payment trends data
    if 'collection_efficiency' in df.columns or 'average_days_to_pay' in df.columns:
        payment_trends = {}
        
        # Get overall metrics
        payment_metrics = [
            'collection_efficiency', 'average_days_to_pay'
        ]
        
        for metric in payment_metrics:
            if metric in df.columns:
                value = df[metric].dropna().iloc[0] if not df[metric].dropna().empty else None
                if value is not None:
                    payment_trends[metric] = value
        
        # Add payment methods if available
        if 'payment_method' in df.columns and 'payment_percentage' in df.columns:
            payment_methods = {}
            method_data = df[['payment_method', 'payment_percentage']].dropna()
            
            for _, row in method_data.iterrows():
                payment_methods[row['payment_method']] = row['payment_percentage']
            
            if payment_methods:
                payment_trends['payment_methods'] = payment_methods
        
        # Add trend by month if available
        if 'month' in df.columns and 'collected' in df.columns and 'outstanding' in df.columns:
            trend_by_month = []
            month_data = df[['month', 'collected', 'outstanding', 'efficiency']].dropna(subset=['month'])
            
            for _, row in month_data.iterrows():
                trend = {col: row[col] for col in ['month', 'collected', 'outstanding', 'efficiency'] 
                        if col in df.columns and pd.notna(row[col])}
                if trend:
                    trend_by_month.append(trend)
            
            if trend_by_month:
                payment_trends['trend_by_month'] = trend_by_month
        
        # Add segment data if available
        if 'customer_segment' in df.columns and 'average_days_to_pay' in df.columns:
            segments = {}
            segment_data = df[['customer_segment', 'average_days_to_pay', 'collection_efficiency']].dropna(subset=['customer_segment'])
            
            for _, row in segment_data.iterrows():
                segment_name = row['customer_segment']
                segments[segment_name] = {
                    'average_days_to_pay': row['average_days_to_pay'] if pd.notna(row['average_days_to_pay']) else None,
                    'collection_efficiency': row['collection_efficiency'] if pd.notna(row['collection_efficiency']) else None
                }
            
            if segments:
                payment_trends['segments'] = segments
        
        if payment_trends:
            result['payment_trends'] = payment_trends
        
    # Check for risk assessment data
    if 'risk_score' in df.columns:
        risk_assessment = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': []
        }
        
        # Group by risk level
        high_risk = df[df['risk_score'] >= 70]
        medium_risk = df[(df['risk_score'] >= 40) & (df['risk_score'] < 70)]
        low_risk = df[df['risk_score'] < 40]
        
        # Process high risk
        for _, row in high_risk.iterrows():
            risk_assessment['high_risk'].append({
                'customer_id': row.get('customer_id', ''),
                'customer_name': row.get('customer_name', ''),
                'outstanding_amount': row.get('amount_due', 0),
                'days_overdue': row.get('days_outstanding', 0),
                'risk_score': row.get('risk_score', 0)
            })
        
        # Process medium risk
        for _, row in medium_risk.iterrows():
            risk_assessment['medium_risk'].append({
                'customer_id': row.get('customer_id', ''),
                'customer_name': row.get('customer_name', ''),
                'outstanding_amount': row.get('amount_due', 0),
                'days_overdue': row.get('days_outstanding', 0),
                'risk_score': row.get('risk_score', 0)
            })
        
        # Process low risk
        for _, row in low_risk.iterrows():
            risk_assessment['low_risk'].append({
                'customer_id': row.get('customer_id', ''),
                'customer_name': row.get('customer_name', ''),
                'outstanding_amount': row.get('amount_due', 0),
                'days_overdue': row.get('days_outstanding', 0),
                'risk_score': row.get('risk_score', 0)
            })
        
        if any(risk_assessment.values()):
            result['risk_assessment'] = risk_assessment
    
    return result