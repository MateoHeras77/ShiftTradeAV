"""
General utility functions for ShiftTradeAV application.
Contains common helper functions used across the application.
"""

import locale
from datetime import datetime, date

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
