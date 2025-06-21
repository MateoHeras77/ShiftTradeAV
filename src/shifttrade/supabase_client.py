import streamlit as st
from datetime import datetime, date, timezone
from supabase import create_client, Client

from .config import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client once
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized successfully.")
except Exception as e:
    supabase = None
    st.error(f"Error crítico al conectar con Supabase: {e}")
    print(f"Error initializing Supabase client: {e}")

# --- Shift request functions ---

def save_shift_request(details: dict, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede guardar la solicitud.")
        return None
    try:
        if 'date_request' in details and isinstance(details['date_request'], (datetime, date)):
            details['date_request'] = str(details['date_request'])
        response = supabase.table('shift_requests').insert(details).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        else:
            err = getattr(response, 'error', None)
            if err:
                st.error(f"Error de Supabase al guardar solicitud: {err.message}")
            return None
    except Exception as e:
        st.error(f"Excepción al guardar solicitud: {e}")
        return None


def update_shift_request_status(request_id: str, updates: dict, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede actualizar la solicitud.")
        return False
    try:
        for key in ['date_accepted_by_cover', 'supervisor_decision_date']:
            if key in updates and isinstance(updates[key], datetime):
                updates[key] = updates[key].isoformat()
        response = supabase.table('shift_requests').update(updates).eq('id', request_id).execute()
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        st.error(f"Excepción al actualizar solicitud: {e}")
        return False


def get_pending_requests(project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener las solicitudes pendientes.")
        return []
    try:
        response = supabase.table('shift_requests').select('*').eq('supervisor_status', 'pending').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Excepción al obtener solicitudes pendientes: {e}")
        return []


def get_shift_request_details(request_id: str, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener los detalles.")
        return None
    try:
        response = supabase.table('shift_requests').select('*').eq('id', request_id).single().execute()
        return response.data if response.data else None
    except Exception as e:
        st.error(f"Excepción al obtener detalles de solicitud: {e}")
        return None


def get_all_shift_requests(project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener todas las solicitudes.")
        return []
    try:
        response = supabase.table('shift_requests').select('*').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Excepción al obtener todas las solicitudes: {e}")
        return []

# --- Employee management functions ---

def get_all_employees(project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return []
    try:
        response = supabase.table('employees').select('*').eq('is_active', True).order('full_name').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error al obtener la lista de empleados: {e}")
        return []


def get_inactive_employees(project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return []
    try:
        response = supabase.table('employees').select('*').eq('is_active', False).order('full_name').execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error al obtener la lista de empleados inactivos: {e}")
        return []


def get_employee_by_name(full_name: str, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return None
    try:
        response = supabase.table('employees').select('*').eq('full_name', full_name).eq('is_active', True).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error al obtener datos del empleado {full_name}: {e}")
        return None


def get_employee_by_email(email: str, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return None
    try:
        response = supabase.table('employees').select('*').eq('email', email).eq('is_active', True).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error al obtener datos del empleado por email {email}: {e}")
        return None


def check_employee_exists(full_name: str = None, email: str = None, project_id: str = None):
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
    except Exception:
        return False


def add_employee(full_name: str, raic_color: str, email: str, project_id: str):
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
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        st.error(f"Error al agregar empleado: {e}")
        return False


def update_employee(employee_id: int, full_name: str, raic_color: str, email: str, project_id: str):
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
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        st.error(f"Error al actualizar empleado: {e}")
        return False


def deactivate_employee(employee_id: int, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    try:
        response = supabase.table('employees').update({
            'is_active': False,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', employee_id).execute()
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        st.error(f"Error al desactivar empleado: {e}")
        return False


def reactivate_employee(employee_id: int, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    try:
        response = supabase.table('employees').update({
            'is_active': True,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', employee_id).execute()
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        st.error(f"Error al reactivar empleado: {e}")
        return False
