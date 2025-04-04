"""
Data manager for fetching and caching data from various sources
"""
import os
import json
import logging
import datetime
import pandas as pd
from typing import Dict, Any, Optional
import traceback


from utils.data_processors import (
    process_marketing_data,
    process_sales_data,
    process_logistics_data,
    process_collection_data
)
import config

logger = logging.getLogger(__name__)

class DataManager:
    """
    Data manager for fetching and caching data from various sources
    """
    def __init__(self):
        """Initialize the data manager"""
        self.cache_dir = config.DATA_CACHE_DIR
        self._marketing_data = None
        self._sales_data = None
        self._logistics_data = None
        self._collection_data = None
        
        # Load cached data if available
        self._load_cached_data()
    
    def _load_cached_data(self):
        """Load data from cache files if they exist"""
        data_types = ['marketing', 'sales', 'logistics', 'collection']
        
        for data_type in data_types:
            cache_file = os.path.join(self.cache_dir, f"{data_type}_data.json")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    
                    # Convert list format to proper dictionary structure for sales data
                    if data_type == 'sales' and isinstance(data, list):
                        data = {
                            "raw_data": data,
                            "aggregations": {},
                            "kpis": {
                                "total_ventas": sum(item.get('IMPORTE_TOTAL', 0) for item in data),
                                "total_transacciones": len(data),
                                "ultima_actualizacion": datetime.datetime.now().isoformat()
                            }
                        }
                    
                    # Set the data to the appropriate attribute
                    setattr(self, f"_{data_type}_data", data)
                    logger.info(f"Loaded cached {data_type} data from {cache_file}")
                except Exception as e:
                    logger.error(f"Error loading cached {data_type} data: {str(e)}")
    
    def _save_cached_data(self, data_type: str, data: Dict[str, Any]):
        """
        Save data to cache file
        
        Args:
            data_type: Type of data (marketing, sales, etc.)
            data: Data to cache
        """
        cache_file = os.path.join(self.cache_dir, f"{data_type}_data.json")
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {data_type} data to cache file {cache_file}")
        except Exception as e:
            logger.error(f"Error saving {data_type} data to cache: {str(e)}")
    
    def get_marketing_data(self) -> Dict[str, Any]:
        """
        Get marketing data
        
        Returns:
            Marketing data dictionary
        """
        if self._marketing_data is None:
            self.refresh_marketing_data()
        return self._marketing_data or {}
    
    def get_sales_data(self, filters=None, aggregation=None):
        print(f"DEBUG: Solicitando datos de ventas. filters={filters}, aggregation={aggregation}")
        
        if not self._sales_data:
            # Si no hay datos cargados, cargar datos de muestra
            self._sales_data = self._get_sample_sales_data()
    
        print(f"DEBUG: Tipo de self._sales_data: {type(self._sales_data)}")
        print(f"DEBUG: Claves en self._sales_data: {self._sales_data.keys() if isinstance(self._sales_data, dict) else 'No es un diccionario'}")
        
        # Asegurarse de que _sales_data tenga la estructura esperada
        if not isinstance(self._sales_data, dict) or 'raw_data' not in self._sales_data:
            print("ERROR: self._sales_data no tiene la estructura esperada")
            return {"error": "Estructura de datos inválida"}
        
        # Crear DataFrame de vendedores
        df_vendedores = pd.DataFrame(self._sales_data['raw_data'])
        
        if 'NOMBRE_ASESOR' in df_vendedores.columns and 'IMPORTE_TOTAL' in df_vendedores.columns:
            vendedores_analysis = df_vendedores.groupby('NOMBRE_ASESOR').agg({
                'IMPORTE_TOTAL': ['sum', 'mean', 'count'],
                'CLIENTE': 'nunique'
            }).reset_index()
            
            vendedores_analysis.columns = ['NOMBRE_ASESOR', 'VENTAS_TOTALES', 'VENTA_PROMEDIO', 'NUMERO_VENTAS', 'CLIENTES_UNICOS']
            vendedores_analysis = vendedores_analysis.sort_values('VENTAS_TOTALES', ascending=False)
            
            # Añadir este análisis a las agregaciones existentes
            self._sales_data['aggregations']['analisis_vendedores'] = vendedores_analysis.to_dict('records')
            
            # Añadir KPIs relacionados con vendedores
            self._sales_data['kpis']['top_vendedor'] = vendedores_analysis.iloc[0]['NOMBRE_ASESOR']
            self._sales_data['kpis']['total_vendedores'] = len(vendedores_analysis)
            self._sales_data['kpis']['promedio_ventas_por_vendedor'] = vendedores_analysis['VENTAS_TOTALES'].mean()
        result = self._filter_and_aggregate_sales(filters, aggregation)
        if isinstance(result, dict) and 'kpis' not in result:
            result['kpis'] = self._sales_data('kpis',{})
        return result

    def _preprocess_sales_data(self, df):
        """
        Preprocesa los datos de ventas para un acceso y análisis eficiente
        
        Args:
            df: DataFrame de pandas con los datos de ventas
            
        Returns:
            Diccionario con datos procesados y métricas precalculadas
        """
        print(f"DEBUG: Iniciando preprocesamiento de datos, shape={df.shape}")
        
        # Asegurar que las fechas estén en formato datetime
        if 'FECHA' in df.columns:
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
            
            # Añadir columnas calculadas útiles
            df['MES'] = df['FECHA'].dt.month
            df['AÑO'] = df['FECHA'].dt.year
            df['TRIMESTRE'] = df['FECHA'].dt.quarter
            df['SEMANA'] = df['FECHA'].dt.isocalendar().week
            
            print(f"DEBUG: Fechas procesadas y columnas temporales añadidas")
        
        # Asegurar que los valores numéricos sean de tipo float
        if 'IMPORTE_TOTAL' in df.columns:
            df['IMPORTE_TOTAL'] = pd.to_numeric(df['IMPORTE_TOTAL'], errors='coerce')
            print(f"DEBUG: IMPORTE_TOTAL convertido a numérico")
        
        if 'PRECIO_UNITARIO' in df.columns:
            df['PRECIO_UNITARIO'] = pd.to_numeric(df['PRECIO_UNITARIO'], errors='coerce')
        
        if 'CANTIDAD' in df.columns:
            df['CANTIDAD'] = pd.to_numeric(df['CANTIDAD'], errors='coerce')

        # Calcular el total de ventas
        total_ventas = df['IMPORTE_TOTAL'].sum() if 'IMPORTE_TOTAL' in df.columns else 0
        print(f"DEBUG: Total de ventas calculado: {total_ventas}")
        
        # Realizar agregaciones precalculadas para consultas comunes
        aggregations = {}
        print("DEBUG: Calculando agregaciones...")
        
        if 'VENDEDOR' in df.columns and 'IMPORTE_TOTAL' in df.columns:
            print("DEBUG: Calculando ventas_por_vendedor")
            vendedor_agg = df.groupby('VENDEDOR')['IMPORTE_TOTAL'].agg(['sum', 'count', 'mean']).reset_index()
            aggregations["ventas_por_vendedor"] = vendedor_agg.to_dict('records')
        
        if 'CLIENTE' in df.columns and 'IMPORTE_TOTAL' in df.columns:
            print("DEBUG: Calculando ventas_por_cliente")
            cliente_agg = df.groupby('CLIENTE')['IMPORTE_TOTAL'].agg(['sum', 'count', 'mean']).reset_index()
            aggregations["ventas_por_cliente"] = cliente_agg.to_dict('records')
        
        if all(col in df.columns for col in ['AÑO', 'MES', 'IMPORTE_TOTAL']):
            print("DEBUG: Calculando ventas_por_mes")
            # Agrupar por año y mes
            monthly_sales = df.groupby(['AÑO', 'MES'])['IMPORTE_TOTAL'].agg(['sum', 'count']).reset_index()
            aggregations["ventas_por_mes"] = monthly_sales.to_dict('records')
        
        if 'ARTICULO' in df.columns and 'IMPORTE_TOTAL' in df.columns:
            print("DEBUG: Calculando ventas_por_articulo")
            articulo_agg = df.groupby('ARTICULO')['IMPORTE_TOTAL'].agg(['sum', 'count']).reset_index()
            aggregations["ventas_por_articulo"] = articulo_agg.to_dict('records')
        
        if 'LINEA' in df.columns and 'IMPORTE_TOTAL' in df.columns:
            print("DEBUG: Calculando ventas_por_linea")
            linea_agg = df.groupby('LINEA')['IMPORTE_TOTAL'].agg(['sum', 'count']).reset_index()
            aggregations["ventas_por_linea"] = linea_agg.to_dict('records')
            
        # Agregar datos específicos para responder las preguntas de ventas
        if 'TIPO_CLIENTE' in df.columns and 'CLIENTE' in df.columns and 'IMPORTE_TOTAL' in df.columns:
            print("DEBUG: Calculando métricas por tipo de cliente")
            tipo_cliente_agg = df.groupby('TIPO_CLIENTE')['IMPORTE_TOTAL'].agg(['sum', 'count', 'mean']).reset_index()
            aggregations["ventas_por_tipo_cliente"] = tipo_cliente_agg.to_dict('records')
        
        # Para ciclo de ventas, agrupar por fecha
        if 'FECHA' in df.columns and 'CLASIFICACION' in df.columns:
            print("DEBUG: Analizando ciclo de ventas")
            # Filtrar solo ventas completadas
            ventas_df = df[df['CLASIFICACION'] == 'Ventas']
            
            ciclo_ventas_mensual = ventas_df.groupby(['AÑO', 'MES'])['IMPORTE_TOTAL'].agg(['sum', 'count', 'mean']).reset_index()
            aggregations["ciclo_ventas_mensual"] = ciclo_ventas_mensual.to_dict('records')
        
        # Para retención de clientes, necesitamos analizar transacciones repetidas
        if 'CLIENTE' in df.columns and 'FECHA' in df.columns:
            print("DEBUG: Calculando retención de clientes")
            # Conseguir primera y última compra de cada cliente
            cliente_compras = df.groupby('CLIENTE')['FECHA'].agg(['min', 'max', 'count']).reset_index()
            cliente_compras.columns = ['CLIENTE', 'primera_compra', 'ultima_compra', 'total_compras']
            
            # Calcular si los clientes son recurrentes (más de una compra)
            clientes_totales = cliente_compras.shape[0]
            clientes_recurrentes = cliente_compras[cliente_compras['total_compras'] > 1].shape[0]
            
            if clientes_totales > 0:
                tasa_retencion = (clientes_recurrentes / clientes_totales) * 100
            else:
                tasa_retencion = 0
                
            aggregations["retencion_clientes"] = {
                "clientes_totales": clientes_totales,
                "clientes_recurrentes": clientes_recurrentes,
                "tasa_retencion": tasa_retencion
            }
        
        # Calcular KPIs críticos
        current_date = datetime.datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # Filtrar datos del mes actual para KPIs actuales
        current_month_data = df[(df['AÑO'] == current_year) & (df['MES'] == current_month)] if 'AÑO' in df.columns and 'MES' in df.columns else pd.DataFrame()
        
        kpis = {
            "total_ventas": float(total_ventas),
            "ticket_promedio": float(df['IMPORTE_TOTAL'].mean()) if 'IMPORTE_TOTAL' in df.columns else 0,
            "total_transacciones": len(df),
            "total_clientes": df['CLIENTE'].nunique() if 'CLIENTE' in df.columns else 0,
            "total_vendedores": df['VENDEDOR'].nunique() if 'VENDEDOR' in df.columns else 0,
            "ventas_mes_actual": float(current_month_data['IMPORTE_TOTAL'].sum()) if not current_month_data.empty and 'IMPORTE_TOTAL' in current_month_data.columns else 0,
            "ultima_actualizacion": datetime.datetime.now().isoformat()
        }
        
        # Añadir datos de tendencia (últimos 6 meses si hay datos suficientes)
        if 'FECHA' in df.columns and 'IMPORTE_TOTAL' in df.columns:
            print("DEBUG: Calculando tendencia de últimos 6 meses")
            # Obtener los últimos 6 meses
            last_6_months = {}
            today = datetime.datetime.now()
            
            for i in range(6):
                target_date = today - datetime.timedelta(days=30 * i)
                month_key = f"{target_date.year}-{target_date.month:02d}"
                
                month_data = df[
                    (df['FECHA'].dt.year == target_date.year) & 
                    (df['FECHA'].dt.month == target_date.month)
                ]
                
                if not month_data.empty:
                    last_6_months[month_key] = {
                        "ventas": float(month_data['IMPORTE_TOTAL'].sum()),
                        "transacciones": len(month_data),
                        "clientes": month_data['CLIENTE'].nunique() if 'CLIENTE' in month_data else 0,
                        "ticket_promedio": float(month_data['IMPORTE_TOTAL'].mean()) if 'IMPORTE_TOTAL' in month_data.columns else 0
                    }
            
            kpis["tendencia_6_meses"] = last_6_months
        
        print(f"DEBUG: Preprocesamiento completado. Agregaciones: {len(aggregations)}, KPIs: {len(kpis)}")
        
        # Convertir el DataFrame a lista de diccionarios para formato raw_data
        raw_data = df.to_dict(orient='records')
        
        # Crear el diccionario con estructura correcta
        processed_data = {
            "raw_data": raw_data,  # Lista de diccionarios con todos los registros
            "aggregations": aggregations,  # Diccionario con agregaciones precalculadas
            "kpis": kpis  # Diccionario con KPIs precalculados
        }
        
        print(f"DEBUG: Estructura de datos procesados creada correctamente")
        return processed_data
    
    def _filter_and_aggregate_sales(self, filters=None, aggregation=None):
        """
        Aplica filtros y agregaciones a los datos de ventas
        """
        print(f"DEBUG _filter_and_aggregate_sales: Iniciando con filters={filters}, aggregation={aggregation}")
        print(f"DEBUG: Tipo de self._sales_data en _filter_and_aggregate_sales: {type(self._sales_data)}")

        # Format validation and conversion - single clean block
        if isinstance(self._sales_data, list):
            print("DEBUG: Converting list sales data to dictionary format")
            self._sales_data = {
                "raw_data": self._sales_data,
                "aggregations": {},
                "kpis": {"total_ventas": 0}
            }
        elif not isinstance(self._sales_data, dict):
            print("DEBUG: Invalid data format, initializing empty structure")
            self._sales_data = {
                "raw_data": [],
                "aggregations": {},
                "kpis": {"total_ventas": 0}
            }
        
        if not self._sales_data:
            print("DEBUG: self._sales_data está vacío")
            return {"error": "No hay datos de ventas disponibles"}
        if not self._sales_data:
            return {"error": "No hay datos de ventas disponibles"}
        
        # Si no hay filtros ni agregación, devolver los KPIs generales
        if not filters and not aggregation:
            return {
                "kpis": self._sales_data["kpis"],
                "data_summary": {
                    "total_records": len(self._sales_data["raw_data"]),
                    "aggregations_available": list(self._sales_data["aggregations"].keys())
                }
            }
        
        # Si hay una agregación específica y está precalculada, devolverla directamente
        if aggregation and not filters:
            if aggregation in self._sales_data["aggregations"]:
                return {
                    "aggregation": aggregation,
                    "data": self._sales_data["aggregations"][aggregation]
                }
        
        # Si hay filtros, necesitamos aplicarlos a los datos crudos
        if filters:
            # Verificar que raw_data es una lista
            raw_data = self._sales_data.get("raw_data", [])
            if not isinstance(raw_data, list):
                return {"error": "Los datos sin procesar no están en el formato esperado (lista)"}
            
            # Convertir datos crudos a DataFrame para filtrado eficiente
            import pandas as pd
            
            # Verificar que hay datos para procesar
            if not raw_data:
                return {
                    "filters": filters,
                    "aggregation": aggregation,
                    "result": "No hay datos disponibles para aplicar filtros",
                    "data": {}
                }
            
            try:
                df = pd.DataFrame(raw_data)
            except Exception as e:
                return {
                    "error": f"Error al convertir datos a DataFrame: {str(e)}",
                    "traceback": traceback.format_exc()
                }
            
            # Aplicar cada filtro
            for field, value in filters.items():
                if field in df.columns:
                    # Manejar diferentes tipos de filtros
                    if isinstance(value, list):
                        # Filtro por lista de valores
                        df = df[df[field].isin(value)]
                    elif isinstance(value, dict) and all(k in ['min', 'max'] for k in value.keys()):
                        # Filtro por rango
                        if 'min' in value and value['min'] is not None:
                            df = df[df[field] >= value['min']]
                        if 'max' in value and value['max'] is not None:
                            df = df[df[field] <= value['max']]
                    elif isinstance(value, dict) and 'regex' in value:
                        # Filtro por expresión regular
                        df = df[df[field].astype(str).str.contains(value['regex'], na=False)]
                    elif isinstance(value, dict) and 'date_range' in value:
                        # Filtro por rango de fechas
                        if field == 'FECHA' and 'from' in value['date_range'] and 'to' in value['date_range']:
                            try:
                                from_date = pd.to_datetime(value['date_range']['from'])
                                to_date = pd.to_datetime(value['date_range']['to'])
                                df = df[(df[field] >= from_date) & (df[field] <= to_date)]
                            except Exception as e:
                                logger.warning(f"Error al procesar rango de fechas: {str(e)}")
                    else:
                        # Filtro simple por valor exacto
                        df = df[df[field] == value]
            
            # Si después de filtrar no quedan datos, devolver resultado vacío
            if len(df) == 0:
                return {
                    "filters": filters,
                    "aggregation": aggregation,
                    "result": "No hay datos que cumplan con los filtros especificados",
                    "data": {}
                }
            
            # Si hay agregación, aplicarla a los datos filtrados
            if aggregation:
                try:
                    if aggregation == "por_vendedor" and "VENDEDOR" in df.columns and "IMPORTE_TOTAL" in df.columns:
                        result = df.groupby("VENDEDOR")["IMPORTE_TOTAL"].agg(['sum', 'count', 'mean']).reset_index()
                        return {
                            "filters": filters,
                            "aggregation": aggregation,
                            "data": result.to_dict(orient='records')
                        }
                    elif aggregation == "por_cliente" and "CLIENTE" in df.columns and "IMPORTE_TOTAL" in df.columns:
                        result = df.groupby("CLIENTE")["IMPORTE_TOTAL"].agg(['sum', 'count', 'mean']).reset_index()
                        return {
                            "filters": filters,
                            "aggregation": aggregation,
                            "data": result.to_dict(orient='records')
                        }
                    elif aggregation == "por_mes" and "FECHA" in df.columns and "IMPORTE_TOTAL" in df.columns:
                        # Asegurar que FECHA sea datetime
                        df['FECHA'] = pd.to_datetime(df['FECHA'])
                        df['MES'] = df['FECHA'].dt.month
                        df['AÑO'] = df['FECHA'].dt.year
                        result = df.groupby(['AÑO', 'MES'])['IMPORTE_TOTAL'].agg(['sum', 'count']).reset_index()
                        return {
                            "filters": filters,
                            "aggregation": aggregation,
                            "data": result.to_dict(orient='records')
                        }
                    else:
                        # Agregación no soportada
                        return {
                            "filters": filters,
                            "aggregation": aggregation,
                            "result": f"Agregación '{aggregation}' no soportada o faltan campos requeridos",
                            "data": df.to_dict(orient='records')
                        }
                except Exception as e:
                    return {
                        "error": f"Error al aplicar agregación: {str(e)}",
                        "traceback": traceback.format_exc()
                    }
            
            # Si no hay agregación, devolver los datos filtrados
            return {
                "filters": filters,
                "total_records": len(df),
                "data": df.to_dict(orient='records')
            }
        
        # Si llegamos aquí, la combinación de filtros y agregación no está soportada
        return {
            "error": "Combinación de filtros y agregación no soportada",
            "filters": filters,
            "aggregation": aggregation
        }
    
    def get_logistics_data(self) -> Dict[str, Any]:
        """
        Get logistics data
        
        Returns:
            Logistics data dictionary
        """
        if self._logistics_data is None:
            self.refresh_logistics_data()
        return self._logistics_data or {}
    
    def get_collection_data(self) -> Dict[str, Any]:
        """
        Get collection data
        
        Returns:
            Collection data dictionary
        """
        if self._collection_data is None:
            self.refresh_collection_data()
        return self._collection_data or {}
    
    def refresh_marketing_data(self) -> Dict[str, Any]:
        """
        Refresh marketing data from source
        
        Returns:
            Updated marketing data
        """
        try:
            # Get marketing data endpoint from config
            endpoint = config.DATA_ENDPOINTS.get('marketing')
            
            # For development, use sample data if endpoint is not configured
            if not endpoint:
                logger.info("Using sample marketing data (no endpoint configured)")
                data = self._get_sample_marketing_data()
            else:
                # In production, fetch from endpoint
                from endpoints.data_endpoints import fetch_data
                raw_data = fetch_data(endpoint)
                data = process_marketing_data(raw_data)
            
            # Add timestamp
            data["last_updated"] = datetime.datetime.now().isoformat()
            
            # Cache the data
            self._marketing_data = data
            self._save_cached_data('marketing', data)
            
            return data
        except Exception as e:
            logger.error(f"Error refreshing marketing data: {str(e)}")
            return {}
    
    def refresh_sales_data(self) -> Dict[str, Any]:
        """
        Refresh sales data from source

        Returns:
            Updated sales data
        """
        try:
            # Get sales data endpoint from config
            endpoint = config.DATA_ENDPOINTS.get('sales')

            # For development, use sample data if endpoint is not configured
            if not endpoint:
                logger.info("Using sample sales data (no endpoint configured)")
                data = self._get_sample_sales_data()
            else:
                # In production, fetch from endpoint
                from endpoints.data_endpoints import fetch_data
                raw_data = fetch_data(endpoint)
                data = process_sales_data(raw_data)

                # Convert to pandas DataFrame for preprocessing
                sales_df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data

                # Preprocess the data to ensure correct format
                data = self._preprocess_sales_data(sales_df)

            # Add timestamp
            data["last_updated"] = datetime.datetime.now().isoformat()

            # Cache the data
            self._sales_data = data
            self._save_cached_data('sales', data)

            return data
        except Exception as e:
            logger.error(f"Error refreshing sales data: {str(e)}")
            return {}
    
    def refresh_logistics_data(self) -> Dict[str, Any]:
        """
        Refresh logistics data from source
        
        Returns:
            Updated logistics data
        """
        try:
            # Get logistics data endpoint from config
            endpoint = config.DATA_ENDPOINTS.get('logistics')
            
            # For development, use sample data if endpoint is not configured
            if not endpoint:
                logger.info("Using sample logistics data (no endpoint configured)")
                data = self._get_sample_logistics_data()
            else:
                # In production, fetch from endpoint
                from endpoints.data_endpoints import fetch_data
                raw_data = fetch_data(endpoint)
                data = process_logistics_data(raw_data)
            
            # Add timestamp
            data["last_updated"] = datetime.datetime.now().isoformat()
            
            # Cache the data
            self._logistics_data = data
            self._save_cached_data('logistics', data)
            
            return data
        except Exception as e:
            logger.error(f"Error refreshing logistics data: {str(e)}")
            return {}
    
    def refresh_collection_data(self) -> Dict[str, Any]:
        """
        Refresh collection data from source
        
        Returns:
            Updated collection data
        """
        try:
            # Get collection data endpoint from config
            endpoint = config.DATA_ENDPOINTS.get('collection')
            
            # For development, use sample data if endpoint is not configured
            if not endpoint:
                logger.info("Using sample collection data (no endpoint configured)")
                data = self._get_sample_collection_data()
            else:
                # In production, fetch from endpoint
                from endpoints.data_endpoints import fetch_data
                raw_data = fetch_data(endpoint)
                data = process_collection_data(raw_data)
            
            # Add timestamp
            data["last_updated"] = datetime.datetime.now().isoformat()
            
            # Cache the data
            self._collection_data = data
            self._save_cached_data('collection', data)
            
            return data
        except Exception as e:
            logger.error(f"Error refreshing collection data: {str(e)}")
            return {}
    
    def refresh_all_data(self):
        """Refresh all data sources"""
        self.refresh_marketing_data()
        self.refresh_sales_data()
        self.refresh_logistics_data()
        self.refresh_collection_data()
        logger.info("All data refreshed successfully")
    
    # Sample data methods for development/testing
    def _get_sample_marketing_data(self) -> Dict[str, Any]:
        """Get sample marketing data"""
        return {
            "total_marketing_spend": 150000,
            "customer_acquisition_cost": 120.45,
            "brand_awareness_score": 72,
            "campaigns": [
                {
                    "id": "cam-001",
                    "name": "Summer Promotion",
                    "channel": "digital",
                    "cost": 45000,
                    "revenue": 125000,
                    "leads": 550,
                    "conversions": 112
                },
                {
                    "id": "cam-002",
                    "name": "Product Launch",
                    "channel": "mixed",
                    "cost": 65000,
                    "revenue": 190000,
                    "leads": 720,
                    "conversions": 145
                },
                {
                    "id": "cam-003",
                    "name": "Brand Awareness",
                    "channel": "social",
                    "cost": 40000,
                    "revenue": 85000,
                    "leads": 380,
                    "conversions": 75
                }
            ],
            "channel_performance": {
                "social_media": {
                    "spend": 55000,
                    "roi": 2.2,
                    "engagement_rate": 3.5
                },
                "email": {
                    "spend": 30000,
                    "roi": 3.1,
                    "open_rate": 22.5,
                    "click_rate": 4.2
                },
                "ppc": {
                    "spend": 45000,
                    "roi": 1.8,
                    "click_through_rate": 2.3,
                    "conversion_rate": 1.9
                },
                "content": {
                    "spend": 20000,
                    "roi": 2.5,
                    "page_views": 45000,
                    "average_time_on_page": 120
                }
            }
        }
    
    def _get_sample_sales_data(self) -> Dict[str, Any]:
        """Get sample sales data"""
        return {
            "total_revenue": 2500000,
            "total_units": 18500,
            "avg_deal_size": 135.14,
            "conversion_rate": 22.5,
            "products": [
                {
                    "id": "prod-001",
                    "name": "Product A",
                    "revenue": 950000,
                    "units": 7200,
                    "growth": 12.5
                },
                {
                    "id": "prod-002",
                    "name": "Product B",
                    "revenue": 750000,
                    "units": 5500,
                    "growth": 8.3
                },
                {
                    "id": "prod-003",
                    "name": "Product C",
                    "revenue": 800000,
                    "units": 5800,
                    "growth": -2.1
                }
            ],
            "regions": [
                {
                    "id": "reg-001",
                    "name": "North",
                    "revenue": 950000,
                    "growth": 10.2
                },
                {
                    "id": "reg-002",
                    "name": "South",
                    "revenue": 600000,
                    "growth": 5.7
                },
                {
                    "id": "reg-003",
                    "name": "East",
                    "revenue": 500000,
                    "growth": 7.3
                },
                {
                    "id": "reg-004",
                    "name": "West",
                    "revenue": 450000,
                    "growth": 12.1
                }
            ],
            "sales_reps": [
                {
                    "id": "rep-001",
                    "name": "John Smith",
                    "revenue": 350000,
                    "deals_closed": 45,
                    "quota_attainment": 110
                },
                {
                    "id": "rep-002",
                    "name": "Emily Johnson",
                    "revenue": 420000,
                    "deals_closed": 52,
                    "quota_attainment": 125
                },
                {
                    "id": "rep-003",
                    "name": "Michael Brown",
                    "revenue": 280000,
                    "deals_closed": 38,
                    "quota_attainment": 92
                }
            ],
            "forecasts": {
                "next_month": {
                    "revenue_forecast": 850000,
                    "growth_percentage": 5.2,
                    "by_product": {
                        "prod-001": {
                            "revenue_forecast": 330000,
                            "units_forecast": 2500
                        },
                        "prod-002": {
                            "revenue_forecast": 260000,
                            "units_forecast": 1900
                        },
                        "prod-003": {
                            "revenue_forecast": 260000,
                            "units_forecast": 1900
                        }
                    }
                },
                "next_quarter": {
                    "revenue_forecast": 2600000,
                    "growth_percentage": 4.0,
                    "by_product": {
                        "prod-001": {
                            "revenue_forecast": 990000,
                            "units_forecast": 7500
                        },
                        "prod-002": {
                            "revenue_forecast": 780000,
                            "units_forecast": 5700
                        },
                        "prod-003": {
                            "revenue_forecast": 830000,
                            "units_forecast": 6000
                        }
                    }
                }
            }
        }
    
    def _get_sample_logistics_data(self) -> Dict[str, Any]:
        """Get sample logistics data"""
        return {
            "inventory": [
                {
                    "product_id": "prod-001",
                    "product_name": "Product A",
                    "warehouse_id": "wh-001",
                    "quantity": 1200,
                    "unit_cost": 45.50,
                    "status": "normal"
                },
                {
                    "product_id": "prod-002",
                    "product_name": "Product B",
                    "warehouse_id": "wh-001",
                    "quantity": 850,
                    "unit_cost": 32.75,
                    "status": "normal"
                },
                {
                    "product_id": "prod-003",
                    "product_name": "Product C",
                    "warehouse_id": "wh-001",
                    "quantity": 120,
                    "unit_cost": 78.20,
                    "status": "low"
                },
                {
                    "product_id": "prod-001",
                    "product_name": "Product A",
                    "warehouse_id": "wh-002",
                    "quantity": 750,
                    "unit_cost": 45.50,
                    "status": "normal"
                },
                {
                    "product_id": "prod-004",
                    "product_name": "Product D",
                    "warehouse_id": "wh-002",
                    "quantity": 0,
                    "unit_cost": 65.30,
                    "status": "out_of_stock"
                }
            ],
            "warehouses": [
                {
                    "warehouse_id": "wh-001",
                    "name": "Main Warehouse",
                    "location": "Chicago, IL",
                    "capacity": 10000,
                    "utilization": 65
                },
                {
                    "warehouse_id": "wh-002",
                    "name": "East Warehouse",
                    "location": "Atlanta, GA",
                    "capacity": 8000,
                    "utilization": 48
                }
            ],
            "shipping": {
                "total_deliveries": 1250,
                "on_time_deliveries": 1150,
                "average_delivery_time": 2.3,
                "carriers": [
                    {
                        "carrier_id": "car-001",
                        "name": "Fast Shipping Co",
                        "deliveries": 750,
                        "on_time_percentage": 94.5,
                        "average_cost": 12.50
                    },
                    {
                        "carrier_id": "car-002",
                        "name": "Value Delivery",
                        "deliveries": 500,
                        "on_time_percentage": 88.2,
                        "average_cost": 8.75
                    }
                ]
            },
            "supply_chain": {
                "efficiency_score": 82,
                "bottlenecks": [
                    "Supplier delays for Product C components",
                    "Limited capacity at East Warehouse during peak season"
                ],
                "improvement_areas": [
                    "Streamline order processing workflow",
                    "Implement real-time inventory tracking"
                ],
                "lead_times": {
                    "prod-001": 12,
                    "prod-002": 15,
                    "prod-003": 22,
                    "prod-004": 18
                },
                "costs": {
                    "procurement": 450000,
                    "warehousing": 320000,
                    "distribution": 380000
                },
                "suppliers": [
                    {
                        "supplier_id": "sup-001",
                        "name": "Main Components Inc",
                        "reliability_score": 92,
                        "lead_time": 10,
                        "cost_index": 85
                    },
                    {
                        "supplier_id": "sup-002",
                        "name": "Quality Parts Ltd",
                        "reliability_score": 87,
                        "lead_time": 14,
                        "cost_index": 78
                    }
                ]
            }
        }
    
    def _get_sample_collection_data(self) -> Dict[str, Any]:
        """Get sample collection data"""
        return {
            "accounts_receivable": {
                "total_ar": 850000,
                "total_overdue": 180000,
                "average_days_outstanding": 32,
                "aging": {
                    "current": 480000,
                    "1_30": 190000,
                    "31_60": 95000,
                    "61_90": 45000,
                    "over_90": 40000
                },
                "invoices": [
                    {
                        "invoice_id": "inv-001",
                        "customer_id": "cust-001",
                        "customer_name": "ABC Corporation",
                        "amount_due": 45000,
                        "due_date": "2025-02-15",
                        "days_outstanding": 40,
                        "status": "overdue"
                    },
                    {
                        "invoice_id": "inv-002",
                        "customer_id": "cust-002",
                        "customer_name": "XYZ Industries",
                        "amount_due": 32000,
                        "due_date": "2025-03-10",
                        "days_outstanding": 15,
                        "status": "current"
                    },
                    {
                        "invoice_id": "inv-003",
                        "customer_id": "cust-003",
                        "customer_name": "Global Services",
                        "amount_due": 28500,
                        "due_date": "2025-01-20",
                        "days_outstanding": 65,
                        "status": "overdue"
                    }
                ]
            },
            "payment_trends": {
                "collection_efficiency": 85.2,
                "average_days_to_pay": 28,
                "payment_methods": {
                    "bank_transfer": 65,
                    "credit_card": 25,
                    "check": 10
                },
                "trend_by_month": [
                    {
                        "month": "January",
                        "collected": 280000,
                        "outstanding": 75000,
                        "efficiency": 78.9
                    },
                    {
                        "month": "February",
                        "collected": 310000,
                        "outstanding": 62000,
                        "efficiency": 83.3
                    },
                    {
                        "month": "March",
                        "collected": 290000,
                        "outstanding": 53000,
                        "efficiency": 84.5
                    }
                ],
                "segments": {
                    "enterprise": {
                        "average_days_to_pay": 32,
                        "collection_efficiency": 82.5
                    },
                    "mid_market": {
                        "average_days_to_pay": 25,
                        "collection_efficiency": 88.3
                    },
                    "small_business": {
                        "average_days_to_pay": 22,
                        "collection_efficiency": 79.8
                    }
                }
            },
            "risk_assessment": {
                "high_risk": [
                    {
                        "customer_id": "cust-008",
                        "customer_name": "Acme Solutions",
                        "outstanding_amount": 38000,
                        "days_overdue": 75,
                        "risk_score": 82
                    },
                    {
                        "customer_id": "cust-015",
                        "customer_name": "Metro Technologies",
                        "outstanding_amount": 42500,
                        "days_overdue": 90,
                        "risk_score": 88
                    }
                ],
                "medium_risk": [
                    {
                        "customer_id": "cust-003",
                        "customer_name": "Global Services",
                        "outstanding_amount": 28500,
                        "days_overdue": 45,
                        "risk_score": 65
                    },
                    {
                        "customer_id": "cust-012",
                        "customer_name": "Prime Enterprises",
                        "outstanding_amount": 19500,
                        "days_overdue": 35,
                        "risk_score": 58
                    }
                ],
                "low_risk": [
                    {
                        "customer_id": "cust-002",
                        "customer_name": "XYZ Industries",
                        "outstanding_amount": 32000,
                        "days_overdue": 5,
                        "risk_score": 22
                    },
                    {
                        "customer_id": "cust-007",
                        "customer_name": "Innovate Systems",
                        "outstanding_amount": 15200,
                        "days_overdue": 10,
                        "risk_score": 30
                    }
                ]
            }
        }