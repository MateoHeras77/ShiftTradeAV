from utils import date_utils, calendar
from datetime import datetime
import pytz

# Prueba con diferentes fechas para verificar la conversión entre UTC y Toronto
print("===== PRUEBAS DE CONVERSIÓN DE FECHAS =====")

# 1. Fecha actual en UTC
now_utc = datetime.now(pytz.UTC)
print(f"Fecha actual UTC: {now_utc}")
print(f"Formateada: {date_utils.format_date(now_utc.isoformat())}")

# 2. Fecha en formato string ISO
date_str = "2025-06-15T00:00:00Z"  # Media noche UTC
print(f"\nFecha string ISO: {date_str}")
print(f"Formateada: {date_utils.format_date(date_str)}")

# 3. Fecha en Toronto (para verificar que no cambia el día)
toronto_tz = pytz.timezone('America/Toronto')
now_toronto = datetime.now(toronto_tz)
print(f"\nFecha actual Toronto: {now_toronto}")
print(f"Formateada: {date_utils.format_date(now_toronto.isoformat())}")

# 4. Prueba específica con una fecha en la que podría haber cambio de día
# (Por ejemplo, 20:00 UTC que sería 16:00 en Toronto EST, no debería cambiar de día)
test_date = datetime(2025, 6, 15, 20, 0, 0, tzinfo=pytz.UTC)
print(f"\nFecha prueba específica UTC (20:00): {test_date}")
print(f"Formateada: {date_utils.format_date(test_date.isoformat())}")

# 5. Ahora probamos la función create_calendar_file
print("\n===== PRUEBA DE FUNCIÓN CREATE_CALENDAR_FILE =====")

# Crear datos de prueba similares a los que tendría un registro de shift_request
test_shift_data = {
    'id': '123',
    'date_request': "2025-06-15T00:00:00Z",  # UTC midnight
    'flight_number': 'AV255',
    'requester_name': 'Prueba Usuario',
    'cover_name': 'Prueba Cobertura',
    'supervisor_name': 'Supervisor'
}

# Generar el contenido del calendario
calendar_content = calendar.create_calendar_file(test_shift_data, is_for_requester=True)
print(f"Extracto del calendario generado:\n{calendar_content[:500]}...")

# 6. Prueba con fecha en la noche (para verificar comportamiento en franjas que pueden cambiar de día)
test_shift_data_night = {
    'id': '123',
    'date_request': "2025-06-15T22:00:00Z",  # 22:00 UTC (18:00 EST)
    'flight_number': 'AV205',
    'requester_name': 'Prueba Usuario',
    'cover_name': 'Prueba Cobertura',
    'supervisor_name': 'Supervisor'
}

calendar_content_night = calendar.create_calendar_file(test_shift_data_night, is_for_requester=True)
print(f"\nExtracto del calendario generado (fecha noche):\n{calendar_content_night[:500]}...")
