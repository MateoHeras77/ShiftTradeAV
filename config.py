import os
import streamlit as st

def get_config_value(name, default=None):
    """Retrieve configuration value from environment variable or Streamlit secrets."""
    return os.getenv(name) or st.secrets.get(name, default)

PROJECT_ID = get_config_value("PROJECT_ID")
SUPERVISOR_PASSWORD = get_config_value("SUPERVISOR_PASSWORD")
ADMIN_PASSWORD = get_config_value("ADMIN_PASSWORD")
