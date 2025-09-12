#!/usr/bin/env python3
"""
Integration Test: Complete Business Logic Validation
Tests the full workflow with all business validation rules applied.
"""

import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

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
mock_streamlit.error = lambda x: print(f"STREAMLIT ERROR: {x}")
mock_streamlit.success = lambda x: print(f"STREAMLIT SUCCESS: {x}")
mock_streamlit.info = lambda x: print(f"STREAMLIT INFO: {x}")
sys.modules['streamlit'] = mock_streamlit

from utils.business_validation import validate_shift_request


def test_complete_workflow():
    """Test complete workflow with business validation."""
    print("🚀 Testing Complete Business Logic Validation Workflow")
    print("=" * 70)
    
    project_id = "test-project-id"
    future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    test_cases = [
        {
            "name": "✅ Valid Request",
            "data": {
                'employee_email': 'pilot@avianca.com',
                'employee_name': 'Juan Pérez',
                'flight_number': 'AV205',
                'date': future_date,
                'supervisor_email': 'supervisor@avianca.com'
            },
            "expected_valid": True
        },
        {
            "name": "❌ Invalid Email Domain",
            "data": {
                'employee_email': 'pilot@gmail.com',
                'employee_name': 'Juan Pérez',
                'flight_number': 'AV205',
                'date': future_date,
                'supervisor_email': 'supervisor@avianca.com'
            },
            "expected_valid": False
        },
        {
            "name": "❌ Invalid Flight Number",
            "data": {
                'employee_email': 'pilot@avianca.com',
                'employee_name': 'Juan Pérez',
                'flight_number': 'INVALID_FLIGHT',
                'date': future_date,
                'supervisor_email': 'supervisor@avianca.com'
            },
            "expected_valid": False
        },
        {
            "name": "❌ Past Date",
            "data": {
                'employee_email': 'pilot@avianca.com',
                'employee_name': 'Juan Pérez',
                'flight_number': 'AV205',
                'date': past_date,
                'supervisor_email': 'supervisor@avianca.com'
            },
            "expected_valid": False
        },
        {
            "name": "❌ Empty Flight Number",
            "data": {
                'employee_email': 'pilot@avianca.com',
                'employee_name': 'Juan Pérez',
                'flight_number': '',
                'date': future_date,
                'supervisor_email': 'supervisor@avianca.com'
            },
            "expected_valid": False
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}/{total_tests}: {test_case['name']}")
        print("-" * 50)
        
        # Mock Supabase for database operations (simulate no duplicates/overlaps)
        with patch('utils.business_validation.get_supabase_client') as mock_supabase:
            mock_client = Mock()
            mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
            mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {'supervisor_email': 'supervisor@avianca.com', 'cargo': 'Piloto'}
            ]
            mock_supabase.return_value = mock_client
            
            is_valid, errors = validate_shift_request(test_case['data'], project_id)
            
            print(f"   Expected: {'Valid' if test_case['expected_valid'] else 'Invalid'}")
            print(f"   Actual: {'Valid' if is_valid else 'Invalid'}")
            
            if errors:
                print("   Errors found:")
                for error in errors:
                    print(f"     • {error}")
            
            # Check if result matches expectation
            if is_valid == test_case['expected_valid']:
                print("   ✅ PASS")
                passed_tests += 1
            else:
                print("   ❌ FAIL")
    
    print("\n" + "=" * 70)
    print("🎯 INTEGRATION TEST SUMMARY")
    print("=" * 70)
    print(f"📊 Tests Passed: {passed_tests}/{total_tests}")
    print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Business validation is working correctly.")
    else:
        print("⚠️  Some tests failed. Review the validation logic.")
    
    return passed_tests == total_tests


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n🔬 Testing Edge Cases and Boundary Conditions")
    print("=" * 70)
    
    from utils.business_validation import (
        validate_request_date,
        validate_flight_number,
        validate_business_email,
        validate_status_transition
    )
    
    edge_cases = [
        # Date edge cases
        {
            "function": validate_request_date,
            "test": "Today's date",
            "input": datetime.now().strftime('%Y-%m-%d'),
            "expected": True
        },
        {
            "function": validate_request_date,
            "test": "90 days from now (boundary)",
            "input": (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
            "expected": True
        },
        {
            "function": validate_request_date,
            "test": "91 days from now (over limit)",
            "input": (datetime.now() + timedelta(days=91)).strftime('%Y-%m-%d'),
            "expected": False
        },
        
        # Email edge cases
        {
            "function": validate_business_email,
            "test": "Uppercase domain",
            "input": "pilot@AVIANCA.COM",
            "expected": True
        },
        {
            "function": validate_business_email,
            "test": "Mixed case",
            "input": "Pilot@Avianca.com",
            "expected": True
        },
        {
            "function": validate_business_email,
            "test": "Empty string",
            "input": "",
            "expected": False
        },
        {
            "function": validate_business_email,
            "test": "No @ symbol",
            "input": "pilotavianca.com",
            "expected": False
        },
        
        # Flight edge cases
        {
            "function": validate_flight_number,
            "test": "Lowercase flight",
            "input": "av205",
            "expected": False
        },
        {
            "function": validate_flight_number,
            "test": "With spaces",
            "input": "AV 205",
            "expected": False
        },
        {
            "function": validate_flight_number,
            "test": "None value",
            "input": None,
            "expected": False
        },
        
        # Status transition edge cases
        {
            "function": validate_status_transition,
            "test": "Same status transition",
            "input": ("pending", "pending"),
            "expected": False
        },
        {
            "function": validate_status_transition,
            "test": "Invalid from status",
            "input": ("invalid", "approved"),
            "expected": False
        }
    ]
    
    passed_edge_tests = 0
    total_edge_tests = len(edge_cases)
    
    for i, test in enumerate(edge_cases, 1):
        print(f"\n🧪 Edge Test {i}/{total_edge_tests}: {test['test']}")
        
        try:
            if isinstance(test['input'], tuple):
                result, _ = test['function'](*test['input'])
            else:
                result, _ = test['function'](test['input'])
            
            print(f"   Input: {test['input']}")
            print(f"   Expected: {'Valid' if test['expected'] else 'Invalid'}")
            print(f"   Actual: {'Valid' if result else 'Invalid'}")
            
            if result == test['expected']:
                print("   ✅ PASS")
                passed_edge_tests += 1
            else:
                print("   ❌ FAIL")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n📊 Edge Tests Passed: {passed_edge_tests}/{total_edge_tests}")
    return passed_edge_tests == total_edge_tests


def show_implementation_recommendations():
    """Show recommendations for implementing business validation."""
    print("\n📚 Implementation Recommendations")
    print("=" * 70)
    
    recommendations = [
        "1. Add validation to employee request forms (app/main.py)",
        "2. Add supervisor authorization to approval workflow (app/pages/3_supervisor.py)",
        "3. Implement real-time validation for better UX",
        "4. Add validation error handling with user-friendly messages",
        "5. Create validation middleware for all form submissions",
        "6. Add logging for validation failures for audit purposes",
        "7. Implement rate limiting to prevent spam requests",
        "8. Add unit tests for each validation function",
        "9. Create integration tests for complete workflows",
        "10. Document all business rules for future developers"
    ]
    
    for rec in recommendations:
        print(f"   ✅ {rec}")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Review the business_validation_demo.py file for integration examples")
    print(f"   2. Update your application pages to use these validation functions")
    print(f"   3. Run the test suite regularly to ensure validation works")
    print(f"   4. Monitor validation errors in production for improvements")


def main():
    """Run all integration tests."""
    print("🧪 COMPLETE BUSINESS LOGIC VALIDATION TEST SUITE")
    print("=" * 70)
    
    # Run main workflow tests
    workflow_passed = test_complete_workflow()
    
    # Run edge case tests
    edge_cases_passed = test_edge_cases()
    
    # Show implementation recommendations
    show_implementation_recommendations()
    
    # Final summary
    print("\n" + "=" * 70)
    print("🏆 FINAL TEST SUMMARY")
    print("=" * 70)
    
    if workflow_passed and edge_cases_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Business validation is ready for production integration")
    else:
        print("⚠️  Some tests failed - review and fix before production")
    
    print(f"✅ Workflow Tests: {'PASSED' if workflow_passed else 'FAILED'}")
    print(f"✅ Edge Case Tests: {'PASSED' if edge_cases_passed else 'FAILED'}")


if __name__ == "__main__":
    main()
