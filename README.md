# ShiftTradeAV - Aplicación de Cambio de Turnos para Avianca

## Descripción
ShiftTradeAV es una aplicación desarrollada con Streamlit y Supabase que permite a los empleados de Avianca solicitar, aceptar y aprobar cambios de turnos de forma eficiente y organizada.

## Características
- Sistema de solicitud de cambio de turnos fácil de usar
- Notificaciones por correo electrónico
- Archivos .ics compatibles con Google Calendar e iOS
- Indicadores de carga para mantener informados a los usuarios
- Historial completo de solicitudes con filtros
- Autenticación para supervisores
- Sistema seguro de tokens para aceptación de turnos

## Estructura
La aplicación se organiza ahora en el paquete `shifttrade` dentro del directorio `src`:
1. `1_Formulario.py` - Formulario principal de solicitud de cambio de turno
2. `src/shifttrade/pages/2_Solicitud.py` - Página para aceptar cubrir un turno
3. `src/shifttrade/pages/3_Supervisor.py` - Panel del supervisor para aprobar o rechazar solicitudes
4. `src/shifttrade/pages/4_Admin_Empleados.py` - Administración de empleados
5. `src/shifttrade/pages/5_Historial.py` - Historial de solicitudes
6. `src/shifttrade/utils.py` - Funciones auxiliares para formatear fechas y obtener horarios de vuelos

## Configuración
Crea un directorio `.streamlit` en la raíz del proyecto y dentro coloca un archivo `secrets.toml` con el siguiente contenido:
```toml
SUPABASE_URL = "URL_DE_TU_PROYECTO"
SUPABASE_KEY = "CLAVE_DE_TU_PROYECTO"
SMTP_SERVER = "SERVIDOR_SMTP"
SMTP_PORT = "PUERTO_SMTP"
SMTP_USERNAME = "USUARIO_SMTP"
SMTP_PASSWORD = "CONTRASEÑA_SMTP"
SENDER_EMAIL = "EMAIL_REMITENTE"
```

## Entorno de Desarrollo
Para aislar las dependencias puedes crear un entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows usa .venv\Scripts\activate
pip install -r requirements.txt
```

Para ejecutar las pruebas después de instalar las dependencias:
```bash
pytest
```

## Ejecución
Para ejecutar las diferentes partes de la aplicación:
```bash
# Formulario de solicitud
streamlit run 1_Formulario.py --server.port 8501

# Página para aceptar cubrir un turno
streamlit run src/shifttrade/pages/2_Solicitud.py --server.port 8502

# Panel del supervisor
streamlit run src/shifttrade/pages/3_Supervisor.py --server.port 8503

# Administración de empleados (opcional)
streamlit run src/shifttrade/pages/4_Admin_Empleados.py --server.port 8504

# Historial de solicitudes
streamlit run src/shifttrade/pages/5_Historial.py --server.port 8505
```

## Seguridad
- Contraseña para acceso de supervisores
- Tokens únicos para validar aceptaciones de cambios
- Caducidad automática de tokens (24 horas)
- Validación de campos obligatorios

## Base de Datos
La aplicación utiliza Supabase con dos tablas principales:
1. `shift_requests` - Almacena todas las solicitudes de cambio
2. `tokens` - Gestiona los tokens generados para aceptación de turnos
