import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, date, timedelta
import uuid
import pytz
import streamlit as st

from .config import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SENDER_EMAIL,
)
from . import utils  # for format_date and flight schedule helper


def send_email(recipient_email: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
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


def create_calendar_file(shift_data, is_for_requester=True):
    try:
        shift_date_str = shift_data.get("date_request", shift_data.get("date"))
        if isinstance(shift_date_str, str):
            shift_date = datetime.fromisoformat(
                shift_date_str.replace("Z", "+00:00")
            ).date()
        elif isinstance(shift_date_str, date):
            shift_date = shift_date_str
        else:
            shift_date = datetime.now().date()

        flight_info = shift_data.get("flight_number", "Vuelo no especificado")
        schedule_info = utils.get_flight_schedule_info(flight_info)
        start_time = schedule_info["start_time"]
        end_time = schedule_info["end_time"]
        is_overnight = schedule_info["is_overnight"]

        toronto_tz = pytz.timezone("America/Toronto")
        shift_start_naive = datetime.combine(
            shift_date, datetime.strptime(start_time, "%H:%M").time()
        )
        if is_overnight:
            shift_end_date = shift_date + timedelta(days=1)
            shift_end_naive = datetime.combine(
                shift_end_date, datetime.strptime(end_time, "%H:%M").time()
            )
        else:
            shift_end_naive = datetime.combine(
                shift_date, datetime.strptime(end_time, "%H:%M").time()
            )

        shift_start = toronto_tz.localize(shift_start_naive)
        shift_end = toronto_tz.localize(shift_end_naive)
        shift_start_utc = shift_start.astimezone(pytz.UTC)
        shift_end_utc = shift_end.astimezone(pytz.UTC)

        def fmt(dt):
            return dt.strftime("%Y%m%dT%H%M%SZ")

        now_utc = datetime.now(pytz.UTC)
        dtstamp = fmt(now_utc)
        event_uid = f"shift-change-{shift_data.get('id', uuid.uuid4())}"

        flight_schedule_display = schedule_info["display_schedule"]
        if is_for_requester:
            summary = (
                f"TURNO CEDIDO: {flight_info} ({flight_schedule_display})"
            )
            description = (
                f"Turno cedido - Intercambio aprobado\\n"
                f"Vuelo: {flight_info}\\nHorario: {flight_schedule_display}\\n"
                f"Cubierto por: {shift_data.get('cover_name', 'N/A')}\\n"
                f"Supervisor: {shift_data.get('supervisor_name', 'N/A')}"
            )
            status = "CANCELLED"
        else:
            summary = (
                f"TURNO ACEPTADO: {flight_info} ({flight_schedule_display})"
            )
            description = (
                f"Turno aceptado por intercambio\\n"
                f"Vuelo: {flight_info}\\nHorario: {flight_schedule_display}\\n"
                f"Solicitante original: {shift_data.get('requester_name', 'N/A')}\\n"
                f"Supervisor: {shift_data.get('supervisor_name', 'N/A')}"
            )
            status = "CONFIRMED"

        # Build the iCalendar file with CRLF line endings for better
        # compatibility with calendar clients such as Google Calendar and iOS.
        ical_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//ShiftTradeAV//Shift Management//ES",
            "CALSCALE:GREGORIAN",
            "METHOD:REQUEST",
            "",
            "BEGIN:VEVENT",
            f"UID:{event_uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{fmt(shift_start_utc)}",
            f"DTEND:{fmt(shift_end_utc)}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{description}",
            "LOCATION:Avianca",
            f"STATUS:{status}",
            "SEQUENCE:1",
            "END:VEVENT",
            "",
            "END:VCALENDAR",
        ]
        ical_content = "\r\n".join(ical_lines) + "\r\n"
        return ical_content
    except Exception as e:
        print(f"Error creating calendar file: {e}")
        return None


def send_email_with_calendar(
    recipient_email: str,
    subject: str,
    body: str,
    shift_data,
    is_for_requester=True,
) -> bool:
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg.attach(MIMEText(body, "plain"))

        calendar_content = create_calendar_file(shift_data, is_for_requester)
        if calendar_content:
            person_type = "solicitante" if is_for_requester else "cobertura"
            filename = f"turno_{person_type}_{shift_data.get('flight_number', 'AV')}.ics"
            attachment = MIMEBase("text", "calendar")
            attachment.set_payload(calendar_content.encode("utf-8"))
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition", f'attachment; filename="{filename}"'
            )
            attachment.add_header(
                "Content-Type", "text/calendar; method=REQUEST; charset=UTF-8"
            )
            msg.attach(attachment)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        print(f"Email with calendar sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Error sending email with calendar to {recipient_email}: {e}")
        st.error(
            f"Error al enviar correo con calendario a {recipient_email}: {e}"
        )
        return send_email(recipient_email, subject, body)
