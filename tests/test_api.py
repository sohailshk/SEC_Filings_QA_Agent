"""
API Testing for SEC Filings QA Agent

This module provides comprehensive tests for all API endpoints,
including validation, error handling, and integration testing.
"""

import pytest
import json
import time
from .conftest import (
    TEST_QUESTIONS, TEST_COMPANIES, INVALID_REQUESTS,
    assert_valid_api_response, assert_valid_question_response,
    assert_valid_process_response, assert_valid_status_response
)


class TestHealthEndpoint:
    """Test the health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert_valid_api_response(data)
        assert data['success'] is True
    
    def test_health_check_content(self, client):
        """Test health check response content"""
        response = client.get('/api/v1/health')
        data = response.get_json()
        
        assert 'data' in data
        health_data = data['data']
        
        # Should contain system status information
        expected_keys = ['database', 'vector_database', 'services_initialized']
        for key in expected_keys:
            assert key in health_data


class TestStatusEndpoint:
    """Test the system status endpoint"""
    
    def test_status_success(self, client):
        """Test successful status retrieval"""
        response = client.get('/api/v1/status')
        assert response.status_code == 200
        
        data = response.get_json()
        assert_valid_status_response(data)
    
    def test_status_content_structure(self, client):
        """Test status response structure"""
        response = client.get('/api/v1/status')
        data = response.get_json()
        
        status_data = data['data']
        
        # Check for required sections
        assert 'database' in status_data
        assert 'vector_database' in status_data
        assert 'services_initialized' in status_data
        assert 'timestamp' in status_data
        
        # Check database stats
        db_stats = status_data['database']
        assert isinstance(db_stats, dict)
        
        # Check vector database stats
        vector_stats = status_data['vector_database']
        assert isinstance(vector_stats, dict)


class TestQuestionEndpoint:
    """Test the question answering endpoint"""
    
    def test_question_missing_body(self, client):
        """Test question endpoint with missing request body"""
        response = client.post('/api/v1/questions')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_question_empty_question(self, client):
        """Test question endpoint with empty question"""
        response = client.post('/api/v1/questions', 
                             json={'question': ''})
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'question is required' in data['error'].lower()
    
    def test_question_too_long(self, client):
        """Test question endpoint with overly long question"""
        long_question = 'a' * 1001
        response = client.post('/api/v1/questions',
                             json={'question': long_question})
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'too long' in data['error'].lower()
    
    def test_question_invalid_ticker(self, client):
        """Test question endpoint with invalid ticker"""
        response = client.post('/api/v1/questions',
                             json={
                                 'question': 'Test question',
                                 'ticker': 'VERYLONGTICKER'
                             })
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
    
    def test_question_invalid_k_value(self, client):
        """Test question endpoint with invalid k value"""
        response = client.post('/api/v1/questions',
                             json={
                                 'question': 'Test question',
                                 'k': 15
                             })
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'k cannot exceed' in data['error'].lower()
    
    def test_question_valid_request(self, client):
        """Test question endpoint with valid request"""
        # Note: This test may fail if no data is loaded
        response = client.post('/api/v1/questions',
                             json={
                                 'question': 'What are the main business activities?',
                                 'k': 5
                             })
        
        # Should return 200 regardless of whether data is found
        assert response.status_code == 200
        
        data = response.get_json()
        assert_valid_question_response(data)


class TestProcessEndpoint:
    """Test the process filings endpoint"""
    
    def test_process_invalid_ticker(self, client):
        """Test process endpoint with invalid ticker"""
        response = client.post('/api/v1/companies/INVALID_TICKER_TOOLONG/process',
                             json={'filing_type': '8-K', 'limit': 5})
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
    
    def test_process_invalid_limit(self, client):
        """Test process endpoint with invalid limit"""
        response = client.post('/api/v1/companies/AAPL/process',
                             json={'filing_type': '8-K', 'limit': 25})
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'limit cannot exceed' in data['error'].lower()
    
    def test_process_invalid_filing_type(self, client):
        """Test process endpoint with invalid filing type"""
        response = client.post('/api/v1/companies/AAPL/process',
                             json={'filing_type': 'INVALID', 'limit': 5})
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'invalid filing type' in data['error'].lower()
    
    def test_process_valid_request_structure(self, client):
        """Test process endpoint request structure (may fail due to external API)"""
        # Note: This test may fail due to external API dependencies
        response = client.post('/api/v1/companies/AAPL/process',
                             json={'filing_type': '8-K', 'limit': 1})
        
        # Should return either success or a specific error
        data = response.get_json()
        assert_valid_api_response(data)
        
        if data['success']:
            assert_valid_process_response(data)
        else:
            # Expected to fail due to missing API keys or network issues
            assert 'error' in data


class TestSearchEndpoint:
    """Test the search endpoint"""
    
    def test_search_missing_body(self, client):
        """Test search endpoint with missing request body"""
        response = client.post('/api/v1/search')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
    
    def test_search_empty_query(self, client):
        """Test search endpoint with empty query"""
        response = client.post('/api/v1/search',
                             json={'query': ''})
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'query is required' in data['error'].lower()
    
    def test_search_query_too_long(self, client):
        """Test search endpoint with overly long query"""
        long_query = 'a' * 501
        response = client.post('/api/v1/search',
                             json={'query': long_query})
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
    
    def test_search_invalid_k_value(self, client):
        """Test search endpoint with invalid k value"""
        response = client.post('/api/v1/search',
                             json={'query': 'test query', 'k': 25})
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
    
    def test_search_valid_request(self, client):
        """Test search endpoint with valid request"""
        response = client.post('/api/v1/search',
                             json={'query': 'business operations', 'k': 5})
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert_valid_api_response(data)
        
        if data['success']:
            search_data = data['data']
            assert 'query' in search_data
            assert 'results' in search_data
            assert 'num_results' in search_data
            assert isinstance(search_data['results'], list)


class TestCompanyEndpoint:
    """Test the company summary endpoint"""
    
    def test_company_invalid_ticker(self, client):
        """Test company endpoint with invalid ticker"""
        response = client.get('/api/v1/companies/INVALID_TICKER_TOOLONG')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
    
    def test_company_not_found(self, client):
        """Test company endpoint with non-existent company"""
        response = client.get('/api/v1/companies/XXXX')
        
        # Should return 200 but with not found error
        assert response.status_code == 200
        
        data = response.get_json()
        if not data['success']:
            # Expected if company not in database
            assert 'not found' in data['error'].lower()
    
    def test_company_valid_ticker_format(self, client):
        """Test company endpoint with valid ticker format"""
        response = client.get('/api/v1/companies/AAPL')
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert_valid_api_response(data)


class TestErrorHandling:
    """Test error handling across endpoints"""
    
    def test_404_endpoint(self, client):
        """Test non-existent endpoint returns 404"""
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404
        
        data = response.get_json()
        assert data['success'] is False
        assert data['status_code'] == 404
    
    def test_405_method_not_allowed(self, client):
        """Test wrong HTTP method returns 405"""
        response = client.get('/api/v1/questions')  # Should be POST
        assert response.status_code == 405
        
        data = response.get_json()
        assert data['success'] is False
        assert data['status_code'] == 405
    
    def test_invalid_json(self, client):
        """Test invalid JSON in request body"""
        response = client.post('/api/v1/questions',
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_content_type_validation(self, client):
        """Test that endpoints validate content type"""
        response = client.post('/api/v1/questions',
                             data='question=test',
                             content_type='application/x-www-form-urlencoded')
        # Should handle gracefully
        assert response.status_code in [400, 415]


class TestFrontendRoutes:
    """Test frontend route accessibility"""
    
    def test_home_page(self, client):
        """Test that home page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'text/html' in response.content_type
    
    def test_api_info_page(self, client):
        """Test API info endpoint"""
        response = client.get('/api')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'message' in data
        assert 'version' in data
        assert 'endpoints' in data


@pytest.mark.integration
class TestIntegrationWorkflow:
    """Integration tests for complete workflows"""
    
    def test_complete_question_workflow(self, client):
        """Test complete question answering workflow"""
        # 1. Check system status
        status_response = client.get('/api/v1/status')
        assert status_response.status_code == 200
        
        # 2. Submit a question
        question_response = client.post('/api/v1/questions',
                                      json={
                                          'question': 'What are the main business risks?',
                                          'k': 3
                                      })
        assert question_response.status_code == 200
        
        # 3. Verify response structure
        data = question_response.get_json()
        assert_valid_question_response(data)
    
    def test_search_workflow(self, client):
        """Test search workflow"""
        # 1. Perform search
        search_response = client.post('/api/v1/search',
                                    json={
                                        'query': 'revenue growth',
                                        'k': 5
                                    })
        assert search_response.status_code == 200
        
        # 2. Verify response structure
        data = search_response.get_json()
        assert_valid_api_response(data)


if __name__ == "__main__":
    print("🧪 SEC Filings QA Agent - API Testing Suite")
    print("=" * 60)
    
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
