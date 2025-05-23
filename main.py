import streamlit as st
from datetime import datetime
import utils  # Your utility functions for Supabase, tokens, and email

# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx" # Replace with your actual Supabase project ID

st.set_page_config(page_title="Solicitud de Cambio de Turno", layout="centered")

st.title("✈️ Formulario de Solicitud de Cambio de Turno")

with st.form("shift_request_form"):
    st.header("Detalles del Turno")
    date_request_input = st.date_input("Fecha del turno original", value=datetime.today())
    flight_number = st.text_input("Número de Vuelo")

    st.header("Empleado que Solicita el Cambio")
    requester_name = st.text_input("Nombre del solicitante")
    requester_employee_number = st.text_input("Número de empleado del solicitante")
    requester_email = st.text_input("Email del solicitante")

    st.header("Empleado que Cubrirá el Turno")
    cover_name = st.text_input("Nombre del compañero que cubrirá")
    cover_employee_number = st.text_input("Número de empleado del compañero")
    cover_email = st.text_input("Email del compañero que cubrirá")

    submit_button = st.form_submit_button("Enviar Solicitud")

if submit_button:
    if not all([date_request_input, flight_number, requester_name, requester_employee_number, requester_email, cover_name, cover_employee_number, cover_email]):
        st.error("Por favor, completa todos los campos.")
    else:
        with st.spinner("Procesando la solicitud..."):
            request_details = {
                "date_request": str(date_request_input), # Ensure it's a string for Supabase if not handled by client
                "flight_number": flight_number,
                "requester_name": requester_name,
                "requester_employee_number": requester_employee_number,
                "requester_email": requester_email,
                "cover_name": cover_name,
                "cover_employee_number": cover_employee_number,
                "cover_email": cover_email,
                "supervisor_status": "pending" # Initial status
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
                    # 3. Create a unique link with the token
                    # IMPORTANT: Ensure accept.py is running, potentially on a different port.
                    # Example: streamlit run accept.py --server.port 8502
                    accept_url = f"http://localhost:8502/?token={token}" # Assumes accept.py runs on port 8502

                    # 4. Send the link by email to the covering employee
                    st.caption("Enviando correo electrónico...")
                    email_subject = "Solicitud de Cobertura de Turno"
                    email_body = f"""Hola {cover_name},

{requester_name} ha solicitado que cubras su turno para el vuelo {flight_number} el {date_request_input}.

Para aceptar, por favor haz clic en el siguiente enlace (válido por 24 horas):
{accept_url}

Gracias."""
                    email_sent = utils.send_email(cover_email, email_subject, email_body)
                    progress_bar.progress(100)

                    if email_sent:
                        st.success(f"Solicitud enviada con ID: {shift_request_id}")
                        st.info(f"Se ha enviado un correo a {cover_email} con el enlace para aceptar el cambio.")
                    else:
                        st.success(f"Solicitud enviada con ID: {shift_request_id}")
                        st.error("Error al enviar el correo de aceptación. Por favor, contacta al administrador.")
                else:
                    st.error("Error al generar el token de aceptación. La solicitud fue guardada, pero el correo no pudo ser enviado.")
            else:
                st.error("Error al guardar la solicitud en la base de datos.")

st.markdown("---")
st.caption("ShiftTradeAV - Gestión de Cambios de Turno")
