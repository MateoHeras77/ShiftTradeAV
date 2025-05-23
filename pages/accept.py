import streamlit as st
from datetime import datetime

try:
    import utils # Your utility functions
except st.errors.StreamlitSecretNotFoundError as e:
    st.error(
        "CRITICAL ERROR: Could not load application secrets required by 'utils.py'.\n"
        "Please ensure that the file '.streamlit/secrets.toml' exists in your project root "
        "(/Users/mateoheras/Library/CloudStorage/OneDrive-Personal/GitHub/ShiftTradeAV/.streamlit/secrets.toml) "
        "and contains all necessary secrets (e.g., SUPABASE_URL, SUPABASE_KEY, SMTP details).\n\n"
        f"Details from Streamlit: {e}"
    )
    st.caption("The application cannot continue without these secrets. Please create or correct the secrets.toml file and restart.")
    st.stop()
except ImportError as e:
    st.error(f"Failed to import the 'utils' module. Please ensure 'utils.py' exists in the same directory and is free of errors. Details: {e}")
    st.stop()

# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx" # Replace with your actual Supabase project ID

st.set_page_config(page_title="Aceptar Cambio de Turno", layout="centered")

st.title("✔️ Aceptar Cambio de Turno")

query_params = st.query_params
token = query_params.get("token")

if not token:
    st.error("Token no proporcionado. Por favor, usa el enlace enviado a tu correo.")
    st.stop()

with st.spinner("Validando token..."):
    # 1. Validate the token
    shift_request_id = utils.verify_token(str(token), PROJECT_ID) # Ensure token is string

if not shift_request_id:
    st.error("El token es inválido, ha expirado o ya ha sido utilizado.")
    st.image("https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbjV0ZzNocG9jM3hpYjB4Yms4YmY5N3V2eHdyM2N5Y2NnbnZtY2NqZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/jB57hZPa2mX5B9B22N/giphy.gif", caption="Token Inválido")
    st.stop()

st.info(f"Token válido. Estás a punto de aceptar cubrir un turno.")
st.write(f"ID de la solicitud de cambio: {shift_request_id}") # For debugging or info

# Fetch shift request details to show some info (optional but good UX)
with st.spinner("Cargando detalles del turno..."):
    request_details = utils.get_shift_request_details(shift_request_id, PROJECT_ID)
if request_details:
    st.markdown(f"""
    **Detalles del Turno a Cubrir:**
    - **Fecha del Turno Original:** {utils.format_date(request_details.get('date_request', 'N/A'))}
    - **Vuelo:** {request_details.get('flight_number', 'N/A')}
    
    **Información del Solicitante:**
    - **Nombre:** {request_details.get('requester_name', 'N/A')}
    - **Número de Empleado:** {request_details.get('requester_employee_number', 'N/A')}
    - **Email:** {request_details.get('requester_email', 'N/A')}

    **Confirmación de Tus Datos (Quien Cubre):**
    - **Nombre:** {request_details.get('cover_name', 'N/A')}
    - **Número de Empleado:** {request_details.get('cover_employee_number', 'N/A')}
    - **Email:** {request_details.get('cover_email', 'N/A')}
    """)
else:
    st.warning("No se pudieron cargar los detalles completos de la solicitud.")


if st.button("✅ Aceptar Cambio de Turno"):
    with st.spinner("Procesando la aceptación..."):
        # 2. Update `date_accepted_by_cover` in `shift_requests`
        #    Mark token as `used`
        progress_bar = st.progress(0)
        st.caption("Actualizando estado de la solicitud...")
        now_utc = datetime.utcnow()
        update_success = utils.update_shift_request_status(
            shift_request_id,
            {
                "date_accepted_by_cover": now_utc.isoformat()
            },
            PROJECT_ID
        )
        progress_bar.progress(33)
        
        st.caption("Marcando token como utilizado...")
        token_marked = utils.mark_token_as_used(str(token), PROJECT_ID)
        progress_bar.progress(50)

        if update_success and token_marked:
            # Re-fetch details to get emails for confirmation
            st.caption("Preparando correos de confirmación...")
            updated_request_details = utils.get_shift_request_details(shift_request_id, PROJECT_ID)
            progress_bar.progress(66)
            
            if updated_request_details:
                requester_email = updated_request_details.get('requester_email')
                cover_email = updated_request_details.get('cover_email') # Your email
                requester_name = updated_request_details.get('requester_name')
                cover_name = updated_request_details.get('cover_name')
                flight_number = updated_request_details.get('flight_number')

                # 3. Send confirmation emails
                st.caption("Enviando correos de confirmación...")
                confirmation_subject = "Confirmación de Cambio de Turno Aceptado"
                emails_sent = True
                
                # Email to requester
                if requester_email:
                    requester_body = f"""Hola {requester_name},

Buenas noticias. {cover_name} ha aceptado cubrir tu turno para el vuelo {flight_number}.
La solicitud está ahora pendiente de aprobación por el supervisor.

Saludos."""
                    if not utils.send_email(requester_email, confirmation_subject, requester_body):
                        emails_sent = False
                progress_bar.progress(83)

                # Email to cover (yourself)
                if cover_email:
                    cover_body = f"""Hola {cover_name},

Has aceptado cubrir el turno de {requester_name} para el vuelo {flight_number}.
La solicitud está ahora pendiente de aprobación por el supervisor.

Gracias por tu colaboración."""
                    if not utils.send_email(cover_email, confirmation_subject, cover_body):
                        emails_sent = False
                progress_bar.progress(100)

                st.success("¡Has aceptado cubrir el turno!")
                if emails_sent:
                    st.info("Se han enviado correos de confirmación a ambas partes.")
                else:
                    st.warning("Se actualizó el estado, pero hubo un problema al enviar algunos correos de confirmación.")
                st.balloons()
            else:
                st.warning("Se actualizó el estado, pero hubo un problema al obtener los detalles para enviar los correos de confirmación.")
        else:
            st.error("Hubo un error al procesar tu aceptación. Por favor, inténtalo de nuevo o contacta al administrador.")

st.markdown("---")
st.caption("ShiftTradeAV - Aceptación de Turno")

# To run this page, you would typically navigate to:
# streamlit run accept.py --server.runOnSave true --server.port 8501 (or another port if 8501 is taken)
# And then open http://localhost:8501/?token=YOUR_TOKEN_HERE
