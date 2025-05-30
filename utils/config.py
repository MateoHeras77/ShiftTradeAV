"""
Módulo de configuración para ShiftTradeAV.
Centraliza la configuración del cliente Supabase y parámetros del SMTP.
"""

import streamlit as st
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Email configuration
SMTP_SERVER = st.secrets["SMTP_SERVER"]
SMTP_PORT = int(st.secrets["SMTP_PORT"])
SMTP_USERNAME = st.secrets["SMTP_USERNAME"]
SMTP_PASSWORD = st.secrets["SMTP_PASSWORD"]
SENDER_EMAIL = st.secrets["SENDER_EMAIL"]

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client initialized successfully.")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    st.error(f"Error crítico al conectar con Supabase: {e}")
    supabase = None  # Ensure supabase is None if initialization fails
