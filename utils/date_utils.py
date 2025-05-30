"""
Módulo de utilidades de fecha para ShiftTradeAV.
Contiene funciones para formateo de fechas y manejo de zonas horarias.
"""

import locale
import pytz
from datetime import datetime, date

def format_date(date_str):
    """
    Convierte una cadena de fecha ISO 8601 a formato 'año-mes-día (Nombre del día)' 
    con ajuste a zona horaria de Toronto (EST/EDT)
    """
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
            # Para gestionar cadenas ISO 8601 (GMT/UTC)
            dt_utc = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Convertir de UTC a zona horaria de Toronto (America/Toronto)
            toronto_tz = pytz.timezone('America/Toronto')
            dt = dt_utc.replace(tzinfo=pytz.UTC).astimezone(toronto_tz)
            # Agregar indicador de zona horaria
            time_suffix = ""
            if isinstance(dt, datetime) and dt.hour > 0:
                time_suffix = f" {dt.strftime('%H:%M')} (hora Toronto)"
        elif isinstance(date_str, (datetime, date)):
            # Si ya es un objeto datetime o date
            dt = date_str
            time_suffix = ""
        else:
            return str(date_str)  # Devolver la cadena original si no se puede convertir
          
        # Formatear la fecha con el día de la semana (con nombres en español)
        if isinstance(dt, datetime):
            # Formato: Año-mes-día (Día de la semana) Hora:Minuto (hora Toronto)
            fecha_formateada = dt.strftime('%Y-%m-%d')
            # Obtener el día de la semana en español
            dias_semana = {
                'Monday': 'Lunes',
                'Tuesday': 'Martes',
                'Wednesday': 'Miércoles',
                'Thursday': 'Jueves',
                'Friday': 'Viernes',
                'Saturday': 'Sábado',
                'Sunday': 'Domingo'
            }
            dia_semana = dias_semana.get(dt.strftime('%A'), dt.strftime('%A'))
            return f"{fecha_formateada} ({dia_semana}){time_suffix}"
        else:
            # Si es un objeto date
            fecha_formateada = dt.strftime('%Y-%m-%d')
            dias_semana = {
                'Monday': 'Lunes',
                'Tuesday': 'Martes',
                'Wednesday': 'Miércoles',
                'Thursday': 'Jueves',
                'Friday': 'Viernes',
                'Saturday': 'Sábado',
                'Sunday': 'Domingo'
            }
            dia_semana = dias_semana.get(dt.strftime('%A'), dt.strftime('%A'))
            return f"{fecha_formateada} ({dia_semana})"
            
    except (ValueError, TypeError) as e:
        print(f"Error al formatear la fecha {date_str}: {e}")
        return str(date_str)  # Devolver la cadena original en caso de error

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
