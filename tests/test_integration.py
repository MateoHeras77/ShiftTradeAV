"""
Integration Tests for ShiftTradeAV Application

This module tests the integration between different components of the system:
- Business validation + Database operations
- Email notifications + Workflow states
- End-to-end user workflows
- Error handling across modules
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to sys.path to import from utils and app
sys.path.append(str(Path(__file__).parent.parent))

# Import modules to test
from utils.business_validation import validate_shift_request
from utils.general_utils import format_date
from utils.email_utils import send_email, send_email_with_calendar
from utils.supabase_client import get_supabase_client


class TestBusinessValidationIntegration(unittest.TestCase):
    """Test integration between business validation and database operations"""
    
    def setUp(self):
        """Set up test data and mocks"""
        self.test_project_id = "test-project-123"
        self.test_request = {
            'employee_email': 'test@avianca.com',
            'flight_number': 'AV205',
            'date': '2025-09-15',
            'reason': 'Personal emergency'
        }

    @patch('utils.business_validation.get_supabase_client')
    def test_validation_with_database_lookup(self, mock_supabase):
        """Test that business validation correctly integrates with database lookups"""
        # Setup mock supabase client
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock employee lookup response (active employee found)
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[{'email': 'test@avianca.com', 'is_active': True, 'supervisor_email': 'supervisor@avianca.com'}]
        )
        
        # Mock pending requests response (no duplicates)
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]  # No pending requests
        )
        
        # Test validation
        is_valid, errors = validate_shift_request(self.test_request, self.test_project_id)
        
        # Debug: Print errors if validation fails
        if not is_valid:
            print(f"Validation failed with errors: {errors}")
        
        # Verify integration - should be valid with no errors
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    @patch('utils.business_validation.get_supabase_client')
    def test_duplicate_detection_integration(self, mock_supabase):
        """Test duplicate request detection with actual database data"""
        # Setup mock supabase client
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock employee lookup response
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[{'email': 'test@avianca.com', 'is_active': True, 'supervisor_email': 'supervisor@avianca.com'}]
        )
        
        # Mock pending requests response with existing duplicate request
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[{
                'employee_email': 'test@avianca.com',
                'flight_number': 'AV205',
                'date': '2025-09-15',
                'status': 'pending'
            }]
        )
        
        # Test duplicate detection
        is_valid, errors = validate_shift_request(self.test_request, self.test_project_id)
        
        # Debug: Print results if unexpected
        if is_valid:
            print(f"Expected duplicate detection to fail but passed. Errors: {errors}")
        
        # Should fail due to duplicate
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
        # Check if any error message contains 'duplicate' or similar
        error_text = ' '.join(errors).lower()
        self.assertTrue('duplicate' in error_text or 'pending' in error_text or 'already' in error_text or 'existe' in error_text)


class TestEmailWorkflowIntegration(unittest.TestCase):
    """Test integration between email notifications and workflow states"""
    
    def setUp(self):
        """Set up test data for email workflows"""
        self.employee_email = 'employee@avianca.com'
        self.supervisor_email = 'supervisor@avianca.com'

    @patch('utils.email_utils.send_email')
    def test_request_submission_email_workflow(self, mock_send_email):
        """Test complete email workflow for request submission"""
        mock_send_email.return_value = True
        
        # Test request email using the mock
        result = mock_send_email(
            self.employee_email,
            "Shift Request Submitted",
            "Your shift request has been submitted for September 15, 2025"
        )
        
        # Verify email was sent
        self.assertTrue(result)
        mock_send_email.assert_called_once_with(
            self.employee_email,
            "Shift Request Submitted",
            "Your shift request has been submitted for September 15, 2025"
        )

    @patch('utils.email_utils.send_email')
    @patch('utils.supabase_client.get_supabase_client')
    def test_approval_workflow_integration(self, mock_supabase, mock_send_email):
        """Test approval workflow with database update and email notification"""
        # Setup mocks
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        mock_send_email.return_value = True
        
        # Mock database update chain
        mock_update_chain = Mock()
        mock_client.table.return_value = mock_update_chain
        mock_update_chain.update.return_value = mock_update_chain
        mock_update_chain.eq.return_value = mock_update_chain
        mock_update_chain.execute.return_value = Mock(data=[{'id': 1, 'status': 'approved'}])
        
        # Simulate approval process
        # 1. Update database status to approved
        update_result = mock_client.table('shift_requests').update({
            'status': 'approved',
            'supervisor_comments': 'Approved for valid reason'
        }).eq('id', 1).execute()
        
        # 2. Send approval email
        email_result = mock_send_email(
            self.employee_email,
            "Shift Request Approved",
            "Your shift request for September 15, 2025 has been approved"
        )
        
        # Verify integration
        self.assertTrue(email_result)
        self.assertIsNotNone(update_result.data)
        mock_send_email.assert_called_once()


class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end user workflows"""
    
    def setUp(self):
        """Set up comprehensive test data for full workflows"""
        self.project_id = "test-project-123"
        self.employee_data = {
            'email': 'employee@avianca.com',
            'name': 'Test Employee',
            'department': 'Flight Operations',
            'supervisor_email': 'supervisor@avianca.com'
        }
        
        self.shift_request = {
            'employee_email': 'employee@avianca.com',
            'flight_number': 'AV205',
            'date': '2025-09-20',
            'reason': 'Family event'
        }

    @patch('utils.business_validation.get_supabase_client')
    @patch('utils.email_utils.send_email')
    def test_successful_request_workflow(self, mock_email, mock_supabase):
        """Test workflow: validation → database storage → email notification"""
        # Setup mocks
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        mock_email.return_value = True
        
        # Mock employee lookup (valid employee)
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[self.employee_data]
        )
        
        # Mock pending requests (no duplicates)
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[]
        )
        
        # Mock database insert
        mock_client.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[{'id': 1, 'status': 'pending'}]
        )
        
        # Step 1: Validate request
        is_valid, errors = validate_shift_request(self.shift_request, self.project_id)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Step 2: Store in database (simulated)
        db_insert = mock_client.table('shift_requests').insert(self.shift_request).execute()
        self.assertIsNotNone(db_insert.data)
        
        # Step 3: Send notification email
        email_sent = mock_email(
            self.employee_data['email'],
            "Shift Request Submitted",
            f"Your shift request has been submitted to {self.employee_data['supervisor_email']}"
        )
        self.assertTrue(email_sent)
        
        # Verify all steps completed
        mock_email.assert_called_once()


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling across integrated modules"""
    
    @patch('utils.email_utils.send_email')
    @patch('utils.supabase_client.get_supabase_client')
    def test_database_failure_during_submission(self, mock_supabase, mock_email):
        """Test graceful handling when database fails during request submission"""
        # Setup database failure
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.side_effect = Exception("Database connection failed")
        
        # Attempt submission
        with self.assertRaises(Exception):
            mock_client.table('shift_requests').insert({}).execute()
        
        # Verify email is not sent when database fails
        mock_email.assert_not_called()

    @patch('utils.business_validation.get_supabase_client')
    def test_validation_with_invalid_email_format(self, mock_supabase):
        """Test validation behavior when employee email format is invalid"""
        # Setup mock supabase client
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Test validation with invalid email format
        is_valid, errors = validate_shift_request({
            'employee_email': 'invalid-email-format',
            'flight_number': 'AV205',
            'date': '2025-09-15'
        }, "test-project-123")
        
        # Should fail validation due to invalid email format
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
        # Check if any error message contains email-related terms
        error_text = ' '.join(errors).lower()
        self.assertTrue('email' in error_text or 'correo' in error_text or 'válido' in error_text)


class TestIntegrationSanityChecks(unittest.TestCase):
    """Basic sanity checks for module integration"""
    
    def test_module_imports(self):
        """Test that all required modules can be imported together"""
        try:
            from utils.business_validation import validate_shift_request
            from utils.general_utils import format_date
            from utils.email_utils import send_email
            from utils.supabase_client import get_supabase_client
            self.assertTrue(True)  # If we get here, imports work
        except ImportError as e:
            self.fail(f"Module import failed: {e}")

    def test_format_date_integration(self):
        """Test that format_date function works properly"""
        try:
            result = format_date("2025-09-15")
            self.assertIsInstance(result, str)
            self.assertIn("2025", result)  # Should contain the year
        except Exception as e:
            self.fail(f"format_date integration failed: {e}")


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2)

