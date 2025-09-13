import streamlit as st
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


# Project ID for Supabase calls
PROJECT_ID = "eynioxgzavfftukadjqm" # Replace with your actual Supabase project ID

st.set_page_config(
    page_title="Accept Shift Change",
    page_icon="✔️",
    layout="centered"
)

st.title("✔️ Accept Shift Change")

query_params = st.query_params
token = query_params.get("token")

if not token:
    st.error("Token not provided. Please use the link sent to your email.")
    st.stop()

with st.spinner("Validating token..."):
    # 1. Validate the token
    shift_request_id = utils.verify_token(str(token), PROJECT_ID) # Ensure token is string

if not shift_request_id:
    st.error("The token is invalid, expired, or has already been used.")
    st.image("https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbjV0ZzNocG9jM3hpYjB4Yms4YmY5N3V2eHdyM2N5Y2NnbnZtY2NqZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/jB57hZPa2mX5B9B22N/giphy.gif", caption="Invalid Token")
    st.stop()

st.info(f"Valid token. You are about to accept to cover a shift.")
st.write(f"Shift change request ID: {shift_request_id}") # For debugging or info

# Fetch shift request details to show some info (optional but good UX)
with st.spinner("Loading shift details..."):
    request_details = utils.get_shift_request_details(shift_request_id, PROJECT_ID)
if request_details:
    st.markdown(f"""
    **Shift to Cover Details:**
    - **Date of Shift to Change:** {format_date(request_details.get('date_request', 'N/A'))}
    - **Flight:** {request_details.get('flight_number', 'N/A')}
    
    **Requester Information:**
    - **Name:** {request_details.get('requester_name', 'N/A')}
    - **RAIC Color (Requester):** {request_details.get('requester_employee_number', 'N/A')}
    - **Email:** {request_details.get('requester_email', 'N/A')}

    **Your Information (Cover):**
    - **Name:** {request_details.get('cover_name', 'N/A')}
    - **RAIC Color (Cover):** {request_details.get('cover_employee_number', 'N/A')}
    - **Email:** {request_details.get('cover_email', 'N/A')}
    """)
else:
    st.warning("Could not load full request details.")


st.header("Required Confirmations")

# Mandatory confirmations checkbox
confirmations_checked = st.checkbox(
    """**I confirm that:**
    
1. Both I and my coworker have at least two days off within the week we are requesting.

2. I accept the terms and conditions of the shift change system.""",
    value=False,
    key="mandatory_confirmations_accept"
)

if not confirmations_checked:
    st.warning("⚠️ You must confirm both points before accepting the shift change.")


if st.button("✅ Accept Shift Change", disabled=not confirmations_checked):
    with st.spinner("Processing acceptance..."):
        # 2. Update `date_accepted_by_cover` in `shift_requests`
        #    Mark token as `used`
        progress_bar = st.progress(0)
        st.caption("Updating request status...")
        now_utc = datetime.utcnow()
        update_success = utils.update_shift_request_status(
            shift_request_id,
            {
                "date_accepted_by_cover": now_utc.isoformat()
            },
            PROJECT_ID
        )
        progress_bar.progress(33)
        
        st.caption("Marking token as used...")
        token_marked = utils.mark_token_as_used(str(token), PROJECT_ID)
        progress_bar.progress(50)

        if update_success and token_marked:
            # Re-fetch details to get emails for confirmation
            st.caption("Preparing confirmation emails...")
            updated_request_details = utils.get_shift_request_details(shift_request_id, PROJECT_ID)
            progress_bar.progress(66)
            
            if updated_request_details:
                requester_email = updated_request_details.get('requester_email')
                cover_email = updated_request_details.get('cover_email') # Your email
                requester_name = updated_request_details.get('requester_name')
                cover_name = updated_request_details.get('cover_name')
                flight_number = updated_request_details.get('flight_number')
                date_request = updated_request_details.get('date_request')

                # 3. Send confirmation emails
                st.caption("Sending confirmation emails...")
                confirmation_subject = "Shift Change Acceptance Confirmation"
                emails_sent = True
                
                # Get current date for acceptance
                acceptance_date = datetime.now().strftime("%d/%m/%Y")
                
                # Email to requester
                if requester_email:
                    requester_body = f"""Hello {requester_name},

Good news. {cover_name} has accepted to cover your shift.

**Change details:**
• Acceptance date: {acceptance_date}
• Flight: {flight_number}
• Shift date: {format_date(date_request)}
• Covering coworker: {cover_name}

The request is now pending supervisor approval.

Best regards."""
                    if not utils.send_email(requester_email, confirmation_subject, requester_body):
                        emails_sent = False
                progress_bar.progress(83)

                # Email to cover (yourself)
                if cover_email:
                    cover_body = f"""Hello {cover_name},

You have accepted to cover {requester_name}'s shift.

**Change details:**
• Acceptance date: {acceptance_date}
• Flight: {flight_number}
• Shift date: {format_date(date_request)}
• Requester: {requester_name}

The request is now pending supervisor approval.

Thank you for your collaboration."""
                    if not utils.send_email(cover_email, confirmation_subject, cover_body):
                        emails_sent = False
                progress_bar.progress(100)

                st.success("You have accepted to cover the shift!")
                if emails_sent:
                    st.info("Confirmation emails have been sent to both parties.")
                else:
                    st.warning("Status updated, but there was a problem sending some confirmation emails.")
                st.balloons()
            else:
                st.warning("Status updated, but there was a problem retrieving details to send confirmation emails.")
        else:
            st.error("There was an error processing your acceptance. Please try again or contact the administrator.")

st.markdown("---")
st.caption("ShiftTradeAV - Shift Acceptance")

# To run this page, you would typically navigate to:
# streamlit run accept.py --server.runOnSave true --server.port 8501 (or another port if 8501 is taken)
# And then open http://localhost:8501/?token=YOUR_TOKEN_HERE
