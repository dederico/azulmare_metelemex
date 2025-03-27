"""
Simplified Flask application using direct OpenAI integration
"""
import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)