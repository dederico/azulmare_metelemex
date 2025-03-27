"""
Configuration settings for the Decision Making Assistant
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI API settings
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')

# Agent settings
AGENT_TEMPERATURE = float(os.getenv('AGENT_TEMPERATURE', '0.2'))
AGENT_MAX_TOKENS = int(os.getenv('AGENT_MAX_TOKENS', '4000'))

# Data endpoints
DATA_REFRESH_INTERVAL = int(os.getenv('DATA_REFRESH_INTERVAL', '86400'))  # 24 hours in seconds
DATA_ENDPOINTS = {
    'marketing': os.getenv('MARKETING_DATA_ENDPOINT', ''),
    'sales': os.getenv('SALES_DATA_ENDPOINT', ''),
    'logistics': os.getenv('LOGISTICS_DATA_ENDPOINT', ''),
    'collection': os.getenv('COLLECTION_DATA_ENDPOINT', '')
}

# Data cache settings
DATA_CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'cached')
os.makedirs(DATA_CACHE_DIR, exist_ok=True)

# Flask settings
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')