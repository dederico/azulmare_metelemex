#!/usr/bin/env python
"""
Entry point script for running the Decision Making Assistant application
"""
import os
import argparse
import logging
import uvicorn
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the application"""
    parser = argparse.ArgumentParser(description='Run the Decision Making Assistant')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 5000)),
                        help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to run the server on')
    parser.add_argument('--debug', action='store_true',
                        help='Run in debug mode')
    args = parser.parse_args()
    
    logger.info(f"Starting Decision Making Assistant on {args.host}:{args.port} (debug: {args.debug})")
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")

if __name__ == "__main__":
    main()