import streamlit as st
import pandas as pd # Import pandas for DataFrame
from datetime import datetime
import pytz
from utils import shift_request, email_utils, date_utils, calendar

# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx" # Replace with your actual Supabase project ID

st.set_page_config(
    page_title="Panel del Supervisor",
    page_icon="👑",
    layout="wide"
)

# --- Password Protection ---
if 'supervisor_authenticated' not in st.session_state:
    st.session_state.supervisor_authenticated = False

if not st.session_state.supervisor_authenticated:
    st.title("👑 Panel de Aprobación del Supervisor") # Show title before password
    st.warning("🔒 Área restringida - Se requiere contraseña de supervisor")
    supervisor_login_password = st.text_input("Contraseña de supervisor", type="password", key="supervisor_page_password")
    
    if st.button("Acceder", key="supervisor_login_button"):
        if supervisor_login_password == "supervisor123": # Temporary password
            st.session_state.supervisor_authenticated = True
            st.success("✅ Acceso concedido") # This message will be briefly shown before rerun
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")
    # Hide sidebar and the rest of the page if not authenticated
    st.sidebar.empty() # Clear sidebar
    st.stop() # Stop further execution if not authenticated
# --- End Password Protection ---

st.title("👑 Panel de Aprobación del Supervisor")

st.sidebar.header("Acciones")
if st.sidebar.button("Refrescar Datos"):
    # El método spinner no está disponible para st.sidebar
    refresh_status = st.sidebar.empty()
    refresh_status.info("Refrescando datos...")
    # Clear relevant session state to force data refresh if needed
    if 'pending_requests_data' in st.session_state:
        del st.session_state.pending_requests_data
    st.rerun()

st.sidebar.markdown("---")

# Main panel content is now only for pending_requests
st.header("Solicitudes Pendientes de Aprobación")
# 1. Display a list of all requests with `supervisor_status = 'pending'`
if 'pending_requests_data' not in st.session_state:
    with st.spinner("Cargando solicitudes pendientes..."):
        st.session_state.pending_requests_data = shift_request.get_pending_requests(PROJECT_ID)

pending_requests = st.session_state.pending_requests_data

if not pending_requests:
    st.info("No hay solicitudes de cambio de turno pendientes de aprobación.")
else:
    st.subheader(f"Total Pendientes: {len(pending_requests)}")
    
    # Ordenar solicitudes por fecha (más cercanas primero)
    try:
        # Convertir las fechas de string a objetos datetime para ordenarlas correctamente
        for req in pending_requests:
            if 'date_request' in req:
                # Intentar convertir a objeto datetime, si ya es un string ISO
                try:
                    req['date_request_obj'] = datetime.fromisoformat(req['date_request'].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    # Si hay un error, asignar fecha lejana para que aparezca al final
                    req['date_request_obj'] = datetime(2099, 1, 1)
            else:
                req['date_request_obj'] = datetime(2099, 1, 1)  # Fecha lejana por defecto
        
        # Ordenar la lista por la fecha (más cercanas primero)
        pending_requests = sorted(pending_requests, key=lambda x: x['date_request_obj'])
    except Exception as e:
        st.warning(f"No se pudieron ordenar las solicitudes por fecha: {e}")    
    for req in pending_requests:
        req_id = req.get('id')
        formatted_date = date_utils.format_date(req.get('date_request', 'N/A'))
        with st.expander(f"Fecha: {formatted_date} - Vuelo: {req.get('flight_number', 'N/A')} - Solicitante: {req.get('requester_name', 'N/A')}"):
                # Verificar si el cubridor ha aceptado la solicitud
                has_cover_accepted = req.get('date_accepted_by_cover') is not None and req.get('date_accepted_by_cover') != 'N/A'
                
                # Información básica de la solicitud
                st.markdown(f"""
                - **Fecha Solicitud:** {date_utils.format_date(req.get('date_request', 'N/A'))}
                - **Número de Vuelo:** {req.get('flight_number')}
                - **Solicitante:** {req.get('requester_name')} ({req.get('requester_employee_number')}, {req.get('requester_email')})
                - **Cubridor:** {req.get('cover_name')} ({req.get('cover_employee_number')}, {req.get('cover_email')})
                """)
                  # Mostrar estado de aceptación del cubridor con colores
                if has_cover_accepted:
                    st.success(f"✅ **ACEPTADO POR EL CUBRIDOR:** {date_utils.format_date(req.get('date_accepted_by_cover'))}")
                else:
                    st.error("❌ **PENDIENTE DE ACEPTACIÓN POR EL CUBRIDOR**")
                    st.warning("⚠️ El cubridor aún no ha aceptado esta solicitud. No se recomienda aprobarla hasta que el cubridor confirme.")

                supervisor_name_input = st.text_input("Nombre del Supervisor", key=f"supervisor_name_{req_id}")
                supervisor_password_input = st.text_input("Contraseña del Supervisor", type="password", key=f"supervisor_password_{req_id}")
                supervisor_comments = st.text_area("Comentarios (opcional para aprobación, obligatorio para rechazo)", key=f"comments_{req_id}")

                col1, col2, col_spacer = st.columns([1,1,5])
                with col1:
                    # Verificar si el cubridor ha aceptado para habilitar o deshabilitar el botón de aprobar
                    has_cover_accepted = req.get('date_accepted_by_cover') is not None and req.get('date_accepted_by_cover') != 'N/A'
                    
                    approve_button = st.button("✅ Aprobar", key=f"approve_{req_id}", type="primary", disabled=not has_cover_accepted)
                    
                    if approve_button:
                        if not supervisor_name_input:
                            st.warning("Por favor, ingresa tu nombre de supervisor.")
                        elif supervisor_password_input != "Avianca2025*":
                            st.error("Contraseña del supervisor incorrecta.")
                        elif not has_cover_accepted:
                            st.error("No se puede aprobar esta solicitud porque el cubridor aún no la ha aceptado.")
                        else:
                            approval_container = st.container()
                            with approval_container:
                                with st.spinner(f"Aprobando solicitud {req_id}..."):
                                    progress_bar = st.progress(0)
                                    st.caption("Actualizando estado en la base de datos...")
                                    now_utc = datetime.utcnow()
                                    updates = {
                                        "supervisor_status": "approved",
                                        "supervisor_decision_date": now_utc.isoformat(),
                                        "supervisor_comments": supervisor_comments,
                                        "supervisor_name": supervisor_name_input
                                    }
                                    update_success = shift_request.update_shift_request_status(req_id, updates, PROJECT_ID)
                                    progress_bar.progress(50)
                                    
                                    if update_success:
                                        st.caption("Enviando notificaciones por correo...")
                                          # Get formatted dates for the emails (en zona horaria de Toronto)
                                        toronto_tz = pytz.timezone('America/Toronto')
                                        now_toronto = datetime.now(toronto_tz)
                                        fecha_aprobacion = now_toronto.strftime("%d/%m/%Y")
                                        fecha_vuelo = date_utils.format_date(req.get('date_request'))
                                        
                                        # Obtener la fecha real de aceptación y mostrarla con hora Toronto
                                        date_accepted_by_cover = req.get('date_accepted_by_cover')
                                        if date_accepted_by_cover:
                                            dt_utc = datetime.fromisoformat(date_accepted_by_cover.replace('Z', '+00:00'))
                                            toronto_tz = pytz.timezone('America/Toronto')
                                            dt_toronto = dt_utc.astimezone(toronto_tz)
                                            fecha_aceptacion = dt_toronto.strftime('%d/%m/%Y %H:%M (hora Toronto)')
                                        else:
                                            fecha_aceptacion = "N/A"
                                        # Email to requester
                                        requester_subject = "✅ Cambio de Turno APROBADO"
                                        requester_body = f"""Hola {req.get('requester_name')},

¡Excelentes noticias! Tu solicitud de cambio de turno ha sido APROBADA.

**Detalles del cambio aprobado:**
• Vuelo: {req.get('flight_number')}
• Fecha del turno: {fecha_vuelo}
• Compañero que cubre: {req.get('cover_name')}
• Supervisor que aprobó: {supervisor_name_input}
• Fecha de aprobación: {fecha_aprobacion}

**Cronología:**
1. Solicitud enviada ✅
2. Aceptado por {req.get('cover_name')} el {fecha_aceptacion} ✅
3. Aprobado por supervisor el {fecha_aprobacion} ✅

**Comentarios del supervisor:** {supervisor_comments if supervisor_comments else "Sin comentarios adicionales"}

El cambio de turno está oficialmente autorizado.

Saludos,
ShiftTradeAV"""

                                        # Email to cover employee
                                        cover_subject = "✅ Cambio de Turno APROBADO"
                                        cover_body = f"""Hola {req.get('cover_name')},

El cambio de turno que aceptaste cubrir ha sido APROBADO por el supervisor.

**Detalles del cambio aprobado:**
• Vuelo: {req.get('flight_number')}
• Fecha del turno: {fecha_vuelo}
• Solicitante original: {req.get('requester_name')}
• Supervisor que aprobó: {supervisor_name_input}
• Fecha de aprobación: {fecha_aprobacion}

**Cronología:**
1. Solicitud enviada ✅
2. Tú aceptaste el {fecha_aceptacion} ✅
3. Aprobado por supervisor el {fecha_aprobacion} ✅

**Comentarios del supervisor:** {supervisor_comments if supervisor_comments else "Sin comentarios adicionales"}

Gracias por tu colaboración. El cambio está oficialmente autorizado.

Saludos,
ShiftTradeAV"""

                                        # Send emails with calendar attachments
                                        email1 = email_utils.send_email_with_calendar(
                                            req.get('requester_email'), 
                                            requester_subject, 
                                            requester_body,
                                            req,  # shift_data
                                            is_for_requester=True
                                        )
                                        email2 = email_utils.send_email_with_calendar(
                                            req.get('cover_email'), 
                                            cover_subject, 
                                            cover_body,
                                            req,  # shift_data
                                            is_for_requester=False
                                        )
                                        progress_bar.progress(100)
                                        
                                        st.success(f"Solicitud {req_id} aprobada por {supervisor_name_input}.")
                                        if not (email1 and email2):
                                            st.warning("La aprobación fue guardada, pero hubo problemas al enviar algunas notificaciones por correo.")
                                        
                                        # Clear pending requests cache and rerun
                                        if 'pending_requests_data' in st.session_state:
                                            del st.session_state.pending_requests_data
                                        st.rerun()
                                    else:
                                        st.error(f"Error al aprobar la solicitud {req_id}.")

                with col2:
                    if st.button("❌ Rechazar", key=f"reject_{req_id}"):
                        if not supervisor_name_input:
                            st.warning("Por favor, ingresa tu nombre de supervisor.")
                        elif supervisor_password_input != "Avianca2025*":
                            st.error("Contraseña del supervisor incorrecta.")
                        elif not supervisor_comments:
                            st.warning("Por favor, añade un comentario explicando el motivo del rechazo.")
                        else:
                            rejection_container = st.container()
                            with rejection_container:
                                with st.spinner(f"Rechazando solicitud {req_id}..."):
                                    progress_bar = st.progress(0)
                                    st.caption("Actualizando estado en la base de datos...")
                                    now_utc = datetime.utcnow()
                                    updates = {
                                        "supervisor_status": "rejected",
                                        "supervisor_decision_date": now_utc.isoformat(),
                                        "supervisor_comments": supervisor_comments,
                                        "supervisor_name": supervisor_name_input
                                    }
                                    update_success = shift_request.update_shift_request_status(req_id, updates, PROJECT_ID)
                                    progress_bar.progress(50)
                                    
                                    if update_success:
                                        st.caption("Enviando notificaciones por correo...")
                                          # Get formatted dates for the emails (en zona horaria de Toronto)
                                        toronto_tz = pytz.timezone('America/Toronto')
                                        now_toronto = datetime.now(toronto_tz)
                                        # Formato: 2025-05-29 (jueves) 23:18 (hora Toronto)
                                        dia_semana_rechazo = now_toronto.strftime('%A')
                                        dias_es = {
                                            'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles', 'Thursday': 'jueves',
                                            'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo'
                                        }
                                        dia_semana_rechazo_es = dias_es.get(dia_semana_rechazo, dia_semana_rechazo).capitalize()
                                        fecha_rechazo = now_toronto.strftime(f'%Y-%m-%d ({dia_semana_rechazo_es}) %H:%M (hora Toronto)')
                                        fecha_vuelo = date_utils.format_date(req.get('date_request'))
                                        # Obtener la fecha real de aceptación y mostrarla con hora Toronto y día en español
                                        date_accepted_by_cover = req.get('date_accepted_by_cover')
                                        if date_accepted_by_cover:
                                            dt_utc = datetime.fromisoformat(date_accepted_by_cover.replace('Z', '+00:00'))
                                            dt_toronto = dt_utc.astimezone(toronto_tz)
                                            dia_semana_aceptacion = dt_toronto.strftime('%A')
                                            dia_semana_aceptacion_es = dias_es.get(dia_semana_aceptacion, dia_semana_aceptacion).capitalize()
                                            fecha_aceptacion = dt_toronto.strftime(f'%Y-%m-%d ({dia_semana_aceptacion_es}) %H:%M (hora Toronto)')
                                        else:
                                            fecha_aceptacion = "N/A"
                                        # Email to requester
                                        requester_subject = "❌ Cambio de Turno RECHAZADO"
                                        requester_body = f"""Hola {req.get('requester_name')},

Lamentamos informarte que tu solicitud de cambio de turno ha sido RECHAZADA.

**Detalles de la solicitud rechazada:**
• Vuelo: {req.get('flight_number')}
• Fecha del turno: {fecha_vuelo}
• Compañero que había aceptado: {req.get('cover_name')}
• Supervisor que rechazó: {supervisor_name_input}
• Fecha de rechazo: {fecha_rechazo}

**Cronología:**
1. Solicitud enviada ✅
2. Aceptado por {req.get('cover_name')} el {fecha_aceptacion} ✅
3. Rechazado por supervisor el {fecha_rechazo} ❌

**Motivo del rechazo:** {supervisor_comments}

Puedes presentar una nueva solicitud si consideras que las circunstancias han cambiado.

Saludos,
ShiftTradeAV"""

                                        # Email to cover employee
                                        cover_subject = "❌ Cambio de Turno RECHAZADO"
                                        cover_body = f"""Hola {req.get('cover_name')},

Te informamos que el cambio de turno que habías aceptado cubrir ha sido RECHAZADO por el supervisor.

**Detalles de la solicitud rechazada:**
• Vuelo: {req.get('flight_number')}
• Fecha del turno: {fecha_vuelo}
• Solicitante original: {req.get('requester_name')}
• Supervisor que rechazó: {supervisor_name_input}
• Fecha de rechazo: {fecha_rechazo}

**Cronología:**
1. Solicitud enviada ✅
2. Tú aceptaste el {fecha_aceptacion} ✅
3. Rechazado por supervisor el {fecha_rechazo} ❌

**Motivo del rechazo:** {supervisor_comments}

Ya no necesitas cubrir este turno. Gracias por tu disposición.

Saludos,
ShiftTradeAV"""

                                        email1 = email_utils.send_email(req.get('requester_email'), requester_subject, requester_body)
                                        email2 = email_utils.send_email(req.get('cover_email'), cover_subject, cover_body)
                                        progress_bar.progress(100)
                                        
                                        st.success(f"Solicitud {req_id} rechazada por {supervisor_name_input}.")
                                        if not (email1 and email2):
                                            st.warning("El rechazo fue guardado, pero hubo problemas al enviar algunas notificaciones por correo.")
                                        
                                        # Clear pending requests cache and rerun
                                        if 'pending_requests_data' in st.session_state:
                                            del st.session_state.pending_requests_data
                                        st.rerun()
                st.markdown("---")

# Removed the 'history_view' block and related logic

st.markdown("---")
st.caption("ShiftTradeAV - Panel del Supervisor")

# To run this page:
# streamlit run supervisor.py --server.runOnSave true
