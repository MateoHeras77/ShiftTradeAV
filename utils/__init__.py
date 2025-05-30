"""
Paquete de utilidades para ShiftTradeAV.
Este paquete contiene módulos separados para diferentes funcionalidades:

- config: Configuración y conexión a Supabase
- auth: Funciones relacionadas con autenticación y tokens
- email_utils: Funciones para envío de correos electrónicos
- date_utils: Funciones para manejo de fechas y zonas horarias
- shift_request: Funciones para gestión de solicitudes de cambio de turno
- employee: Funciones para gestión de empleados
- calendar: Funciones para generación de archivos de calendario
"""

# Importación de todos los módulos para facilitar el acceso
from .config import *
from .auth import *
from .email_utils import *
from .date_utils import *
from .shift_request import *
from .employee import *
from .calendar import *
