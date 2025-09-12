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

# Import specialized modules from utils package
from utils.token_utils import generate_token, verify_token, mark_token_as_used
from utils.email_utils import send_email, send_email_with_calendar
from utils.shift_requests import (
    save_shift_request, update_shift_request_status, get_pending_requests,
    get_shift_request_details, get_all_shift_requests
)
from utils.employee_management import (
    get_all_employees, get_employee_by_name, get_employee_by_email,
    check_employee_exists, add_employee, update_employee,
    deactivate_employee, reactivate_employee, get_inactive_employees
)
from utils.calendar_utils import (
    create_calendar_file, save_calendar_file, get_flight_schedule_info
)
from utils.general_utils import format_date
