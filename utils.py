import streamlit as st
import smtplib
import uuid
from datetime import datetime, timedelta, timezone, date # Import date
from email.mime.text import MIMEText
from supabase import create_client, Client # Import Supabase client
import locale

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

def generate_token(shift_request_id: str, project_id: str): # project_id is not strictly needed if supabase client is global
    """Generates a unique token, stores it in Supabase, and returns the token."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede generar el token.")
        return None
    token = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24) # Use timezone.utc

    try:
        response = supabase.table('tokens').insert({
            "token": str(token),
            "shift_request_id": str(shift_request_id),
            "expires_at": expires_at.isoformat(),
            "used": False
        }).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Token {token} saved for shift_request_id {shift_request_id}")
            return str(token)
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

def verify_token(token_str: str, project_id: str):
    """Verifies a token against Supabase. Returns the shift_request_id if valid, else None."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede verificar el token.")
        return None
    try:
        response = supabase.table('tokens').select('shift_request_id, expires_at, used').eq('token', token_str).single().execute()
        if response.data:
            token_data = response.data
            expires_at_str = token_data['expires_at']
            expires_at = datetime.fromisoformat(expires_at_str) # Assumes ISO format from Supabase

            if not token_data['used'] and expires_at > datetime.now(timezone.utc): # Compare with UTC now
                return token_data['shift_request_id']
            else:
                if token_data['used']: st.warning("Token ya ha sido utilizado.")
                if expires_at <= datetime.now(timezone.utc): st.warning("Token ha expirado.")
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

def mark_token_as_used(token_str: str, project_id: str):
    """Marks a token as used in Supabase."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede marcar el token.")
        return False
    try:
        response = supabase.table('tokens').update({'used': True}).eq('token', token_str).execute()
        if response.data and len(response.data) > 0:
            print(f"Token {token_str} marked as used.")
            return True
        else:
            error_message = "No se pudo marcar el token como usado o no se encontró."
            if hasattr(response, 'error') and response.error: error_message = response.error.message
            print(f"Failed to mark token {token_str} as used: {error_message}")
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

def save_shift_request(details: dict, project_id: str):
    """Saves shift request details to Supabase and returns the new request's ID."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede guardar la solicitud.")
        return None
    try:
        # Ensure date_request is string. Streamlit date_input gives datetime.date
        if 'date_request' in details and isinstance(details['date_request'], (datetime, uuid.UUID, date)): # Use imported date type
             details['date_request'] = str(details['date_request'])

        response = supabase.table('shift_requests').insert(details).execute()
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

def get_pending_requests(project_id: str):
    """Fetches all shift requests with supervisor_status = 'pending'."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener las solicitudes pendientes.")
        return []
    try:
        # No ordenamos aquí ya que lo haremos más precisamente en el frontend
        response = supabase.table('shift_requests').select('*').eq('supervisor_status', 'pending').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Exception fetching pending requests: {e}")
        st.error(f"Excepción al obtener solicitudes pendientes: {e}")
        return []

def get_shift_request_details(request_id: str, project_id: str):
    """Fetches details for a specific shift request."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener los detalles.")
        return None
    try:
        response = supabase.table('shift_requests').select('*').eq('id', request_id).single().execute()
        return response.data if response.data else None
    except Exception as e:
        print(f"Exception fetching shift request details for {request_id}: {e}")
        st.error(f"Excepción al obtener detalles de solicitud: {e}")
        return None

def get_all_shift_requests(project_id: str):
    """Fetches all shift requests from the database."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener todas las solicitudes.")
        return []
    try:
        # No aplicamos ordenamiento en la consulta para hacer el sorting en el frontend con más control
        response = supabase.table('shift_requests').select('*').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Exception fetching all shift requests: {e}")
        st.error(f"Excepción al obtener todas las solicitudes: {e}")
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

# Remember to install the Supabase Python library: pip install supabase
# For smtplib, it's part of Python's standard library.
