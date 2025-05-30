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

def format_date(date_input):
    """
    Convierte una cadena de fecha ISO, un objeto datetime o un objeto date
    a un formato legible en español y ajustado a la zona horaria de Toronto.
    - Datetime (o string con hora): 'YYYY-MM-DD (Día) HH:MM (hora Toronto)'
    - Date (o string YYYY-MM-DD): 'YYYY-MM-DD (Día)'
    """
    try:
        # Intento de configurar el locale a español (mejor esfuerzo, el mapeo manual es el principal)
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_TIME, 'es')
                except locale.Error:
                    pass  # Usar el mapeo manual si el locale falla

        toronto_tz = pytz.timezone('America/Toronto')
        
        processed_dt = None # This will hold the datetime object for formatting time
        processed_date = None # This will hold the date object for formatting date-only

        if isinstance(date_input, str):
            original_date_input_str = date_input # for error messages
            try:
                # Prioritize parsing as "YYYY-MM-DD" if it matches that length
                if len(date_input) == 10:
                    dt_naive = datetime.strptime(date_input, '%Y-%m-%d')
                    processed_date = dt_naive.date()
                else: # Attempt to parse as full ISO datetime
                    # Handle 'Z' for UTC explicitly for fromisoformat
                    if date_input.endswith('Z'):
                        date_input = date_input[:-1] + '+00:00'
                    
                    dt_utc_aware = datetime.fromisoformat(date_input)
                    # Convert to Toronto time
                    processed_dt = dt_utc_aware.astimezone(toronto_tz)

            except ValueError:
                # If primary parsing failed, try the other way around or log error
                if processed_date is None and processed_dt is None: # Neither YYYY-MM-DD nor full ISO worked
                    try: # Last attempt for YYYY-MM-DD if it wasn't 10 chars but still valid
                        dt_naive = datetime.strptime(original_date_input_str, '%Y-%m-%d')
                        processed_date = dt_naive.date()
                    except ValueError:
                        print(f"Error al parsear la cadena de fecha: '{original_date_input_str}'")
                        return str(original_date_input_str) # Return original on error
        
        elif isinstance(date_input, datetime):
            dt_to_convert = date_input
            if dt_to_convert.tzinfo is None or dt_to_convert.tzinfo.utcoffset(dt_to_convert) is None:
                # Asumir UTC si es naive, luego convertir a Toronto
                processed_dt = pytz.utc.localize(dt_to_convert).astimezone(toronto_tz)
            else:
                # Si ya tiene zona horaria, convertir a Toronto
                processed_dt = dt_to_convert.astimezone(toronto_tz)

        elif isinstance(date_input, date):
            # Es un objeto date puro, no datetime
            processed_date = date_input
            
        else:
            return str(date_input) # Tipo no soportado

        # Formateo final
        if processed_dt: # Implica que es un datetime y debe tener hora
            fecha_formateada_str = processed_dt.strftime('%Y-%m-%d')
            dia_semana_str = DIAS_SEMANA_ES[processed_dt.weekday()]
            hora_str = processed_dt.strftime('%H:%M')
            return f"{fecha_formateada_str} ({dia_semana_str}) {hora_str} (hora Toronto)"
        
        elif processed_date: # Implica que es solo una fecha
            # Para obtener el día de la semana, podemos convertir temporalmente a datetime (medianoche)
            # No se necesita conversión de zona horaria para un 'date' puro en este contexto de formateo.
            temp_dt_for_weekday = datetime(processed_date.year, processed_date.month, processed_date.day)
            fecha_formateada_str = processed_date.strftime('%Y-%m-%d')
            dia_semana_str = DIAS_SEMANA_ES[temp_dt_for_weekday.weekday()]
            return f"{fecha_formateada_str} ({dia_semana_str})"
        
        else: # No se pudo procesar
             return str(date_input)

    except Exception as e: # Captura errores inesperados durante el formateo
        print(f"Error general al formatear la fecha '{date_input}': {e}")
        return str(date_input) # Devolver la cadena original en caso de error grave

def convert_to_toronto_timezone(dt):
    """
    Convierte un objeto datetime a la zona horaria de Toronto.
    Si dt no tiene zona horaria, se asume UTC.
    """
    toronto_tz = pytz.timezone('America/Toronto')
    
    # Si el objeto datetime no tiene zona horaria, asumimos UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
        
    # Convertir a zona horaria de Toronto
    return dt.astimezone(toronto_tz)

def convert_to_utc(dt):
    """
    Convierte un objeto datetime a UTC.
    Si dt no tiene zona horaria, se asume Toronto.
    """
    toronto_tz = pytz.timezone('America/Toronto')
    
    # Si el objeto datetime no tiene zona horaria, asumimos Toronto
    if dt.tzinfo is None:
        dt = toronto_tz.localize(dt)
        
    # Convertir a UTC
    return dt.astimezone(pytz.UTC)

def get_current_toronto_time():
    """
    Obtiene la fecha y hora actual en zona horaria de Toronto.
    """
    toronto_tz = pytz.timezone('America/Toronto')
    return datetime.now(toronto_tz)
