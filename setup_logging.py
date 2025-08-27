#!/usr/bin/env python3
"""
Simple logging setup for error tracking and analysis.
Run this to enable error logging across the application.
"""

import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configure logging
log_file = os.path.join(log_dir, f'errors_{datetime.now().strftime("%Y%m%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also print to console
    ]
)

# Create logger
logger = logging.getLogger('linkedin_automation')
logger.info("Logging initialized. Errors will be tracked for analysis.")

def get_logger(name):
    """Get a logger instance for a specific module."""
    return logging.getLogger(f'linkedin_automation.{name}')

if __name__ == "__main__":
    print(f"Logging configured. Log file: {log_file}")
    logger.info("Test log entry - setup complete")