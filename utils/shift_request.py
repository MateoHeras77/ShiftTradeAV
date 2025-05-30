"""
Módulo de gestión de solicitudes de cambio de turno para ShiftTradeAV.
Contiene funciones para interactuar con solicitudes de cambio de turno en Supabase.
"""

import streamlit as st
from datetime import datetime, date
import pytz
import uuid
from .config import supabase

def save_shift_request(details: dict, project_id: str):
    """Saves shift request details to Supabase and returns the new request's ID."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede guardar la solicitud.")
        return None
    try:
        # Convertir fecha de zona horaria Toronto a UTC para almacenar en Supabase
        if 'date_request' in details:
            if isinstance(details['date_request'], (datetime, uuid.UUID)):
                # Si es un objeto datetime, asumimos que ya tiene zona horaria
                details['date_request'] = details['date_request'].astimezone(pytz.UTC).isoformat()
            elif isinstance(details['date_request'], date):
                # Si es un objeto date (sin hora), convertirlo a datetime con hora 00:00 en Toronto
                toronto_tz = pytz.timezone('America/Toronto')
                dt_toronto = toronto_tz.localize(datetime.combine(details['date_request'], datetime.min.time()))
                # Convertir a UTC para almacenar en la base de datos
                dt_utc = dt_toronto.astimezone(pytz.UTC)
                details['date_request'] = dt_utc.isoformat()
            elif isinstance(details['date_request'], str):
                # Si ya es string, intentar convertir a datetime para aplicar la zona horaria
                try:
                    dt = datetime.fromisoformat(details['date_request'].replace('Z', '+00:00'))
                    # Si no tiene timezone, asumimos que es hora local (Toronto)
                    if dt.tzinfo is None:
                        toronto_tz = pytz.timezone('America/Toronto')
                        dt = toronto_tz.localize(dt)
                    # Convertir a UTC
                    details['date_request'] = dt.astimezone(pytz.UTC).isoformat()
                except ValueError:
                    # Si no se puede convertir, dejarlo como está
                    pass

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
        # Ensure timestamp fields are ISO strings in UTC timezone if they are datetime objects
        for key in ['date_accepted_by_cover', 'supervisor_decision_date']:
            if key in updates:
                if isinstance(updates[key], datetime):
                    # Si ya es un objeto datetime, verificar si tiene timezone
                    if updates[key].tzinfo is None:
                        # Si no tiene timezone, asumimos que es hora local (Toronto)
                        toronto_tz = pytz.timezone('America/Toronto')
                        updates[key] = toronto_tz.localize(updates[key])
                    # Convertir a UTC para almacenar en la base de datos
                    updates[key] = updates[key].astimezone(pytz.UTC).isoformat()
                elif isinstance(updates[key], str):
                    try:
                        # Intentar convertir de string a datetime con timezone
                        dt = datetime.fromisoformat(updates[key].replace('Z', '+00:00'))
                        if dt.tzinfo is None:
                            toronto_tz = pytz.timezone('America/Toronto')
                            dt = toronto_tz.localize(dt)
                        updates[key] = dt.astimezone(pytz.UTC).isoformat()
                    except ValueError:
                        # Si no se puede convertir, dejar como está
                        pass
        
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
        
        # Procesamiento adicional para asegurar manejo correcto de caracteres especiales
        data = response.data if response.data else []
        
        # Asegurar que los caracteres especiales se manejen correctamente
        for record in data:
            for key, value in record.items():
                if isinstance(value, str):
                    # Asegurarse de que la codificación de caracteres sea correcta
                    record[key] = value
                    
        return data
    except Exception as e:
        print(f"Exception fetching all shift requests: {e}")
        st.error(f"Excepción al obtener todas las solicitudes: {e}")
        return []
