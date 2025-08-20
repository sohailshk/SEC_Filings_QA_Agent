"""
Performance and Load Testing for SEC Filings QA Agent

This module provides performance testing to ensure the application
can handle expected loads and responds within acceptable time limits.
"""

import pytest
import time
import threading
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import json


class PerformanceTestSuite:
    """Performance testing suite for the SEC Filings QA Agent"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        
    def measure_response_time(self, url, method="GET", json_data=None, timeout=30):
        """Measure response time for a single request"""
        start_time = time.time()
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=json_data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'success': True,
                'response_time': response_time,
                'status_code': response.status_code,
                'response_size': len(response.content)
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'response_time': end_time - start_time,
                'error': str(e)
            }
    
    def load_test_endpoint(self, url, method="GET", json_data=None, 
                          num_requests=10, concurrent_users=5, timeout=30):
        """Perform load testing on an endpoint"""
        print(f"🔥 Load testing: {url}")
        print(f"📊 {num_requests} requests with {concurrent_users} concurrent users")
        
        results = []
        
        def make_request():
            return self.measure_response_time(url, method, json_data, timeout)
        
        # Execute requests concurrently
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Analyze results
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            
            stats = {
                'total_requests': num_requests,
                'successful_requests': len(successful_requests),
                'failed_requests': len(failed_requests),
                'success_rate': len(successful_requests) / num_requests * 100,
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'median_response_time': statistics.median(response_times),
                'p95_response_time': self.percentile(response_times, 95),
                'p99_response_time': self.percentile(response_times, 99),
                'requests_per_second': len(successful_requests) / max(response_times) if response_times else 0
            }
            
            if len(response_times) > 1:
                stats['std_deviation'] = statistics.stdev(response_times)
            else:
                stats['std_deviation'] = 0
        else:
            stats = {
                'total_requests': num_requests,
                'successful_requests': 0,
                'failed_requests': num_requests,
                'success_rate': 0,
                'error': 'All requests failed'
            }
        
        return stats
    
    def percentile(self, data, percent):
        """Calculate percentile of a dataset"""
        sorted_data = sorted(data)
        index = (percent / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    def test_health_endpoint_performance(self):
        """Test health endpoint performance"""
        url = f"{self.api_base}/health"
        stats = self.load_test_endpoint(url, num_requests=20, concurrent_users=5)
        
        print("\n📈 Health Endpoint Performance:")
        self.print_performance_stats(stats)
        
        # Assertions
        assert stats['success_rate'] >= 95, "Health endpoint success rate should be >= 95%"
        assert stats['avg_response_time'] <= 2.0, "Health endpoint average response time should be <= 2s"
        assert stats['p95_response_time'] <= 5.0, "Health endpoint 95th percentile should be <= 5s"
        
        return stats
    
    def test_status_endpoint_performance(self):
        """Test status endpoint performance"""
        url = f"{self.api_base}/status"
        stats = self.load_test_endpoint(url, num_requests=15, concurrent_users=3)
        
        print("\n📈 Status Endpoint Performance:")
        self.print_performance_stats(stats)
        
        # Assertions
        assert stats['success_rate'] >= 90, "Status endpoint success rate should be >= 90%"
        assert stats['avg_response_time'] <= 3.0, "Status endpoint average response time should be <= 3s"
        
        return stats
    
    def test_question_endpoint_performance(self):
        """Test question endpoint performance"""
        url = f"{self.api_base}/questions"
        json_data = {
            'question': 'What are the main business operations?',
            'k': 3
        }
        
        stats = self.load_test_endpoint(url, method="POST", json_data=json_data,
                                      num_requests=10, concurrent_users=2, timeout=60)
        
        print("\n📈 Question Endpoint Performance:")
        self.print_performance_stats(stats)
        
        # More lenient assertions for complex endpoint
        assert stats['success_rate'] >= 80, "Question endpoint success rate should be >= 80%"
        assert stats['avg_response_time'] <= 30.0, "Question endpoint average response time should be <= 30s"
        
        return stats
    
    def test_frontend_performance(self):
        """Test frontend page load performance"""
        url = self.base_url
        stats = self.load_test_endpoint(url, num_requests=15, concurrent_users=5)
        
        print("\n📈 Frontend Performance:")
        self.print_performance_stats(stats)
        
        # Assertions
        assert stats['success_rate'] >= 95, "Frontend success rate should be >= 95%"
        assert stats['avg_response_time'] <= 2.0, "Frontend average response time should be <= 2s"
        
        return stats
    
    def test_concurrent_mixed_load(self):
        """Test mixed load with different endpoints concurrently"""
        print("\n🔥 Mixed Load Test - Simulating real usage patterns")
        
        def health_check_load():
            url = f"{self.api_base}/health"
            return self.load_test_endpoint(url, num_requests=10, concurrent_users=2)
        
        def status_check_load():
            url = f"{self.api_base}/status"
            return self.load_test_endpoint(url, num_requests=5, concurrent_users=1)
        
        def frontend_load():
            url = self.base_url
            return self.load_test_endpoint(url, num_requests=8, concurrent_users=2)
        
        # Run different loads concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            health_future = executor.submit(health_check_load)
            status_future = executor.submit(status_check_load)
            frontend_future = executor.submit(frontend_load)
            
            health_stats = health_future.result()
            status_stats = status_future.result()
            frontend_stats = frontend_future.result()
        
        print("\n📊 Mixed Load Results:")
        print("Health endpoint:", f"{health_stats['success_rate']:.1f}% success")
        print("Status endpoint:", f"{status_stats['success_rate']:.1f}% success")
        print("Frontend:", f"{frontend_stats['success_rate']:.1f}% success")
        
        # Overall system should handle mixed load well
        overall_success = (
            health_stats['success_rate'] >= 90 and
            status_stats['success_rate'] >= 90 and
            frontend_stats['success_rate'] >= 90
        )
        
        assert overall_success, "System should handle mixed load with >90% success rate"
        
        return {
            'health': health_stats,
            'status': status_stats,
            'frontend': frontend_stats
        }
    
    def print_performance_stats(self, stats):
        """Print formatted performance statistics"""
        if 'error' in stats:
            print(f"❌ Error: {stats['error']}")
            return
        
        print(f"✅ Success Rate: {stats['success_rate']:.1f}%")
        print(f"📊 Requests: {stats['successful_requests']}/{stats['total_requests']}")
        print(f"⚡ Avg Response Time: {stats['avg_response_time']:.3f}s")
        print(f"🏃 Min Response Time: {stats['min_response_time']:.3f}s")
        print(f"🐌 Max Response Time: {stats['max_response_time']:.3f}s")
        print(f"📈 Median Response Time: {stats['median_response_time']:.3f}s")
        print(f"🎯 95th Percentile: {stats['p95_response_time']:.3f}s")
        print(f"🎯 99th Percentile: {stats['p99_response_time']:.3f}s")
        
        if stats['std_deviation'] > 0:
            print(f"📏 Std Deviation: {stats['std_deviation']:.3f}s")
    
    def run_performance_suite(self):
        """Run the complete performance test suite"""
        print("🚀 Starting Performance Test Suite")
        print("=" * 60)
        
        test_results = {}
        
        try:
            # Test individual endpoints
            test_results['health'] = self.test_health_endpoint_performance()
            test_results['status'] = self.test_status_endpoint_performance()
            test_results['frontend'] = self.test_frontend_performance()
            
            # Test more complex endpoint (may be slower)
            print("\n⚠️ Testing question endpoint (may take longer)...")
            test_results['question'] = self.test_question_endpoint_performance()
            
            # Test mixed load
            test_results['mixed_load'] = self.test_concurrent_mixed_load()
            
            # Summary
            print("\n" + "=" * 60)
            print("🏆 Performance Test Summary")
            print("=" * 60)
            
            for test_name, result in test_results.items():
                if test_name == 'mixed_load':
                    print(f"Mixed Load Test: ✅ PASS")
                else:
                    success_rate = result.get('success_rate', 0)
                    avg_time = result.get('avg_response_time', 0)
                    status = "✅ PASS" if success_rate >= 80 else "❌ FAIL"
                    print(f"{test_name.title()}: {status} ({success_rate:.1f}% success, {avg_time:.2f}s avg)")
            
            return test_results
            
        except Exception as e:
            print(f"❌ Performance test suite failed: {e}")
            return None


# Pytest integration
def test_health_performance():
    """Pytest wrapper for health endpoint performance test"""
    tester = PerformanceTestSuite()
    result = tester.test_health_endpoint_performance()
    assert result['success_rate'] >= 95


def test_status_performance():
    """Pytest wrapper for status endpoint performance test"""
    tester = PerformanceTestSuite()
    result = tester.test_status_endpoint_performance()
    assert result['success_rate'] >= 90


def test_frontend_performance():
    """Pytest wrapper for frontend performance test"""
    tester = PerformanceTestSuite()
    result = tester.test_frontend_performance()
    assert result['success_rate'] >= 95


@pytest.mark.slow
def test_question_performance():
    """Pytest wrapper for question endpoint performance test"""
    tester = PerformanceTestSuite()
    result = tester.test_question_endpoint_performance()
    assert result['success_rate'] >= 70  # More lenient for complex operations


@pytest.mark.slow
def test_mixed_load_performance():
    """Pytest wrapper for mixed load performance test"""
    tester = PerformanceTestSuite()
    result = tester.test_concurrent_mixed_load()
    assert result is not None


if __name__ == "__main__":
    print("🧪 SEC Filings QA Agent - Performance Testing Suite")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running, starting performance tests...")
            tester = PerformanceTestSuite()
            results = tester.run_performance_suite()
            
            if results:
                print("\n🎉 Performance testing completed successfully!")
            else:
                print("\n❌ Performance testing failed!")
        else:
            print("❌ Server returned non-200 status code")
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the application first:")
        print("   python app.py")
        print("   Then run the performance tests.")
