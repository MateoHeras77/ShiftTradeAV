# ShiftTradeAV - Aplicación de Cambio de Turnos para Avianca

## Descripción
ShiftTradeAV es una aplicación desarrollada con Streamlit y Supabase que permite a los empleados de Avianca solicitar, aceptar y aprobar cambios de turnos de forma eficiente y organizada.

## Características
- Sistema de solicitud de cambio de turnos fácil de usar
- Notificaciones por correo electrónico
- Panel de aprobación para supervisores
- Indicadores de carga para mantener informados a los usuarios
- Historial completo de solicitudes con filtros
- Autenticación para supervisores
- Sistema seguro de tokens para aceptación de turnos

## Estructura
La aplicación se divide en tres partes principales:
1. `main.py` - Formulario de solicitud de cambio de turno
2. `accept.py` - Página para aceptar cubrir un turno
3. `supervisor.py` - Panel del supervisor para aprobar/rechazar solicitudes
4. `utils.py` - Funciones compartidas para operaciones con Supabase, emails y tokens

## Configuración
Para usar la aplicación es necesario configurar los secretos en un archivo `.streamlit/secrets.toml` con:
```toml
SUPABASE_URL = "URL_DE_TU_PROYECTO"
SUPABASE_KEY = "CLAVE_DE_TU_PROYECTO"
SMTP_SERVER = "SERVIDOR_SMTP"
SMTP_PORT = "PUERTO_SMTP"
SMTP_USERNAME = "USUARIO_SMTP"
SMTP_PASSWORD = "CONTRASEÑA_SMTP"
SENDER_EMAIL = "EMAIL_REMITENTE"
```

## Ejecución
Para ejecutar las diferentes partes de la aplicación:
```bash
# Formulario de solicitud
streamlit run main.py --server.port 8501

# Página de aceptación 
streamlit run accept.py --server.port 8502

# Panel del supervisor
streamlit run supervisor.py --server.port 8503
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
