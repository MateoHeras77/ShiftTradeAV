"""
Calendar utilities for shift management.
Handles calendar file creation and flight schedule information.
"""

import uuid
from datetime import datetime, timedelta, date
import pytz

def get_flight_schedule_info(flight_number):
    """
    Returns flight schedule information including proper handling of overnight flights.
    
    Args:
        flight_number: String containing the flight number (e.g., 'AV205', 'AV625')
    
    Returns:
        Dictionary with flight details including start_time, end_time, is_overnight, and display_schedule
    """
    flight_schedules = {
        'AV255': {
            'start_time': '05:00',
            'end_time': '10:00',
            'is_overnight': False,
            'display_schedule': '5:00-10:00'
        },
        'AV619': {
            'start_time': '04:00',
            'end_time': '09:00',
            'is_overnight': False,
            'display_schedule': '04:00-09:00'
        },
        'AV627': {
            'start_time': '13:00',
            'end_time': '17:30',
            'is_overnight': False,
            'display_schedule': '13:00-17:30'
        },
        'AV205': {
            'start_time': '20:00',
            'end_time': '00:30',
            'is_overnight': True,
            'display_schedule': '20:00-00:30 (día siguiente)'
        },
        'AV625': {
            'start_time': '20:00',
            'end_time': '02:30',
            'is_overnight': True,
            'display_schedule': '20:00-02:30 (día siguiente)'
        },
        'AV255-AV627': {
            'start_time': '05:00',
            'end_time': '17:30',
            'is_overnight': False,
            'display_schedule': '5:00-17:30'
        },
        'AV619-AV627': {
            'start_time': '04:00',
            'end_time': '17:30',
            'is_overnight': False,
            'display_schedule': '4:00-17:30'
        },
        'AV627-AV205': {
            'start_time': '13:00',
            'end_time': '00:30',
            'is_overnight': True,
            'display_schedule': '13:00-00:30 (día siguiente)'
        }
    }
    
    # Default values if flight not found
    default_schedule = {
        'start_time': '09:00',
        'end_time': '17:00',
        'is_overnight': False,
        'display_schedule': '09:00-17:00'
    }
    
    return flight_schedules.get(flight_number, default_schedule)

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
        if isinstance(shift_date_str, str):
            shift_date = datetime.fromisoformat(shift_date_str.replace('Z', '+00:00')).date()
        elif isinstance(shift_date_str, date):
            shift_date = shift_date_str
        else:
            shift_date = datetime.now().date()
        
        # Extract flight information
        flight_info = shift_data.get('flight_number', 'Vuelo no especificado')
        
        # Get flight schedule details using the helper function
        schedule_info = get_flight_schedule_info(flight_info)
        start_time = schedule_info['start_time']
        end_time = schedule_info['end_time']
        is_overnight = schedule_info['is_overnight']
        
        # Create datetime objects for the shift in Toronto timezone
        toronto_tz = pytz.timezone('America/Toronto')
        
        # Create naive datetime objects first
        shift_start_naive = datetime.combine(shift_date, datetime.strptime(start_time, "%H:%M").time())
        
        # Handle overnight flights - end time is on the next day
        if is_overnight:
            shift_end_date = shift_date + timedelta(days=1)
            shift_end_naive = datetime.combine(shift_end_date, datetime.strptime(end_time, "%H:%M").time())
        else:
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
        flight_schedule_display = schedule_info['display_schedule']
        
        if is_for_requester:
            # For the person who requested the change - they are GIVING UP this shift
            summary = f"SHIFT GIVEN UP: {flight_info} ({flight_schedule_display})"
            description = f"Shift given up - Approved exchange\\nFlight: {flight_info}\\nSchedule: {flight_schedule_display}\\nCovered by: {shift_data.get('cover_name', 'N/A')}\\nSupervisor: {shift_data.get('supervisor_name', 'N/A')}"
            status = "CANCELLED"
        else:
            # For the person covering the shift - they are TAKING this shift
            summary = f"SHIFT ACCEPTED: {flight_info} ({flight_schedule_display})"
            description = f"Shift accepted by exchange\\nFlight: {flight_info}\\nSchedule: {flight_schedule_display}\\nOriginal requester: {shift_data.get('employee_name', 'N/A')}\\nSupervisor: {shift_data.get('supervisor_name', 'N/A')}"
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
        import tempfile
        
        calendar_content = create_calendar_file(shift_data, is_for_requester)
        if not calendar_content:
            return None, None
        
        # Create a temporary file
        suffix = "_requester.ics" if is_for_requester else "_cover.ics"
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, prefix=filename_prefix, delete=False) as temp_file:
            temp_file.write(calendar_content)
            temp_file_path = temp_file.name
        
        return temp_file_path, calendar_content
        
    except Exception as e:
        print(f"Error saving calendar file: {e}")
        return None, None
