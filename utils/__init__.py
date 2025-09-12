"""
Utils package for ShiftTradeAV application.
Contains all utility modules organized by functionality.
"""

# Import all functions to make them available at package level
from .token_utils import generate_token, verify_token, mark_token_as_used
from .email_utils import send_email, send_email_with_calendar
from .shift_requests import (
    save_shift_request, update_shift_request_status, get_pending_requests,
    get_shift_request_details, get_all_shift_requests
)
from .employee_management import (
    get_all_employees, get_employee_by_name, get_employee_by_email,
    check_employee_exists, add_employee, update_employee,
    deactivate_employee, reactivate_employee, get_inactive_employees
)
from .calendar_utils import (
    create_calendar_file, save_calendar_file, get_flight_schedule_info
)

__all__ = [
    # Token management
    'generate_token', 'verify_token', 'mark_token_as_used',
    
    # Email utilities
    'send_email', 'send_email_with_calendar',
    
    # Shift request management
    'save_shift_request', 'update_shift_request_status', 'get_pending_requests',
    'get_shift_request_details', 'get_all_shift_requests',
    
    # Employee management
    'get_all_employees', 'get_employee_by_name', 'get_employee_by_email',
    'check_employee_exists', 'add_employee', 'update_employee',
    'deactivate_employee', 'reactivate_employee', 'get_inactive_employees',
    
    # Calendar utilities
    'create_calendar_file', 'save_calendar_file', 'get_flight_schedule_info'
]
