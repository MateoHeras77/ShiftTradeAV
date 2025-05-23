import streamlit as st
import pandas as pd # Import pandas for DataFrame
from datetime import datetime
import utils # Your utility functions

# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx" # Replace with your actual Supabase project ID

st.set_page_config(page_title="Panel del Supervisor", layout="wide")

st.title("👑 Panel de Aprobación del Supervisor")

# Initialize session state for view mode if it doesn't exist
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'pending_requests' # Default view

st.sidebar.header("Acciones")
if st.sidebar.button("Refrescar Datos"):
    # El método spinner no está disponible para st.sidebar
    refresh_status = st.sidebar.empty()
    refresh_status.info("Refrescando datos...")
    # Clear relevant session state to force data refresh if needed
    if 'all_requests_for_history' in st.session_state:
        del st.session_state.all_requests_for_history
    if 'pending_requests_data' in st.session_state:
        del st.session_state.pending_requests_data
    st.rerun()

st.sidebar.markdown("---")

# Sidebar buttons to switch views
if st.sidebar.button("Ver Solicitudes Pendientes", key="view_pending"):
    st.session_state.view_mode = 'pending_requests'
    st.rerun()

if st.sidebar.button("Ver Historial de Solicitudes", key="view_history"):
    st.session_state.view_mode = 'history_view'
    st.rerun()

st.sidebar.markdown("---")

# Main panel content based on view_mode
if st.session_state.view_mode == 'pending_requests':
    st.header("Solicitudes Pendientes de Aprobación")
    # 1. Display a list of all requests with `supervisor_status = 'pending'`
    if 'pending_requests_data' not in st.session_state:
        with st.spinner("Cargando solicitudes pendientes..."):
            st.session_state.pending_requests_data = utils.get_pending_requests(PROJECT_ID)
    
    pending_requests = st.session_state.pending_requests_data

    if not pending_requests:
        st.info("No hay solicitudes de cambio de turno pendientes de aprobación.")
        # Add a button to switch to history view if no pending requests
        if st.button("Ver Historial de Solicitudes", key="pending_to_history_button"):
            st.session_state.view_mode = 'history_view'
            st.rerun()
    else:
        st.subheader(f"Total Pendientes: {len(pending_requests)}")
        for req in pending_requests:
            req_id = req.get('id')
            with st.expander(f"Solicitud ID: {req_id} - Vuelo: {req.get('flight_number', 'N/A')} - Solicitante: {req.get('requester_name', 'N/A')}"):
                st.markdown(f"""
                - **Fecha Solicitud:** {req.get('date_request')}
                - **Número de Vuelo:** {req.get('flight_number')}
                - **Solicitante:** {req.get('requester_name')} ({req.get('requester_employee_number')}, {req.get('requester_email')})
                - **Cubridor:** {req.get('cover_name')} ({req.get('cover_employee_number')}, {req.get('cover_email')})
                - **Fecha Aceptación por Cubridor:** {req.get('date_accepted_by_cover', 'N/A')}
                """)

                supervisor_name_input = st.text_input("Nombre del Supervisor", key=f"supervisor_name_{req_id}")
                supervisor_password_input = st.text_input("Contraseña del Supervisor", type="password", key=f"supervisor_password_{req_id}")
                supervisor_comments = st.text_area("Comentarios (opcional para aprobación, obligatorio para rechazo)", key=f"comments_{req_id}")

                col1, col2, col_spacer = st.columns([1,1,5])
                with col1:
                    if st.button("✅ Aprobar", key=f"approve_{req_id}", type="primary"):
                        if not supervisor_name_input:
                            st.warning("Por favor, ingresa tu nombre de supervisor.")
                        elif supervisor_password_input != "Avianca2025*":
                            st.error("Contraseña del supervisor incorrecta.")
                        else:
                            approval_container = st.container()
                            with approval_container:
                                with st.spinner(f"Aprobando solicitud {req_id}..."):
                                    progress_bar = st.progress(0)
                                    st.caption("Actualizando estado en la base de datos...")
                                    updates = {
                                        "supervisor_status": "approved",
                                        "supervisor_decision_date": datetime.utcnow().isoformat(),
                                        "supervisor_comments": supervisor_comments,
                                        "supervisor_name": supervisor_name_input
                                    }
                                    update_success = utils.update_shift_request_status(req_id, updates, PROJECT_ID)
                                    progress_bar.progress(50)
                                    
                                    if update_success:
                                        st.caption("Enviando notificaciones por correo...")
                                        # 3. Notify both employees
                                        email1 = utils.send_email(req.get('requester_email'), 
                                                 "Cambio de Turno APROBADO", 
                                                 f"Tu solicitud de cambio para el vuelo {req.get('flight_number')} ha sido APROBADA por el supervisor {supervisor_name_input}. Comentarios: {supervisor_comments}")
                                        email2 = utils.send_email(req.get('cover_email'), 
                                                 "Cambio de Turno APROBADO", 
                                                 f"El cambio de turno que aceptaste cubrir para el vuelo {req.get('flight_number')} ha sido APROBADO por el supervisor {supervisor_name_input}. Comentarios: {supervisor_comments}")
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
                                    updates = {
                                        "supervisor_status": "rejected",
                                        "supervisor_decision_date": datetime.utcnow().isoformat(),
                                        "supervisor_comments": supervisor_comments,
                                        "supervisor_name": supervisor_name_input
                                    }
                                    update_success = utils.update_shift_request_status(req_id, updates, PROJECT_ID)
                                    progress_bar.progress(50)
                                    
                                    if update_success:
                                        st.caption("Enviando notificaciones por correo...")
                                        # 3. Notify both employees
                                        email1 = utils.send_email(req.get('requester_email'), 
                                                 "Cambio de Turno RECHAZADO", 
                                                 f"Tu solicitud de cambio para el vuelo {req.get('flight_number')} ha sido RECHAZADA por el supervisor {supervisor_name_input}. Motivo: {supervisor_comments}")
                                        email2 = utils.send_email(req.get('cover_email'), 
                                                 "Cambio de Turno RECHAZADO", 
                                                 f"El cambio de turno que aceptaste cubrir para el vuelo {req.get('flight_number')} ha sido RECHAZADO por el supervisor {supervisor_name_input}. Motivo: {supervisor_comments}")
                                        progress_bar.progress(100)
                                        
                                        st.success(f"Solicitud {req_id} rechazada por {supervisor_name_input}.")
                                        if not (email1 and email2):
                                            st.warning("El rechazo fue guardado, pero hubo problemas al enviar algunas notificaciones por correo.")
                                        
                                        # Clear pending requests cache and rerun
                                        if 'pending_requests_data' in st.session_state:
                                            del st.session_state.pending_requests_data
                                        st.rerun()
                st.markdown("---")

elif st.session_state.view_mode == 'history_view':
    st.header("Historial de Todas las Solicitudes")

    # Fetch all requests (not just pending) for history, cache in session state
    if 'all_requests_for_history' not in st.session_state:
        with st.spinner("Cargando historial de solicitudes..."):
            st.session_state.all_requests_for_history = utils.get_all_shift_requests(PROJECT_ID)
    
    all_requests_for_history = st.session_state.all_requests_for_history

    if not all_requests_for_history:
        st.info("No hay historial de solicitudes disponible.")
        # Add a button to switch to pending view if no history
        if st.button("Ver Solicitudes Pendientes", key="history_to_pending_button"):
            st.session_state.view_mode = 'pending_requests'
            st.rerun()
    else:
        df_history = pd.DataFrame(all_requests_for_history)
        
        columns_to_display = [
            'id', 'date_request', 'flight_number', 'requester_name', 
            'cover_name', 'supervisor_status', 'supervisor_name', 
            'supervisor_decision_date', 'supervisor_comments'
        ]
        existing_columns_in_df = [col for col in columns_to_display if col in df_history.columns]
        
        df_display_full = df_history[existing_columns_in_df].copy()

        # Convert relevant date columns to datetime objects if they are not already
        if 'date_request' in df_display_full.columns: # Assuming this is the original shift date
            df_display_full['date_request'] = pd.to_datetime(df_display_full['date_request'], errors='coerce').dt.strftime('%Y-%m-%d')
        if 'supervisor_decision_date' in df_display_full.columns:
            df_display_full['supervisor_decision_date'] = pd.to_datetime(df_display_full['supervisor_decision_date'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')

        rename_map = {
            'id': 'ID',
            'date_request': 'Fecha Vuelo Orig.',
            'flight_number': 'Vuelo',
            'requester_name': 'Solicitante',
            'cover_name': 'Cubridor',
            'supervisor_status': 'Estado Sup.',
            'supervisor_name': 'Supervisor',
            'supervisor_decision_date': 'Fecha Decisión Sup.',
            'supervisor_comments': 'Comentarios Sup.'
        }
        df_display_filtered = df_display_full.rename(columns={k: v for k, v in rename_map.items() if k in df_display_full.columns})
        
        # Ensure the order of columns after renaming
        ordered_renamed_columns = [rename_map[col] for col in existing_columns_in_df if col in rename_map and rename_map[col] in df_display_filtered.columns]
        df_display_filtered = df_display_filtered[ordered_renamed_columns]


        st.markdown("### Filtrar Historial")
        filter_cols = st.columns(3)
        
        with filter_cols[0]:
            if 'Solicitante' in df_display_filtered.columns:
                requester_names = sorted(df_display_filtered['Solicitante'].dropna().unique().tolist())
                selected_requester = st.selectbox("Por Solicitante", ["Todos"] + requester_names, key="hist_requester_filter_main")
                if selected_requester != "Todos":
                    df_display_filtered = df_display_filtered[df_display_filtered['Solicitante'] == selected_requester]
        
        with filter_cols[1]:
            if 'Cubridor' in df_display_filtered.columns:
                cover_names = sorted(df_display_filtered['Cubridor'].dropna().unique().tolist())
                selected_cover = st.selectbox("Por Cubridor", ["Todos"] + cover_names, key="hist_cover_filter_main")
                if selected_cover != "Todos":
                    df_display_filtered = df_display_filtered[df_display_filtered['Cubridor'] == selected_cover]

        with filter_cols[2]:
            if 'Estado Sup.' in df_display_filtered.columns:
                status_options = sorted(df_display_filtered['Estado Sup.'].dropna().unique().tolist())
                selected_status = st.selectbox("Por Estado Sup.", ["Todos"] + status_options, key="hist_status_filter_main")
                if selected_status != "Todos":
                    df_display_filtered = df_display_filtered[df_display_filtered['Estado Sup.'] == selected_status]
        
        st.dataframe(df_display_filtered, use_container_width=True)

st.markdown("---")
st.caption("ShiftTradeAV - Panel del Supervisor")

# To run this page:
# streamlit run supervisor.py --server.runOnSave true
