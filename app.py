"""
Main Flask application for Decision Making Assistant
"""
import os
import logging
import asyncio
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after logging is configured
from data.data_manager import DataManager
from agents.triage_agent import create_triage_agent
from endpoints.data_endpoints import setup_data_scheduler

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

# Initialize data manager
data_manager = DataManager()

# Create triage agent and all specialized agents
triage_agent = create_triage_agent(data_manager)

# Setup daily data fetching scheduler
setup_data_scheduler(data_manager)

@app.route('/')
def home():
    """Render the home page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/query', methods=['POST'])
async def query():
    """Process a query from higher management"""
    try:
        data = request.json
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({"error": "Query is required"}), 400
        
        # Run the query through the triage agent
        result = await triage_agent.process_query(user_query)
        
        return jsonify({
            "status": "success",
            "response": result,
            "agent": triage_agent.name
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
    # This is only used for development
    # For production, use run.py or a WSGI server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)