import streamlit as st
import smtplib
import uuid
from datetime import datetime, timedelta, timezone, date # Import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from supabase import create_client, Client # Import Supabase client
import locale
import pytz  # type: ignore  # For timezone handling
from dataclasses import asdict
from typing import List, Optional

from models import ShiftRequest, Employee, Token

# Supabase configuration
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized successfully.")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    st.error(f"Error crítico al conectar con Supabase: {e}")
    supabase = None # Ensure supabase is None if initialization fails

# Email configuration
SMTP_SERVER = st.secrets["SMTP_SERVER"]
SMTP_PORT = int(st.secrets["SMTP_PORT"]) # Ensure SMTP_PORT is an integer
SMTP_USERNAME = st.secrets["SMTP_USERNAME"]
SMTP_PASSWORD = st.secrets["SMTP_PASSWORD"]
SENDER_EMAIL = st.secrets["SENDER_EMAIL"]


def _shift_request_from_dict(data: dict) -> ShiftRequest:
    return ShiftRequest(**data)


def _employee_from_dict(data: dict) -> Employee:
    return Employee(**data)


def _token_from_dict(data: dict) -> Token:
    expires_at_raw = data.get("expires_at")
    expires_at = datetime.fromisoformat(expires_at_raw) if isinstance(expires_at_raw, str) else expires_at_raw
    assert isinstance(expires_at, datetime)
    return Token(
        token=data["token"],
        shift_request_id=data["shift_request_id"],
        expires_at=expires_at,
        used=data.get("used", False),
    )

def generate_token(shift_request_id: str, project_id: str) -> Optional[Token]:
    """Generate a unique token, store it in Supabase and return a ``Token`` instance."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede generar el token.")
        return None
    token = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    try:
        record = {
            "token": str(token),
            "shift_request_id": str(shift_request_id),
            "expires_at": expires_at.isoformat(),
            "used": False,
        }
        response = supabase.table("tokens").insert(record).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Token {token} saved for shift_request_id {shift_request_id}")
            return Token(token=str(token), shift_request_id=str(shift_request_id), expires_at=expires_at, used=False)
        else:
            error_message = "No data returned from Supabase or error in response."
            if hasattr(response, 'error') and response.error:
                error_message = response.error.message
            elif hasattr(response, 'status_code') and response.status_code not in [200, 201]:
                 error_message = f"Status: {response.status_code}, Detail: {getattr(response, 'data', 'N/A')}"
            print(f"Error saving token to Supabase: {error_message}")
            st.error(f"Error de Supabase al guardar token: {error_message}")
            return None
    except Exception as e:
        print(f"Exception saving token to Supabase: {e}")
        st.error(f"Excepción al guardar token en Supabase: {e}")
        return None

def verify_token(token_str: str, project_id: str) -> Optional[Token]:
    """Verify a token against Supabase and return a ``Token`` instance if valid."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede verificar el token.")
        return None
    try:
        response = (
            supabase.table("tokens")
            .select("shift_request_id, expires_at, used")
            .eq("token", token_str)
            .single()
            .execute()
        )
        if response.data:
            token_data = response.data
            expires_at_str = token_data["expires_at"]
            expires_at = datetime.fromisoformat(expires_at_str)

            if not token_data["used"] and expires_at > datetime.now(timezone.utc):
                return Token(
                    token=token_str,
                    shift_request_id=token_data["shift_request_id"],
                    expires_at=expires_at,
                    used=False,
                )
            else:
                if token_data["used"]:
                    st.warning("Token ya ha sido utilizado.")
                if expires_at <= datetime.now(timezone.utc):
                    st.warning("Token ha expirado.")
                return None
        else:
            error_message = "Token no encontrado o error en la respuesta."
            if hasattr(response, 'error') and response.error: error_message = response.error.message
            st.error(f"Error de Supabase al verificar token: {error_message}")
            print(f"Token not found or error: {error_message}")
            return None
    except Exception as e:
        print(f"Exception verifying token: {e}")
        st.error(f"Excepción al verificar token: {e}")
        return None

def mark_token_as_used(token: Token, project_id: str) -> bool:
    """Mark a token as used in Supabase."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede marcar el token.")
        return False
    try:
        response = (
            supabase.table("tokens").update({"used": True}).eq("token", token.token).execute()
        )
        if response.data and len(response.data) > 0:
            print(f"Token {token.token} marked as used.")
            return True
        else:
            error_message = "No se pudo marcar el token como usado o no se encontró."
            if hasattr(response, 'error') and response.error: error_message = response.error.message
            print(f"Failed to mark token {token.token} as used: {error_message}")
            st.error(f"Error de Supabase al marcar token como usado: {error_message}")
            return False
    except Exception as e:
        print(f"Exception marking token as used: {e}")
        st.error(f"Excepción al marcar token como usado: {e}")
        return False

def send_email(recipient_email, subject, body):
    """Sends an email."""
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        print(f"Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")
        st.error(f"Error al enviar correo a {recipient_email}: {e}")
        return False

def send_email_with_calendar(
    recipient_email: str,
    subject: str,
    body: str,
    shift_data: ShiftRequest,
    is_for_requester: bool = True,
) -> bool:
    """
    Sends an email with a calendar attachment.
    
    Args:
        recipient_email: Email address of recipient
        subject: Email subject
        body: Email body text
        shift_data: ``ShiftRequest`` instance with shift information
        is_for_requester: Boolean, True if calendar is for the person requesting the shift change
    
    Returns:
        Boolean indicating success
    """
    try:
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        import tempfile
        import os
        
        # Create the message
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Create calendar file
        calendar_content = create_calendar_file(shift_data, is_for_requester)
        
        if calendar_content:
            # Create temporary calendar file
            person_type = "solicitante" if is_for_requester else "cobertura"
            filename = f"turno_{person_type}_{shift_data.flight_number or 'AV'}.ics"
            
            # Create attachment
            calendar_attachment = MIMEBase('text', 'calendar')
            calendar_attachment.set_payload(calendar_content.encode('utf-8'))
            encoders.encode_base64(calendar_attachment)
            calendar_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            calendar_attachment.add_header('Content-Type', 'text/calendar; method=PUBLISH')
            
            msg.attach(calendar_attachment)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        
        print(f"Email with calendar sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email with calendar to {recipient_email}: {e}")
        st.error(f"Error al enviar correo con calendario a {recipient_email}: {e}")
        # Fallback to regular email
        return send_email(recipient_email, subject, body)

def save_shift_request(details: ShiftRequest, project_id: str) -> Optional[str]:
    """Save shift request details to Supabase and return the new request ID."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede guardar la solicitud.")
        return None
    try:
        record = asdict(details)
        if record.get("date_request") is not None:
            record["date_request"] = str(record["date_request"])

        response = supabase.table("shift_requests").insert(record).execute()
        if response.data and len(response.data) > 0:
            new_id = response.data[0]['id']
            print(f"Shift request saved with ID: {new_id}")
            return new_id
        else:
            error_message = "No data returned from Supabase or error in response."
            if hasattr(response, 'error') and response.error: error_message = response.error.message
            elif hasattr(response, 'status_code') and response.status_code not in [200, 201]:
                 error_message = f"Status: {response.status_code}, Detail: {getattr(response, 'data', 'N/A')}"
            print(f"Error saving shift request: {error_message}")
            st.error(f"Error de Supabase al guardar solicitud: {error_message}")
            return None
    except Exception as e:
        print(f"Exception saving shift request: {e}")
        st.error(f"Excepción al guardar solicitud: {e}")
        return None

def update_shift_request_status(request_id: str, updates: dict, project_id: str):
    """Updates a shift request in Supabase."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede actualizar la solicitud.")
        return False
    try:
        # Ensure timestamp fields are ISO strings if they are datetime objects
        for key in ['date_accepted_by_cover', 'supervisor_decision_date']:
            if key in updates and isinstance(updates[key], datetime):
                updates[key] = updates[key].isoformat()
        
        response = supabase.table('shift_requests').update(updates).eq('id', request_id).execute()
        if response.data and len(response.data) > 0:
            print(f"Shift request {request_id} updated.")
            return True
        else:
            error_message = "No se pudo actualizar la solicitud o no se encontró."
            if hasattr(response, 'error') and response.error: error_message = response.error.message
            print(f"Failed to update shift request {request_id}: {error_message}")
            st.error(f"Error de Supabase al actualizar solicitud: {error_message}")
            return False
    except Exception as e:
        print(f"Exception updating shift request: {e}")
        st.error(f"Excepción al actualizar solicitud: {e}")
        return False

def get_pending_requests(project_id: str) -> List[ShiftRequest]:
    """Fetch all shift requests with supervisor_status = 'pending'."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener las solicitudes pendientes.")
        return []
    try:
        # No ordenamos aquí ya que lo haremos más precisamente en el frontend
        response = (
            supabase.table("shift_requests")
            .select("*")
            .eq("supervisor_status", "pending")
            .execute()
        )
        if response.data:
            return [_shift_request_from_dict(item) for item in response.data]
        return []
    except Exception as e:
        print(f"Exception fetching pending requests: {e}")
        st.error(f"Excepción al obtener solicitudes pendientes: {e}")
        return []

def get_shift_request_details(request_id: str, project_id: str) -> Optional[ShiftRequest]:
    """Fetch details for a specific shift request."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener los detalles.")
        return None
    try:
        response = (
            supabase.table("shift_requests")
            .select("*")
            .eq("id", request_id)
            .single()
            .execute()
        )
        if response.data:
            return _shift_request_from_dict(response.data)
        return None
    except Exception as e:
        print(f"Exception fetching shift request details for {request_id}: {e}")
        st.error(f"Excepción al obtener detalles de solicitud: {e}")
        return None

def get_all_shift_requests(project_id: str) -> List[ShiftRequest]:
    """Fetch all shift requests from the database."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener todas las solicitudes.")
        return []
    try:
        # No aplicamos ordenamiento en la consulta para hacer el sorting en el frontend con más control
        response = supabase.table("shift_requests").select("*").execute()
        if response.data:
            return [_shift_request_from_dict(item) for item in response.data]
        return []
    except Exception as e:
        print(f"Exception fetching all shift requests: {e}")
        st.error(f"Excepción al obtener todas las solicitudes: {e}")
        return []

# Employee management functions
def get_all_employees(project_id: str) -> List[Employee]:
    """Get all active employees from the database."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return []
    
    try:
        response = (
            supabase.table("employees")
            .select("*")
            .eq("is_active", True)
            .order("full_name")
            .execute()
        )
        if response.data:
            return [_employee_from_dict(emp) for emp in response.data]
        else:
            print("No employees found or error in response.")
            return []
            
    except Exception as e:
        print(f"Error fetching employees: {e}")
        st.error(f"Error al obtener la lista de empleados: {e}")
        return []

def get_employee_by_name(full_name: str, project_id: str) -> Optional[Employee]:
    """Get employee details by full name."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return None
    
    try:
        response = (
            supabase.table("employees")
            .select("*")
            .eq("full_name", full_name)
            .eq("is_active", True)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return _employee_from_dict(response.data[0])
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching employee {full_name}: {e}")
        st.error(f"Error al obtener datos del empleado {full_name}: {e}")
        return None

def get_employee_by_email(email: str, project_id: str) -> Optional[Employee]:
    """Get employee details by email."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return None
    
    try:
        response = (
            supabase.table("employees")
            .select("*")
            .eq("email", email)
            .eq("is_active", True)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return _employee_from_dict(response.data[0])
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching employee by email {email}: {e}")
        st.error(f"Error al obtener datos del empleado por email {email}: {e}")
        return None

def check_employee_exists(full_name: Optional[str] = None, email: Optional[str] = None, project_id: Optional[str] = None):
    """Check if an employee with the given name or email already exists."""
    if not supabase:
        return False
    
    try:
        if full_name:
            response = supabase.table('employees').select('id').eq('full_name', full_name).eq('is_active', True).execute()
            if response.data and len(response.data) > 0:
                return True
        
        if email:
            response = supabase.table('employees').select('id').eq('email', email).eq('is_active', True).execute()
            if response.data and len(response.data) > 0:
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking if employee exists: {e}")
        return False

def add_employee(full_name: str, raic_color: str, email: str, project_id: str):
    """Add a new employee to the database."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    
    try:
        response = supabase.table('employees').insert({
            'full_name': full_name,
            'raic_color': raic_color,
            'email': email,
            'is_active': True
        }).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Employee {full_name} added successfully")
            return True
        else:
            print("Error adding employee or no data returned.")
            return False
            
    except Exception as e:
        print(f"Error adding employee: {e}")
        st.error(f"Error al agregar empleado: {e}")
        return False

def update_employee(employee_id: int, full_name: str, raic_color: str, email: str, project_id: str):
    """Update an existing employee."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    
    try:
        response = supabase.table('employees').update({
            'full_name': full_name,
            'raic_color': raic_color,
            'email': email,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', employee_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Employee {employee_id} updated successfully")
            return True
        else:
            print("Error updating employee or no data returned.")
            return False
            
    except Exception as e:
        print(f"Error updating employee: {e}")
        st.error(f"Error al actualizar empleado: {e}")
        return False

def deactivate_employee(employee_id: int, project_id: str):
    """Deactivate an employee (soft delete)."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    
    try:
        response = supabase.table('employees').update({
            'is_active': False,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', employee_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Employee {employee_id} deactivated successfully")
            return True
        else:
            print("Error deactivating employee or no data returned.")
            return False
            
    except Exception as e:
        print(f"Error deactivating employee: {e}")
        st.error(f"Error al desactivar empleado: {e}")
        return False

def reactivate_employee(employee_id: int, project_id: str):
    """Reactivate an employee."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    
    try:
        response = supabase.table('employees').update({
            'is_active': True,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', employee_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Employee {employee_id} reactivated successfully")
            return True
        else:
            print("Error reactivating employee or no data returned.")
            return False
            
    except Exception as e:
        print(f"Error reactivating employee: {e}")
        st.error(f"Error al reactivar empleado: {e}")
        return False

def get_inactive_employees(project_id: str) -> List[Employee]:
    """Get all inactive employees from the database."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return []
    
    try:
        response = (
            supabase.table("employees")
            .select("*")
            .eq("is_active", False)
            .order("full_name")
            .execute()
        )

        if response.data:
            return [_employee_from_dict(emp) for emp in response.data]
        else:
            print("No inactive employees found or error in response.")
            return []
            
    except Exception as e:
        print(f"Error fetching inactive employees: {e}")
        st.error(f"Error al obtener la lista de empleados inactivos: {e}")
        return []

# Función para formatear fechas al formato "año-mes-día (Nombre del día)"
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

def create_calendar_file(shift_data: ShiftRequest, is_for_requester: bool = True) -> Optional[str]:
    """
    Creates an .ics calendar file for a shift change.
    
    Args:
        shift_data: ``ShiftRequest`` instance with shift information
        is_for_requester: Boolean, True if calendar is for the person requesting the shift change
    
    Returns:
        String containing the .ics file content
    """
    try:
        # Parse the shift date from shift_data
        shift_date_str = shift_data.date_request
        if isinstance(shift_date_str, str):
            shift_date = datetime.fromisoformat(shift_date_str.replace('Z', '+00:00')).date()
        else:
            shift_date = datetime.now().date()
        
        # Extract flight information
        flight_info = shift_data.flight_number or 'Vuelo no especificado'
        
        # Get flight schedule details using the helper function
        schedule_info = get_flight_schedule_info(flight_info)
        start_time = schedule_info['start_time']
        end_time = schedule_info['end_time']
        is_overnight = schedule_info['is_overnight']
        
        # Create datetime objects for the shift in Toronto timezone
        toronto_tz = pytz.timezone('America/Toronto')
        
        # Create naive datetime objects first
        shift_start_naive = datetime.combine(shift_date, datetime.strptime(start_time, "%H:%M").time())
        
        # Handle overnight flights - end time is on the next day
        if is_overnight:
            shift_end_date = shift_date + timedelta(days=1)
            shift_end_naive = datetime.combine(shift_end_date, datetime.strptime(end_time, "%H:%M").time())
        else:
            shift_end_naive = datetime.combine(shift_date, datetime.strptime(end_time, "%H:%M").time())
        
        # Localize to Toronto timezone
        shift_start = toronto_tz.localize(shift_start_naive)
        shift_end = toronto_tz.localize(shift_end_naive)
        
        # Convert to UTC for iCal format
        shift_start_utc = shift_start.astimezone(pytz.UTC)
        shift_end_utc = shift_end.astimezone(pytz.UTC)
        
        # Format for iCal (UTC)
        def format_datetime_for_ical(dt):
            return dt.strftime('%Y%m%dT%H%M%SZ')  # Added Z suffix for UTC
        
        # Current timestamp for DTSTAMP in UTC
        now_utc = datetime.now(pytz.UTC)
        dtstamp = format_datetime_for_ical(now_utc)
        
        # Generate unique ID
        event_uid = f"shift-change-{shift_data.id or uuid.uuid4()}"
        
        # Determine event title and description based on who the calendar is for
        flight_schedule_display = schedule_info['display_schedule']
        
        if is_for_requester:
            # For the person who requested the change - they are GIVING UP this shift
            summary = f"TURNO CEDIDO: {flight_info} ({flight_schedule_display})"
            description = (
                f"Turno cedido - Intercambio aprobado\\nVuelo: {flight_info}\\nHorario: {flight_schedule_display}\\nCubierto por: {shift_data.cover_name or 'N/A'}\\nSupervisor: {shift_data.supervisor_name or 'N/A'}"
            )
            status = "CANCELLED"
        else:
            # For the person covering the shift - they are TAKING this shift
            summary = f"TURNO ACEPTADO: {flight_info} ({flight_schedule_display})"
            description = (
                f"Turno aceptado por intercambio\\nVuelo: {flight_info}\\nHorario: {flight_schedule_display}\\nSolicitante original: {shift_data.requester_name or 'N/A'}\\nSupervisor: {shift_data.supervisor_name or 'N/A'}"
            )
            status = "CONFIRMED"
        
        # Create iCal content with single event
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

def save_calendar_file(
    shift_data: ShiftRequest,
    is_for_requester: bool = True,
    filename_prefix: str = "shift_change",
) -> tuple[Optional[str], Optional[str]]:
    """
    Creates and saves a calendar file to a temporary location.
    
    Args:
        shift_data: ``ShiftRequest`` instance containing shift information
        is_for_requester: Boolean, True if calendar is for the person requesting the shift change
        filename_prefix: String prefix for the filename
    
    Returns:
        Tuple of (file_path, calendar_content) or (None, None) if error
    """
    try:
        import tempfile
        import os
        
        calendar_content = create_calendar_file(shift_data, is_for_requester)
        if not calendar_content:
            return None, None
        
        # Create a temporary file
        suffix = "_solicitante.ics" if is_for_requester else "_cobertura.ics"
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, prefix=filename_prefix, delete=False) as temp_file:
            temp_file.write(calendar_content)
            temp_file_path = temp_file.name
        
        return temp_file_path, calendar_content
        
    except Exception as e:
        print(f"Error saving calendar file: {e}")
        return None, None

def get_flight_schedule_info(flight_number):
    """
    Returns flight schedule information including proper handling of overnight flights.
    
    Args:
        flight_number: String containing the flight number (e.g., 'AV205', 'AV625')
    
    Returns:
        Dictionary with flight details including start_time, end_time, is_overnight, and display_schedule
    """
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
    
    # Default values if flight not found
    default_schedule = {
        'start_time': '09:00',
        'end_time': '17:00',
        'is_overnight': False,
        'display_schedule': '09:00-17:00'
    }
    
    return flight_schedules.get(flight_number, default_schedule)

# Remember to install the Supabase Python library: pip install supabase
# For smtplib, it's part of Python's standard library.
