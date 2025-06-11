import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

SMTP_SERVER = st.secrets["SMTP_SERVER"]
SMTP_PORT = int(st.secrets["SMTP_PORT"])
SMTP_USERNAME = st.secrets["SMTP_USERNAME"]
SMTP_PASSWORD = st.secrets["SMTP_PASSWORD"]
SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
