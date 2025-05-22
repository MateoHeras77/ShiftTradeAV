import streamlit as st
from datetime import datetime
import utils # Your utility functions

# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx" # Replace with your actual Supabase project ID

st.set_page_config(page_title="Panel del Supervisor", layout="wide")

st.title("👑 Panel de Aprobación del Supervisor")

st.sidebar.header("Acciones")
if st.sidebar.button("Refrescar Solicitudes"):
    st.rerun()

# 1. Display a list of all requests with `supervisor_status = 'pending'`
pending_requests = utils.get_pending_requests(PROJECT_ID)

if not pending_requests:
    st.info("No hay solicitudes de cambio de turno pendientes de aprobación.")
    st.stop()

st.subheader(f"Solicitudes Pendientes ({len(pending_requests)})")

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

        supervisor_comments = st.text_area("Comentarios (opcional)", key=f"comments_{req_id}")

        # 2. Buttons for Approve/Reject
        col1, col2, col_spacer = st.columns([1,1,5])
        with col1:
            if st.button("✅ Aprobar", key=f"approve_{req_id}", type="primary"):
                updates = {
                    "supervisor_status": "approved",
                    "supervisor_decision_date": datetime.utcnow().isoformat(),
                    "supervisor_comments": supervisor_comments
                }
                if utils.update_shift_request_status(req_id, updates, PROJECT_ID):
                    st.success(f"Solicitud {req_id} aprobada.")
                    # 3. Notify both employees
                    utils.send_email(req.get('requester_email'), "Cambio de Turno APROBADO", f"Tu solicitud de cambio para el vuelo {req.get('flight_number')} ha sido APROBADA por el supervisor. Comentarios: {supervisor_comments}")
                    utils.send_email(req.get('cover_email'), "Cambio de Turno APROBADO", f"El cambio de turno que aceptaste cubrir para el vuelo {req.get('flight_number')} ha sido APROBADO por el supervisor. Comentarios: {supervisor_comments}")
                    st.rerun() # Refresh the list
                else:
                    st.error(f"Error al aprobar la solicitud {req_id}.")

        with col2:
            if st.button("❌ Rechazar", key=f"reject_{req_id}"):
                if not supervisor_comments: # Require comments for rejection
                    st.warning("Por favor, añade un comentario explicando el motivo del rechazo.")
                else:
                    updates = {
                        "supervisor_status": "rejected",
                        "supervisor_decision_date": datetime.utcnow().isoformat(),
                        "supervisor_comments": supervisor_comments
                    }
                    if utils.update_shift_request_status(req_id, updates, PROJECT_ID):
                        st.success(f"Solicitud {req_id} rechazada.")
                        # 3. Notify both employees
                        utils.send_email(req.get('requester_email'), "Cambio de Turno RECHAZADO", f"Tu solicitud de cambio para el vuelo {req.get('flight_number')} ha sido RECHAZADA por el supervisor. Motivo: {supervisor_comments}")
                        utils.send_email(req.get('cover_email'), "Cambio de Turno RECHAZADO", f"El cambio de turno que aceptaste cubrir para el vuelo {req.get('flight_number')} ha sido RECHAZADO por el supervisor. Motivo: {supervisor_comments}")
                        st.rerun() # Refresh the list
                    else:
                        st.error(f"Error al rechazar la solicitud {req_id}.")
        st.markdown("---")


st.markdown("---")
st.caption("ShiftTradeAV - Panel del Supervisor")

# To run this page:
# streamlit run supervisor.py --server.runOnSave true
