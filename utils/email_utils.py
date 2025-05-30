"""
Módulo de utilidades de correo electrónico para ShiftTradeAV.
Contiene funciones para envío de correos electrónicos con y sin adjuntos de calendario.
"""

import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from .config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL
from .calendar import create_calendar_file

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
        st.error(f"Error al enviar correo a {recipient_email}: {e}")
        return False

def send_email_with_calendar(recipient_email, subject, body, shift_data, is_for_requester=True):
    """
    Sends an email with a calendar attachment.
    
    Args:
        recipient_email: Email address of recipient
        subject: Email subject
        body: Email body text
        shift_data: Dictionary containing shift information for calendar creation
        is_for_requester: Boolean, True if calendar is for the person requesting the shift change
    
    Returns:
        Boolean indicating success
    """
    try:
        # Create the message
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Create calendar file
        calendar_content = create_calendar_file(shift_data, is_for_requester)
        
        if calendar_content:
            # Create temporary calendar file
            person_type = "solicitante" if is_for_requester else "cobertura"
            filename = f"turno_{person_type}_{shift_data.get('flight_number', 'AV')}.ics"
            
            # Create attachment
            calendar_attachment = MIMEBase('text', 'calendar')
            calendar_attachment.set_payload(calendar_content.encode('utf-8'))
            encoders.encode_base64(calendar_attachment)
            calendar_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            calendar_attachment.add_header('Content-Type', 'text/calendar; method=PUBLISH')
            
            msg.attach(calendar_attachment)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        
        print(f"Email with calendar sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email with calendar to {recipient_email}: {e}")
        st.error(f"Error al enviar correo con calendario a {recipient_email}: {e}")
        # Fallback to regular email
        return send_email(recipient_email, subject, body)
