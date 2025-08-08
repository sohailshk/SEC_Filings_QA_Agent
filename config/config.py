"""
Configuration module for SEC Filings QA Agent

This module handles all configuration settings for the application,
loading from environment variables with sensible defaults.

Best Practice: Centralized configuration management with environment-based settings
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """
    Base configuration class with common settings.
    Uses environment variables with fallback defaults.
    """
    
    # SEC API Configuration
    SEC_API_KEY = os.getenv('SEC_API_KEY')
    SEC_API_BASE_URL = os.getenv('SEC_API_BASE_URL', 'https://api.sec-api.io')
    
    # Google Gemini API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/sec_filings.db')
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', 'data/vector_index')
    
    # Embedding and NLP Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    @classmethod
    def validate_config(cls):
        """
        Validate that all required configuration is present.
        Raises ValueError if required settings are missing.
        
        Returns:
            bool: True if all required config is valid
        """
        if not cls.SEC_API_KEY:
            raise ValueError("SEC_API_KEY is required but not set in environment variables")
        
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required but not set in environment variables")
        
        if cls.CHUNK_SIZE <= 0:
            raise ValueError("CHUNK_SIZE must be a positive integer")
            
        if cls.CHUNK_OVERLAP < 0:
            raise ValueError("CHUNK_OVERLAP must be non-negative")
            
        if cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be less than CHUNK_SIZE")
        
        return True

class DevelopmentConfig(Config):
    """Development environment specific configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production environment specific configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing environment specific configuration"""
    DEBUG = True
    DATABASE_PATH = 'data/test_sec_filings.db'
    VECTOR_DB_PATH = 'data/test_vector_index'

# Configuration mapping for different environments
config_mapping = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(environment=None):
    """
    Get configuration class based on environment.
    
    Args:
        environment (str): Environment name (development, production, testing)
        
    Returns:
        Config: Configuration class instance
    """
    if environment is None:
        environment = os.getenv('FLASK_ENV', 'default')
    
    config_class = config_mapping.get(environment, DevelopmentConfig)
    config_class.validate_config()
    
    return config_class
