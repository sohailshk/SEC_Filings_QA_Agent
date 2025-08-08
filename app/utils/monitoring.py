"""
Enhanced error handling and monitoring utilities
"""
import logging
import time
from functools import wraps
from flask import request, jsonify
import traceback

def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def handle_errors(f):
    """Decorator for comprehensive error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            start_time = time.time()
            result = f(*args, **kwargs)
            end_time = time.time()
            
            # Log successful requests
            logging.info(f"Request to {request.endpoint} completed in {end_time - start_time:.2f}s")
            return result
            
        except Exception as e:
            logging.error(f"Error in {request.endpoint}: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            
            return jsonify({
                'success': False,
                'message': 'An internal error occurred',
                'error_type': type(e).__name__
            }), 500
            
    return decorated_function

def rate_limit_handler(e):
    """Handle rate limit exceeded errors"""
    return jsonify({
        'success': False,
        'message': 'Rate limit exceeded. Please try again later.',
        'retry_after': str(e.retry_after)
    }), 429

def validate_request_data(required_fields=None):
    """Decorator to validate request JSON data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if required_fields:
                data = request.get_json() or {}
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'message': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class PerformanceMonitor:
    """Monitor API performance and usage"""
    
    def __init__(self):
        self.request_count = 0
        self.total_processing_time = 0
        self.error_count = 0
    
    def log_request(self, processing_time):
        self.request_count += 1
        self.total_processing_time += processing_time
    
    def log_error(self):
        self.error_count += 1
    
    def get_stats(self):
        avg_time = self.total_processing_time / max(self.request_count, 1)
        return {
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'average_processing_time': round(avg_time, 3),
            'success_rate': round((self.request_count - self.error_count) / max(self.request_count, 1) * 100, 2)
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()
