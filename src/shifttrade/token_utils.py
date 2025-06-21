import uuid
from datetime import datetime, timedelta, timezone
import streamlit as st

from .supabase_client import supabase


def generate_token(shift_request_id: str, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede generar el token.")
        return None
    token = uuid.uuid4()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    try:
        response = supabase.table('tokens').insert({
            "token": str(token),
            "shift_request_id": str(shift_request_id),
            "expires_at": expires_at.isoformat(),
            "used": False,
        }).execute()
        if response.data and len(response.data) > 0:
            return str(token)
        else:
            err = getattr(response, 'error', None)
            if err:
                st.error(f"Error de Supabase al guardar token: {err.message}")
            return None
    except Exception as e:
        st.error(f"Excepción al guardar token en Supabase: {e}")
        return None


def verify_token(token_str: str, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede verificar el token.")
        return None
    try:
        response = (
            supabase.table('tokens')
            .select('shift_request_id, expires_at, used')
            .eq('token', token_str)
            .single()
            .execute()
        )
        if response.data:
            token_data = response.data
            expires_at_str = token_data['expires_at']
            expires_at = datetime.fromisoformat(expires_at_str)
            if not token_data['used'] and expires_at > datetime.now(timezone.utc):
                return token_data['shift_request_id']
            else:
                if token_data['used']:
                    st.warning("Token ya ha sido utilizado.")
                if expires_at <= datetime.now(timezone.utc):
                    st.warning("Token ha expirado.")
                return None
        else:
            st.error("Error de Supabase al verificar token: Token no encontrado")
            return None
    except Exception as e:
        st.error(f"Excepción al verificar token: {e}")
        return None


def mark_token_as_used(token_str: str, project_id: str):
    if not supabase:
        st.error("Cliente Supabase no inicializado. No se puede marcar el token.")
        return False
    try:
        response = supabase.table('tokens').update({'used': True}).eq('token', token_str).execute()
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        st.error(f"Excepción al marcar token como usado: {e}")
        return False
