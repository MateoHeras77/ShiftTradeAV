"""
Utilities module for ShiftTradeAV application.
Common utility functions and imports from specialized modules.
"""

import locale
from datetime import datetime, date
import sys
import os

# Add the project root to the Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import specialized modules from utils package (using absolute import from project root)
import sys
sys.path.insert(0, project_root)

# Use absolute imports to avoid conflicts
import utils.token_utils as token_utils
import utils.email_utils as email_utils
import utils.shift_requests as shift_requests
import utils.employee_management as employee_management
import utils.calendar_utils as calendar_utils

# Re-export functions for convenience
generate_token = token_utils.generate_token
verify_token = token_utils.verify_token
mark_token_as_used = token_utils.mark_token_as_used

send_email = email_utils.send_email
send_email_with_calendar = email_utils.send_email_with_calendar

save_shift_request = shift_requests.save_shift_request
update_shift_request_status = shift_requests.update_shift_request_status
get_pending_requests = shift_requests.get_pending_requests
get_shift_request_details = shift_requests.get_shift_request_details
get_all_shift_requests = shift_requests.get_all_shift_requests

get_all_employees = employee_management.get_all_employees
get_employee_by_name = employee_management.get_employee_by_name
get_employee_by_email = employee_management.get_employee_by_email
check_employee_exists = employee_management.check_employee_exists
add_employee = employee_management.add_employee
update_employee = employee_management.update_employee
deactivate_employee = employee_management.deactivate_employee
reactivate_employee = employee_management.reactivate_employee
get_inactive_employees = employee_management.get_inactive_employees

create_calendar_file = calendar_utils.create_calendar_file
save_calendar_file = calendar_utils.save_calendar_file
get_flight_schedule_info = calendar_utils.get_flight_schedule_info
from utils.general_utils import format_date
