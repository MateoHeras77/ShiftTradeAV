"""
Shift request management module.
Handles all CRUD operations for shift requests.
"""

import streamlit as st
from datetime import datetime, timezone, date
from .supabase_client import get_supabase_client

def save_shift_request(details: dict, project_id: str):
    """Saves shift request details to Supabase and returns the new request's ID."""
    supabase = get_supabase_client()
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede guardar la solicitud.")
        return None
    
    try:
        # Ensure date_request is string. Streamlit date_input gives datetime.date
        if 'date_request' in details and isinstance(details['date_request'], (datetime, date)):
            details['date_request'] = str(details['date_request'])

        response = supabase.table('shift_requests').insert(details).execute()
        if response.data and len(response.data) > 0:
            new_id = response.data[0]['id']
            print(f"Shift request saved with ID: {new_id}")
            return new_id
        else:
            error_message = "No data returned from Supabase or error in response."
            if hasattr(response, 'error') and response.error: 
                error_message = response.error.message
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
    supabase = get_supabase_client()
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
            if hasattr(response, 'error') and response.error: 
                error_message = response.error.message
            print(f"Failed to update shift request {request_id}: {error_message}")
            st.error(f"Error de Supabase al actualizar solicitud: {error_message}")
            return False
    except Exception as e:
        print(f"Exception updating shift request: {e}")
        st.error(f"Excepción al actualizar solicitud: {e}")
        return False

def get_pending_requests(project_id: str):
    """Fetches all shift requests with supervisor_status = 'pending'."""
    supabase = get_supabase_client()
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener las solicitudes pendientes.")
        return []
    
    try:
        response = supabase.table('shift_requests').select('*').eq('supervisor_status', 'pending').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Exception fetching pending requests: {e}")
        st.error(f"Excepción al obtener solicitudes pendientes: {e}")
        return []

def get_shift_request_details(request_id: str, project_id: str):
    """Fetches details for a specific shift request."""
    supabase = get_supabase_client()
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
    supabase = get_supabase_client()
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se pueden obtener todas las solicitudes.")
        return []
    
    try:
        response = supabase.table('shift_requests').select('*').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Exception fetching all shift requests: {e}")
        st.error(f"Excepción al obtener todas las solicitudes: {e}")
        return []
