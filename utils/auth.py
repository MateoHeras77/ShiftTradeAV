"""
Módulo de autenticación para ShiftTradeAV.
Contiene funciones para generación y validación de tokens.
"""

import streamlit as st
import uuid
from datetime import datetime, timedelta, timezone
from .config import supabase

def generate_token(shift_request_id: str, project_id: str):
    """Generates a unique token, stores it in Supabase, and returns the token."""
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede generar el token.")
        return None
    token = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)  # Use timezone.utc

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
            expires_at = datetime.fromisoformat(expires_at_str)  # Assumes ISO format from Supabase

            if not token_data['used'] and expires_at > datetime.now(timezone.utc):  # Compare with UTC now
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
