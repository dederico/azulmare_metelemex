"""
Data endpoints for fetching data from external sources
"""
import requests
import logging
import schedule
import time
import threading
from typing import Dict, Any, Optional

import config

logger = logging.getLogger(__name__)

def fetch_data(endpoint: str) -> Dict[str, Any]:
    """
    Fetch data from an endpoint
    
    Args:
        endpoint: URL endpoint to fetch data from
        
    Returns:
        Dictionary containing the fetched data
    """
    try:
        response = requests.get(endpoint, timeout=30)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Try to parse as JSON
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {endpoint}: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Error parsing JSON from {endpoint}: {str(e)}")
        raise

def setup_data_scheduler(data_manager) -> None:
    """
    Set up a scheduler to refresh data periodically
    
    Args:
        data_manager: Data manager instance
    """
    # Set up the schedule to refresh data
    refresh_interval = config.DATA_REFRESH_INTERVAL
    
    # Convert seconds to hours for better readability in logging
    hours = refresh_interval / 3600
    logger.info(f"Setting up data refresh scheduler to run every {hours} hours")
    
    # Schedule the refresh job
    schedule.every(refresh_interval).seconds.do(data_manager.refresh_all_data)
    
    # Start the scheduler in a background thread
    scheduler_thread = threading.Thread(target=_run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Data refresh scheduler started")

def _run_scheduler() -> None:
    """Run the scheduler in a loop"""
    while True:
        schedule.run_pending()
        time.sleep(1)