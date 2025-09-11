# ShiftTradeAV - Shift Swap Application for Avianca

## Overview
ShiftTradeAV is a Streamlit application backed by Supabase that allows Avianca employees to request, accept, and approve shift swaps in an organized way.

## Features
- Simple shift change request form
- Email notifications
- Supervisor approval dashboard
- Progress indicators to keep users informed
- Complete request history with filters
- Supervisor authentication
- Secure token system for shift acceptance

## Project Structure
```
app/
  main.py                # Shift change request form
  utils.py               # Shared functions for Supabase, email and tokens
  pages/
    2_accept.py          # Accept a shift request
    3_supervisor.py      # Supervisor approval panel
    4_employee_admin.py  # Employee administration
    5_history.py         # Request history
```

## Configuration
Create a `.streamlit/secrets.toml` file with the following content:
```toml
SUPABASE_URL = "YOUR_PROJECT_URL"
SUPABASE_KEY = "YOUR_PROJECT_KEY"
SMTP_SERVER = "SMTP_SERVER"
SMTP_PORT = "SMTP_PORT"
SMTP_USERNAME = "SMTP_USERNAME"
SMTP_PASSWORD = "SMTP_PASSWORD"
SENDER_EMAIL = "SENDER_EMAIL"
```

## Run the App
```bash
streamlit run app/main.py
```

## Security
- Password protection for supervisors
- Unique tokens to validate acceptance links
- Automatic token expiration (24 hours)
- Required field validation

## Database
ShiftTradeAV uses Supabase with two main tables:
1. `shift_requests` - stores all swap requests
2. `tokens` - manages generated tokens for request acceptance
