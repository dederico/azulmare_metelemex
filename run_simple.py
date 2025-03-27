"""
Run script for the simplified app with async support
"""
import os
import logging
import asyncio
from aioflask import Flask
from simple_app import app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)