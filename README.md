# Decision Making Assistant

A multi-agent AI system designed to assist higher management in making informed decisions by analyzing data from different business domains.

## Overview

This system uses specialized AI agents to analyze data from different departments (Marketing, Sales, Logistics, and Collections) and provide insights to executives and decision-makers. Each agent is an expert in its domain and can process relevant data to answer specific questions.

The system architecture includes:

- **Triage Agent**: The main entry point that routes queries to specialized agents
- **Specialized Agents**: Domain-specific agents for marketing, sales, logistics, and collections
- **Data Management**: Automatic data fetching and processing from various sources
- **Web Interface**: Simple interface for interacting with the assistant

## Features

- **Multi-Agent Architecture**: Each business domain has a dedicated agent with specialized knowledge
- **Automated Data Refreshing**: Daily data updates from configured endpoints
- **Intelligent Query Routing**: Queries are analyzed and sent to the most appropriate agent
- **Data Caching**: Fetched data is cached to improve performance
- **Interactive Dashboard**: Monitor system status and data freshness

## Setup and Installation

### Prerequisites

- Python 3.9+
- Flask
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/decision-assistant.git
cd decision-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables by creating a `.env` file:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
FLASK_SECRET_KEY=your_secret_key

# Optional: Configure data endpoints
MARKETING_DATA_ENDPOINT=https://your-api.com/marketing-data
SALES_DATA_ENDPOINT=https://your-api.com/sales-data
LOGISTICS_DATA_ENDPOINT=https://your-api.com/logistics-data
COLLECTION_DATA_ENDPOINT=https://your-api.com/collection-data
```

### Running the Application

1. Start the Flask application:
```bash
python app.py
```

2. Access the application in your browser at:
```
http://localhost:5000
```

## Usage

1. **Ask a Question**: Type your business question in the input field and submit
2. **View Response**: The system will route your question to the appropriate agent and display the response
3. **Check Dashboard**: View system status and data freshness in the dashboard

## Example Queries

- "What was our marketing ROI for the Summer Promotion campaign?"
- "Show me the sales forecast for next quarter by product."
- "Which products are running low on inventory?"
- "Identify our high-risk accounts receivable and suggest collection strategies."

## Project Structure

```
decision-assistant/
├── app.py                     # Main Flask application
├── config.py                  # Configuration settings
├── agents/                    # Agent implementations
│   ├── base_agent.py          # Base agent class
│   ├── marketing_agent.py     # Marketing specialist agent
│   ├── sales_agent.py         # Sales specialist agent
│   ├── logistics_agent.py     # Logistics specialist agent
│   ├── collection_agent.py    # Collection specialist agent
│   └── triage_agent.py        # Main dispatcher agent
├── data/                      # Data handling
│   ├── data_manager.py        # Data fetching and processing
│   └── cached/                # Cached data files
├── endpoints/                 # Data fetching endpoints
│   └── data_endpoints.py      # Data fetching functions
├── static/                    # Static assets
│   └── css/                   # CSS stylesheets
├── templates/                 # HTML templates
├── utils/                     # Utility functions
│   └── data_processors.py     # Data processing utilities
└── requirements.txt           # Dependencies
```

## Customization

### Adding New Data Sources

1. Add the endpoint URL to your `.env` file
2. Update the `config.py` file to include the new endpoint
3. Create a data processor function in `utils/data_processors.py`
4. Add a refresh method in `data/data_manager.py`

### Creating a New Specialized Agent

1. Create a new agent file in the `agents/` directory
2. Extend the `BaseAgent` class and implement necessary tools
3. Register the new agent with the triage agent in `agents/triage_agent.py`

## License

[MIT License](LICENSE)

## Acknowledgements

- This project uses the OpenAI Agents SDK
- Inspiration from modern multi-agent architectures