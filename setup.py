#!/usr/bin/env python
"""
Setup script for the Decision Making Assistant
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup")

def setup_directories():
    """Create required directories if they don't exist"""
    directories = [
        "data/cached",
        "static/css",
        "templates",
        "utils"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            logger.info(f"Creating directory: {directory}")
            path.mkdir(parents=True, exist_ok=True)

def setup_virtual_environment():
    """Set up a virtual environment if it doesn't exist"""
    venv_path = Path("venv")
    if venv_path.exists():
        logger.info("Virtual environment already exists")
        return
    
    logger.info("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        logger.info("Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create virtual environment: {e}")
        sys.exit(1)

def install_dependencies():
    """Install dependencies based on the platform"""
    logger.info("Installing dependencies...")
    
    # Determine the pip executable based on whether we're in a venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # We're in a venv
        pip_cmd = [sys.executable, "-m", "pip"]
    else:
        # We're not in a venv, use the venv pip
        if os.name == 'nt':  # Windows
            pip_cmd = ["venv\\Scripts\\pip"]
        else:  # macOS/Linux
            pip_cmd = ["venv/bin/pip"]
    
    try:
        # First try with the simplified requirements
        logger.info("Installing with simplified requirements...")
        subprocess.run(pip_cmd + ["install", "-r", "requirements_simplified.txt"], check=True)
        logger.info("Dependencies installed successfully with simplified requirements")
    except subprocess.CalledProcessError:
        logger.warning("Failed to install with simplified requirements. Trying alternate approach...")
        try:
            # Install core dependencies first to avoid conflicts
            subprocess.run(pip_cmd + ["install", "flask", "pydantic", "python-dotenv"], check=True)
            logger.info("Core dependencies installed")
            
            # Then install data processing libraries
            subprocess.run(pip_cmd + ["install", "pandas", "numpy", "openpyxl", "xlrd"], check=True)
            logger.info("Data processing libraries installed")
            
            # Finally install OpenAI
            subprocess.run(pip_cmd + ["install", "openai>=1.66.5"], check=True)
            logger.info("OpenAI library installed")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            logger.error("Please refer to INSTALLATION.md for manual installation steps")
            sys.exit(1)

def create_env_file():
    """Create a .env file if it doesn't exist"""
    env_path = Path(".env")
    if env_path.exists():
        logger.info(".env file already exists")
        return
    
    env_example_path = Path(".env.example")
    if not env_example_path.exists():
        logger.warning(".env.example file not found. Creating basic .env file")
        with open(env_path, "w") as f:
            f.write("# OpenAI API settings\n")
            f.write("OPENAI_API_KEY=your_api_key_here\n")
            f.write("OPENAI_MODEL=gpt-4o\n\n")
            f.write("# Flask settings\n")
            f.write("FLASK_SECRET_KEY=your_secret_key_here\n")
    else:
        logger.info("Creating .env file from .env.example")
        with open(env_example_path, "r") as src, open(env_path, "w") as dst:
            dst.write(src.read())
    
    logger.info(".env file created. Please edit it with your API keys")

def main():
    """Main setup function"""
    logger.info("Setting up Decision Making Assistant")
    
    # Setup directories
    setup_directories()
    
    # Setup virtual environment
    setup_virtual_environment()
    
    # Install dependencies
    install_dependencies()
    
    # Create .env file
    create_env_file()
    
    logger.info("Setup completed!")
    logger.info("To activate the virtual environment:")
    if os.name == 'nt':  # Windows
        logger.info("  venv\\Scripts\\activate")
    else:  # macOS/Linux
        logger.info("  source venv/bin/activate")
    
    logger.info("To start the application:")
    logger.info("  python run.py")
    
    logger.info("Don't forget to edit the .env file with your API keys!")

if __name__ == "__main__":
    main()