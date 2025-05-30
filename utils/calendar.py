"""
Módulo de calendario para ShiftTradeAV.
Contiene funciones para crear y manejar archivos de calendario iCalendar (.ics).
"""

import pytz
import uuid
import tempfile
from datetime import datetime, date

def create_calendar_file(shift_data, is_for_requester=True):
    """
    Creates an .ics calendar file for a shift change.
    
    Args:
        shift_data: Dictionary containing shift information (from shift_requests table)
        is_for_requester: Boolean, True if calendar is for the person requesting the shift change
    
    Returns:
        String containing the .ics file content
    """
    try:        
        # Parse the shift date from shift_data
        shift_date_str = shift_data.get('date_request', shift_data.get('date'))
        toronto_tz = pytz.timezone('America/Toronto')
        
        if isinstance(shift_date_str, str):
            # Convertir la cadena ISO a datetime con zona horaria UTC
            dt_utc = datetime.fromisoformat(shift_date_str.replace('Z', '+00:00'))
            # Convertir a zona horaria de Toronto para preservar la fecha correcta
            dt_toronto = dt_utc.replace(tzinfo=pytz.UTC).astimezone(toronto_tz)
            # Extraer solo la fecha
            shift_date = dt_toronto.date()
        elif isinstance(shift_date_str, datetime):
            # Si es un objeto datetime, asegurarse de que tenga zona horaria
            if shift_date_str.tzinfo is None:
                # Si no tiene zona horaria, asumir que es Toronto
                shift_date_str = toronto_tz.localize(shift_date_str)
            else:
                # Si ya tiene zona horaria, convertir a Toronto
                shift_date_str = shift_date_str.astimezone(toronto_tz)
            shift_date = shift_date_str.date()
        elif isinstance(shift_date_str, date):
            shift_date = shift_date_str
        else:
            # Valor predeterminado: fecha actual en zona horaria de Toronto
            shift_date = datetime.now(toronto_tz).date()
        
        # Extract flight information
        flight_info = shift_data.get('flight_number', 'Vuelo no especificado')
        
        # Determine schedule based on flight
        if 'AV255' in flight_info:
            start_time = "05:00"
            end_time = "10:00"
        elif 'AV627' in flight_info:
            start_time = "13:00"
            end_time = "17:30"
        elif 'AV205' in flight_info:
            start_time = "20:00"
            end_time = "23:59"
        else:
            start_time = "09:00"  # Default
            end_time = "17:00"    # Default
        
        # Create naive datetime objects first
        shift_start_naive = datetime.combine(shift_date, datetime.strptime(start_time, "%H:%M").time())
        shift_end_naive = datetime.combine(shift_date, datetime.strptime(end_time, "%H:%M").time())
        
        # Localize to Toronto timezone
        shift_start = toronto_tz.localize(shift_start_naive)
        shift_end = toronto_tz.localize(shift_end_naive)
        
        # Convert to UTC for iCal format
        shift_start_utc = shift_start.astimezone(pytz.UTC)
        shift_end_utc = shift_end.astimezone(pytz.UTC)
        
        # Format for iCal (UTC)
        def format_datetime_for_ical(dt):
            return dt.strftime('%Y%m%dT%H%M%SZ')  # Added Z suffix for UTC
        
        # Current timestamp for DTSTAMP in UTC
        now_utc = datetime.now(pytz.UTC)
        dtstamp = format_datetime_for_ical(now_utc)
        
        # Generate unique ID
        event_uid = f"shift-change-{shift_data.get('id', uuid.uuid4())}"
        
        # Determine event title and description based on who the calendar is for
        if is_for_requester:
            # For the person who requested the change - they are GIVING UP this shift
            summary = f"TURNO CEDIDO: {flight_info}"
            description = f"Turno cedido - Intercambio aprobado\\nCubierto por: {shift_data.get('cover_name', 'N/A')}\\nSupervisor: {shift_data.get('supervisor_name', 'N/A')}"
            status = "CANCELLED"
        else:
            # For the person covering the shift - they are TAKING this shift
            summary = f"TURNO ACEPTADO: {flight_info}"
            description = f"Turno aceptado por intercambio\\nSolicitante original: {shift_data.get('requester_name', 'N/A')}\\nSupervisor: {shift_data.get('supervisor_name', 'N/A')}"
            status = "CONFIRMED"
        
        # Create iCal content with single event
        ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ShiftTradeAV//Shift Management//ES
CALSCALE:GREGORIAN
METHOD:PUBLISH

BEGIN:VEVENT
UID:{event_uid}
DTSTAMP:{dtstamp}
DTSTART:{format_datetime_for_ical(shift_start_utc)}
DTEND:{format_datetime_for_ical(shift_end_utc)}
SUMMARY:{summary}
DESCRIPTION:{description}
LOCATION:Avianca
STATUS:{status}
SEQUENCE:1
END:VEVENT

END:VCALENDAR"""
        
        return ical_content
        
    except Exception as e:
        print(f"Error creating calendar file: {e}")
        return None

def save_calendar_file(shift_data, is_for_requester=True, filename_prefix="shift_change"):
    """
    Creates and saves a calendar file to a temporary location.
    
    Args:
        shift_data: Dictionary containing shift information
        is_for_requester: Boolean, True if calendar is for the person requesting the shift change
        filename_prefix: String prefix for the filename
    
    Returns:
        Tuple of (file_path, calendar_content) or (None, None) if error
    """
    try:
        calendar_content = create_calendar_file(shift_data, is_for_requester)
        if not calendar_content:
            return None, None
        
        # Create a temporary file
        suffix = "_solicitante.ics" if is_for_requester else "_cobertura.ics"
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, prefix=filename_prefix, delete=False) as temp_file:
            temp_file.write(calendar_content)
            temp_file_path = temp_file.name
        
        return temp_file_path, calendar_content
        
    except Exception as e:
        print(f"Error saving calendar file: {e}")
        return None, None
