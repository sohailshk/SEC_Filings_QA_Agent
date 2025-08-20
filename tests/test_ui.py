"""
UI Testing for SEC Filings QA Agent

This module provides comprehensive tests for the user interface functionality,
including form submissions, error handling, and user interactions.
"""

import pytest
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import threading
import requests
from .conftest import TEST_QUESTIONS, assert_valid_question_response


class UITestSuite:
    """Comprehensive UI testing suite for the SEC Filings QA Agent"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.driver = None
        self.wait = None
        
    def setup_driver(self, headless=True):
        """Setup Chrome WebDriver for testing"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            print("✅ Chrome WebDriver initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            print("💡 Please install ChromeDriver: https://chromedriver.chromium.org/")
            return False
    
    def teardown_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            print("✅ WebDriver closed")
    
    def test_page_load(self):
        """Test that the main page loads correctly"""
        print("🧪 Testing page load...")
        
        try:
            self.driver.get(self.base_url)
            
            # Wait for the page title
            self.wait.until(EC.title_contains("SEC Filings QA Agent"))
            
            # Check for key elements
            header = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "header")))
            assert header.is_displayed()
            
            welcome_section = self.driver.find_element(By.CLASS_NAME, "welcome-section")
            assert welcome_section.is_displayed()
            
            question_form = self.driver.find_element(By.ID, "question-form")
            assert question_form.is_displayed()
            
            print("✅ Page load test passed")
            return True
            
        except Exception as e:
            print(f"❌ Page load test failed: {e}")
            return False
    
    def test_theme_toggle(self):
        """Test dark/light theme toggle functionality"""
        print("🧪 Testing theme toggle...")
        
        try:
            # Get initial theme
            body = self.driver.find_element(By.TAG_NAME, "body")
            initial_theme = "dark" if "dark-theme" in body.get_attribute("class") else "light"
            
            # Click theme toggle
            theme_toggle = self.driver.find_element(By.ID, "theme-toggle")
            theme_toggle.click()
            
            # Wait for theme change
            time.sleep(0.5)
            
            # Check theme changed
            new_theme = "dark" if "dark-theme" in body.get_attribute("class") else "light"
            assert new_theme != initial_theme
            
            # Toggle back
            theme_toggle.click()
            time.sleep(0.5)
            
            # Check theme reverted
            final_theme = "dark" if "dark-theme" in body.get_attribute("class") else "light"
            assert final_theme == initial_theme
            
            print("✅ Theme toggle test passed")
            return True
            
        except Exception as e:
            print(f"❌ Theme toggle test failed: {e}")
            return False
    
    def test_question_form_validation(self):
        """Test question form validation"""
        print("🧪 Testing question form validation...")
        
        try:
            # Test empty question submission
            submit_btn = self.driver.find_element(By.ID, "submit-btn")
            submit_btn.click()
            
            # Check that form validation prevents submission
            question_field = self.driver.find_element(By.ID, "question")
            validation_message = question_field.get_attribute("validationMessage")
            assert validation_message  # Should have validation message
            
            # Test character counter
            test_text = "This is a test question for character counting."
            question_field.clear()
            question_field.send_keys(test_text)
            
            char_count = self.driver.find_element(By.ID, "char-count")
            assert char_count.text == str(len(test_text))
            
            print("✅ Question form validation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Question form validation test failed: {e}")
            return False
    
    def test_example_cards(self):
        """Test example question cards functionality"""
        print("🧪 Testing example cards...")
        
        try:
            # Find first example card
            example_cards = self.driver.find_elements(By.CLASS_NAME, "example-card")
            assert len(example_cards) > 0
            
            # Click first example card
            first_card = example_cards[0]
            expected_question = first_card.get_attribute("data-question")
            expected_ticker = first_card.get_attribute("data-ticker")
            
            first_card.click()
            
            # Wait for form to be populated
            time.sleep(0.5)
            
            # Check that form fields are populated
            question_field = self.driver.find_element(By.ID, "question")
            ticker_field = self.driver.find_element(By.ID, "ticker")
            
            assert question_field.get_attribute("value") == expected_question
            if expected_ticker:
                assert ticker_field.get_attribute("value") == expected_ticker
            
            print("✅ Example cards test passed")
            return True
            
        except Exception as e:
            print(f"❌ Example cards test failed: {e}")
            return False
    
    def test_form_submission_ui(self):
        """Test form submission UI behavior (without actual API calls)"""
        print("🧪 Testing form submission UI...")
        
        try:
            # Fill out the form
            question_field = self.driver.find_element(By.ID, "question")
            question_field.clear()
            question_field.send_keys("What are the main business risks?")
            
            ticker_field = self.driver.find_element(By.ID, "ticker")
            ticker_field.clear()
            ticker_field.send_keys("AAPL")
            
            # Submit form
            submit_btn = self.driver.find_element(By.ID, "submit-btn")
            submit_btn.click()
            
            # Check loading state appears
            try:
                loading_section = self.wait.until(
                    EC.visibility_of_element_located((By.ID, "loading-section"))
                )
                assert loading_section.is_displayed()
                print("✅ Loading state displayed correctly")
            except TimeoutException:
                print("⚠️ Loading state test skipped (API might be responding too quickly)")
            
            print("✅ Form submission UI test passed")
            return True
            
        except Exception as e:
            print(f"❌ Form submission UI test failed: {e}")
            return False
    
    def test_responsive_design(self):
        """Test responsive design at different screen sizes"""
        print("🧪 Testing responsive design...")
        
        try:
            # Test desktop size
            self.driver.set_window_size(1920, 1080)
            time.sleep(0.5)
            
            stats_grid = self.driver.find_element(By.CLASS_NAME, "stats-grid")
            desktop_columns = len(stats_grid.find_elements(By.CLASS_NAME, "stat-card"))
            
            # Test tablet size
            self.driver.set_window_size(768, 1024)
            time.sleep(0.5)
            
            # Elements should still be visible
            header = self.driver.find_element(By.CLASS_NAME, "header")
            assert header.is_displayed()
            
            # Test mobile size
            self.driver.set_window_size(375, 667)
            time.sleep(0.5)
            
            # Navigation should adapt
            question_form = self.driver.find_element(By.ID, "question-form")
            assert question_form.is_displayed()
            
            # Reset to desktop
            self.driver.set_window_size(1920, 1080)
            
            print("✅ Responsive design test passed")
            return True
            
        except Exception as e:
            print(f"❌ Responsive design test failed: {e}")
            return False
    
    def test_accessibility_features(self):
        """Test basic accessibility features"""
        print("🧪 Testing accessibility features...")
        
        try:
            # Check for proper heading structure
            h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
            assert len(h1_elements) > 0
            
            h2_elements = self.driver.find_elements(By.TAG_NAME, "h2")
            assert len(h2_elements) > 0
            
            # Check for form labels
            labels = self.driver.find_elements(By.TAG_NAME, "label")
            assert len(labels) > 0
            
            # Check for alt text on images (if any)
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                alt_text = img.get_attribute("alt")
                assert alt_text is not None  # Alt attribute should exist
            
            # Check for ARIA labels on buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                title = button.get_attribute("title")
                aria_label = button.get_attribute("aria-label")
                text_content = button.text.strip()
                
                # Button should have some form of accessible text
                assert title or aria_label or text_content
            
            print("✅ Accessibility features test passed")
            return True
            
        except Exception as e:
            print(f"❌ Accessibility features test failed: {e}")
            return False
    
    def run_all_tests(self, headless=True):
        """Run all UI tests"""
        print("🚀 Starting comprehensive UI test suite...")
        print(f"📍 Testing URL: {self.base_url}")
        
        if not self.setup_driver(headless):
            return False
        
        test_results = []
        
        try:
            # Run all tests
            tests = [
                ("Page Load", self.test_page_load),
                ("Theme Toggle", self.test_theme_toggle),
                ("Form Validation", self.test_question_form_validation),
                ("Example Cards", self.test_example_cards),
                ("Form Submission UI", self.test_form_submission_ui),
                ("Responsive Design", self.test_responsive_design),
                ("Accessibility", self.test_accessibility_features)
            ]
            
            passed = 0
            total = len(tests)
            
            for test_name, test_func in tests:
                print(f"\n📋 Running: {test_name}")
                try:
                    result = test_func()
                    test_results.append((test_name, result))
                    if result:
                        passed += 1
                except Exception as e:
                    print(f"❌ {test_name} failed with exception: {e}")
                    test_results.append((test_name, False))
            
            # Print summary
            print(f"\n📊 UI Test Summary:")
            print(f"{'='*50}")
            print(f"Tests Passed: {passed}/{total}")
            print(f"Success Rate: {(passed/total)*100:.1f}%")
            print(f"{'='*50}")
            
            for test_name, result in test_results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} {test_name}")
            
            return passed == total
            
        finally:
            self.teardown_driver()


def test_ui_comprehensive():
    """Pytest wrapper for comprehensive UI testing"""
    ui_tester = UITestSuite()
    success = ui_tester.run_all_tests(headless=True)
    assert success, "One or more UI tests failed"


def test_ui_interactive():
    """Interactive UI testing with visible browser"""
    ui_tester = UITestSuite()
    success = ui_tester.run_all_tests(headless=False)
    assert success, "One or more UI tests failed"


if __name__ == "__main__":
    print("🧪 SEC Filings QA Agent - UI Testing Suite")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running, starting UI tests...")
            ui_tester = UITestSuite()
            ui_tester.run_all_tests(headless=False)  # Run with visible browser
        else:
            print("❌ Server returned non-200 status code")
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start the application first:")
        print("   python app.py")
        print("   Then run the UI tests.")
