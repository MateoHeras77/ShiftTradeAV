"""
Módulo de utilidades de fecha para ShiftTradeAV.
Contiene funciones para formateo de fechas y manejo de zonas horarias.
"""

import locale
import pytz
from datetime import datetime, date

# Definición de los días de la semana en español para evitar problemas de locale
DIAS_SEMANA_ES = [
    'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'
]

def get_flight_specific_datetime(date_str, flight_number_str):
    """
    Takes a date string (YYYY-MM-DD) and a flight number,
    returns a Toronto-localized datetime object with flight-specific time.
    Defaults to 00:00 if flight number doesn't match known schedules.
    Returns the original date_str if it cannot be parsed, to be handled by format_date.
    """
    toronto_tz = pytz.timezone('America/Toronto')
    
    if not date_str or not isinstance(date_str, str):
        # Pass invalid or None date_str to format_date to handle as "N/A" or original.
        return date_str

    try:
        base_dt_naive = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        # print(f"Warning: Could not parse date_str '{date_str}' as YYYY-MM-DD in get_flight_specific_datetime.")
        # Pass unparseable date_str to format_date to handle as original string.
        return date_str

    hour, minute = 0, 0  # Default to midnight

    if flight_number_str == "255":
        hour, minute = 5, 0
    elif flight_number_str == "AV627":
        hour, minute = 13, 0
    elif flight_number_str == "AV205":
        hour, minute = 20, 0
    
    dt_with_flight_time_naive = base_dt_naive.replace(hour=hour, minute=minute, second=0, microsecond=0)
    dt_toronto_aware = toronto_tz.localize(dt_with_flight_time_naive)
    
    return dt_toronto_aware

def format_date(date_input):
    """
    Convierte una cadena de fecha ISO, un objeto datetime o un objeto date
    a un formato legible en español y ajustado a la zona horaria de Toronto.
    - Datetime (o string con hora): 'YYYY-MM-DD (Día) HH:MM (hora Toronto)'
    - Date (o string YYYY-MM-DD or DD/MM/YYYY): 'YYYY-MM-DD (Día)'
    Retorna 'N/A' si la entrada es 'N/A'.
    Retorna la entrada original como string si no se puede parsear.
    """
    if date_input == "N/A" or date_input is None:
        return "N/A"

    try:
        # Intento de configurar el locale a español (mejor esfuerzo)
        try: locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except locale.Error:
            try: locale.setlocale(locale.LC_TIME, 'es_ES')
            except locale.Error:
                try: locale.setlocale(locale.LC_TIME, 'es')
                except locale.Error: pass # Usar el mapeo manual si el locale falla

        toronto_tz = pytz.timezone('America/Toronto')
        
        processed_dt = None  # Para objetos datetime (con hora)
        processed_date = None # Para objetos date (solo fecha)

        if isinstance(date_input, str):
            original_date_input_str = str(date_input) # Asegurar que es string para manipulación
            parsed_successfully = False
            
            # Intento 1: Parsear como full ISO datetime string (ej. de la BD)
            # Buscar 'T' o ':' como indicadores de timestamp. Debe ser más largo que una simple fecha.
            if not parsed_successfully and ('T' in original_date_input_str or (':' in original_date_input_str and len(original_date_input_str) > 10)) and original_date_input_str.count('-') >= 2 :
                try:
                    # Asegurar que el offset +00:00 esté presente para fromisoformat si termina en Z
                    iso_str = original_date_input_str.replace('Z', '+00:00')
                    dt_from_iso = datetime.fromisoformat(iso_str)
                    
                    # Si es naive (sin tzinfo), asumir UTC. Si tiene tzinfo, convertir a UTC.
                    if dt_from_iso.tzinfo is None or dt_from_iso.tzinfo.utcoffset(dt_from_iso) is None:
                        dt_utc = pytz.utc.localize(dt_from_iso)
                    else:
                        dt_utc = dt_from_iso.astimezone(pytz.utc)
                    
                    processed_dt = dt_utc.astimezone(toronto_tz)
                    parsed_successfully = True
                except ValueError:
                    # Falló el parseo ISO, intentar otros formatos
                    pass

            # Intento 2: Parsear como "YYYY-MM-DD"
            if not parsed_successfully and len(original_date_input_str) == 10 and original_date_input_str.count('-') == 2:
                try:
                    dt_naive = datetime.strptime(original_date_input_str, '%Y-%m-%d')
                    processed_date = dt_naive.date()
                    parsed_successfully = True
                except ValueError:
                    pass

            # Intento 3: Parsear como "DD/MM/YYYY"
            if not parsed_successfully and len(original_date_input_str) == 10 and original_date_input_str.count('/') == 2:
                try:
                    dt_naive = datetime.strptime(original_date_input_str, '%d/%m/%Y')
                    processed_date = dt_naive.date() # La información de hora se pierde
                    # print(f"Advertencia: Parseado '{original_date_input_str}' como solo fecha usando DD/MM/YYYY. Información de hora no disponible.")
                    parsed_successfully = True
                except ValueError:
                    pass
            
            if not parsed_successfully:
                # print(f"Advertencia: No se pudo parsear la cadena de fecha '{original_date_input_str}' con formatos conocidos.")
                return original_date_input_str # Devolver original si falla todo parseo

        elif isinstance(date_input, datetime):
            dt_to_convert = date_input
            if dt_to_convert.tzinfo is None or dt_to_convert.tzinfo.utcoffset(dt_to_convert) is None:
                processed_dt = pytz.utc.localize(dt_to_convert).astimezone(toronto_tz)
            else:
                processed_dt = dt_to_convert.astimezone(toronto_tz)

        elif isinstance(date_input, date):
            processed_date = date_input
            
        else:
            # print(f"Advertencia: Tipo de entrada de fecha no soportado '{type(date_input)}' para valor '{date_input}'.")
            return str(date_input) # Tipo no soportado

        # Formateo final
        if processed_dt: # Es un objeto datetime y debe tener hora
            fecha_formateada_str = processed_dt.strftime('%Y-%m-%d')
            dia_semana_str = DIAS_SEMANA_ES[processed_dt.weekday()] # Lunes=0, Domingo=6
            hora_str = processed_dt.strftime('%H:%M')
            return f"{fecha_formateada_str} ({dia_semana_str}) {hora_str} (hora Toronto)"
        
        elif processed_date: # Es solo una fecha
            temp_dt_for_weekday = datetime(processed_date.year, processed_date.month, processed_date.day)
            fecha_formateada_str = processed_date.strftime('%Y-%m-%d')
            dia_semana_str = DIAS_SEMANA_ES[temp_dt_for_weekday.weekday()]
            return f"{fecha_formateada_str} ({dia_semana_str})"
        
        # print(f"Advertencia: La entrada de fecha '{date_input}' no se procesó a un formato reconocido de fecha/datetime.")
        return str(date_input) # Fallback

    except Exception as e:
        # print(f"Error general al formatear la fecha '{date_input}': {e}")
        return str(date_input) # Devolver la cadena original en caso de error grave

def convert_to_toronto_timezone(dt):
    """
    Convierte un objeto datetime a la zona horaria de Toronto.
    Si dt no tiene zona horaria, se asume UTC.
    """
    toronto_tz = pytz.timezone('America/Toronto')
    
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        return dt.astimezone(toronto_tz)
    return dt # o manejar error/log

def convert_to_utc(dt):
    """
    Convierte un objeto datetime a UTC.
    Si dt no tiene zona horaria, se asume Toronto.
    """
    toronto_tz = pytz.timezone('America/Toronto')
    utc_tz = pytz.utc

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = toronto_tz.localize(dt) # Asumir Toronto si es naive
        return dt.astimezone(utc_tz)
    return dt # o manejar error/log

def get_current_toronto_time():
    """
    Obtiene la fecha y hora actual en zona horaria de Toronto.
    """
    toronto_tz = pytz.timezone('America/Toronto')
    return datetime.now(toronto_tz)
