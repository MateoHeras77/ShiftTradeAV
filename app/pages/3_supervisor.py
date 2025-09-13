import streamlit as st
import pandas as pd  # Import pandas for DataFrame
from datetime import datetime
import sys
from pathlib import Path

# Allow running this page directly via Streamlit
project_root = Path(__file__).resolve().parents[2]
app_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(app_dir))
import app_utils as utils  # Utility functions
from utils.general_utils import format_date  # Direct import for format_date function



def render_pending_request(req):
    """Render a single pending request with approve/reject actions."""
    req_id = req.get("id")
    formatted_date = format_date(req.get("date_request", "N/A"))
    expander_title = f"Date: {formatted_date} - Flight: {req.get('flight_number', 'N/A')} - Requester: {req.get('employee_name', 'N/A')}"

    with st.expander(expander_title):
        with st.form(key=f"form_{req_id}"):
            st.markdown(
                f"""
                - **Request Date:** {format_date(req.get('date_request', 'N/A'))}
                - **Flight Number:** {req.get('flight_number')}
                - **Requester:** {req.get('employee_name')} ({req.get('raic_color')}, {req.get('employee_email')})
                - **Covering Employee:** {req.get('cover_name')} ({req.get('cover_email')})
                """
            )

            has_cover_accepted = (
                req.get("date_accepted_by_cover") is not None
                and req.get("date_accepted_by_cover") != "N/A"
            )
            if has_cover_accepted:
                st.success(
                    f"✅ **ACCEPTED BY COVERING EMPLOYEE:** {format_date(req.get('date_accepted_by_cover'))}"
                )
            else:
                st.error("❌ **PENDING ACCEPTANCE BY COVERING EMPLOYEE**")
                st.warning(
                    "⚠️ The covering employee has not accepted this request yet. Do not approve until they confirm."
                )

            supervisor_name_input_val = st.text_input(
                "Supervisor Name", key=f"supervisor_name_form_{req_id}"
            )
            supervisor_password_input_val = st.text_input(
                "Supervisor Password",
                type="password",
                key=f"supervisor_password_form_{req_id}",
            )
            supervisor_comments_val = st.text_area(
                "Comments (optional for approval, required for rejection)",
                key=f"comments_form_{req_id}",
            )

            col1, col2, _ = st.columns([1, 1, 5])
            with col1:
                approve_submitted = st.form_submit_button(
                    "✅ Approve", type="primary", disabled=not has_cover_accepted
                )
            with col2:
                reject_submitted = st.form_submit_button("❌ Reject")

        if approve_submitted:
            if not supervisor_name_input_val:
                st.warning("Please enter your supervisor name.")
            elif supervisor_password_input_val != CORRECT_PASSWORD:
                st.error("Incorrect supervisor password.")
            elif not has_cover_accepted:
                st.error(
                    "Cannot approve this request because the covering employee has not accepted it yet."
                )
            else:
                with st.spinner(f"Approving request {req_id}..."):
                    progress_bar = st.progress(0)
                    st.caption("Updating status in the database...")
                    now_utc = datetime.utcnow()
                    updates = {
                        "supervisor_status": "approved",
                        "supervisor_decision_date": now_utc.isoformat(),
                        "supervisor_comments": supervisor_comments_val,
                        "supervisor_name": supervisor_name_input_val,
                    }
                    update_success = utils.update_shift_request_status(
                        req_id, updates, PROJECT_ID
                    )
                    progress_bar.progress(50)

                    if update_success:
                        st.caption("Sending email notifications...")
                        fecha_aprobacion = datetime.now().strftime("%d/%m/%Y")
                        fecha_vuelo = format_date(req.get("date_request"))
                        fecha_aceptacion = (
                            format_date(req.get("date_accepted_by_cover"))
                            if req.get("date_accepted_by_cover")
                            else "N/A"
                        )

                        requester_subject = "✅ Shift Change APPROVED"
                        requester_body = f"""Hello {req.get('employee_name')},

Great news! Your shift change request has been APPROVED.

**Approved change details:**
• Flight: {req.get('flight_number')}
• Shift date: {fecha_vuelo}
• Covering colleague: {req.get('cover_name')}
• Approved by supervisor: {supervisor_name_input_val}
• Approval date: {fecha_aprobacion}

**Timeline:**
1. Request submitted ✅
2. Accepted by {req.get('cover_name')} on {fecha_aceptacion} ✅
3. Approved by supervisor on {fecha_aprobacion} ✅

**Supervisor comments:** {supervisor_comments_val if supervisor_comments_val else 'No additional comments'}

The shift change is officially authorized.

Best regards,
ShiftTradeAV"""
                        cover_subject = "✅ Shift Change APPROVED"
                        cover_body = f"""Hello {req.get('cover_name')},

The shift change you agreed to cover has been APPROVED by the supervisor.

**Approved change details:**
• Flight: {req.get('flight_number')}
• Shift date: {fecha_vuelo}
• Original requester: {req.get('employee_name')}
• Approved by supervisor: {supervisor_name_input_val}
• Approval date: {fecha_aprobacion}

**Timeline:**
1. Request submitted ✅
2. You accepted on {fecha_aceptacion} ✅
3. Approved by supervisor on {fecha_aprobacion} ✅

**Supervisor comments:** {supervisor_comments_val if supervisor_comments_val else 'No additional comments'}

Thank you for your cooperation. The change is officially authorized.

Best regards,
ShiftTradeAV"""
                        email1 = utils.send_email_with_calendar(
                            req.get("employee_email"),
                            requester_subject,
                            requester_body,
                            req,
                            is_for_requester=True,
                        )
                        email2 = utils.send_email_with_calendar(
                            req.get("cover_email"),
                            cover_subject,
                            cover_body,
                            req,
                            is_for_requester=False,
                        )
                        progress_bar.progress(100)

                        st.success(
                            f"Request {req_id} approved by {supervisor_name_input_val}."
                        )
                        if not (email1 and email2):
                            st.warning(
                                "Approval was saved, but there were problems sending some email notifications."
                            )

                        if "pending_requests_data" in st.session_state:
                            del st.session_state.pending_requests_data
                        st.rerun()
                    else:
                        st.error(f"Error approving request {req_id}.")

        elif reject_submitted:
            if not supervisor_name_input_val:
                st.warning("Please enter your supervisor name.")
            elif supervisor_password_input_val != CORRECT_PASSWORD:
                st.error("Incorrect supervisor password.")
            elif not supervisor_comments_val:
                st.warning(
                    "Please add a comment explaining the reason for rejection."
                )
            else:
                with st.spinner(f"Rejecting request {req_id}..."):
                    progress_bar = st.progress(0)
                    st.caption("Updating status in the database...")
                    now_utc = datetime.utcnow()
                    updates = {
                        "supervisor_status": "rejected",
                        "supervisor_decision_date": now_utc.isoformat(),
                        "supervisor_comments": supervisor_comments_val,
                        "supervisor_name": supervisor_name_input_val,
                    }
                    update_success = utils.update_shift_request_status(
                        req_id, updates, PROJECT_ID
                    )
                    progress_bar.progress(50)

                    if update_success:
                        st.caption("Sending email notifications...")
                        fecha_rechazo = datetime.now().strftime("%d/%m/%Y")
                        fecha_vuelo = format_date(req.get("date_request"))
                        fecha_aceptacion = (
                            format_date(req.get("date_accepted_by_cover"))
                            if req.get("date_accepted_by_cover")
                            else "N/A"
                        )

                        requester_subject = "❌ Shift Change REJECTED"
                        requester_body = f"""Hello {req.get('employee_name')},

We regret to inform you that your shift change request has been REJECTED.

**Rejected request details:**
• Flight: {req.get('flight_number')}
• Shift date: {fecha_vuelo}
• Colleague who had accepted: {req.get('cover_name')}
• Supervisor who rejected: {supervisor_name_input_val}
• Rejection date: {fecha_rechazo}

**Timeline:**
1. Request submitted ✅
2. Accepted by {req.get('cover_name')} on {fecha_aceptacion} ✅
3. Rejected by supervisor on {fecha_rechazo} ❌

**Reason for rejection:** {supervisor_comments_val}

You can submit a new request if circumstances change.

Best regards,
ShiftTradeAV"""
                        cover_subject = "❌ Shift Change REJECTED"
                        cover_body = f"""Hello {req.get('cover_name')},

We inform you that the shift change you had agreed to cover has been REJECTED by the supervisor.

**Rejected request details:**
• Flight: {req.get('flight_number')}
• Shift date: {fecha_vuelo}
• Original requester: {req.get('employee_name')}
• Supervisor who rejected: {supervisor_name_input_val}
• Rejection date: {fecha_rechazo}

**Timeline:**
1. Request submitted ✅
2. You accepted on {fecha_aceptacion} ✅
3. Rejected by supervisor on {fecha_rechazo} ❌

**Reason for rejection:** {supervisor_comments_val}

You no longer need to cover this shift. Thank you for your willingness.

Best regards,
ShiftTradeAV"""
                        email1 = utils.send_email(
                            req.get("employee_email"),
                            requester_subject,
                            requester_body,
                        )
                        email2 = utils.send_email(
                            req.get("cover_email"), cover_subject, cover_body
                        )
                        progress_bar.progress(100)

                        st.success(
                            f"Request {req_id} rejected by {supervisor_name_input_val}."
                        )
                        if not (email1 and email2):
                            st.warning(
                                "Rejection was saved, but there were problems sending some email notifications."
                            )

                        if "pending_requests_data" in st.session_state:
                            del st.session_state.pending_requests_data
                        st.rerun()
                    else:
                        st.error(f"Error rejecting request {req_id}.")

    st.markdown("---")


# Project ID for Supabase calls
PROJECT_ID = "eynioxgzavfftukadjqm"  # Replace with your actual Supabase project ID
CORRECT_PASSWORD = "supervisor2025"

st.set_page_config(page_title="Supervisor Panel", page_icon="👑", layout="wide")

# Password protection
if "supervisor_password_correct" not in st.session_state:
    st.session_state.supervisor_password_correct = False

if not st.session_state.supervisor_password_correct:
    st.title("👑 Supervisor Panel Access")
    password_attempt = st.text_input(
        "Enter the password to access:",
        type="password",
        key="supervisor_page_password",
    )
    if password_attempt:
        if password_attempt == CORRECT_PASSWORD:
            st.session_state.supervisor_password_correct = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()  # Do not render the rest of the page if password is not correct

# --- Main Page Content Starts Here ---
st.title("👑 Supervisor Approval Panel")

# Initialize session state for view mode if it doesn't exist
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "pending_requests"  # Default view

st.sidebar.header("Actions")
if st.sidebar.button("Refresh Data"):
    refresh_status = st.sidebar.empty()
    refresh_status.info("Refreshing data...")
    if "all_requests_for_history" in st.session_state:
        del st.session_state.all_requests_for_history
    if "pending_requests_data" in st.session_state:
        del st.session_state.pending_requests_data
    st.rerun()

st.sidebar.markdown("---")

# Sidebar buttons to switch views
if st.sidebar.button("View Pending Requests", key="view_pending"):
    st.session_state.view_mode = "pending_requests"
    st.rerun()

if st.sidebar.button("View Request History", key="view_history"):
    st.session_state.view_mode = "history_view"
    st.rerun()

st.sidebar.markdown("---")

# Main panel content based on view_mode
if st.session_state.view_mode == "pending_requests":
    st.header("Pending Approval Requests")
    # 1. Display a list of all requests with `supervisor_status = 'pending'`
    if "pending_requests_data" not in st.session_state:
        with st.spinner("Loading pending requests..."):
            st.session_state.pending_requests_data = utils.get_pending_requests(
                PROJECT_ID
            )

    pending_requests = st.session_state.pending_requests_data

    if not pending_requests:
        st.info("There are no shift change requests pending approval.")
        # Add a button to switch to history view if no pending requests
        if st.button("View Request History", key="pending_to_history_button"):
            st.session_state.view_mode = "history_view"
            st.rerun()
    else:
        st.subheader(f"Total Pending: {len(pending_requests)}")

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
            st.warning(f"Could not sort requests by date: {e}")

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
            st.subheader("✅ Requests with confirmed cover")
            for req in accepted_by_cover:
                render_pending_request(req)

        if awaiting_cover:
            st.subheader("⏳ Requests awaiting acceptance by covering employee")
            for req in awaiting_cover:
                render_pending_request(req)

        st.markdown("---")

elif st.session_state.view_mode == "history_view":
    st.header("History of All Requests")

    # Fetch all requests (not just pending) for history, cache in session state
    if "all_requests_for_history" not in st.session_state:
        with st.spinner("Loading request history..."):
            st.session_state.all_requests_for_history = utils.get_all_shift_requests(
                PROJECT_ID
            )

    all_requests_for_history = st.session_state.all_requests_for_history

    if not all_requests_for_history:
        st.info("No request history available.")
        # Add a button to switch to pending view if no history
        if st.button("View Pending Requests", key="history_to_pending_button"):
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
            st.warning(f"Could not sort history by date: {e}")

        columns_to_display = [
            "id",
            "date_request",
            "flight_number",
            "employee_name",
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
                format_date
            )
        if "supervisor_decision_date" in df_display_full.columns:
            df_display_full["supervisor_decision_date"] = df_display_full[
                "supervisor_decision_date"
            ].apply(format_date)

        rename_map = {
            "id": "ID",
            "date_request": "Original Shift Date",
            "flight_number": "Flight",
            "employee_name": "Requester",
            "cover_name": "Covering Employee",
            "supervisor_status": "Supervisor Status",
            "supervisor_name": "Supervisor",
            "supervisor_decision_date": "Supervisor Decision Date",
            "supervisor_comments": "Supervisor Comments",
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

        st.markdown("### Filter History")
        filter_cols = st.columns(3)

        with filter_cols[0]:
            if "Requester" in df_display_filtered.columns:
                requester_names = sorted(
                    df_display_filtered["Requester"].dropna().unique().tolist()
                )
                selected_requester = st.selectbox(
                    "By Requester",
                    ["All"] + requester_names,
                    key="hist_requester_filter_main",
                )
                if selected_requester != "All":
                    df_display_filtered = df_display_filtered[
                        df_display_filtered["Requester"] == selected_requester
                    ]

        with filter_cols[1]:
            if "Covering Employee" in df_display_filtered.columns:
                cover_names = sorted(
                    df_display_filtered["Covering Employee"].dropna().unique().tolist()
                )
                selected_cover = st.selectbox(
                    "By Covering Employee",
                    ["All"] + cover_names,
                    key="hist_cover_filter_main",
                )
                if selected_cover != "All":
                    df_display_filtered = df_display_filtered[
                        df_display_filtered["Covering Employee"] == selected_cover
                    ]

        with filter_cols[2]:
            if "Supervisor Status" in df_display_filtered.columns:
                status_options = sorted(
                    df_display_filtered["Supervisor Status"].dropna().unique().tolist()
                )
                selected_status = st.selectbox(
                    "By Supervisor Status",
                    ["All"] + status_options,
                    key="hist_status_filter_main",
                )
                if selected_status != "All":
                    df_display_filtered = df_display_filtered[
                        df_display_filtered["Supervisor Status"] == selected_status
                    ]

        st.dataframe(df_display_filtered, use_container_width=True)

st.markdown("---")
st.caption("ShiftTradeAV - Supervisor Panel")

# To run this page:
# streamlit run supervisor.py --server.runOnSave true
