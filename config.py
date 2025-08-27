#!/usr/bin/env python3
"""
Centralized configuration management using environment variables.
All sensitive data should be in .env file (never committed to git).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

class Config:
    """Centralized configuration for LinkedIn Automation system."""
    
    # Google Sheets Configuration
    SHEET_URL = os.getenv('LINKEDIN_SHEET_URL')
    CREDS_PATH = os.getenv('LINKEDIN_CREDS_PATH')
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Chrome Configuration  
    CHROME_PROFILE_PATH = os.getenv('CHROME_PROFILE_PATH')
    CHROME_BINARY_PATH = os.getenv('CHROME_BINARY_PATH')
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH')
    
    # Output Configuration
    OUTPUT_FILE_PATH = os.getenv('OUTPUT_FILE_PATH')
    
    @classmethod
    def validate(cls, required_vars=None):
        """Validate that required environment variables are set."""
        if required_vars is None:
            required_vars = ['LINKEDIN_SHEET_URL', 'LINKEDIN_CREDS_PATH']
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please create a .env file based on .env.example"
            )
        
        return True
    
    @classmethod
    def get_all(cls):
        """Get all configuration as a dictionary."""
        return {
            'sheet_url': cls.SHEET_URL,
            'creds_path': cls.CREDS_PATH,
            'telegram_bot_token': cls.TELEGRAM_BOT_TOKEN,
            'telegram_chat_id': cls.TELEGRAM_CHAT_ID,
            'chrome_profile_path': cls.CHROME_PROFILE_PATH,
            'chrome_binary_path': cls.CHROME_BINARY_PATH,
            'chromedriver_path': cls.CHROMEDRIVER_PATH,
            'output_file_path': cls.OUTPUT_FILE_PATH,
        }