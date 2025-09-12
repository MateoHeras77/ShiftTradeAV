#!/usr/bin/env python3
"""
Test the new business validation module
"""

import sys
import os
from unittest.mock import Mock

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
mock_streamlit.error = lambda x: print(f"ERROR: {x}")
sys.modules['streamlit'] = mock_streamlit

from utils.business_validation import (
    validate_request_date,
    validate_flight_number,
    validate_business_email,
    validate_status_transition,
    get_validation_summary
)

def test_business_validation():
    """Test the business validation functions."""
    print("🚀 Testing New Business Validation Module")
    print("=" * 50)
    
    # Test date validation
    print("📅 Testing Date Validation...")
    is_valid, error = validate_request_date("2025-09-18")  # Future date
    print(f"   Future date: {is_valid} - {error}")
    
    is_valid, error = validate_request_date("2025-09-10")  # Past date
    print(f"   Past date: {is_valid} - {error}")
    
    # Test flight validation
    print("✈️ Testing Flight Validation...")
    is_valid, error = validate_flight_number("AV205")
    print(f"   Valid flight: {is_valid} - {error}")
    
    is_valid, error = validate_flight_number("INVALID")
    print(f"   Invalid flight: {is_valid} - {error}")
    
    # Test email validation
    print("📧 Testing Email Validation...")
    is_valid, error = validate_business_email("pilot@avianca.com")
    print(f"   Company email: {is_valid} - {error}")
    
    is_valid, error = validate_business_email("pilot@gmail.com")
    print(f"   External email: {is_valid} - {error}")
    
    # Test status transitions
    print("🔄 Testing Status Transitions...")
    is_valid, error = validate_status_transition("pending", "approved")
    print(f"   pending → approved: {is_valid} - {error}")
    
    is_valid, error = validate_status_transition("approved", "pending")
    print(f"   approved → pending: {is_valid} - {error}")
    
    # Test validation summary
    print("📋 Testing Validation Summary...")
    summary = get_validation_summary()
    for rule, description in summary.items():
        print(f"   {rule}: {description}")
    
    print("=" * 50)
    print("✅ Business validation module test completed!")

if __name__ == "__main__":
    test_business_validation()
