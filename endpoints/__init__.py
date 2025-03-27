"""
Endpoints package initialization
"""
from .data_endpoints import fetch_data, setup_data_scheduler

__all__ = [
    'fetch_data',
    'setup_data_scheduler'
]