"""
Test Configuration for SEC Filings QA Agent

This module provides test configuration and utilities for comprehensive testing
of the SEC filings question-answering system.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import our application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config.config import TestingConfig


class TestConfig(TestingConfig):
    """Test-specific configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    # Use temporary directories for testing
    @classmethod
    def setup_test_dirs(cls):
        """Setup temporary directories for testing"""
        cls.test_temp_dir = tempfile.mkdtemp()
        cls.DATABASE_PATH = os.path.join(cls.test_temp_dir, 'test_sec_filings.db')
        cls.VECTOR_DB_PATH = os.path.join(cls.test_temp_dir, 'test_vector_index')
        cls.LOG_FILE = os.path.join(cls.test_temp_dir, 'test_app.log')
        
        # Create directories
        os.makedirs(os.path.dirname(cls.VECTOR_DB_PATH), exist_ok=True)
        
        return cls.test_temp_dir
    
    @classmethod
    def cleanup_test_dirs(cls):
        """Cleanup temporary directories after testing"""
        if hasattr(cls, 'test_temp_dir') and os.path.exists(cls.test_temp_dir):
            shutil.rmtree(cls.test_temp_dir)


@pytest.fixture(scope='session')
def app():
    """Create and configure a test app instance"""
    # Setup test configuration
    test_temp_dir = TestConfig.setup_test_dirs()
    
    # Create the app with test configuration
    app = create_app()
    app.config.from_object(TestConfig)
    
    # Provide the app context
    ctx = app.app_context()
    ctx.push()
    
    yield app
    
    # Cleanup
    ctx.pop()
    TestConfig.cleanup_test_dirs()


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()


# Test data for various scenarios
TEST_QUESTIONS = [
    {
        'question': 'What are the main risk factors?',
        'ticker': 'AAPL',
        'filing_type': '10-K',
        'k': 5
    },
    {
        'question': 'Compare revenue growth between companies',
        'ticker': '',
        'filing_type': '',
        'k': 3
    },
    {
        'question': 'What are the competitive advantages mentioned in filings?',
        'ticker': 'MSFT',
        'filing_type': '10-Q',
        'k': 7
    }
]

TEST_COMPANIES = [
    {
        'ticker': 'AAPL',
        'filing_type': '8-K',
        'limit': 2
    },
    {
        'ticker': 'MSFT',
        'filing_type': '10-Q',
        'limit': 1
    }
]

INVALID_REQUESTS = [
    # Invalid question requests
    {'question': ''},  # Empty question
    {'question': 'a' * 1001},  # Too long question
    {'question': 'Valid question', 'ticker': 'TOOLONGTICKE'},  # Invalid ticker
    {'question': 'Valid question', 'k': 15},  # Invalid k value
    
    # Invalid process requests
    {'ticker': ''},  # Empty ticker
    {'ticker': 'AAPL', 'limit': 25},  # Too high limit
    {'ticker': 'AAPL', 'filing_type': 'INVALID'},  # Invalid filing type
]

def get_test_html_content():
    """Return sample SEC filing HTML content for testing"""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Sample SEC Filing</title></head>
    <body>
        <div>
            <h2>Item 1. Business</h2>
            <p>We are a technology company that designs, manufactures and markets smartphones, 
            personal computers, tablets, wearables and accessories.</p>
            
            <h2>Item 1A. Risk Factors</h2>
            <p>Our business is subject to various risks including:</p>
            <ul>
                <li>Competition in the technology industry</li>
                <li>Supply chain disruptions</li>
                <li>Regulatory changes</li>
                <li>Cybersecurity threats</li>
            </ul>
            
            <h2>Item 2. Properties</h2>
            <p>Our corporate headquarters are located in Cupertino, California.</p>
        </div>
    </body>
    </html>
    """


def get_mock_sec_api_response():
    """Return mock SEC API response for testing"""
    return {
        'filings': [
            {
                'accessionNumber': '0000320193-23-000077',
                'filedAt': '2023-08-04',
                'formType': '10-Q',
                'ticker': 'AAPL',
                'linkToFilingDetails': 'https://www.sec.gov/Archives/edgar/data/320193/000032019323000077/aapl-20230701.htm',
                'linkToTxt': 'https://www.sec.gov/Archives/edgar/data/320193/000032019323000077/aapl-20230701.txt',
                'periodOfReport': '2023-07-01'
            }
        ]
    }


def assert_valid_api_response(response_data):
    """Assert that API response has valid structure"""
    assert 'success' in response_data
    if response_data['success']:
        assert 'data' in response_data
        assert 'message' in response_data
    else:
        assert 'error' in response_data
        assert 'status_code' in response_data


def assert_valid_question_response(response_data):
    """Assert that question response has valid structure"""
    assert_valid_api_response(response_data)
    if response_data['success']:
        data = response_data['data']
        assert 'question' in data
        assert 'answer' in data
        assert 'sources' in data
        assert isinstance(data['sources'], list)


def assert_valid_process_response(response_data):
    """Assert that process response has valid structure"""
    assert_valid_api_response(response_data)
    if response_data['success']:
        data = response_data['data']
        assert 'ticker' in data
        assert 'filings_processed' in data
        assert 'total_chunks_created' in data
        assert isinstance(data['filings_processed'], int)
        assert isinstance(data['total_chunks_created'], int)


def assert_valid_status_response(response_data):
    """Assert that status response has valid structure"""
    assert_valid_api_response(response_data)
    if response_data['success']:
        data = response_data['data']
        assert 'database' in data
        assert 'vector_database' in data
        assert 'services_initialized' in data
        assert 'timestamp' in data
