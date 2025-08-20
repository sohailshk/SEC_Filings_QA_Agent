# Testing Guide for SEC Filings QA Agent

## 🧪 Comprehensive Testing Instructions

This guide provides step-by-step instructions for testing all aspects of the SEC Filings QA Agent, including UI, API, and performance testing.

---

## Prerequisites

### 1. Install Testing Dependencies

```bash
# Install additional testing packages
pip install pytest pytest-cov selenium requests

# For UI testing (optional - requires Chrome browser)
# Download ChromeDriver from: https://chromedriver.chromium.org/
# Add ChromeDriver to your PATH
```

### 2. Start the Application

```bash
# Make sure your application is running
python app.py

# Verify it's running at http://localhost:5000
curl http://localhost:5000/api/v1/health
```

---

## 🖥️ UI Testing

### Manual UI Testing Checklist

#### 1. Page Load and Basic Functionality
- [ ] Page loads without errors
- [ ] All sections are visible (header, welcome, stats, form, examples, footer)
- [ ] Theme toggle works (dark/light mode)
- [ ] Responsive design works on different screen sizes

#### 2. Question Form Testing
- [ ] Form validation works (empty question prevention)
- [ ] Character counter updates correctly
- [ ] All form fields accept input
- [ ] Example cards populate the form when clicked
- [ ] Form submission shows loading state

#### 3. Theme and Visual Testing
- [ ] Dark theme applies correctly
- [ ] Light theme applies correctly
- [ ] Theme preference persists after page reload
- [ ] All colors and contrasts are appropriate
- [ ] Icons and fonts load correctly

#### 4. Responsive Design Testing
- [ ] Desktop layout (1920x1080)
- [ ] Tablet layout (768x1024)
- [ ] Mobile layout (375x667)
- [ ] All elements remain functional at different sizes

### Automated UI Testing

```bash
# Run automated UI tests (requires ChromeDriver)
cd tests
python test_ui.py

# Run with visible browser (for debugging)
python -c "
from test_ui import UITestSuite
tester = UITestSuite()
tester.run_all_tests(headless=False)
"
```

### UI Test Scenarios

#### Scenario 1: Basic Question Flow
1. Open the application
2. Click on the first example card
3. Verify form is populated
4. Modify the question slightly
5. Submit the form
6. Verify loading state appears
7. Check results display (if data available)

#### Scenario 2: Form Validation
1. Try submitting empty form
2. Enter a very long question (>1000 chars)
3. Enter invalid ticker (>10 chars)
4. Verify validation messages appear

#### Scenario 3: Theme Testing
1. Toggle to dark theme
2. Verify all elements are properly styled
3. Reload page and verify theme persists
4. Toggle back to light theme

---

## 🔌 API Testing

### Manual API Testing

#### 1. Health Check
```bash
# Test health endpoint
curl -X GET http://localhost:5000/api/v1/health

# Expected response:
{
  "success": true,
  "message": "Service is healthy",
  "data": {
    "database": {...},
    "vector_database": {...},
    "services_initialized": true
  }
}
```

#### 2. System Status
```bash
# Test status endpoint
curl -X GET http://localhost:5000/api/v1/status

# Expected response includes system statistics
```

#### 3. Question Answering
```bash
# Test question endpoint
curl -X POST http://localhost:5000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main business risks?",
    "k": 5
  }'

# With company filter
curl -X POST http://localhost:5000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are Apple'\''s revenue drivers?",
    "ticker": "AAPL",
    "filing_type": "10-K",
    "k": 5
  }'
```

#### 4. Search Functionality
```bash
# Test search endpoint
curl -X POST http://localhost:5000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "revenue growth strategy",
    "k": 10
  }'
```

#### 5. Company Information
```bash
# Test company endpoint
curl -X GET http://localhost:5000/api/v1/companies/AAPL
```

#### 6. Process Filings (requires API keys)
```bash
# Test processing endpoint
curl -X POST http://localhost:5000/api/v1/companies/AAPL/process \
  -H "Content-Type: application/json" \
  -d '{
    "filing_type": "8-K",
    "limit": 2
  }'
```

### Automated API Testing

```bash
# Run all API tests
pytest tests/test_api.py -v

# Run specific test classes
pytest tests/test_api.py::TestHealthEndpoint -v
pytest tests/test_api.py::TestQuestionEndpoint -v

# Run with coverage
pytest tests/test_api.py --cov=app --cov-report=html
```

### API Test Scenarios

#### Scenario 1: Complete Question Workflow
1. Check system status
2. Submit a question
3. Verify response format
4. Check for proper error handling

#### Scenario 2: Error Handling
1. Submit invalid requests
2. Test malformed JSON
3. Test missing required fields
4. Verify appropriate error messages

#### Scenario 3: Performance Validation
1. Submit multiple concurrent requests
2. Measure response times
3. Check for memory leaks
4. Verify system stability

---

## ⚡ Performance Testing

### Load Testing

```bash
# Run performance tests
python tests/test_performance.py

# Or with pytest
pytest tests/test_performance.py -v
```

### Performance Test Scenarios

#### 1. Individual Endpoint Testing
- Health endpoint: 20 requests, 5 concurrent users
- Status endpoint: 15 requests, 3 concurrent users
- Frontend: 15 requests, 5 concurrent users

#### 2. Mixed Load Testing
- Simulate real user patterns
- Multiple endpoints simultaneously
- Measure overall system performance

#### 3. Stress Testing
```bash
# Custom stress test script
python -c "
from tests.test_performance import PerformanceTestSuite
tester = PerformanceTestSuite()

# Heavy load test
stats = tester.load_test_endpoint(
    'http://localhost:5000/api/v1/health',
    num_requests=100,
    concurrent_users=10
)
print('Heavy load results:', stats)
"
```

### Performance Benchmarks

#### Expected Performance Metrics
- **Health endpoint**: < 1s average response time
- **Status endpoint**: < 2s average response time
- **Question endpoint**: < 30s average response time
- **Frontend**: < 1s average response time
- **Success rate**: > 95% for all endpoints

---

## 🔍 Integration Testing

### End-to-End Testing Scenarios

#### Scenario 1: Complete User Journey
1. User visits the application
2. Browses example questions
3. Submits a custom question
4. Reviews the answer and sources
5. Submits another question with filters

#### Scenario 2: Data Processing Workflow
1. Process new SEC filings
2. Verify data is stored correctly
3. Search for content from new filings
4. Ask questions about the new data

#### Scenario 3: Error Recovery
1. Submit invalid requests
2. Verify appropriate error messages
3. Test system recovery
4. Verify system remains stable

### Test Data Validation

#### 1. Response Format Validation
```python
# All API responses should follow this format
{
  "success": true/false,
  "message": "Description of result",
  "data": {...} or "error": "Error description"
}
```

#### 2. Answer Quality Validation
- Answers should be relevant to questions
- Sources should be properly cited
- Response time should be reasonable
- No system errors in responses

---

## 🐛 Debugging and Troubleshooting

### Common Issues and Solutions

#### 1. UI Tests Failing
```bash
# Check if ChromeDriver is installed and in PATH
chromedriver --version

# Install ChromeDriver if missing
# Download from: https://chromedriver.chromium.org/
```

#### 2. API Tests Failing
```bash
# Check if server is running
curl http://localhost:5000/api/v1/health

# Check application logs
tail -f app.log
```

#### 3. Performance Issues
```bash
# Monitor system resources
htop  # or Task Manager on Windows

# Check for memory leaks
# Monitor application memory usage during tests
```

### Test Environment Setup

#### 1. Clean Test Environment
```bash
# Reset test database
rm -f data/test_sec_filings.db
rm -rf data/test_vector_index/

# Clear test logs
rm -f test_app.log
```

#### 2. Mock Data Setup
```python
# Use the test configuration in conftest.py
# Tests will use temporary directories and mock data
```

---

## 📊 Test Reporting

### Generate Test Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Generate XML report for CI/CD
pytest tests/ --cov=app --cov-report=xml --junitxml=report.xml

# Generate comprehensive test report
pytest tests/ -v --tb=short --cov=app --cov-report=term-missing
```

### Test Results Interpretation

#### Coverage Targets
- **Minimum**: 70% code coverage
- **Good**: 80% code coverage
- **Excellent**: 90% code coverage

#### Performance Targets
- **API Response Time**: < 2s for simple endpoints
- **UI Load Time**: < 3s for initial page load
- **Success Rate**: > 95% for all tests

---

## ✅ Testing Checklist

### Before Deployment
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] UI tests pass (manual and automated)
- [ ] API tests pass
- [ ] Performance tests meet benchmarks
- [ ] Security tests pass
- [ ] Cross-browser testing completed
- [ ] Mobile responsiveness verified
- [ ] Error handling tested
- [ ] Documentation updated

### After Deployment
- [ ] Health check responds correctly
- [ ] All endpoints accessible
- [ ] UI loads properly
- [ ] Sample questions work
- [ ] Error pages display correctly
- [ ] Performance meets expectations
- [ ] Monitoring and logging work
- [ ] Backup and recovery tested

---

## 🎯 Continuous Testing

### Automated Testing Pipeline

```bash
# Create a simple test script
cat > run_tests.sh << 'EOF'
#!/bin/bash
echo "🧪 Running comprehensive test suite..."

# Start server in background
python app.py &
SERVER_PID=$!
sleep 10  # Wait for server to start

# Run tests
echo "Running API tests..."
pytest tests/test_api.py -v

echo "Running performance tests..."
pytest tests/test_performance.py -v

echo "Running UI tests..."
python tests/test_ui.py

# Stop server
kill $SERVER_PID

echo "✅ All tests completed!"
EOF

chmod +x run_tests.sh
./run_tests.sh
```

### Regular Testing Schedule
- **Daily**: Automated API and unit tests
- **Weekly**: Full UI and performance testing
- **Before releases**: Complete test suite
- **After deployment**: Smoke tests and health checks

---

## 📚 Additional Resources

### Testing Tools
- [Pytest Documentation](https://docs.pytest.org/)
- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [Flask Testing Guide](https://flask.palletsprojects.com/en/2.3.x/testing/)

### Performance Tools
- [Locust](https://locust.io/) - Advanced load testing
- [Artillery](https://artillery.io/) - Performance testing
- [k6](https://k6.io/) - Developer-centric load testing

### Monitoring Tools
- [Sentry](https://sentry.io/) - Error tracking
- [New Relic](https://newrelic.com/) - Application monitoring
- [Datadog](https://www.datadoghq.com/) - Infrastructure monitoring

---

## 🎉 Conclusion

This comprehensive testing guide ensures your SEC Filings QA Agent is thoroughly tested across all dimensions:

- **Functionality**: All features work as expected
- **Performance**: Meets speed and scalability requirements
- **Reliability**: Handles errors gracefully
- **Usability**: Provides excellent user experience
- **Security**: Protects against common vulnerabilities

Follow this guide regularly to maintain high quality and reliability of your application!
