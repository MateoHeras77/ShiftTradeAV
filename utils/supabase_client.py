"""
Supabase client initialization and management.
Handles the connection to the Supabase database.
"""

import streamlit as st
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY

# Global variable to hold the Supabase client
supabase: Client = None

def initialize_supabase_client():
    """Initialize the Supabase client."""
    global supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
        return supabase
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        st.error(f"Error crítico al conectar con Supabase: {e}")
        supabase = None
        return None

def get_supabase_client():
    """Get the Supabase client, initializing if necessary."""
    global supabase
    if supabase is None:
        return initialize_supabase_client()
    return supabase

# Initialize client on module import
initialize_supabase_client()
