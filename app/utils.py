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

def format_date(date_str):
    """Convierte una cadena de fecha ISO 8601 a formato 'año-mes-día (Nombre del día)'"""
    try:
        # Intentar configurar el locale a español
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES')
            except locale.Error:
                try:
                    # Fallback a español genérico
                    locale.setlocale(locale.LC_TIME, 'es')
                except locale.Error:
                    # Si no hay locales en español, usar el predeterminado
                    pass
        
        # Convertir la cadena a un objeto datetime
        if isinstance(date_str, str):
            # Para gestionar cadenas ISO 8601
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        elif isinstance(date_str, (datetime, date)):
            # Si ya es un objeto datetime o date
            dt = date_str
        else:
            return str(date_str)  # Devolver la cadena original si no se puede convertir
            
        # Formatear la fecha con el día de la semana
        if isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d (%A)')
        else:
            # Si es un objeto date
            return dt.strftime('%Y-%m-%d (%A)')
            
    except (ValueError, TypeError) as e:
        print(f"Error al formatear la fecha {date_str}: {e}")
        return str(date_str)  # Devolver la cadena original en caso de error
