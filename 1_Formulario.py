import streamlit as st
from datetime import datetime
import re
import pytz
from utils import auth, email_utils, date_utils, shift_request, employee

# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx" # Replace with your actual Supabase project ID

# Function to validate email format
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

st.set_page_config(
    page_title="Solicitar Cambio",
    page_icon="✈️",
    layout="centered"
)


st.title("✈️ Formulario de Solicitud de Cambio de Turno")

# Load employees data for dropdowns
if 'employees_data' not in st.session_state:
    with st.spinner("Cargando lista de empleados..."):
        st.session_state.employees_data = employee.get_all_employees(PROJECT_ID)

employees = st.session_state.employees_data

# Check if there are employees in the database
if not employees:
    st.warning("⚠️ No se encontraron empleados en la base de datos.")
    st.info("💡 Contacta al administrador para que agregue empleados al sistema.")
    st.stop()

employee_names = ["Seleccionar empleado..."] + [emp['full_name'] for emp in employees]

# Initialize session state for form data
if 'requester_data' not in st.session_state:
    st.session_state.requester_data = {}
if 'cover_data' not in st.session_state:
    st.session_state.cover_data = {}

# Add refresh button for employee list
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Actualizar Lista"):
        st.session_state.employees_data = employee.get_all_employees(PROJECT_ID)
        st.rerun()

# Form sections outside of st.form for better reactivity
st.header("Detalles del Turno")
st.info("📋 Nota: Todas las fechas y horas se muestran en la zona horaria de Toronto (EST/EDT)")
date_request_input = st.date_input("Fecha del turno a Cambiar", value=datetime.today())

# Flight options with schedules
flight_options = [
    "Seleccionar vuelo...",
    "AV255 (5:00-10:00)",
    "AV627 (13:00-17:30)", 
    "AV205 (20:00-23:59)"
]

selected_flight = st.selectbox("Número de Vuelo", flight_options)

# Extract just the flight number for storage
if selected_flight != "Seleccionar vuelo...":
    flight_number = selected_flight.split(" ")[0]  # Extract AV255, AV627, or AV205
else:
    flight_number = ""

st.header("Empleado que Solicita el Cambio")

# Dropdown for requester
selected_requester = st.selectbox("Seleccionar solicitante", employee_names, key="requester_select")

# Auto-fill fields for requester
if selected_requester != "Seleccionar empleado...":
    requester_employee = next((emp for emp in employees if emp['full_name'] == selected_requester), None)
    if requester_employee:
        st.session_state.requester_data = requester_employee
        requester_name = st.text_input("Nombre del solicitante", value=requester_employee['full_name'], disabled=True)
        requester_employee_number = st.text_input("Color del RAIC (Solicitante)", value=requester_employee['raic_color'], disabled=True)
        requester_email = st.text_input("Email del solicitante", value=requester_employee['email'], disabled=True)
    else:
        requester_name = st.text_input("Nombre del solicitante")
        requester_employee_number = st.text_input("Color del RAIC (Solicitante)")
        requester_email = st.text_input("Email del solicitante", placeholder="ejemplo@empresa.com")
else:
    requester_name = st.text_input("Nombre del solicitante")
    requester_employee_number = st.text_input("Color del RAIC (Solicitante)")
    requester_email = st.text_input("Email del solicitante", placeholder="ejemplo@empresa.com")

# Option to add manual data if not in dropdown
if selected_requester == "Seleccionar empleado...":
    st.caption("💡 ¿El empleado no está en la lista? Completa manualmente los campos o contacta al administrador para agregarlo al sistema.")

st.header("Empleado que Cubrirá el Turno")

# Dropdown for cover employee
selected_cover = st.selectbox("Seleccionar compañero que cubrirá", employee_names, key="cover_select")

# Prevent selecting the same person for both roles
if selected_requester != "Seleccionar empleado..." and selected_cover == selected_requester:
    st.error("❌ El solicitante y el compañero que cubrirá no pueden ser la misma persona.")

# Auto-fill fields for cover employee
if selected_cover != "Seleccionar empleado...":
    cover_employee = next((emp for emp in employees if emp['full_name'] == selected_cover), None)
    if cover_employee:
        st.session_state.cover_data = cover_employee
        cover_name = st.text_input("Nombre del compañero que cubrirá", value=cover_employee['full_name'], disabled=True)
        cover_employee_number = st.text_input("Color del RAIC (Cubridor)", value=cover_employee['raic_color'], disabled=True)
        cover_email = st.text_input("Email del compañero que cubrirá", value=cover_employee['email'], disabled=True)
    else:
        cover_name = st.text_input("Nombre del compañero que cubrirá")
        cover_employee_number = st.text_input("Color del RAIC (Cubridor)")
        cover_email = st.text_input("Email del compañero que cubrirá", placeholder="compañero@empresa.com")
else:
    cover_name = st.text_input("Nombre del compañero que cubrirá")
    cover_employee_number = st.text_input("Color del RAIC (Cubridor)")
    cover_email = st.text_input("Email del compañero que cubrirá", placeholder="compañero@empresa.com")

# Option to add manual data if not in dropdown
if selected_cover == "Seleccionar empleado...":
    st.caption("💡 ¿El empleado no está en la lista? Completa manualmente los campos o contacta al administrador para agregarlo al sistema.")

st.caption("⚠️ Verifica cuidadosamente el email - es la única forma de contactar al compañero")

# Submit button outside of form
submit_button = st.button("Enviar Solicitud", type="primary")

if submit_button:
    # Validation checks
    if not all([date_request_input, flight_number, requester_name, requester_employee_number, requester_email, cover_name, cover_employee_number, cover_email]):
        st.error("Por favor, completa todos los campos.")
    elif selected_requester != "Seleccionar empleado..." and selected_cover == selected_requester:
        st.error("❌ El solicitante y el compañero que cubrirá no pueden ser la misma persona.")
    elif not validate_email(requester_email):
        st.error("❌ El email del solicitante no tiene un formato válido. Por favor, verifica que incluya @ y un dominio válido.")
    elif not validate_email(cover_email):
        st.error("❌ El email del compañero que cubrirá no tiene un formato válido. Por favor, verifica que incluya @ y un dominio válido.")
    else:
        with st.spinner("Procesando la solicitud..."):            # Convertir la fecha a datetime en zona horaria de Toronto
            toronto_tz = pytz.timezone('America/Toronto')
            # Combinar la fecha con tiempo a las 00:00 y aplicar zona horaria de Toronto
            date_with_tz = toronto_tz.localize(datetime.combine(date_request_input, datetime.min.time()))
            
            request_details = {
                "date_request": date_with_tz.isoformat(), # Fecha con zona horaria explícita
                "flight_number": flight_number,
                "requester_name": requester_name,
                "requester_employee_number": requester_employee_number,
                "requester_email": requester_email,
                "cover_name": cover_name,
                "cover_employee_number": cover_employee_number,
                "cover_email": cover_email,
                "supervisor_status": "pending" # Initial status
            }            # 1. Save data to Supabase (shift_requests table)
            progress_bar = st.progress(0)
            st.caption("Guardando solicitud en la base de datos...")
            shift_request_id = shift_request.save_shift_request(request_details, PROJECT_ID)
            progress_bar.progress(33)

            if shift_request_id:
                st.caption("Generando token de aceptación...")
                # 2. Generate a UUID token
                token = auth.generate_token(shift_request_id, PROJECT_ID)
                progress_bar.progress(66)

                if token:
                    # 3. Create a unique link with the token for Streamlit Cloud
                    accept_url = f"https://shifttrade.streamlit.app/Solicitud?token={token}"

                    # 4. Send the link by email to the covering employee
                    st.caption("Enviando correo electrónico...")
                    email_subject = "Solicitud de Cobertura de Turno"
                      # Get current date for the request in Toronto timezone
                    toronto_tz = pytz.timezone('America/Toronto')
                    now_toronto = datetime.now(toronto_tz)
                    fecha_solicitud = now_toronto.strftime("%d/%m/%Y")
                    email_body = f"""Hola {cover_name},

{requester_name} ha solicitado que cubras su turno para el vuelo {flight_number} el {date_utils.format_date(date_request_input)}.

**Detalles de la solicitud:**
• Fecha de solicitud: {date_utils.format_date(now_toronto)}
• Vuelo: {flight_number}
• Fecha del turno: {date_utils.format_date(date_request_input)}
• Solicitante: {requester_name}

Para aceptar, por favor haz clic en el siguiente enlace (válido por 24 horas):
{accept_url}

Gracias."""
                    email_sent = email_utils.send_email(cover_email, email_subject, email_body)
                    progress_bar.progress(100)

                    if email_sent:
                        st.success(f"✅ Solicitud enviada con ID: {shift_request_id}")
                        st.info("Se ha enviado un correo de confirmación al compañero que cubrirá el turno.")
                        st.balloons()
                    else:
                        st.warning("La solicitud fue guardada, pero hubo un problema al enviar el correo de confirmación.")
                else:
                    st.warning("No se pudo generar el token de aceptación. La solicitud fue guardada, pero no se pudo enviar el enlace de aceptación.")
            else:
                st.error("No se pudo guardar la solicitud. Por favor, inténtalo de nuevo.")

st.markdown("---")
st.caption("ShiftTradeAV - Solicitud de Cambio de Turno")
