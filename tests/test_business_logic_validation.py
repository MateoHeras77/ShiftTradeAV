#!/usr/bin/env python3
"""
Business Logic Validation Tests for ShiftTradeAV
Tests critical business rules and validation logic that should be implemented.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
import uuid

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Streamlit before importing any modules that use it
mock_streamlit = Mock()
mock_streamlit.secrets = {
    'SUPABASE_URL': 'https://test.supabase.co',
    'SUPABASE_KEY': 'test-key',
    'SMTP_SERVER': 'smtp.test.com',
    'SMTP_PORT': '587',
    'SMTP_USERNAME': 'test@test.com',
    'SMTP_PASSWORD': 'test-password',
    'SENDER_EMAIL': 'noreply@test.com'
}
mock_streamlit.session_state = {}
sys.modules['streamlit'] = mock_streamlit

from utils.shift_requests import get_all_shift_requests, save_shift_request
from utils.employee_management import get_all_employees, get_employee_by_email
from utils.token_utils import generate_token, verify_token
from utils.supabase_client import get_supabase_client


class TestBusinessLogicValidation(unittest.TestCase):
    """Test critical business logic validation rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_date_future = datetime.now() + timedelta(days=7)
        self.test_date_past = datetime.now() - timedelta(days=1)
        self.test_date_today = datetime.now()
        
        # Sample test data
        self.valid_employee = {
            'id': 1,
            'nombre': 'Juan Pérez',
            'email': 'juan.perez@avianca.com',
            'cargo': 'Piloto',
            'supervisor_email': 'supervisor@avianca.com'
        }
        
        self.valid_shift_request = {
            'flight_number': 'AV205',
            'date': self.test_date_future.strftime('%Y-%m-%d'),
            'employee_email': 'juan.perez@avianca.com',
            'employee_name': 'Juan Pérez',
            'supervisor_email': 'supervisor@avianca.com'
        }

    @patch('utils.supabase_client.get_supabase_client')
    def test_past_date_validation(self, mock_supabase):
        """Test that requests for past dates are rejected."""
        print("🧪 Testing Past Date Validation...")
        
        # Test case 1: Past date should be rejected
        past_request = self.valid_shift_request.copy()
        past_request['date'] = self.test_date_past.strftime('%Y-%m-%d')
        
        # Mock Supabase to not create the request
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # This should implement validation logic
        result = self._validate_request_date(past_request['date'])
        self.assertFalse(result, "Past date requests should be rejected")
        print(f"   ✅ Past date {past_request['date']} correctly rejected")
        
        # Test case 2: Today should be allowed
        today_request = self.valid_shift_request.copy()
        today_request['date'] = self.test_date_today.strftime('%Y-%m-%d')
        
        result = self._validate_request_date(today_request['date'])
        self.assertTrue(result, "Today's date should be allowed")
        print(f"   ✅ Today's date {today_request['date']} correctly accepted")
        
        # Test case 3: Future date should be allowed
        future_request = self.valid_shift_request.copy()
        future_request['date'] = self.test_date_future.strftime('%Y-%m-%d')
        
        result = self._validate_request_date(future_request['date'])
        self.assertTrue(result, "Future date should be allowed")
        print(f"   ✅ Future date {future_request['date']} correctly accepted")

    def _validate_request_date(self, request_date):
        """
        Business logic validation for request dates.
        This is what should be implemented in the actual application.
        """
        try:
            request_dt = datetime.strptime(request_date, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            # Rule: Cannot request shifts for past dates
            if request_dt < today:
                return False
                
            # Rule: Cannot request shifts more than 90 days in advance
            max_advance_days = 90
            if request_dt > today + timedelta(days=max_advance_days):
                return False
                
            return True
        except (ValueError, TypeError):
            return False

    @patch('utils.supabase_client.get_supabase_client')
    def test_duplicate_request_prevention(self, mock_supabase):
        """Test that duplicate requests are prevented."""
        print("🧪 Testing Duplicate Request Prevention...")
        
        # Mock existing requests
        existing_requests = [
            {
                'id': 1,
                'flight_number': 'AV205',
                'date': self.test_date_future.strftime('%Y-%m-%d'),
                'employee_email': 'juan.perez@avianca.com',
                'status': 'pending'
            }
        ]
        
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = existing_requests
        mock_supabase.return_value = mock_client
        
        # Test duplicate request
        duplicate_request = self.valid_shift_request.copy()
        
        has_duplicate = self._check_duplicate_request(
            duplicate_request['employee_email'],
            duplicate_request['flight_number'],
            duplicate_request['date']
        )
        
        self.assertTrue(has_duplicate, "Duplicate request should be detected")
        print("   ✅ Duplicate request correctly detected")
        
        # Test non-duplicate request
        unique_request = self.valid_shift_request.copy()
        unique_request['flight_number'] = 'AV255'
        
        # Mock no existing requests for this flight
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        has_duplicate = self._check_duplicate_request(
            unique_request['employee_email'],
            unique_request['flight_number'],
            unique_request['date']
        )
        
        self.assertFalse(has_duplicate, "Unique request should not be flagged as duplicate")
        print("   ✅ Unique request correctly allowed")

    def _check_duplicate_request(self, employee_email, flight_number, date):
        """
        Business logic to check for duplicate requests.
        This is what should be implemented in the actual application.
        """
        try:
            supabase = get_supabase_client()
            
            # Check for existing pending requests with same employee, flight, and date
            result = supabase.table('shift_requests').select('*').eq(
                'employee_email', employee_email
            ).eq(
                'flight_number', flight_number
            ).eq(
                'date', date
            ).execute()
            
            # Check if any pending requests exist
            existing_requests = [req for req in result.data if req.get('status') in ['pending', 'approved']]
            return len(existing_requests) > 0
            
        except Exception as e:
            print(f"Error checking duplicates: {e}")
            return False

    @patch('utils.supabase_client.get_supabase_client')
    def test_supervisor_authorization(self, mock_supabase):
        """Test supervisor authorization logic."""
        print("🧪 Testing Supervisor Authorization...")
        
        # Mock employee data
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                'email': 'juan.perez@avianca.com',
                'supervisor_email': 'supervisor@avianca.com',
                'cargo': 'Piloto'
            }
        ]
        mock_supabase.return_value = mock_client
        
        # Test valid supervisor
        is_authorized = self._validate_supervisor_authorization(
            'supervisor@avianca.com',
            'juan.perez@avianca.com'
        )
        self.assertTrue(is_authorized, "Valid supervisor should be authorized")
        print("   ✅ Valid supervisor correctly authorized")
        
        # Test invalid supervisor
        is_authorized = self._validate_supervisor_authorization(
            'wrong.supervisor@avianca.com',
            'juan.perez@avianca.com'
        )
        self.assertFalse(is_authorized, "Invalid supervisor should not be authorized")
        print("   ✅ Invalid supervisor correctly rejected")

    def _validate_supervisor_authorization(self, supervisor_email, employee_email):
        """
        Business logic to validate supervisor authorization.
        This is what should be implemented in the actual application.
        """
        try:
            supabase = get_supabase_client()
            
            # Get employee information
            result = supabase.table('employees').select('supervisor_email').eq(
                'email', employee_email
            ).execute()
            
            if not result.data:
                return False
                
            employee = result.data[0]
            expected_supervisor = employee.get('supervisor_email')
            
            return supervisor_email == expected_supervisor
            
        except Exception as e:
            print(f"Error validating supervisor: {e}")
            return False

    @patch('utils.supabase_client.get_supabase_client')
    def test_shift_overlap_detection(self, mock_supabase):
        """Test shift overlap detection logic."""
        print("🧪 Testing Shift Overlap Detection...")
        
        # Mock existing shifts for the employee
        existing_shifts = [
            {
                'id': 1,
                'employee_email': 'juan.perez@avianca.com',
                'flight_number': 'AV255',
                'date': self.test_date_future.strftime('%Y-%m-%d'),
                'status': 'approved'
            }
        ]
        
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = existing_shifts
        mock_supabase.return_value = mock_client
        
        # Test overlapping shift (same date)
        has_overlap = self._check_shift_overlap(
            'juan.perez@avianca.com',
            self.test_date_future.strftime('%Y-%m-%d')
        )
        self.assertTrue(has_overlap, "Overlapping shift should be detected")
        print("   ✅ Shift overlap correctly detected")
        
        # Test non-overlapping shift (different date)
        different_date = (self.test_date_future + timedelta(days=1)).strftime('%Y-%m-%d')
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
        
        has_overlap = self._check_shift_overlap(
            'juan.perez@avianca.com',
            different_date
        )
        self.assertFalse(has_overlap, "Non-overlapping shift should be allowed")
        print("   ✅ Non-overlapping shift correctly allowed")

    def _check_shift_overlap(self, employee_email, date):
        """
        Business logic to check for shift overlaps.
        This is what should be implemented in the actual application.
        """
        try:
            supabase = get_supabase_client()
            
            # Check for existing approved shifts on the same date
            result = supabase.table('shift_requests').select('*').eq(
                'employee_email', employee_email
            ).eq(
                'date', date
            ).execute()
            
            # Check if any approved shifts exist on the same date
            approved_shifts = [shift for shift in result.data if shift.get('status') == 'approved']
            return len(approved_shifts) > 0
            
        except Exception as e:
            print(f"Error checking shift overlap: {e}")
            return False

    def test_flight_number_validation(self):
        """Test flight number validation logic."""
        print("🧪 Testing Flight Number Validation...")
        
        # Valid flight numbers
        valid_flights = ['AV205', 'AV255', 'AV625', 'AV627']
        for flight in valid_flights:
            is_valid = self._validate_flight_number(flight)
            self.assertTrue(is_valid, f"Flight {flight} should be valid")
            print(f"   ✅ Flight {flight} correctly validated")
        
        # Invalid flight numbers
        invalid_flights = ['', 'INVALID', 'AV999', '123', 'av205']
        for flight in invalid_flights:
            is_valid = self._validate_flight_number(flight)
            self.assertFalse(is_valid, f"Flight {flight} should be invalid")
            print(f"   ✅ Flight {flight} correctly rejected")

    def _validate_flight_number(self, flight_number):
        """
        Business logic to validate flight numbers.
        This is what should be implemented in the actual application.
        """
        # Valid flight numbers for this application
        valid_flights = {
            'AV205': {'type': 'overnight', 'route': 'BOG-MIA'},
            'AV255': {'type': 'day', 'route': 'BOG-LIM'},
            'AV625': {'type': 'overnight', 'route': 'BOG-MEX'},
            'AV627': {'type': 'day', 'route': 'BOG-CCS'}
        }
        
        return flight_number in valid_flights

    @patch('utils.token_utils.get_supabase_client')
    def test_token_security_validation(self, mock_supabase):
        """Test token security and lifecycle validation."""
        print("🧪 Testing Token Security Validation...")
        
        # Setup mock supabase client
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[{'token': 'test_token_123', 'id': 1}]
        )
        mock_supabase.return_value = mock_client
        
        # Test token generation
        token = generate_token("test_request_123", "test_project_456")
        self.assertIsNotNone(token, "Token should be generated")
        self.assertTrue(len(token) > 10, "Token should have sufficient length")
        print(f"   ✅ Token generated: {token[:8]}...")
        
        # Test token uniqueness
        token2 = generate_token("test_request_124", "test_project_456")
        self.assertNotEqual(token, token2, "Tokens should be unique")
        print("   ✅ Token uniqueness validated")
        
        # Test token format (should be UUID-like)
        try:
            uuid.UUID(token)
            print("   ✅ Token format is valid UUID")
        except ValueError:
            self.fail("Token should be valid UUID format")

    def test_email_validation_edge_cases(self):
        """Test email validation for business-specific rules."""
        print("🧪 Testing Business Email Validation...")
        
        # Should only accept company emails
        company_emails = [
            'pilot@avianca.com',
            'supervisor@avianca.com',
            'admin@avianca.com'
        ]
        
        for email in company_emails:
            is_valid = self._validate_business_email(email)
            self.assertTrue(is_valid, f"Company email {email} should be valid")
            print(f"   ✅ Company email {email} accepted")
        
        # Should reject external emails
        external_emails = [
            'user@gmail.com',
            'test@yahoo.com',
            'pilot@otherairline.com'
        ]
        
        for email in external_emails:
            is_valid = self._validate_business_email(email)
            self.assertFalse(is_valid, f"External email {email} should be rejected")
            print(f"   ✅ External email {email} rejected")

    def _validate_business_email(self, email):
        """
        Business logic to validate company emails.
        This is what should be implemented in the actual application.
        """
        if not email or '@' not in email:
            return False
            
        # Only accept avianca.com emails
        return email.lower().endswith('@avianca.com')

    def test_request_status_workflow(self):
        """Test request status workflow validation."""
        print("🧪 Testing Request Status Workflow...")
        
        # Valid status transitions
        valid_transitions = [
            ('pending', 'approved'),
            ('pending', 'rejected'),
            ('approved', 'completed'),
            ('rejected', 'pending')  # Allow resubmission
        ]
        
        for from_status, to_status in valid_transitions:
            is_valid = self._validate_status_transition(from_status, to_status)
            self.assertTrue(is_valid, f"Transition {from_status} -> {to_status} should be valid")
            print(f"   ✅ Status transition {from_status} -> {to_status} allowed")
        
        # Invalid status transitions
        invalid_transitions = [
            ('approved', 'pending'),
            ('completed', 'pending'),
            ('completed', 'approved'),
            ('rejected', 'completed')
        ]
        
        for from_status, to_status in invalid_transitions:
            is_valid = self._validate_status_transition(from_status, to_status)
            self.assertFalse(is_valid, f"Transition {from_status} -> {to_status} should be invalid")
            print(f"   ✅ Status transition {from_status} -> {to_status} correctly blocked")

    def _validate_status_transition(self, from_status, to_status):
        """
        Business logic to validate status transitions.
        This is what should be implemented in the actual application.
        """
        valid_transitions = {
            'pending': ['approved', 'rejected'],
            'approved': ['completed'],
            'rejected': ['pending'],  # Allow resubmission
            'completed': []  # Final state
        }
        
        return to_status in valid_transitions.get(from_status, [])


def run_business_logic_tests():
    """Run all business logic validation tests."""
    print("🚀 Running Business Logic Validation Tests for ShiftTradeAV")
    print("=" * 70)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBusinessLogicValidation)
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    result = runner.run(suite)
    
    print("=" * 70)
    print("🎯 BUSINESS LOGIC VALIDATION SUMMARY")
    print("=" * 70)
    
    if result.wasSuccessful():
        print("✅ All business logic validation tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed")
        print(f"❌ {len(result.errors)} error(s) occurred")
    
    print(f"📊 Tests run: {result.testsRun}")
    print(f"📊 Failures: {len(result.failures)}")
    print(f"📊 Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_business_logic_tests()
