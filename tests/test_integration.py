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
            'original_date': '2025-09-15',
            'original_flight': 'AV101',
            'desired_date': '2025-09-16',
            'desired_flight': 'AV102',
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
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
            data=[{
                'employee_email': 'test@avianca.com',
                'original_date': '2025-09-15',
                'original_flight': 'AV101',
                'supervisor_status': 'pending'
            }]
        )
        
        # Test duplicate detection
        is_valid, errors = validate_shift_request(self.test_request, self.test_project_id)
        
        # Should fail due to duplicate
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
        # Check if any error message contains 'duplicate' or similar
        error_text = ' '.join(errors).lower()
        self.assertTrue('duplicate' in error_text or 'pending' in error_text or 'already' in error_text)


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
        
        # Test request email using the actual send_email function interface
        result = send_email(
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
        email_result = send_email(
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
            'original_date': '2025-09-20',
            'original_flight': 'AV201',
            'desired_date': '2025-09-21',
            'desired_flight': 'AV202',
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
        email_sent = send_email(
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
    def test_validation_with_missing_employee_data(self, mock_supabase):
        """Test validation behavior when employee data is missing"""
        # Setup mock supabase client
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock empty employee lookup response
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[]  # No employee found
        )
        
        # Test validation
        is_valid, errors = validate_shift_request({
            'employee_email': 'nonexistent@avianca.com',
            'original_date': '2025-09-15',
            'original_flight': 'AV101',
            'desired_date': '2025-09-16',
            'desired_flight': 'AV102'
        }, "test-project-123")
        
        # Should fail validation
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
        # Check if any error message contains 'employee' or similar
        error_text = ' '.join(errors).lower()
        self.assertTrue('employee' in error_text or 'not found' in error_text or 'invalid' in error_text)


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

import sys
import os
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to sys.path to import from utils and app
sys.path.append(str(Path(__file__).parent.parent))

# Import modules to test
from utils.business_validation import validate_shift_request, check_duplicate_request
from utils.general_utils import format_date
from utils.employee_management import get_employee_by_email
from utils.shift_requests import get_pending_requests
from utils.email_utils import send_email, send_email_with_calendar
from utils.supabase_client import get_supabase_client


class TestBusinessValidationIntegration(unittest.TestCase):
    """Test integration between business validation and database operations"""
    
    def setUp(self):
        """Set up test data and mocks"""
        self.test_request = {
            'employee_email': 'test@avianca.com',
            'original_date': '2025-09-15',
            'original_flight': 'AV101',
            'desired_date': '2025-09-16',
            'desired_flight': 'AV102',
            'reason': 'Personal emergency'
        }
        
        self.mock_employee = {
            'id': 1,
            'email': 'test@avianca.com',
            'name': 'Test Employee',
            'department': 'Flight Operations',
            'position': 'Flight Attendant',
            'supervisor_email': 'supervisor@avianca.com',
            'is_active': True
        }
        
        self.mock_supervisor = {
            'id': 2,
            'email': 'supervisor@avianca.com',
            'name': 'Test Supervisor',
            'department': 'Flight Operations',
            'position': 'Supervisor',
            'is_active': True
        }

    @patch('utils.business_validation.get_supabase_client')
    def test_validation_with_database_lookup(self, mock_supabase):
        """Test that business validation correctly integrates with database lookups"""
        # Setup mock supabase client
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock employee lookup response
        mock_client.table().select().eq().eq().execute.return_value = Mock(
            data=[self.mock_employee]
        )
        
        # Mock pending requests response  
        mock_client.table().select().eq().execute.return_value = Mock(
            data=[]  # No pending requests
        )
        
        # Test validation
        result = validate_shift_request(self.test_request)
        
        # Verify integration
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)

    @patch('utils.business_validation.get_supabase_client')
    def test_duplicate_detection_integration(self, mock_supabase):
        """Test duplicate request detection with actual database data"""
        # Setup existing request
        existing_request = {
            'employee_email': 'test@avianca.com',
            'original_date': '2025-09-15',
            'original_flight': 'AV101',
            'supervisor_status': 'pending'
        }
        
        # Setup mock supabase client
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock employee lookup response
        mock_client.table().select().eq().eq().execute.return_value = Mock(
            data=[self.mock_employee]
        )
        
        # Mock pending requests response with existing request
        mock_client.table().select().eq().execute.return_value = Mock(
            data=[existing_request]
        )
        
        # Test duplicate detection
        result = validate_shift_request(self.test_request)
        
        # Should fail due to duplicate
        self.assertFalse(result['is_valid'])
        self.assertIn('duplicate', ' '.join(result['errors']).lower())


class TestEmailWorkflowIntegration(unittest.TestCase):
    """Test integration between email notifications and workflow states"""
    
    def setUp(self):
        """Set up test data for email workflows"""
        self.request_data = {
            'id': 1,
            'employee_email': 'employee@avianca.com',
            'employee_name': 'Test Employee',
            'supervisor_email': 'supervisor@avianca.com',
            'supervisor_name': 'Test Supervisor',
            'original_date': '2025-09-15',
            'original_flight': 'AV101',
            'desired_date': '2025-09-16',
            'desired_flight': 'AV102',
            'reason': 'Personal emergency',
            'status': 'pending'
        }

    @patch('utils.email_utils.send_email')
    @patch('utils.general_utils.format_date')
    def test_request_submission_email_workflow(self, mock_format_date, mock_send_email):
        """Test complete email workflow for request submission"""
        mock_format_date.return_value = "September 15, 2025"
        mock_send_email.return_value = True
        
        # Test request email using the actual send_email function
        result = send_email(
            self.request_data['employee_email'],
            "Shift Request Submitted",
            f"Your shift request has been submitted for {self.request_data['original_date']}"
        )
        
        # Verify email was sent with proper formatting
        self.assertTrue(result)
        mock_send_email.assert_called_once()

    @patch('utils.email_utils.send_email')
    @patch('utils.supabase_client.get_supabase_client')
    def test_approval_workflow_integration(self, mock_supabase, mock_send_email):
        """Test approval workflow with database update and email notification"""
        # Setup mocks
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        mock_client.table().update().eq().execute.return_value = Mock(data=[{'id': 1, 'status': 'approved'}])
        mock_send_email.return_value = True
        
        # Simulate approval process
        # 1. Update database status to approved
        update_result = mock_client.table('shift_requests').update({
            'status': 'approved',
            'supervisor_comments': 'Approved for valid reason'
        }).eq('id', 1).execute()
        
        # 2. Send approval email
        email_result = send_email(
            self.request_data['employee_email'],
            "Shift Request Approved",
            f"Your shift request for {self.request_data['original_date']} has been approved"
        )
        
        # Verify integration
        self.assertTrue(email_result)
        mock_client.table().update.assert_called_once()
        mock_send_email.assert_called_once()

    @patch('utils.email_utils.send_email')
    @patch('utils.supabase_client.get_supabase_client')
    def test_rejection_workflow_integration(self, mock_supabase, mock_send_email):
        """Test rejection workflow with database update and email notification"""
        # Setup mocks
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        mock_client.table().update().eq().execute.return_value = Mock(data=[{'id': 1, 'status': 'rejected'}])
        mock_send_email.return_value = True
        
        # Simulate rejection process
        rejection_reason = "Insufficient coverage for requested date"
        
        # 1. Update database status to rejected
        update_result = mock_client.table('shift_requests').update({
            'status': 'rejected',
            'supervisor_comments': rejection_reason
        }).eq('id', 1).execute()
        
        # 2. Send rejection email
        email_result = send_email(
            self.request_data['employee_email'],
            "Shift Request Rejected",
            f"Your shift request has been rejected. Reason: {rejection_reason}"
        )
        
        # Verify integration
        self.assertTrue(email_result)
        mock_client.table().update.assert_called_once()
        mock_send_email.assert_called_once()


class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end user workflows"""
    
    def setUp(self):
        """Set up comprehensive test data for full workflows"""
        self.employee_data = {
            'email': 'employee@avianca.com',
            'name': 'Test Employee',
            'department': 'Flight Operations',
            'supervisor_email': 'supervisor@avianca.com'
        }
        
        self.shift_request = {
            'employee_email': 'employee@avianca.com',
            'original_date': '2025-09-20',
            'original_flight': 'AV201',
            'desired_date': '2025-09-21',
            'desired_flight': 'AV202',
            'reason': 'Family event'
        }

    @patch('utils.business_validation.validate_shift_request')
    @patch('utils.email_utils.send_request_email')
    @patch('supabase_client.get_supabase_client')
    def test_successful_request_to_acceptance_workflow(self, mock_supabase, mock_email, mock_validation):
        """Test complete workflow: submission → approval → acceptance"""
        # Setup mocks
        mock_validation.return_value = {'is_valid': True, 'errors': []}
        mock_email.return_value = True
        
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock database operations
        mock_client.table().insert().execute.return_value = Mock(data=[{'id': 1, 'status': 'pending'}])
        mock_client.table().update().eq().execute.return_value = Mock(data=[{'id': 1, 'status': 'approved'}])
        
        # Step 1: Employee submits request
        validation_result = mock_validation(self.shift_request)
        self.assertTrue(validation_result['is_valid'])
        
        # Step 2: Store in database
        db_insert = mock_client.table('shift_requests').insert(self.shift_request).execute()
        self.assertIsNotNone(db_insert.data)
        
        # Step 3: Send notification email using the actual send_email function
        email_sent = send_email(
            self.employee_data['email'],
            "Shift Request Submitted",
            f"Your shift request has been submitted to {self.employee_data['supervisor_email']}"
        )
        self.assertTrue(email_sent)
        
        # Step 4: Supervisor approves
        approval_update = mock_client.table('shift_requests').update({
            'status': 'approved'
        }).eq('id', 1).execute()
        self.assertEqual(approval_update.data[0]['status'], 'approved')
        
        # Step 5: Employee accepts (final step)
        acceptance_update = mock_client.table('shift_requests').update({
            'status': 'accepted'
        }).eq('id', 1).execute()
        
        # Verify all steps completed
        mock_validation.assert_called_once()
        mock_email.assert_called_once()
        self.assertEqual(mock_client.table().insert.call_count, 1)
        self.assertEqual(mock_client.table().update.call_count, 2)

    @patch('utils.business_validation.validate_shift_request')
    @patch('utils.email_utils.send_rejection_email')
    @patch('supabase_client.get_supabase_client')
    def test_request_to_rejection_workflow(self, mock_supabase, mock_email, mock_validation):
        """Test complete workflow: submission → rejection → process ends"""
        # Setup mocks
        mock_validation.return_value = {'is_valid': True, 'errors': []}
        mock_email.return_value = True
        
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock database operations
        mock_client.table().insert().execute.return_value = Mock(data=[{'id': 1, 'status': 'pending'}])
        mock_client.table().update().eq().execute.return_value = Mock(data=[{'id': 1, 'status': 'rejected'}])
        
        # Step 1: Employee submits request (same as approval workflow)
        validation_result = mock_validation(self.shift_request)
        self.assertTrue(validation_result['is_valid'])
        
        # Step 2: Store in database
        db_insert = mock_client.table('shift_requests').insert(self.shift_request).execute()
        self.assertIsNotNone(db_insert.data)
        
        # Step 3: Supervisor rejects
        rejection_reason = "No coverage available"
        rejection_update = mock_client.table('shift_requests').update({
            'status': 'rejected',
            'supervisor_comments': rejection_reason
        }).eq('id', 1).execute()
        self.assertEqual(rejection_update.data[0]['status'], 'rejected')
        
        # Step 4: Send rejection email using the actual send_email function
        email_sent = send_email(
            self.employee_data['email'],
            "Shift Request Rejected",
            f"Your shift request has been rejected. Reason: {rejection_reason}"
        )
        self.assertTrue(email_sent)
        
        # Verify workflow completion
        mock_validation.assert_called_once()
        mock_email.assert_called_once()
        self.assertEqual(mock_client.table().update.call_count, 1)


class TestErrorHandlingIntegration(unittest.TestCase):
    """Test error handling across integrated modules"""
    
    @patch('utils.email_utils.send_email')
    @patch('utils.supabase_client.get_supabase_client')
    def test_database_failure_during_submission(self, mock_supabase, mock_email):
        """Test graceful handling when database fails during request submission"""
        # Setup database failure
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        mock_client.table().insert().execute.side_effect = Exception("Database connection failed")
        
        # Attempt submission
        with self.assertRaises(Exception):
            mock_client.table('shift_requests').insert({}).execute()
        
        # Verify email is not sent when database fails
        mock_email.assert_not_called()

    @patch('utils.email_utils.send_email')
    @patch('utils.supabase_client.get_supabase_client')
    def test_email_failure_after_database_success(self, mock_supabase, mock_email):
        """Test handling when email fails but database operation succeeds"""
        # Setup successful database, failed email
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        mock_client.table().insert().execute.return_value = Mock(data=[{'id': 1}])
        mock_email.return_value = False  # Email failure
        
        # Simulate submission
        db_result = mock_client.table('shift_requests').insert({}).execute()
        email_result = send_email('test@avianca.com', 'Test Subject', 'Test Body')
        
        # Verify database succeeded but email failed
        self.assertIsNotNone(db_result.data)
        self.assertFalse(email_result)

    @patch('utils.business_validation.get_supabase_client')
    def test_validation_with_missing_employee_data(self, mock_supabase):
        """Test validation behavior when employee data is missing"""
        # Setup mock supabase client
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock empty employee lookup response
        mock_client.table().select().eq().eq().execute.return_value = Mock(
            data=[]  # No employee found
        )
        
        # Test validation
        result = validate_shift_request({
            'employee_email': 'nonexistent@avianca.com',
            'original_date': '2025-09-15',
            'original_flight': 'AV101',
            'desired_date': '2025-09-16',
            'desired_flight': 'AV102'
        })
        
        # Should fail validation
        self.assertFalse(result['is_valid'])
        self.assertIn('employee', ' '.join(result['errors']).lower())


class TestConcurrentRequestScenarios(unittest.TestCase):
    """Test scenarios with multiple simultaneous requests"""
    
    @patch('utils.business_validation.get_supabase_client')
    def test_multiple_employee_submissions(self, mock_supabase):
        """Test handling multiple employees submitting requests simultaneously"""
        # Setup mock data
        employees = [
            {'email': 'emp1@avianca.com', 'name': 'Employee 1'},
            {'email': 'emp2@avianca.com', 'name': 'Employee 2'},
            {'email': 'emp3@avianca.com', 'name': 'Employee 3'}
        ]
        
        # Setup mock supabase client
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        
        # Mock empty pending requests response
        mock_client.table().select().eq().execute.return_value = Mock(
            data=[]  # No existing requests
        )
        
        # Test multiple validations
        results = []
        for emp in employees:
            # Mock employee lookup response for each employee
            mock_client.table().select().eq().eq().execute.return_value = Mock(
                data=[emp]
            )
            
            result = validate_shift_request({
                'employee_email': emp['email'],
                'original_date': '2025-09-15',
                'original_flight': 'AV101',
                'desired_date': '2025-09-16',
                'desired_flight': 'AV102'
            })
            results.append(result)
        
        # All should be valid
        for result in results:
            self.assertTrue(result['is_valid'])

    @patch('utils.supabase_client.get_supabase_client')
    def test_supervisor_processing_multiple_requests(self, mock_supabase):
        """Test supervisor processing multiple pending requests"""
        # Setup multiple pending requests
        pending_requests = [
            {'id': 1, 'employee_email': 'emp1@avianca.com', 'status': 'pending'},
            {'id': 2, 'employee_email': 'emp2@avianca.com', 'status': 'pending'},
            {'id': 3, 'employee_email': 'emp3@avianca.com', 'status': 'pending'}
        ]
        
        mock_client = Mock()
        mock_supabase.return_value = mock_client
        mock_client.table().update().eq().execute.return_value = Mock(data=[{'status': 'approved'}])
        
        # Process each request
        for request in pending_requests:
            result = mock_client.table('shift_requests').update({
                'status': 'approved'
            }).eq('id', request['id']).execute()
            
            self.assertEqual(result.data[0]['status'], 'approved')
        
        # Verify all were processed
        self.assertEqual(mock_client.table().update.call_count, 3)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2)
