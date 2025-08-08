"""
API Routes for SEC Filings Q&A Agent

This module defines all Flask routes for the SEC filings question-answering system.
Provides RESTful API endpoints for processing filings and answering questions.

Best Practices Followed:
- RESTful API design with clear endpoints
- Comprehensive error handling and validation
- Detailed logging for debugging
- Consistent JSON response format
- Input validation and sanitization
"""

from flask import Blueprint, request, jsonify, current_app
import logging
from typing import Dict, Any
import traceback

# Setup logging for this module
logger = logging.getLogger(__name__)

# Create blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def get_main_service():
    """
    Get the main service instance from Flask app context.
    
    Returns:
        SECFilingsService: Main service instance
    """
    return current_app.main_service

def create_error_response(message: str, status_code: int = 400, 
                         details: str = None) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        message (str): Error message
        status_code (int): HTTP status code
        details (str): Additional error details
        
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        'success': False,
        'error': message,
        'status_code': status_code
    }
    
    if details:
        response['details'] = details
    
    logger.error(f"API Error {status_code}: {message}")
    if details:
        logger.error(f"Error details: {details}")
    
    return jsonify(response), status_code

def create_success_response(data: Any, message: str = "Success") -> dict:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message (str): Success message
        
    Returns:
        dict: Success response
    """
    return jsonify({
        'success': True,
        'message': message,
        'data': data
    })

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify service is running.
    
    Returns:
        JSON response with service status
    """
    try:
        main_service = get_main_service()
        status = main_service.get_system_status()
        
        return create_success_response(status, "Service is healthy")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_error_response("Service health check failed", 503, str(e))

@api_bp.route('/companies/<ticker>/process', methods=['POST'])
def process_company_filings(ticker: str):
    """
    Process SEC filings for a specific company.
    
    Args:
        ticker (str): Company ticker symbol
        
    Request Body (JSON):
        {
            "filing_type": "8-K",  # Optional, defaults to "8-K"
            "limit": 5             # Optional, defaults to 5
        }
    
    Returns:
        JSON response with processing results
    """
    try:
        # Validate ticker
        if not ticker or len(ticker) > 10:
            return create_error_response("Invalid ticker symbol")
        
        ticker = ticker.upper().strip()
        
        # Get request parameters
        data = request.get_json() or {}
        filing_type = data.get('filing_type', '8-K')
        limit = data.get('limit', 5)
        
        # Validate parameters
        if limit > 20:
            return create_error_response("Limit cannot exceed 20 filings")
        
        valid_filing_types = ['10-K', '10-Q', '8-K', 'DEF 14A']
        if filing_type not in valid_filing_types:
            return create_error_response(f"Invalid filing type. Must be one of: {valid_filing_types}")
        
        logger.info(f"Processing {filing_type} filings for {ticker} (limit: {limit})")
        
        # Process filings
        main_service = get_main_service()
        results = main_service.process_company_filings(
            ticker=ticker,
            filing_type=filing_type,
            limit=limit
        )
        
        return create_success_response(results, f"Successfully processed filings for {ticker}")
        
    except Exception as e:
        logger.error(f"Failed to process filings for {ticker}: {e}")
        logger.error(traceback.format_exc())
        return create_error_response(
            f"Failed to process filings for {ticker}",
            500,
            str(e)
        )

@api_bp.route('/questions', methods=['POST'])
def answer_question():
    """
    Answer a question using SEC filings.
    
    Request Body (JSON):
        {
            "question": "What are Apple's main risk factors?",
            "ticker": "AAPL",        # Optional
            "filing_type": "10-K",   # Optional
            "k": 5                   # Optional, number of chunks to retrieve
        }
    
    Returns:
        JSON response with answer and sources
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return create_error_response("Request body must be JSON")
        
        question = data.get('question', '').strip()
        if not question:
            return create_error_response("Question is required")
        
        if len(question) > 1000:
            return create_error_response("Question is too long (max 1000 characters)")
        
        # Get optional parameters
        ticker = data.get('ticker', '').strip().upper() if data.get('ticker') else None
        filing_type = data.get('filing_type', '').strip() if data.get('filing_type') else None
        k = data.get('k', 5)
        
        # Validate parameters
        if k > 10:
            return create_error_response("k cannot exceed 10")
        
        if ticker and len(ticker) > 10:
            return create_error_response("Invalid ticker symbol")
        
        logger.info(f"Answering question for {ticker or 'any company'}: {question[:100]}...")
        
        # Generate answer
        main_service = get_main_service()
        answer_response = main_service.answer_question(
            question=question,
            ticker=ticker,
            filing_type=filing_type,
            k=k
        )
        
        return create_success_response(answer_response, "Question answered successfully")
        
    except Exception as e:
        logger.error(f"Failed to answer question: {e}")
        logger.error(traceback.format_exc())
        return create_error_response(
            "Failed to answer question",
            500,
            str(e)
        )

@api_bp.route('/companies/<ticker>', methods=['GET'])
def get_company_summary(ticker: str):
    """
    Get comprehensive summary of a company's filings.
    
    Args:
        ticker (str): Company ticker symbol
    
    Returns:
        JSON response with company information and filings summary
    """
    try:
        # Validate ticker
        if not ticker or len(ticker) > 10:
            return create_error_response("Invalid ticker symbol")
        
        ticker = ticker.upper().strip()
        
        logger.info(f"Getting company summary for {ticker}")
        
        # Get company summary
        main_service = get_main_service()
        summary = main_service.get_company_summary(ticker)
        
        if 'error' in summary:
            return create_error_response(summary['error'], 404)
        
        return create_success_response(summary, f"Company summary for {ticker}")
        
    except Exception as e:
        logger.error(f"Failed to get company summary for {ticker}: {e}")
        return create_error_response(
            f"Failed to get company summary for {ticker}",
            500,
            str(e)
        )

@api_bp.route('/search', methods=['POST'])
def search_filings():
    """
    Search for relevant filing content using semantic search.
    
    Request Body (JSON):
        {
            "query": "revenue growth strategy",
            "ticker": "AAPL",  # Optional
            "k": 10            # Optional, max results
        }
    
    Returns:
        JSON response with search results
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return create_error_response("Request body must be JSON")
        
        query = data.get('query', '').strip()
        if not query:
            return create_error_response("Search query is required")
        
        if len(query) > 500:
            return create_error_response("Query is too long (max 500 characters)")
        
        # Get optional parameters
        ticker = data.get('ticker', '').strip().upper() if data.get('ticker') else None
        k = data.get('k', 10)
        
        # Validate parameters
        if k > 20:
            return create_error_response("k cannot exceed 20")
        
        logger.info(f"Searching filings: {query[:100]}...")
        
        # Perform search
        main_service = get_main_service()
        results = main_service.search_filings(
            query=query,
            ticker=ticker,
            k=k
        )
        
        return create_success_response({
            'query': query,
            'ticker_filter': ticker,
            'results': results,
            'num_results': len(results)
        }, "Search completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to search filings: {e}")
        return create_error_response(
            "Failed to search filings",
            500,
            str(e)
        )

@api_bp.route('/status', methods=['GET'])
def get_system_status():
    """
    Get comprehensive system status and statistics.
    
    Returns:
        JSON response with system status
    """
    try:
        main_service = get_main_service()
        status = main_service.get_system_status()
        
        return create_success_response(status, "System status retrieved")
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return create_error_response(
            "Failed to get system status",
            500,
            str(e)
        )

@api_bp.route('/companies', methods=['GET'])
def list_companies():
    """
    List all companies in the database with their filing counts.
    
    Returns:
        JSON response with companies list
    """
    try:
        main_service = get_main_service()
        
        # Get basic database stats - this is a simple implementation
        # In a more complete system, we'd have a dedicated method for this
        db_stats = main_service.get_system_status()
        
        return create_success_response({
            'message': 'Use /companies/{ticker} to get specific company information',
            'database_stats': db_stats.get('database', {}),
            'available_endpoints': [
                'GET /companies/{ticker} - Get company summary',
                'POST /companies/{ticker}/process - Process company filings',
                'POST /questions - Ask questions about filings',
                'POST /search - Search filing content'
            ]
        }, "Available companies endpoint information")
        
    except Exception as e:
        logger.error(f"Failed to list companies: {e}")
        return create_error_response(
            "Failed to list companies",
            500,
            str(e)
        )

# Error handlers for the blueprint
@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return create_error_response("Endpoint not found", 404)

@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return create_error_response("Method not allowed", 405)

@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return create_error_response("Internal server error", 500)
