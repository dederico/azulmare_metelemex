"""
Simplified Flask application using direct OpenAI integration
"""
import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import traceback
import datetime
import json

# Load environment variables first to ensure API key is available
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY is not set in the environment variables or .env file")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after environment variables are loaded
from agents.direct_agent import DirectAgent, function_tool
from data.data_manager import DataManager

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

# Initialize data manager
data_manager = DataManager()

# Create tools for our agent
@function_tool
def get_marketing_metrics(metric_name=None):
    """Get marketing metrics from the latest data"""
    marketing_data = data_manager.get_marketing_data()
    
    if metric_name:
        if metric_name in marketing_data:
            return {metric_name: marketing_data[metric_name]}
        else:
            return {"error": f"Metric '{metric_name}' not found in marketing data"}
    
    # Return all metrics if no specific one requested
    return marketing_data

@function_tool
def get_sales_data(metric_name=None, time_period="current"):
    """Get sales metrics from the latest data"""
    sales_data = data_manager.get_sales_data()
    
    if metric_name:
        if metric_name in sales_data:
            return {metric_name: sales_data[metric_name]}
        else:
            return {"error": f"Metric '{metric_name}' not found in sales data"}
    
    # Return all metrics if no specific one requested
    return sales_data

@function_tool
def analyze_sales_by_dimension(dimension, date_range=None, filter_by=None):
    """
    Analiza las ventas en una dimensión específica
    """
    try:
        # Configurar filtros según los parámetros
        filters = {}
        
        # Procesar el rango de fechas
        if date_range:
            today = datetime.datetime.now()
            
            if date_range == "mes_actual":
                # Filtrar por el mes actual
                year = today.year
                month = today.month
                filters["FECHA"] = {"date_range": {
                    "from": f"{year}-{month:02d}-01",
                    "to": today.strftime("%Y-%m-%d")
                }}
            # ... resto del código ...
        
        # Obtener los datos con los filtros aplicados
        sales_data = data_manager.get_sales_data(filters=filters, aggregation=f"por_{dimension}")
        
        # Si hay error en los datos, propagarlo
        if "error" in sales_data:
            return sales_data
        
        # Extraer los datos de la dimensión y verificar su formato
        dimension_data = sales_data.get("data", [])
        if not isinstance(dimension_data, list):
            return {
                "error": "Los datos de dimensión no están en el formato esperado (lista)",
                "dimension": dimension,
                "data_type": type(dimension_data).__name__
            }
        
        # Inicializar resultado
        result = {
            "dimension": dimension,
            "date_range": date_range,
            "filtros_aplicados": filters,
            "total_registros": len(dimension_data),
            "total_ventas": 0,
            "top_items": [],
            "insights": []
        }
        
        # Si no hay datos, retornar resultado vacío con mensaje
        if not dimension_data or len(dimension_data) == 0:
            result["insights"].append("No hay datos disponibles para los filtros especificados.")
            return result
        
        # Verificar el formato de los datos antes de procesarlos
        if not all(isinstance(item, dict) for item in dimension_data):
            return {
                "error": "Los datos no tienen el formato esperado (lista de diccionarios)",
                "dimension": dimension,
                "sample_data": dimension_data[:1] if dimension_data else None
            }
        
        # Calcular métricas según la dimensión
        if dimension == "vendedor":
            # Verificar la presencia del campo necesario
            if "sum" not in dimension_data[0]:
                return {
                    "error": "Los datos no contienen el campo 'sum' esperado",
                    "dimension": dimension,
                    "available_fields": list(dimension_data[0].keys()) if dimension_data else []
                }
            
            # Calcular total de ventas
            try:
                total_ventas = sum(item["sum"] for item in dimension_data)
                result["total_ventas"] = total_ventas
            except KeyError as e:
                return {
                    "error": f"Error al calcular total de ventas: {str(e)}",
                    "dimension": dimension,
                    "traceback": traceback.format_exc()
                }
            
            # Resto del código...
        
        # Resto de los bloques para otras dimensiones...
        
        return result
    except Exception as e:
        logger.error(f"Error analizando ventas por {dimension}: {str(e)}")
        return {"error": str(e), "traceback": traceback.format_exc()}

@function_tool
def get_logistics_data(category=None):
    """Get logistics data including inventory and shipping information"""
    logistics_data = data_manager.get_logistics_data()
    
    if category:
        if category in logistics_data:
            return {category: logistics_data[category]}
        else:
            return {"error": f"Category '{category}' not found in logistics data"}
    
    # Return all data if no specific category requested
    return logistics_data

@function_tool
def get_collection_data(category=None):
    """Get accounts receivable and collection data"""
    collection_data = data_manager.get_collection_data()
    
    if category:
        if category in collection_data:
            return {category: collection_data[category]}
        else:
            return {"error": f"Category '{category}' not found in collection data"}
    
    # Return all data if no specific category requested
    return collection_data

# Create the agent
assistant = DirectAgent(
    name="Decision Making Assistant",
    instructions="""
    You are a decision-making assistant for higher management. You have access to data 
    from multiple business domains including marketing, sales, logistics, and collections.
    
    Your role is to analyze this data and provide insights to help executives make informed decisions.
    
    When answering questions:
    1. Use the appropriate tool to fetch relevant data
    2. Analyze the data to extract meaningful insights
    3. Provide clear, concise recommendations based on the data
    4. Support your conclusions with specific data points
    
    Be professional, precise, and focus on actionable insights.
    """,
    tools=[
        get_marketing_metrics,
        get_sales_data,
        get_logistics_data,
        get_collection_data
    ],
    model="gpt-4o"  # Specify a valid model name explicitly
)

@app.route('/')
def home():
    """Render the home page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page"""
    return render_template('dashboard.html')

# Thread pool for running async functions from Flask
thread_pool = ThreadPoolExecutor()

def run_async(coro):
    """Run an async function from a synchronous context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@app.route('/api/query', methods=['POST'])
def query():
    """Process a query from higher management"""
    try:
        data = request.json
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({"error": "Query is required"}), 400
        
        # Run the async function in a separate thread
        response = thread_pool.submit(run_async, assistant.process_query(user_query)).result()
        
        return jsonify({
            "status": "success",
            "response": response,
            "agent": assistant.name
        })
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/refresh', methods=['POST'])
def refresh_data():
    """Manually trigger data refresh"""
    try:
        data_manager.refresh_all_data()
        return jsonify({"status": "success", "message": "Data refreshed successfully"})
    except Exception as e:
        logger.error(f"Error refreshing data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/api/data/sales/analysis', methods=['GET'])
def analyze_sales():
    """Endpoint para análisis de ventas"""
    dimension = request.args.get('dimension', 'vendedor')
    date_range = request.args.get('date_range', 'mes_actual')
    filter_by_str = request.args.get('filter_by', None)
    
    try:
        # Convertir filter_by de string a diccionario si existe
        filter_by = json.loads(filter_by_str) if filter_by_str else None
        
        # Usar la herramienta de análisis
        result = thread_pool.submit(
            run_async, 
            analyze_sales_by_dimension(dimension, date_range, filter_by)
        ).result()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error en endpoint de análisis de ventas: {str(e)}")
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/api/data/sales/vendedores', methods=['GET'])
def get_vendedores_performance():
    """Endpoint específico para rendimiento de vendedores"""
    date_range = request.args.get('date_range', 'mes_actual')
    
    try:
        # Usar la función de análisis con dimensión vendedor
        result = thread_pool.submit(
            run_async, 
            analyze_sales_by_dimension('vendedor', date_range)
        ).result()
        
        # Añadir análisis adicional específico para vendedores
        if 'top_items' in result and result['top_items']:
            # Calcular ranking de vendedores
            for i, vendedor in enumerate(result['top_items']):
                vendedor['ranking'] = i + 1
                
                # Calcular eficiencia (ventas por transacción)
                if 'sum' in vendedor and 'count' in vendedor and vendedor['count'] > 0:
                    vendedor['eficiencia'] = vendedor['sum'] / vendedor['count']
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error en endpoint de rendimiento de vendedores: {str(e)}")
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

@app.route('/api/data/sales/clientes', methods=['GET'])
def get_clientes_insights():
    """Endpoint específico para análisis de clientes"""
    date_range = request.args.get('date_range', 'mes_actual')
    limit = request.args.get('limit', 10, type=int)
    
    try:
        # Obtener análisis básico con dimensión cliente
        result = thread_pool.submit(
            run_async, 
            analyze_sales_by_dimension('cliente', date_range)
        ).result()
        
        # Segmentar clientes por volumen de compra
        if 'top_items' in result:
            # Limitar a los N principales clientes según el parámetro
            result['top_items'] = result['top_items'][:limit]
            
            # Categorizar clientes
            clientes_categorizados = []
            for cliente in result.get('top_items', []):
                categoria = "VIP"
                if 'sum' in cliente:
                    if cliente['sum'] < 10000:
                        categoria = "Pequeño"
                    elif cliente['sum'] < 50000:
                        categoria = "Mediano"
                    elif cliente['sum'] < 100000:
                        categoria = "Grande"
                
                clientes_categorizados.append({
                    "cliente": cliente.get('CLIENTE', 'Desconocido'),
                    "ventas_totales": cliente.get('sum', 0),
                    "transacciones": cliente.get('count', 0),
                    "ticket_promedio": cliente.get('mean', 0),
                    "categoria": categoria
                })
            
            result['clientes_categorizados'] = clientes_categorizados
            
            # Añadir distribución por categoría
            categorias = {}
            for cliente in clientes_categorizados:
                cat = cliente['categoria']
                if cat not in categorias:
                    categorias[cat] = {
                        'clientes': 0,
                        'ventas_totales': 0
                    }
                categorias[cat]['clientes'] += 1
                categorias[cat]['ventas_totales'] += cliente['ventas_totales']
            
            result['distribucion_por_categoria'] = categorias
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error en endpoint de insights de clientes: {str(e)}")
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)