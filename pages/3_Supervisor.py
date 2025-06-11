import streamlit as st
import pandas as pd  # Import pandas for DataFrame
from datetime import datetime
import utils
import supabase_client
import token_utils
import email_utils


def render_pending_request(req):
    """Render a single pending request with approve/reject actions."""
    req_id = req.get("id")
    formatted_date = utils.format_date(req.get("date_request", "N/A"))
    expander_title = f"Fecha: {formatted_date} - Vuelo: {req.get('flight_number', 'N/A')} - Solicitante: {req.get('requester_name', 'N/A')}"

    with st.expander(expander_title):
        with st.form(key=f"form_{req_id}"):
            st.markdown(
                f"""
                - **Fecha Solicitud:** {utils.format_date(req.get('date_request', 'N/A'))}
                - **Número de Vuelo:** {req.get('flight_number')}
                - **Solicitante:** {req.get('requester_name')} ({req.get('requester_employee_number')}, {req.get('requester_email')})
                - **Cubridor:** {req.get('cover_name')} ({req.get('cover_employee_number')}, {req.get('cover_email')})
                """
            )

            has_cover_accepted = (
                req.get("date_accepted_by_cover") is not None
                and req.get("date_accepted_by_cover") != "N/A"
            )
            if has_cover_accepted:
                st.success(
                    f"✅ **ACEPTADO POR EL CUBRIDOR:** {utils.format_date(req.get('date_accepted_by_cover'))}"
                )
            else:
                st.error("❌ **PENDIENTE DE ACEPTACIÓN POR EL CUBRIDOR**")
                st.warning(
                    "⚠️ El cubridor aún no ha aceptado esta solicitud. No se recomienda aprobarla hasta que el cubridor confirme."
                )

            supervisor_name_input_val = st.text_input(
                "Nombre del Supervisor", key=f"supervisor_name_form_{req_id}"
            )
            supervisor_password_input_val = st.text_input(
                "Contraseña del Supervisor",
                type="password",
                key=f"supervisor_password_form_{req_id}",
            )
            supervisor_comments_val = st.text_area(
                "Comentarios (opcional para aprobación, obligatorio para rechazo)",
                key=f"comments_form_{req_id}",
            )

            col1, col2, _ = st.columns([1, 1, 5])
            with col1:
                approve_submitted = st.form_submit_button(
                    "✅ Aprobar", type="primary", disabled=not has_cover_accepted
                )
            with col2:
                reject_submitted = st.form_submit_button("❌ Rechazar")

        if approve_submitted:
            if not supervisor_name_input_val:
                st.warning("Por favor, ingresa tu nombre de supervisor.")
            elif supervisor_password_input_val != CORRECT_PASSWORD:
                st.error("Contraseña del supervisor incorrecta.")
            elif not has_cover_accepted:
                st.error(
                    "No se puede aprobar esta solicitud porque el cubridor aún no la ha aceptado."
                )
            else:
                with st.spinner(f"Aprobando solicitud {req_id}..."):
                    progress_bar = st.progress(0)
                    st.caption("Actualizando estado en la base de datos...")
                    now_utc = datetime.utcnow()
                    updates = {
                        "supervisor_status": "approved",
                        "supervisor_decision_date": now_utc.isoformat(),
                        "supervisor_comments": supervisor_comments_val,
                        "supervisor_name": supervisor_name_input_val,
                    }
                    update_success = supabase_client.update_shift_request_status(
                        req_id, updates, PROJECT_ID
                    )
                    progress_bar.progress(50)

                    if update_success:
                        st.caption("Enviando notificaciones por correo...")
                        fecha_aprobacion = datetime.now().strftime("%d/%m/%Y")
                        fecha_vuelo = utils.format_date(req.get("date_request"))
                        fecha_aceptacion = (
                            utils.format_date(req.get("date_accepted_by_cover"))
                            if req.get("date_accepted_by_cover")
                            else "N/A"
                        )

                        requester_subject = "✅ Cambio de Turno APROBADO"
                        requester_body = f"""Hola {req.get('requester_name')},

¡Excelentes noticias! Tu solicitud de cambio de turno ha sido APROBADA.

**Detalles del cambio aprobado:**
• Vuelo: {req.get('flight_number')}
• Fecha del turno: {fecha_vuelo}
• Compañero que cubre: {req.get('cover_name')}
• Supervisor que aprobó: {supervisor_name_input_val}
• Fecha de aprobación: {fecha_aprobacion}

**Cronología:**
1. Solicitud enviada ✅
2. Aceptado por {req.get('cover_name')} el {fecha_aceptacion} ✅
3. Aprobado por supervisor el {fecha_aprobacion} ✅

**Comentarios del supervisor:** {supervisor_comments_val if supervisor_comments_val else 'Sin comentarios adicionales'}

El cambio de turno está oficialmente autorizado.

Saludos,
ShiftTradeAV"""
                        cover_subject = "✅ Cambio de Turno APROBADO"
                        cover_body = f"""Hola {req.get('cover_name')},

El cambio de turno que aceptaste cubrir ha sido APROBADO por el supervisor.

**Detalles del cambio aprobado:**
• Vuelo: {req.get('flight_number')}
• Fecha del turno: {fecha_vuelo}
• Solicitante original: {req.get('requester_name')}
• Supervisor que aprobó: {supervisor_name_input_val}
• Fecha de aprobación: {fecha_aprobacion}

**Cronología:**
1. Solicitud enviada ✅
2. Tú aceptaste el {fecha_aceptacion} ✅
3. Aprobado por supervisor el {fecha_aprobacion} ✅

**Comentarios del supervisor:** {supervisor_comments_val if supervisor_comments_val else 'Sin comentarios adicionales'}

Gracias por tu colaboración. El cambio está oficialmente autorizado.

Saludos,
ShiftTradeAV"""
                        email1 = email_utils.send_email_with_calendar(
                            req.get("requester_email"),
                            requester_subject,
                            requester_body,
                            req,
                            is_for_requester=True,
                        )
                        email2 = email_utils.send_email_with_calendar(
                            req.get("cover_email"),
                            cover_subject,
                            cover_body,
                            req,
                            is_for_requester=False,
                        )
                        progress_bar.progress(100)

                        st.success(
                            f"Solicitud {req_id} aprobada por {supervisor_name_input_val}."
                        )
                        if not (email1 and email2):
                            st.warning(
                                "La aprobación fue guardada, pero hubo problemas al enviar algunas notificaciones por correo."
                            )

                        if "pending_requests_data" in st.session_state:
                            del st.session_state.pending_requests_data
                        st.rerun()
                    else:
                        st.error(f"Error al aprobar la solicitud {req_id}.")

        elif reject_submitted:
            if not supervisor_name_input_val:
                st.warning("Por favor, ingresa tu nombre de supervisor.")
            elif supervisor_password_input_val != CORRECT_PASSWORD:
                st.error("Contraseña del supervisor incorrecta.")
            elif not supervisor_comments_val:
                st.warning(
                    "Por favor, añade un comentario explicando el motivo del rechazo."
                )
            else:
                with st.spinner(f"Rechazando solicitud {req_id}..."):
                    progress_bar = st.progress(0)
                    st.caption("Actualizando estado en la base de datos...")
                    now_utc = datetime.utcnow()
                    updates = {
                        "supervisor_status": "rejected",
                        "supervisor_decision_date": now_utc.isoformat(),
                        "supervisor_comments": supervisor_comments_val,
                        "supervisor_name": supervisor_name_input_val,
                    }
                    update_success = supabase_client.update_shift_request_status(
                        req_id, updates, PROJECT_ID
                    )
                    progress_bar.progress(50)

                    if update_success:
                        st.caption("Enviando notificaciones por correo...")
                        fecha_rechazo = datetime.now().strftime("%d/%m/%Y")
                        fecha_vuelo = utils.format_date(req.get("date_request"))
                        fecha_aceptacion = (
                            utils.format_date(req.get("date_accepted_by_cover"))
                            if req.get("date_accepted_by_cover")
                            else "N/A"
                        )

                        requester_subject = "❌ Cambio de Turno RECHAZADO"
                        requester_body = f"""Hola {req.get('requester_name')},

Lamentamos informarte que tu solicitud de cambio de turno ha sido RECHAZADA.

**Detalles de la solicitud rechazada:**
• Vuelo: {req.get('flight_number')}
• Fecha del turno: {fecha_vuelo}
• Compañero que había aceptado: {req.get('cover_name')}
• Supervisor que rechazó: {supervisor_name_input_val}
• Fecha de rechazo: {fecha_rechazo}

**Cronología:**
1. Solicitud enviada ✅
2. Aceptado por {req.get('cover_name')} el {fecha_aceptacion} ✅
3. Rechazado por supervisor el {fecha_rechazo} ❌

**Motivo del rechazo:** {supervisor_comments_val}

Puedes presentar una nueva solicitud si consideras que las circunstancias han cambiado.

Saludos,
ShiftTradeAV"""
                        cover_subject = "❌ Cambio de Turno RECHAZADO"
                        cover_body = f"""Hola {req.get('cover_name')},

Te informamos que el cambio de turno que habías aceptado cubrir ha sido RECHAZADO por el supervisor.

**Detalles de la solicitud rechazada:**
• Vuelo: {req.get('flight_number')}
• Fecha del turno: {fecha_vuelo}
• Solicitante original: {req.get('requester_name')}
• Supervisor que rechazó: {supervisor_name_input_val}
• Fecha de rechazo: {fecha_rechazo}

**Cronología:**
1. Solicitud enviada ✅
2. Tú aceptaste el {fecha_aceptacion} ✅
3. Rechazado por supervisor el {fecha_rechazo} ❌

**Motivo del rechazo:** {supervisor_comments_val}

Ya no necesitas cubrir este turno. Gracias por tu disposición.

Saludos,
ShiftTradeAV"""
                        email1 = email_utils.send_email(
                            req.get("requester_email"),
                            requester_subject,
                            requester_body,
                        )
                        email2 = email_utils.send_email(
                            req.get("cover_email"), cover_subject, cover_body
                        )
                        progress_bar.progress(100)

                        st.success(
                            f"Solicitud {req_id} rechazada por {supervisor_name_input_val}."
                        )
                        if not (email1 and email2):
                            st.warning(
                                "El rechazo fue guardado, pero hubo problemas al enviar algunas notificaciones por correo."
                            )

                        if "pending_requests_data" in st.session_state:
                            del st.session_state.pending_requests_data
                        st.rerun()
                    else:
                        st.error(f"Error al rechazar la solicitud {req_id}.")

    st.markdown("---")


# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx"  # Replace with your actual Supabase project ID
CORRECT_PASSWORD = "supervisor2025"

st.set_page_config(page_title="Panel del Supervisor", page_icon="👑", layout="wide")

# Password protection
if "supervisor_password_correct" not in st.session_state:
    st.session_state.supervisor_password_correct = False

if not st.session_state.supervisor_password_correct:
    st.title("👑 Acceso al Panel de Supervisor")
    password_attempt = st.text_input(
        "Ingrese la contraseña para acceder:",
        type="password",
        key="supervisor_page_password",
    )
    if password_attempt:
        if password_attempt == CORRECT_PASSWORD:
            st.session_state.supervisor_password_correct = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta.")
    st.stop()  # Do not render the rest of the page if password is not correct

# --- Main Page Content Starts Here ---
st.title("👑 Panel de Aprobación del Supervisor")

# Initialize session state for view mode if it doesn't exist
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "pending_requests"  # Default view

st.sidebar.header("Acciones")
if st.sidebar.button("Refrescar Datos"):
    # El método spinner no está disponible para st.sidebar
    refresh_status = st.sidebar.empty()
    refresh_status.info("Refrescando datos...")
    # Clear relevant session state to force data refresh if needed
    if "all_requests_for_history" in st.session_state:
        del st.session_state.all_requests_for_history
    if "pending_requests_data" in st.session_state:
        del st.session_state.pending_requests_data
    st.rerun()

st.sidebar.markdown("---")

# Sidebar buttons to switch views
if st.sidebar.button("Ver Solicitudes Pendientes", key="view_pending"):
    st.session_state.view_mode = "pending_requests"
    st.rerun()

if st.sidebar.button("Ver Historial de Solicitudes", key="view_history"):
    st.session_state.view_mode = "history_view"
    st.rerun()

st.sidebar.markdown("---")

# Main panel content based on view_mode
if st.session_state.view_mode == "pending_requests":
    st.header("Solicitudes Pendientes de Aprobación")
    # 1. Display a list of all requests with `supervisor_status = 'pending'`
    if "pending_requests_data" not in st.session_state:
        with st.spinner("Cargando solicitudes pendientes..."):
            st.session_state.pending_requests_data = supabase_client.get_pending_requests(
                PROJECT_ID
            )

    pending_requests = st.session_state.pending_requests_data

    if not pending_requests:
        st.info("No hay solicitudes de cambio de turno pendientes de aprobación.")
        # Add a button to switch to history view if no pending requests
        if st.button("Ver Historial de Solicitudes", key="pending_to_history_button"):
            st.session_state.view_mode = "history_view"
            st.rerun()
    else:
        st.subheader(f"Total Pendientes: {len(pending_requests)}")

        # Ordenar solicitudes por fecha (más cercanas primero)
        try:
            for req in pending_requests:
                if "date_request" in req:
                    try:
                        req["date_request_obj"] = datetime.fromisoformat(
                            req["date_request"].replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        req["date_request_obj"] = datetime(2099, 1, 1)
                else:
                    req["date_request_obj"] = datetime(2099, 1, 1)

            pending_requests = sorted(
                pending_requests, key=lambda x: x["date_request_obj"]
            )
        except Exception as e:
            st.warning(f"No se pudieron ordenar las solicitudes por fecha: {e}")

        accepted_by_cover = [
            r
            for r in pending_requests
            if r.get("date_accepted_by_cover") not in (None, "N/A")
        ]
        awaiting_cover = [
            r
            for r in pending_requests
            if r.get("date_accepted_by_cover") in (None, "N/A")
        ]

        if accepted_by_cover:
            st.subheader("✅ Solicitudes con cubridor confirmado")
            for req in accepted_by_cover:
                render_pending_request(req)

        if awaiting_cover:
            st.subheader("⏳ Solicitudes pendientes de aceptación por el cubridor")
            for req in awaiting_cover:
                render_pending_request(req)

        st.markdown("---")

elif st.session_state.view_mode == "history_view":
    st.header("Historial de Todas las Solicitudes")

    # Fetch all requests (not just pending) for history, cache in session state
    if "all_requests_for_history" not in st.session_state:
        with st.spinner("Cargando historial de solicitudes..."):
            st.session_state.all_requests_for_history = supabase_client.get_all_shift_requests(
                PROJECT_ID
            )

    all_requests_for_history = st.session_state.all_requests_for_history

    if not all_requests_for_history:
        st.info("No hay historial de solicitudes disponible.")
        # Add a button to switch to pending view if no history
        if st.button("Ver Solicitudes Pendientes", key="history_to_pending_button"):
            st.session_state.view_mode = "pending_requests"
            st.rerun()
    else:
        # Convertir la lista de solicitudes a DataFrame para facilitar manipulación
        df_history = pd.DataFrame(all_requests_for_history)

        # Ordenar por fecha de vuelo (convertir a datetime para ordenamiento correcto)
        try:
            # Convertir fecha_request a datetime para ordenar correctamente
            df_history["date_request_dt"] = pd.to_datetime(
                df_history["date_request"], errors="coerce"
            )
            # Ordenar por fecha ascendente (más cercanas primero)
            df_history = df_history.sort_values(by="date_request_dt").reset_index(
                drop=True
            )
            # Eliminar columna auxiliar usada para ordenar
            df_history = df_history.drop("date_request_dt", axis=1)
        except Exception as e:
            st.warning(f"No se pudo ordenar el historial por fecha: {e}")

        columns_to_display = [
            "id",
            "date_request",
            "flight_number",
            "requester_name",
            "cover_name",
            "supervisor_status",
            "supervisor_name",
            "supervisor_decision_date",
            "supervisor_comments",
        ]
        existing_columns_in_df = [
            col for col in columns_to_display if col in df_history.columns
        ]

        df_display_full = df_history[existing_columns_in_df].copy()

        # Convert relevant date columns to datetime objects and format with day name
        if (
            "date_request" in df_display_full.columns
        ):  # Assuming this is the original shift date
            # Usar la función personalizada de formateo para todas las fechas
            df_display_full["date_request"] = df_display_full["date_request"].apply(
                utils.format_date
            )
        if "supervisor_decision_date" in df_display_full.columns:
            df_display_full["supervisor_decision_date"] = df_display_full[
                "supervisor_decision_date"
            ].apply(utils.format_date)

        rename_map = {
            "id": "ID",
            "date_request": "Fecha Vuelo Orig.",
            "flight_number": "Vuelo",
            "requester_name": "Solicitante",
            "cover_name": "Cubridor",
            "supervisor_status": "Estado Sup.",
            "supervisor_name": "Supervisor",
            "supervisor_decision_date": "Fecha Decisión Sup.",
            "supervisor_comments": "Comentarios Sup.",
        }
        df_display_filtered = df_display_full.rename(
            columns={
                k: v for k, v in rename_map.items() if k in df_display_full.columns
            }
        )

        # Ensure the order of columns after renaming
        ordered_renamed_columns = [
            rename_map[col]
            for col in existing_columns_in_df
            if col in rename_map and rename_map[col] in df_display_filtered.columns
        ]
        df_display_filtered = df_display_filtered[ordered_renamed_columns]

        st.markdown("### Filtrar Historial")
        filter_cols = st.columns(3)

        with filter_cols[0]:
            if "Solicitante" in df_display_filtered.columns:
                requester_names = sorted(
                    df_display_filtered["Solicitante"].dropna().unique().tolist()
                )
                selected_requester = st.selectbox(
                    "Por Solicitante",
                    ["Todos"] + requester_names,
                    key="hist_requester_filter_main",
                )
                if selected_requester != "Todos":
                    df_display_filtered = df_display_filtered[
                        df_display_filtered["Solicitante"] == selected_requester
                    ]

        with filter_cols[1]:
            if "Cubridor" in df_display_filtered.columns:
                cover_names = sorted(
                    df_display_filtered["Cubridor"].dropna().unique().tolist()
                )
                selected_cover = st.selectbox(
                    "Por Cubridor",
                    ["Todos"] + cover_names,
                    key="hist_cover_filter_main",
                )
                if selected_cover != "Todos":
                    df_display_filtered = df_display_filtered[
                        df_display_filtered["Cubridor"] == selected_cover
                    ]

        with filter_cols[2]:
            if "Estado Sup." in df_display_filtered.columns:
                status_options = sorted(
                    df_display_filtered["Estado Sup."].dropna().unique().tolist()
                )
                selected_status = st.selectbox(
                    "Por Estado Sup.",
                    ["Todos"] + status_options,
                    key="hist_status_filter_main",
                )
                if selected_status != "Todos":
                    df_display_filtered = df_display_filtered[
                        df_display_filtered["Estado Sup."] == selected_status
                    ]

        st.dataframe(df_display_filtered, use_container_width=True)

st.markdown("---")
st.caption("ShiftTradeAV - Panel del Supervisor")

# To run this page:
# streamlit run supervisor.py --server.runOnSave true
