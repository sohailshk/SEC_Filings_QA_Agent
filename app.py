"""
SEC Filings QA Agent - Main Flask Application

This is the main entry point for the Flask application that provides
a question-answering system for SEC filings analysis.

Author: Built step-by-step following best practices
Date: August 2025
"""

from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

# Import configuration and services
from config.config import get_config
from app.services.main_service import SECFilingsService

# Load environment variables from .env file
load_dotenv()

def create_app():
    """
    Application factory pattern for creating Flask app instances.
    This allows for better testing and configuration management.
    
    Returns:
        Flask: Configured Flask application instance
    """
    
    # Initialize Flask application with template and static folders
    app = Flask(__name__, 
                template_folder='frontend',
                static_folder='frontend/static')
    
    # Enable CORS for frontend integration (if needed later)
    CORS(app)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Setup logging configuration
    setup_logging(config)
    
    # Initialize services
    app.main_service = init_main_service(config)
    
    # Register blueprints (routes)
    register_blueprints(app)
    
    app.logger.info("SEC Filings QA Agent application initialized successfully")
    
    return app

def setup_logging(config):
    """
    Setup logging configuration based on config settings.
    
    Args:
        config: Configuration object
    """
    log_level = getattr(logging, config.LOG_LEVEL.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )

def init_main_service(config):
    """
    Initialize the main SEC filings service with all dependencies.
    
    Args:
        config: Configuration object
        
    Returns:
        SECFilingsService: Initialized main service
    """
    try:
        main_service = SECFilingsService(config)
        logging.info("Main service initialized successfully")
        return main_service
    except Exception as e:
        logging.error(f"Failed to initialize main service: {e}")
        raise

def register_blueprints(app):
    """
    Register all Flask blueprints (route modules) with the application.
    
    Args:
        app (Flask): Flask application instance
    """
    from app.routes.api_routes import api_bp
    
    # Register API routes
    app.register_blueprint(api_bp)
    
    # Add frontend routes
    @app.route('/')
    def index():
        """Serve the main frontend interface"""
        return render_template('index.html')
    
    @app.route('/api')
    def api_info():
        """API information endpoint"""
        return {
            'message': 'SEC Filings QA Agent API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/v1/health',
                'process_filings': '/api/v1/companies/{ticker}/process',
                'ask_question': '/api/v1/questions',
                'company_summary': '/api/v1/companies/{ticker}',
                'search': '/api/v1/search',
                'status': '/api/v1/status'
            },
            'documentation': 'Use the endpoints above to interact with SEC filings data'
        }
    
    logging.info("Blueprints registered successfully")

if __name__ == '__main__':
    """
    Run the application directly when this file is executed.
    For development purposes only.
    """
    app = create_app()
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"🚀 Starting SEC Filings QA Agent on port {port}")
    print(f"📊 Debug mode: {app.config['DEBUG']}")
    print(f"🔗 API Base URL: http://127.0.0.1:{port}/api/v1")
    print(f"📖 Health Check: http://127.0.0.1:{port}/api/v1/health")
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=app.config['DEBUG']
    )
