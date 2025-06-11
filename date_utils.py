import pytz
from datetime import datetime, timedelta, date
import uuid

# Helper timezone functions
TORONTO_TZ = pytz.timezone('America/Toronto')


def to_toronto(dt: datetime) -> datetime:
    """Convert naive or aware datetime to Toronto timezone."""
    if dt.tzinfo is None:
        return TORONTO_TZ.localize(dt)
    return dt.astimezone(TORONTO_TZ)


def to_utc(dt: datetime) -> datetime:
    """Convert naive or aware datetime to UTC."""
    return to_toronto(dt).astimezone(pytz.UTC)


def format_datetime_for_ical(dt: datetime) -> str:
    """Format a datetime in UTC for iCal."""
    return dt.astimezone(pytz.UTC).strftime('%Y%m%dT%H%M%SZ')


# Flight schedule lookup
FLIGHT_SCHEDULES = {
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
        'start_time': '05:00',
        'end_time': '17:30',
        'is_overnight': False,
        'display_schedule': '5:00-17:30'
    },
    'AV627-AV205': {
        'start_time': '13:00',
        'end_time': '00:30',
        'is_overnight': True,
        'display_schedule': '13:00-00:30 (día siguiente)'
    }
}

DEFAULT_SCHEDULE = {
    'start_time': '09:00',
    'end_time': '17:00',
    'is_overnight': False,
    'display_schedule': '09:00-17:00'
}


def get_flight_schedule_info(flight_number: str) -> dict:
    """Return schedule information for a flight number."""
    return FLIGHT_SCHEDULES.get(flight_number, DEFAULT_SCHEDULE)


def create_calendar_file(shift_data: dict, is_for_requester: bool = True) -> str | None:
    """Generate iCal content for a shift change."""
    try:
        shift_date_str = shift_data.get('date_request', shift_data.get('date'))
        if isinstance(shift_date_str, str):
            shift_date = datetime.fromisoformat(shift_date_str.replace('Z', '+00:00')).date()
        elif isinstance(shift_date_str, date):
            shift_date = shift_date_str
        else:
            shift_date = datetime.now().date()

        flight_info = shift_data.get('flight_number', 'Vuelo no especificado')
        schedule_info = get_flight_schedule_info(flight_info)
        start_time = schedule_info['start_time']
        end_time = schedule_info['end_time']
        is_overnight = schedule_info['is_overnight']

        shift_start_naive = datetime.combine(shift_date, datetime.strptime(start_time, "%H:%M").time())
        if is_overnight:
            shift_end_date = shift_date + timedelta(days=1)
        else:
            shift_end_date = shift_date
        shift_end_naive = datetime.combine(shift_end_date, datetime.strptime(end_time, "%H:%M").time())

        shift_start_utc = to_utc(shift_start_naive)
        shift_end_utc = to_utc(shift_end_naive)

        now_utc = datetime.now(pytz.UTC)
        dtstamp = format_datetime_for_ical(now_utc)
        event_uid = f"shift-change-{shift_data.get('id', uuid.uuid4())}"

        flight_schedule_display = schedule_info['display_schedule']
        if is_for_requester:
            summary = f"TURNO CEDIDO: {flight_info} ({flight_schedule_display})"
            description = (
                f"Turno cedido - Intercambio aprobado\\n"
                f"Vuelo: {flight_info}\\n"
                f"Horario: {flight_schedule_display}\\n"
                f"Cubierto por: {shift_data.get('cover_name', 'N/A')}\\n"
                f"Supervisor: {shift_data.get('supervisor_name', 'N/A')}"
            )
            status = "CANCELLED"
        else:
            summary = f"TURNO ACEPTADO: {flight_info} ({flight_schedule_display})"
            description = (
                f"Turno aceptado por intercambio\\n"
                f"Vuelo: {flight_info}\\n"
                f"Horario: {flight_schedule_display}\\n"
                f"Solicitante original: {shift_data.get('requester_name', 'N/A')}\\n"
                f"Supervisor: {shift_data.get('supervisor_name', 'N/A')}"
            )
            status = "CONFIRMED"

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


def save_calendar_file(shift_data: dict, is_for_requester: bool = True, filename_prefix: str = "shift_change"):
    """Create a temporary calendar file and return its path and content."""
    try:
        import tempfile

        calendar_content = create_calendar_file(shift_data, is_for_requester)
        if not calendar_content:
            return None, None

        suffix = "_solicitante.ics" if is_for_requester else "_cobertura.ics"
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, prefix=filename_prefix, delete=False) as temp_file:
            temp_file.write(calendar_content)
            temp_file_path = temp_file.name
        return temp_file_path, calendar_content
    except Exception as e:
        print(f"Error saving calendar file: {e}")
        return None, None
