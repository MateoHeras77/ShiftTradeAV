import locale
from datetime import datetime, date


def format_date(date_value):
    """Return a date formatted as 'YYYY-MM-DD (Weekday)' in Spanish."""
    try:
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_TIME, 'es')
                except locale.Error:
                    pass

        if isinstance(date_value, str):
            dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
        elif isinstance(date_value, (datetime, date)):
            dt = date_value
        else:
            return str(date_value)

        return dt.strftime('%Y-%m-%d (%A)')
    except (ValueError, TypeError) as exc:
        print(f"Error al formatear la fecha {date_value}: {exc}")
        return str(date_value)


def get_flight_schedule_info(flight_number):
    """Return schedule details for a given flight number."""
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

    default_schedule = {
        'start_time': '09:00',
        'end_time': '17:00',
        'is_overnight': False,
        'display_schedule': '09:00-17:00'
    }

    return flight_schedules.get(flight_number, default_schedule)
