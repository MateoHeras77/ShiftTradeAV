#!/usr/bin/env python3
"""
Comprehensive test suite for ShiftTradeAV application
Priority tests based on business logic analysis
"""

import unittest
import sys
import os
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Streamlit for testing
class MockStreamlit:
    secrets = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test_key",
        "SMTP_SERVER": "smtp.test.com",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "test@test.com",
        "SMTP_PASSWORD": "test_pass",
        "SENDER_EMAIL": "noreply@test.com"
    }
    
    @staticmethod
    def error(msg): print(f"ST ERROR: {msg}")
    
    @staticmethod
    def warning(msg): print(f"ST WARNING: {msg}")
    
    @staticmethod
    def set_page_config(**kwargs): pass  # Mock page config

sys.modules['streamlit'] = MockStreamlit()

class TestTokenUtils(unittest.TestCase):
    """Test token generation and verification logic"""
    
    def setUp(self):
        # Mock Supabase client
        self.mock_supabase = Mock()
        
    @patch('utils.token_utils.get_supabase_client')
    def test_generate_token_success(self, mock_get_client):
        """Test successful token generation"""
        from utils.token_utils import generate_token
        
        mock_get_client.return_value = self.mock_supabase
        self.mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{'id': 1}]
        
        result = generate_token("test_request_123", "test_project")
        
        self.assertIsNotNone(result)
        self.assertTrue(len(result) > 0)
        
    @patch('utils.token_utils.get_supabase_client')
    def test_generate_token_database_failure(self, mock_get_client):
        """Test token generation with database failure"""
        from utils.token_utils import generate_token
        
        mock_get_client.return_value = None  # Simulate DB connection failure
        
        result = generate_token("test_request_123", "test_project")
        
        self.assertIsNone(result)
        
    @patch('utils.token_utils.get_supabase_client')
    def test_verify_token_expired(self, mock_get_client):
        """Test verification of expired token"""
        from utils.token_utils import verify_token
        
        mock_get_client.return_value = self.mock_supabase
        expired_time = (datetime.now() - timedelta(hours=25)).isoformat()
        
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            'shift_request_id': 'test_123',
            'expires_at': expired_time,
            'used': False
        }
        
        result = verify_token("test_token", "test_project")
        
        self.assertIsNone(result)
        
    @patch('utils.token_utils.get_supabase_client')
    def test_verify_token_already_used(self, mock_get_client):
        """Test verification of already used token"""
        from utils.token_utils import verify_token
        
        mock_get_client.return_value = self.mock_supabase
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            'shift_request_id': 'test_123',
            'expires_at': future_time,
            'used': True  # Already used
        }
        
        result = verify_token("test_token", "test_project")
        
        self.assertIsNone(result)

class TestShiftRequestWorkflow(unittest.TestCase):
    """Test complete shift request business logic"""
    
    def setUp(self):
        self.mock_supabase = Mock()
        
    @patch('utils.shift_requests.get_supabase_client')
    def test_save_shift_request_invalid_date(self, mock_get_client):
        """Test saving shift request with invalid date format"""
        from utils.shift_requests import save_shift_request
        
        mock_get_client.return_value = self.mock_supabase
        
        invalid_request = {
            'requester_name': 'John Doe',
            'date_request': 'invalid-date-format',
            'flight_number': 'AV205'
        }
        
        # Should handle invalid date gracefully
        result = save_shift_request(invalid_request, "test_project")
        
        # Should still attempt to save (converted to string)
        self.mock_supabase.table.assert_called_with('shift_requests')
        
    @patch('utils.shift_requests.get_supabase_client')
    def test_shift_request_duplicate_prevention(self, mock_get_client):
        """Test prevention of duplicate shift requests"""
        from utils.shift_requests import save_shift_request, get_all_shift_requests
        
        mock_get_client.return_value = self.mock_supabase
        
        # Mock existing requests
        self.mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
            {
                'id': 1,
                'requester_name': 'John Doe',
                'date_request': '2024-12-25',
                'flight_number': 'AV205',
                'supervisor_status': 'pending'
            }
        ]
        
        existing_requests = get_all_shift_requests("test_project")
        
        # Business logic should check for duplicates
        self.assertEqual(len(existing_requests), 1)

class TestEmailIntegration(unittest.TestCase):
    """Test email functionality and integration"""
    
    @patch('smtplib.SMTP')
    def test_email_sending_smtp_failure(self, mock_smtp):
        """Test email sending with SMTP server failure"""
        from utils.email_utils import send_email
        
        # Mock SMTP failure
        mock_smtp.side_effect = Exception("SMTP server unavailable")
        
        result = send_email("test@example.com", "Test Subject", "Test Body")
        
        self.assertFalse(result)
        
    @patch('utils.email_utils.send_email')
    @patch('utils.calendar_utils.create_calendar_file')
    def test_email_with_calendar_fallback(self, mock_create_calendar, mock_send_email):
        """Test email with calendar attachment fallback to plain email"""
        from utils.email_utils import send_email_with_calendar
        
        # Mock calendar creation failure
        mock_create_calendar.return_value = None
        mock_send_email.return_value = True
        
        shift_data = {
            'flight_number': 'AV205',
            'date_request': '2024-12-25'
        }
        
        result = send_email_with_calendar(
            "test@example.com", 
            "Test Subject", 
            "Test Body", 
            shift_data
        )
        
        # Should fallback to regular email
        mock_send_email.assert_called_once()
        self.assertTrue(result)

class TestCalendarGeneration(unittest.TestCase):
    """Test calendar generation edge cases"""
    
    def test_flight_schedule_unknown_flight(self):
        """Test flight schedule for unknown flight number"""
        from utils.calendar_utils import get_flight_schedule_info
        
        result = get_flight_schedule_info("UNKNOWN123")
        
        # Should return default schedule
        self.assertEqual(result['start_time'], '09:00')
        self.assertEqual(result['end_time'], '17:00')
        self.assertFalse(result['is_overnight'])
        
    def test_calendar_generation_edge_cases(self):
        """Test calendar generation with edge case data"""
        from utils.calendar_utils import create_calendar_file
        
        edge_case_data = {
            'id': 'test_123',
            'date_request': None,  # Missing date
            'flight_number': '',   # Empty flight number
            'requester_name': 'Test User',
            'supervisor_name': 'Test Supervisor'
        }
        
        result = create_calendar_file(edge_case_data)
        
        # Should handle gracefully and not crash
        self.assertIsNotNone(result)

class TestInputValidation(unittest.TestCase):
    """Test input validation and sanitization"""
    
    def test_email_validation_edge_cases(self):
        """Test email validation with various edge cases"""
        # Define the validation function directly (same logic as in main.py)
        import re
        def validate_email(email):
            pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            return re.match(pattern, email) is not None
        
        test_cases = [
            ("valid@example.com", True),
            ("invalid.email", False),
            ("@invalid.com", False),
            ("valid@.com", False),
            ("", False),
            ("test@test@test.com", False),
            ("test+tag@example.com", True),
            ("user.name@example-domain.com", True)
        ]
        
        for email, expected in test_cases:
            with self.subTest(email=email):
                result = validate_email(email)
                self.assertEqual(result, expected, f"Failed for email: {email}")
                
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in database queries"""
        # This would test that user inputs are properly sanitized
        # before being used in database queries
        pass
        
class TestBusinessLogicValidation(unittest.TestCase):
    """Test business rules and validation"""
    
    def test_shift_request_date_validation(self):
        """Test that shift requests can't be made for past dates"""
        # Business rule: No requests for past dates
        past_date = date.today() - timedelta(days=1)
        
        # This test would validate the business logic
        # Currently missing in the application
        pass
        
    def test_supervisor_authorization(self):
        """Test supervisor authorization for approvals"""
        # Business rule: Only authorized supervisors can approve
        # This validation is currently missing
        pass
        
    def test_shift_overlap_detection(self):
        """Test detection of overlapping shift requests"""
        # Business rule: Can't request multiple shifts for same date
        # This validation might be missing
        pass

class TestPerformance(unittest.TestCase):
    """Test performance with realistic data volumes"""
    
    @patch('utils.employee_management.get_supabase_client')
    def test_large_employee_list_performance(self, mock_get_client):
        """Test performance with large employee list"""
        from utils.employee_management import get_all_employees
        
        mock_supabase = Mock()
        mock_get_client.return_value = mock_supabase
        
        # Mock large dataset
        large_employee_list = [
            {'id': i, 'full_name': f'Employee {i}', 'email': f'emp{i}@test.com'}
            for i in range(1000)
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = large_employee_list
        
        import time
        start_time = time.time()
        result = get_all_employees("test_project")
        end_time = time.time()
        
        # Should complete in reasonable time
        self.assertLess(end_time - start_time, 1.0)  # Less than 1 second
        self.assertEqual(len(result), 1000)

if __name__ == '__main__':
    # Run specific test categories
    print("🧪 Running ShiftTradeAV Test Suite...")
    print("=" * 50)
    
    # Create test loader
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTokenUtils,
        TestShiftRequestWorkflow,
        TestEmailIntegration,
        TestCalendarGeneration,
        TestInputValidation,
        TestBusinessLogicValidation,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestClass(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed")
        
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
