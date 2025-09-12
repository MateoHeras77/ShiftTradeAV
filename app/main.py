"""Shift change request form."""

import streamlit as st
from datetime import datetime, timedelta
import re
import sys
from pathlib import Path

# Allow running without installing the package
sys.path.append(str(Path(__file__).resolve().parent))
import utils  # Utility functions for Supabase, tokens, and email
# Import specific functions after importing utils module
from utils.general_utils import format_date  # Import directly from general_utils
from utils.business_validation import validate_shift_request  # Import business validation


# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx"  # Replace with your actual Supabase project ID


# Function to validate email format
def validate_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


st.set_page_config(page_title="Shift Change Request", page_icon="✈️", layout="centered")


st.title("✈️ Shift Change Request Form")

if "employees_data" not in st.session_state:
    with st.spinner("Loading employee list..."):
        st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)

employees = st.session_state.employees_data


# Check if there are employees in the database
if not employees:
    st.warning("⚠️ No employees found in the database.")
    st.info("💡 Contact the administrator to add employees to the system.")
    st.stop()

employee_names = ["Select employee..."] + [emp["full_name"] for emp in employees]

# RAIC color options
raic_options = ["Purple", "Yellow", "Green"]

# Initialize session state for form data
if "requester_data" not in st.session_state:
    st.session_state.requester_data = {}
if "cover_data" not in st.session_state:
    st.session_state.cover_data = {}

# Add refresh button for employee list
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh List"):
        st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
        st.rerun()

# Form sections outside of st.form for better reactivity
st.header("Shift Details")
min_shift_date = datetime.now().date()
date_request_input = st.date_input(
    "Date of shift to change", value=min_shift_date, min_value=min_shift_date
)


# Flight options with schedules
flight_options = [
    "Select flight...",
    "AV255 (5:00-10:00)",
    "AV619 (04:00-09:00)",  # NEW FLIGHT
    "AV627 (13:00-17:30)",
    "AV205 (20:00-00:30+1)",  # Overnight flight - arrives next day
    "AV625 (20:00-02:30+1)",  # Overnight flight - arrives next day
    "AV255-AV627 Full Day (5:00-17:30)",
    "AV619-AV627 Full Day (4:00-17:30)",
    "AV627-AV205 Full Day (13:00-00:30+1)",  # Overnight flight - arrives next day
]

selected_flight = st.selectbox("Flight Number", flight_options)

# Extract just the flight number for storage
if selected_flight != "Select flight...":
    flight_number = selected_flight.split(" ")[0]  # Extract AV255, AV627, or AV205
else:
    flight_number = ""


st.header("Employee Requesting the Change")

# Dropdown for requester
selected_requester = st.selectbox(
    "Select requester", employee_names, key="requester_select"
)

# Auto-fill fields for requester
if selected_requester != "Seleccionar empleado...":
    requester_employee = next(
        (emp for emp in employees if emp["full_name"] == selected_requester), None
    )
    if requester_employee:
        st.session_state.requester_data = requester_employee
        requester_name = st.text_input(
            "Requester name",
            value=requester_employee["full_name"],
            disabled=True,
        )
        requester_employee_number = st.selectbox(
            "RAIC color (Requester)",
            raic_options,
            index=(
                raic_options.index(requester_employee["raic_color"])
                if requester_employee["raic_color"] in raic_options
                else 0
            ),
            disabled=True,
        )
        requester_email = st.text_input(
            "Requester email", value=requester_employee["email"], disabled=True
        )
    else:
        requester_name = st.text_input("Requester name")
        requester_employee_number = st.selectbox(
            "RAIC color (Requester)", ["Select color..."] + raic_options
        )
        requester_email = st.text_input(
            "Requester email", placeholder="example@company.com"
        )
else:
    requester_name = st.text_input("Requester name")
    requester_employee_number = st.selectbox(
        "RAIC color (Requester)", ["Select color..."] + raic_options
    )
    requester_email = st.text_input(
        "Requester email", placeholder="example@company.com"
    )

# Option to add manual data if not in dropdown
if selected_requester == "Select employee...":
    st.caption(
        "💡 Employee not in the list? Fill in the fields manually or contact the administrator to add them to the system."
    )


st.header("Employee Covering the Shift")

# Dropdown for cover employee
selected_cover = st.selectbox(
    "Select coworker covering", employee_names, key="cover_select"
)

# Prevent selecting the same person for both roles
if (
    selected_requester != "Select employee..."
    and selected_cover == selected_requester
):
    st.error(
        "❌ The requester and the coworker covering cannot be the same person."
    )

# Auto-fill fields for cover employee
if selected_cover != "Seleccionar empleado...":
    cover_employee = next(
        (emp for emp in employees if emp["full_name"] == selected_cover), None
    )
    if cover_employee:
        st.session_state.cover_data = cover_employee
        cover_name = st.text_input(
            "Name of coworker covering",
            value=cover_employee["full_name"],
            disabled=True,
        )
        cover_employee_number = st.selectbox(
            "RAIC color (Cover)",
            raic_options,
            index=(
                raic_options.index(cover_employee["raic_color"])
                if cover_employee["raic_color"] in raic_options
                else 0
            ),
            disabled=True,
        )
        cover_email = st.text_input(
            "Email of coworker covering",
            value=cover_employee["email"],
            disabled=True,
        )
    else:
        cover_name = st.text_input("Name of coworker covering")
        cover_employee_number = st.selectbox(
            "RAIC color (Cover)",
            ["Select color..."] + raic_options,
            key="manual_cover_color",
        )
        cover_email = st.text_input(
            "Email of coworker covering", placeholder="coworker@company.com"
        )
else:
    cover_name = st.text_input("Name of coworker covering")
    cover_employee_number = st.selectbox(
        "RAIC color (Cover)",
        ["Select color..."] + raic_options,
        key="manual_cover_color_noemp",
    )
    cover_email = st.text_input(
        "Email of coworker covering", placeholder="coworker@company.com"
    )

# Option to add manual data if not in dropdown
if selected_cover == "Select employee...":
    st.caption(
        "💡 Employee not in the list? Fill in the fields manually or contact the administrator to add them to the system."
    )

st.caption(
    "⚠️ Carefully check the email - it is the only way to contact the coworker."
)


st.header("Required Confirmations")

# Mandatory confirmations checkbox
confirmations_checked = st.checkbox(
    """**I confirm that:**
    
1. Both I and my coworker have at least two days off within the week we are requesting.

2. I accept the terms and conditions of the shift change system.""",
    value=False,
    key="mandatory_confirmations"
)

if not confirmations_checked:
    st.warning("⚠️ You must confirm both points before submitting the request.")


# Submit button outside of form
submit_button = st.button("Submit Request", type="primary")


if submit_button:
    # Validation checks
    if not confirmations_checked:
        st.error("❌ You must confirm the terms before submitting the request.")
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
        st.error("Please complete all fields.")
    elif (
        selected_requester != "Select employee..."
        and selected_cover == selected_requester
    ):
        st.error(
            "❌ The requester and the coworker covering cannot be the same person."
        )
    elif not validate_email(requester_email):
        st.error(
            "❌ The requester's email is not valid. Please check that it includes @ and a valid domain."
        )
    elif not validate_email(cover_email):
        st.error(
            "❌ The covering coworker's email is not valid. Please check that it includes @ and a valid domain."
        )
    elif cover_employee_number == "Green" and requester_employee_number != "Green":
        st.error("A Green RAIC can only cover another Green.")
    else:
        with st.spinner("Processing request..."):
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
            st.caption("Saving request to the database...")
            shift_request_id = utils.save_shift_request(request_details, PROJECT_ID)
            progress_bar.progress(33)

            if shift_request_id:
                st.caption("Generating acceptance token...")
                # 2. Generate a UUID token
                token = utils.generate_token(shift_request_id, PROJECT_ID)
                progress_bar.progress(66)

                if token:
                    # 3. Create a unique link with the token for Streamlit Cloud
                    accept_url = (
                        f"https://shifttrade.streamlit.app/Request?token={token}"
                    )

                    # 4. Send the link by email to the covering employee
                    st.caption("Sending email...")
                    email_subject = "Shift Coverage Request"

                    # Get current date for the request
                    request_date = datetime.now().strftime("%d/%m/%Y")

                    # Get flight schedule information for email
                    flight_schedule = utils.get_flight_schedule_info(flight_number)

                    email_body = f"""Hello {cover_name},

{requester_name} has requested that you cover their shift for flight {flight_number} on {format_date(date_request_input)}.

**Request details:**
• Request date: {request_date}
• Flight: {flight_number}
• Schedule: {flight_schedule['display_schedule']}
• Shift date: {format_date(date_request_input)}
• Requester: {requester_name}

To accept, please click the following link (valid for 24 hours):
{accept_url}

Thank you."""
                    email_sent = utils.send_email(
                        cover_email, email_subject, email_body
                    )
                    progress_bar.progress(100)

                    if email_sent:
                        st.success(f"✅ Request sent with ID: {shift_request_id}")
                        st.info(
                            f"📧 An email has been sent to **{cover_email}** with the link to accept the change."
                        )
                        st.info(
                            "💡 **Important note:** If the coworker does not receive the email, check that:"
                        )
                        st.write("• The email is written correctly")
                        st.write("• They check their spam/junk folder")
                        st.write("• The email domain is valid")
                    else:
                        st.success(f"✅ Request saved with ID: {shift_request_id}")
                        st.error("❌ **Error sending acceptance email**")
                        st.warning("⚠️ **Possible causes of the error:**")
                        st.write(
                            "• The entered email may have a typo"
                        )
                        st.write("• The email domain does not exist")
                        st.write("• Temporary issues with the mail server")
                        st.info("🔧 **Solutions:**")
                        st.write("• Check that the email is written correctly")
                        st.write("• Contact the coworker directly with the link:")
                        st.code(accept_url)
                        st.write(
                            "• Or contact the administrator to resend the email"
                        )
                else:
                    st.error(
                        "Error generating acceptance token. The request was saved, but the email could not be sent."
                    )
            else:
                st.error("Error saving the request to the database.")

st.markdown("---")
st.caption("ShiftTradeAV - Shift Change Management")
