import streamlit as st # Import streamlit to access secrets
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText

# Supabase configuration (replace with your actual credentials)
SUPABASE_URL = st.secrets["SUPABASE_URL"] 
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
# from supabase import create_client, Client # Assuming you'll install the supabase-py library

# # Initialize Supabase client
# try:
#     supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# except Exception as e:
#     print(f"Error initializing Supabase client: {e}")
#     supabase = None

# Email configuration (replace with your SMTP server details or SendGrid API key)
SMTP_SERVER = st.secrets["SMTP_SERVER"]
SMTP_PORT = st.secrets["SMTP_PORT"] # Ensure this is an integer if Streamlit loads it as string
SMTP_USERNAME = st.secrets["SMTP_USERNAME"]
SMTP_PASSWORD = st.secrets["SMTP_PASSWORD"]
SENDER_EMAIL = st.secrets["SENDER_EMAIL"]

def generate_token(shift_request_id, project_id):
    """Generates a unique token, stores it in Supabase, and returns the token."""
    token = uuid.uuid4()
    expires_at = datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours

    # This is a placeholder for Supabase interaction.
    # You'll need to implement the actual Supabase call using its Python library.
    print(f"TODO: Save to Supabase in project {project_id}: token={token}, shift_request_id={shift_request_id}, expires_at={expires_at}")
    # Example (conceptual, replace with actual Supabase client usage):
    # if supabase:
    #     try:
    #         data, count = supabase.table('tokens').insert({
    #             "token": str(token),
    #             "shift_request_id": str(shift_request_id),
    #             "expires_at": expires_at.isoformat(),
    #             "used": False
    #         }).execute()
    #         if count and data:
    #             return str(token)
    #         else:
    #             print("Error saving token to Supabase: No data returned or count is None")
    #             return None
    #     except Exception as e:
    #         print(f"Error saving token to Supabase: {e}")
    #         return None
    # else:
    #     print("Supabase client not initialized. Cannot save token.")
    #     return None
    return str(token) # Placeholder

def verify_token(token_str, project_id):
    """Verifies a token against Supabase. Returns the shift_request_id if valid, else None."""
    # This is a placeholder for Supabase interaction.
    print(f"TODO: Verify from Supabase in project {project_id}: token={token_str}")
    # Example (conceptual):
    # if supabase:
    #     try:
    #         response = supabase.table('tokens').select('shift_request_id, expires_at, used').eq('token', token_str).execute()
    #         if response.data:
    #             token_data = response.data[0]
    #             expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00')) # Ensure timezone aware
    #             if not token_data['used'] and expires_at > datetime.utcnow().replace(tzinfo=timezone.utc):
    #                 return token_data['shift_request_id']
    #             else:
    #                 print("Token is used or expired.")
    #                 return None
    #         else:
    #             print("Token not found.")
    #             return None
    #     except Exception as e:
    #         print(f"Error verifying token: {e}")
    #         return None
    # else:
    #     print("Supabase client not initialized. Cannot verify token.")
    #     return None
    # For now, let's assume a dummy shift_request_id if token is "valid_token"
    if token_str == "valid_token_for_testing":
        return "dummy_shift_request_id"
    return None # Placeholder

def mark_token_as_used(token_str, project_id):
    """Marks a token as used in Supabase."""
    # This is a placeholder for Supabase interaction.
    print(f"TODO: Mark as used in Supabase in project {project_id}: token={token_str}")
    # Example (conceptual):
    # if supabase:
    #     try:
    #         data, count = supabase.table('tokens').update({'used': True}).eq('token', token_str).execute()
    #         if count:
    #             print(f"Token {token_str} marked as used.")
    #             return True
    #         else:
    #             print(f"Failed to mark token {token_str} as used or token not found.")
    #             return False
    #     except Exception as e:
    #         print(f"Error marking token as used: {e}")
    #         return False
    # else:
    #     print("Supabase client not initialized. Cannot mark token as used.")
    #     return False
    return True # Placeholder

def send_email(recipient_email, subject, body):
    """Sends an email."""
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        print(f"Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {e}")
        return False

def save_shift_request(details, project_id):
    """Saves shift request details to Supabase and returns the new request's ID."""
    # This is a placeholder for Supabase interaction.
    print(f"TODO: Save shift_request to Supabase in project {project_id}: {details}")
    # Example (conceptual):
    # if supabase:
    #     try:
    #         data, count = supabase.table('shift_requests').insert(details).execute()
    #         if count and data:
    #             print(f"Shift request saved with ID: {data[0]['id']}")
    #             return data[0]['id']
    #         else:
    #             print("Error saving shift request: No data returned or count is None")
    #             return None
    #     except Exception as e:
    #         print(f"Error saving shift request: {e}")
    #         return None
    # else:
    #     print("Supabase client not initialized. Cannot save shift request.")
    #     return None
    return str(uuid.uuid4()) # Placeholder ID

def update_shift_request_status(request_id, updates, project_id):
    """Updates a shift request in Supabase."""
    # This is a placeholder for Supabase interaction.
    print(f"TODO: Update shift_request in Supabase in project {project_id}: id={request_id}, updates={updates}")
    # Example (conceptual):
    # if supabase:
    #     try:
    #         data, count = supabase.table('shift_requests').update(updates).eq('id', request_id).execute()
    #         if count:
    #             print(f"Shift request {request_id} updated.")
    #             return True
    #         else:
    #             print(f"Failed to update shift request {request_id} or request not found.")
    #             return False
    #     except Exception as e:
    #         print(f"Error updating shift request: {e}")
    #         return False
    # else:
    #     print("Supabase client not initialized. Cannot update shift request.")
    #     return False
    return True # Placeholder

def get_pending_requests(project_id):
    """Fetches all shift requests with supervisor_status = 'pending'."""
    # This is a placeholder for Supabase interaction.
    print(f"TODO: Get pending requests from Supabase in project {project_id}")
    # Example (conceptual):
    # if supabase:
    #     try:
    #         response = supabase.table('shift_requests').select('*').eq('supervisor_status', 'pending').execute()
    #         return response.data if response.data else []
    #     except Exception as e:
    #         print(f"Error fetching pending requests: {e}")
    #         return []
    # else:
    #     print("Supabase client not initialized. Cannot fetch pending requests.")
    #     return []
    # Placeholder data
    return [
        {'id': 'dummy_id_1', 'flight_number': 'FL123', 'requester_name': 'John Doe', 'cover_name': 'Jane Smith', 'date_request': '2025-05-22T10:00:00Z'},
        {'id': 'dummy_id_2', 'flight_number': 'FL456', 'requester_name': 'Alice Brown', 'cover_name': 'Bob White', 'date_request': '2025-05-23T11:00:00Z'}
    ]

def get_shift_request_details(request_id, project_id):
    """Fetches details for a specific shift request."""
    # This is a placeholder for Supabase interaction.
    print(f"TODO: Get shift request details from Supabase in project {project_id}: id={request_id}")
    # Example (conceptual):
    # if supabase:
    #     try:
    #         response = supabase.table('shift_requests').select('*').eq('id', request_id).single().execute()
    #         return response.data
    #     except Exception as e:
    #         print(f"Error fetching shift request details for {request_id}: {e}")
    #         return None
    # else:
    #     print("Supabase client not initialized. Cannot fetch shift request details.")
    #     return None
    # Placeholder data
    if request_id == "dummy_shift_request_id":
        return {
            'id': 'dummy_shift_request_id',
            'requester_name': 'Test Requester', 'requester_email': 'requester@example.com',
            'cover_name': 'Test Cover', 'cover_email': 'cover@example.com',
            'flight_number': 'FL789'
        }
    return None

# Remember to install the Supabase Python library: pip install supabase
# And a library for email if you choose SendGrid, e.g., pip install sendgrid
# For smtplib, it's part of Python's standard library.
