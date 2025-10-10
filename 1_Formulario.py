import streamlit as st
from datetime import datetime, timedelta
import re
import utils  # Your utility functions for Supabase, tokens, and email

# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx"  # Replace with your actual Supabase project ID


# Function to validate email format
def validate_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


st.set_page_config(page_title="Solicitar Cambio", page_icon="✈️", layout="centered")

# IMPORTANT: Application decommission banner
# This shows a blocking, prominent message to users and stops the app so
# no new shift trade requests can be created here. The message points users
# to the new SwiftShift service.
st.markdown("# ⚠️ Servicio descontinuado")
st.caption(
    "Esta aplicación ya no acepta nuevas solicitudes de cambio de turno.\n"
    "Por favor, utiliza el servicio actualizado en: https://www.swiftshift.digital/"
)
st.info(
    "Para crear nuevas solicitudes o gestionar cambios de turno, visita: https://www.swiftshift.digital/"
)
# Prevent the rest of the Streamlit app from running
st.stop()


st.title("✈️ Formulario de Solicitud de Cambio de Turno")

# Load employees data for dropdowns
if "employees_data" not in st.session_state:
    with st.spinner("Cargando lista de empleados..."):
        st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)

employees = st.session_state.employees_data

# Check if there are employees in the database
if not employees:
    st.warning("⚠️ No se encontraron empleados en la base de datos.")
    st.info("💡 Contacta al administrador para que agregue empleados al sistema.")
    st.stop()

employee_names = ["Seleccionar empleado..."] + [emp["full_name"] for emp in employees]

# RAIC color options
raic_options = ["Morado", "Amarillo", "Verde"]

# Initialize session state for form data
if "requester_data" not in st.session_state:
    st.session_state.requester_data = {}
if "cover_data" not in st.session_state:
    st.session_state.cover_data = {}

# Add refresh button for employee list
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Actualizar Lista"):
        st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
        st.rerun()

# Form sections outside of st.form for better reactivity
st.header("Detalles del Turno")
min_shift_date = datetime.now().date() #+ timedelta(days=1)
date_request_input = st.date_input(
    "Fecha del turno a Cambiar", value=min_shift_date, min_value=min_shift_date
)

# Flight options with schedules
flight_options = [
    "Seleccionar vuelo...",
    "AV255 (5:00-10:00)",
    "AV619 (04:00-09:00)",  # NUEVO VUELO
    "AV627 (13:00-17:30)",
    "AV205 (20:00-00:30+1)",  # Overnight flight - arrives next day
    "AV625 (20:00-02:30+1)",  # Overnight flight - arrives next day
    "AV255-AV627 Full Day (5:00-17:30)",
    "AV619-AV627 Full Day (4:00-17:30)",
    "AV627-AV205 Full Day (13:00-00:30+1)",  # Overnight flight - arrives next day
]

selected_flight = st.selectbox("Número de Vuelo", flight_options)

# Extract just the flight number for storage
if selected_flight != "Seleccionar vuelo...":
    flight_number = selected_flight.split(" ")[0]  # Extract AV255, AV627, or AV205
else:
    flight_number = ""

st.header("Empleado que Solicita el Cambio")

# Dropdown for requester
selected_requester = st.selectbox(
    "Seleccionar solicitante", employee_names, key="requester_select"
)

# Auto-fill fields for requester
if selected_requester != "Seleccionar empleado...":
    requester_employee = next(
        (emp for emp in employees if emp["full_name"] == selected_requester), None
    )
    if requester_employee:
        st.session_state.requester_data = requester_employee
        requester_name = st.text_input(
            "Nombre del solicitante",
            value=requester_employee["full_name"],
            disabled=True,
        )
        requester_employee_number = st.selectbox(
            "Color del RAIC (Solicitante)",
            raic_options,
            index=(
                raic_options.index(requester_employee["raic_color"])
                if requester_employee["raic_color"] in raic_options
                else 0
            ),
            disabled=True,
        )
        requester_email = st.text_input(
            "Email del solicitante", value=requester_employee["email"], disabled=True
        )
    else:
        requester_name = st.text_input("Nombre del solicitante")
        requester_employee_number = st.selectbox(
            "Color del RAIC (Solicitante)", ["Seleccionar color..."] + raic_options
        )
        requester_email = st.text_input(
            "Email del solicitante", placeholder="ejemplo@empresa.com"
        )
else:
    requester_name = st.text_input("Nombre del solicitante")
    requester_employee_number = st.selectbox(
        "Color del RAIC (Solicitante)", ["Seleccionar color..."] + raic_options
    )
    requester_email = st.text_input(
        "Email del solicitante", placeholder="ejemplo@empresa.com"
    )

# Option to add manual data if not in dropdown
if selected_requester == "Seleccionar empleado...":
    st.caption(
        "💡 ¿El empleado no está en la lista? Completa manualmente los campos o contacta al administrador para agregarlo al sistema."
    )

st.header("Empleado que Cubrirá el Turno")

# Dropdown for cover employee
selected_cover = st.selectbox(
    "Seleccionar compañero que cubrirá", employee_names, key="cover_select"
)

# Prevent selecting the same person for both roles
if (
    selected_requester != "Seleccionar empleado..."
    and selected_cover == selected_requester
):
    st.error(
        "❌ El solicitante y el compañero que cubrirá no pueden ser la misma persona."
    )

# Auto-fill fields for cover employee
if selected_cover != "Seleccionar empleado...":
    cover_employee = next(
        (emp for emp in employees if emp["full_name"] == selected_cover), None
    )
    if cover_employee:
        st.session_state.cover_data = cover_employee
        cover_name = st.text_input(
            "Nombre del compañero que cubrirá",
            value=cover_employee["full_name"],
            disabled=True,
        )
        cover_employee_number = st.selectbox(
            "Color del RAIC (Cubridor)",
            raic_options,
            index=(
                raic_options.index(cover_employee["raic_color"])
                if cover_employee["raic_color"] in raic_options
                else 0
            ),
            disabled=True,
        )
        cover_email = st.text_input(
            "Email del compañero que cubrirá",
            value=cover_employee["email"],
            disabled=True,
        )
    else:
        cover_name = st.text_input("Nombre del compañero que cubrirá")
        cover_employee_number = st.selectbox(
            "Color del RAIC (Cubridor)",
            ["Seleccionar color..."] + raic_options,
            key="manual_cover_color",
        )
        cover_email = st.text_input(
            "Email del compañero que cubrirá", placeholder="compañero@empresa.com"
        )
else:
    cover_name = st.text_input("Nombre del compañero que cubrirá")
    cover_employee_number = st.selectbox(
        "Color del RAIC (Cubridor)",
        ["Seleccionar color..."] + raic_options,
        key="manual_cover_color_noemp",
    )
    cover_email = st.text_input(
        "Email del compañero que cubrirá", placeholder="compañero@empresa.com"
    )

# Option to add manual data if not in dropdown
if selected_cover == "Seleccionar empleado...":
    st.caption(
        "💡 ¿El empleado no está en la lista? Completa manualmente los campos o contacta al administrador para agregarlo al sistema."
    )

st.caption(
    "⚠️ Verifica cuidadosamente el email - es la única forma de contactar al compañero"
)

st.header("Confirmaciones Requeridas")

# Checkbox de confirmaciones obligatorias
confirmations_checked = st.checkbox(
    """**Confirmo que:**
    
1. Yo, junto con mi compañero, tenemos al menos dos días dentro de la semana que solicitamos libres.

2. Acepto los términos y condiciones del sistema de cambio de turnos.""",
    value=False,
    key="mandatory_confirmations"
)

if not confirmations_checked:
    st.warning("⚠️ Debes confirmar ambos puntos antes de enviar la solicitud")

# Submit button outside of form
submit_button = st.button("Enviar Solicitud", type="primary")

if submit_button:
    # Validation checks
    if not confirmations_checked:
        st.error("❌ Debes confirmar los términos antes de enviar la solicitud.")
    elif not all(
        [
            date_request_input,
            flight_number,
            requester_name,
            requester_employee_number,
            requester_email,
            cover_name,
            cover_employee_number,
            cover_email,
        ]
    ):
        st.error("Por favor, completa todos los campos.")
    elif (
        selected_requester != "Seleccionar empleado..."
        and selected_cover == selected_requester
    ):
        st.error(
            "❌ El solicitante y el compañero que cubrirá no pueden ser la misma persona."
        )
    elif not validate_email(requester_email):
        st.error(
            "❌ El email del solicitante no tiene un formato válido. Por favor, verifica que incluya @ y un dominio válido."
        )
    elif not validate_email(cover_email):
        st.error(
            "❌ El email del compañero que cubrirá no tiene un formato válido. Por favor, verifica que incluya @ y un dominio válido."
        )
    elif cover_employee_number == "Verde" and requester_employee_number != "Verde":
        st.error("Un RAIC verde solo puede cubrir a otro verde.")
    else:
        with st.spinner("Procesando la solicitud..."):
            request_details = {
                "date_request": str(
                    date_request_input
                ),  # Ensure it's a string for Supabase if not handled by client
                "flight_number": flight_number,
                "requester_name": requester_name,
                "requester_employee_number": requester_employee_number,
                "requester_email": requester_email,
                "cover_name": cover_name,
                "cover_employee_number": cover_employee_number,
                "cover_email": cover_email,
                "supervisor_status": "pending",  # Initial status
            }

            # 1. Save data to Supabase (shift_requests table)
            progress_bar = st.progress(0)
            st.caption("Guardando solicitud en la base de datos...")
            shift_request_id = utils.save_shift_request(request_details, PROJECT_ID)
            progress_bar.progress(33)

            if shift_request_id:
                st.caption("Generando token de aceptación...")
                # 2. Generate a UUID token
                token = utils.generate_token(shift_request_id, PROJECT_ID)
                progress_bar.progress(66)

                if token:
                    # 3. Create a unique link with the token for Streamlit Cloud
                    accept_url = (
                        f"https://shifttrade.streamlit.app/Solicitud?token={token}"
                    )

                    # 4. Send the link by email to the covering employee
                    st.caption("Enviando correo electrónico...")
                    email_subject = "Solicitud de Cobertura de Turno"

                    # Get current date for the request
                    fecha_solicitud = datetime.now().strftime("%d/%m/%Y")

                    # Get flight schedule information for email
                    flight_schedule = utils.get_flight_schedule_info(flight_number)

                    email_body = f"""Hola {cover_name},

{requester_name} ha solicitado que cubras su turno para el vuelo {flight_number} el {utils.format_date(date_request_input)}.

**Detalles de la solicitud:**
• Fecha de solicitud: {fecha_solicitud}
• Vuelo: {flight_number}
• Horario: {flight_schedule['display_schedule']}
• Fecha del turno: {utils.format_date(date_request_input)}
• Solicitante: {requester_name}

Para aceptar, por favor haz clic en el siguiente enlace (válido por 24 horas):
{accept_url}

Gracias."""
                    email_sent = utils.send_email(
                        cover_email, email_subject, email_body
                    )
                    progress_bar.progress(100)

                    if email_sent:
                        st.success(f"✅ Solicitud enviada con ID: {shift_request_id}")
                        st.info(
                            f"📧 Se ha enviado un correo a **{cover_email}** con el enlace para aceptar el cambio."
                        )
                        st.info(
                            "💡 **Nota importante:** Si el compañero no recibe el correo, verifica que:"
                        )
                        st.write("• El email esté escrito correctamente")
                        st.write("• Revise su carpeta de spam/correo no deseado")
                        st.write("• El dominio del email sea válido")
                    else:
                        st.success(f"✅ Solicitud guardada con ID: {shift_request_id}")
                        st.error("❌ **Error al enviar el correo de aceptación**")
                        st.warning("⚠️ **Posibles causas del error:**")
                        st.write(
                            "• El email ingresado podría tener un error de digitación"
                        )
                        st.write("• El dominio del email no existe")
                        st.write("• Problemas temporales del servidor de correo")
                        st.info("🔧 **Soluciones:**")
                        st.write("• Verifica que el email esté escrito correctamente")
                        st.write("• Contacta directamente al compañero con el enlace:")
                        st.code(accept_url)
                        st.write(
                            "• O contacta al administrador para reenviar el correo"
                        )
                else:
                    st.error(
                        "Error al generar el token de aceptación. La solicitud fue guardada, pero el correo no pudo ser enviado."
                    )
            else:
                st.error("Error al guardar la solicitud en la base de datos.")

st.markdown("---")
st.caption("ShiftTradeAV - Gestión de Cambios de Turno")
