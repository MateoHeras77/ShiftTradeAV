"""
Business Validation Module for ShiftTradeAV
Implements critical business logic validation rules.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st
from .supabase_client import get_supabase_client


def validate_request_date(request_date: str) -> Tuple[bool, str]:
    """
    Validate that request date is not in the past and within allowed range.
    
    Args:
        request_date: Date string in 'YYYY-MM-DD' format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        request_dt = datetime.strptime(request_date, '%Y-%m-%d').date()
        today = datetime.now().date()
        
        # Rule 1: Cannot request shifts for past dates
        if request_dt < today:
            return False, "No se pueden solicitar turnos para fechas pasadas"
        
        # Rule 2: Cannot request shifts more than 90 days in advance
        max_advance_days = 90
        if request_dt > today + timedelta(days=max_advance_days):
            return False, f"No se pueden solicitar turnos con más de {max_advance_days} días de anticipación"
        
        return True, ""
        
    except (ValueError, TypeError):
        return False, "Formato de fecha inválido"


def check_duplicate_request(employee_email: str, flight_number: str, date: str, project_id: str) -> Tuple[bool, str]:
    """
    Check if a duplicate request already exists for the same employee, flight, and date.
    
    Args:
        employee_email: Employee's email address
        flight_number: Flight number (e.g., 'AV205')
        date: Date string in 'YYYY-MM-DD' format
        project_id: Supabase project ID
        
    Returns:
        Tuple of (has_duplicate, error_message)
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False, "Error de conexión a la base de datos"
        
        # Check for existing requests with same employee, flight, and date
        result = supabase.table('shift_requests').select('*').eq(
            'employee_email', employee_email
        ).eq(
            'flight_number', flight_number
        ).eq(
            'date', date
        ).execute()
        
        # Check if any pending or approved requests exist
        existing_requests = [
            req for req in result.data 
            if req.get('status') in ['pending', 'approved']
        ]
        
        if existing_requests:
            return True, f"Ya existe una solicitud para el vuelo {flight_number} en la fecha {date}"
            
        return False, ""
        
    except Exception as e:
        st.error(f"Error verificando solicitudes duplicadas: {e}")
        return False, "Error verificando solicitudes existentes"


def validate_supervisor_authorization(supervisor_email: str, employee_email: str, project_id: str) -> Tuple[bool, str]:
    """
    Validate that the supervisor is authorized to approve/reject requests for the employee.
    
    Args:
        supervisor_email: Supervisor's email address
        employee_email: Employee's email address
        project_id: Supabase project ID
        
    Returns:
        Tuple of (is_authorized, error_message)
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False, "Error de conexión a la base de datos"
        
        # Get employee information
        result = supabase.table('employees').select('supervisor_email, cargo').eq(
            'email', employee_email
        ).execute()
        
        if not result.data:
            return False, "Empleado no encontrado en el sistema"
            
        employee = result.data[0]
        expected_supervisor = employee.get('supervisor_email')
        
        if not expected_supervisor:
            return False, "No se ha asignado supervisor para este empleado"
        
        # Check if the supervisor email matches
        if supervisor_email.lower() != expected_supervisor.lower():
            return False, "No está autorizado para gestionar solicitudes de este empleado"
        
        return True, ""
        
    except Exception as e:
        st.error(f"Error validando autorización de supervisor: {e}")
        return False, "Error validando autorización"


def check_shift_overlap(employee_email: str, date: str, project_id: str) -> Tuple[bool, str]:
    """
    Check if the employee already has an approved shift on the same date.
    
    Args:
        employee_email: Employee's email address
        date: Date string in 'YYYY-MM-DD' format
        project_id: Supabase project ID
        
    Returns:
        Tuple of (has_overlap, error_message)
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False, "Error de conexión a la base de datos"
        
        # Check for existing approved shifts on the same date
        result = supabase.table('shift_requests').select('*').eq(
            'employee_email', employee_email
        ).eq(
            'date', date
        ).eq(
            'status', 'approved'
        ).execute()
        
        if result.data:
            existing_flight = result.data[0].get('flight_number', 'N/A')
            return True, f"Ya tiene un turno aprobado para la fecha {date} (Vuelo: {existing_flight})"
            
        return False, ""
        
    except Exception as e:
        st.error(f"Error verificando solapamiento de turnos: {e}")
        return False, "Error verificando turnos existentes"


def validate_flight_number(flight_number: str) -> Tuple[bool, str]:
    """
    Validate that the flight number is in the approved list.
    
    Args:
        flight_number: Flight number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Valid flight numbers for this application
    valid_flights = {
        'AV205': {'type': 'overnight', 'route': 'BOG-MIA', 'description': 'Bogotá - Miami'},
        'AV255': {'type': 'day', 'route': 'BOG-LIM', 'description': 'Bogotá - Lima'},
        'AV625': {'type': 'overnight', 'route': 'BOG-MEX', 'description': 'Bogotá - México'},
        'AV627': {'type': 'day', 'route': 'BOG-CCS', 'description': 'Bogotá - Caracas'}
    }
    
    if not flight_number:
        return False, "Número de vuelo requerido"
    
    if flight_number not in valid_flights:
        available_flights = ", ".join(valid_flights.keys())
        return False, f"Número de vuelo no válido. Vuelos disponibles: {available_flights}"
    
    return True, ""


def validate_business_email(email: str) -> Tuple[bool, str]:
    """
    Validate that the email belongs to the company domain.
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email or '@' not in email:
        return False, "Formato de email inválido"
    
    # Only accept avianca.com emails
    if not email.lower().endswith('@avianca.com'):
        return False, "Solo se permiten correos corporativos (@avianca.com)"
    
    return True, ""


def validate_status_transition(from_status: str, to_status: str) -> Tuple[bool, str]:
    """
    Validate that a status transition is allowed in the workflow.
    
    Args:
        from_status: Current status
        to_status: Target status
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_transitions = {
        'pending': ['approved', 'rejected'],
        'approved': ['completed'],
        'rejected': ['pending'],  # Allow resubmission
        'completed': []  # Final state
    }
    
    allowed_transitions = valid_transitions.get(from_status, [])
    
    if to_status not in allowed_transitions:
        return False, f"Transición no permitida: {from_status} → {to_status}"
    
    return True, ""


def validate_shift_request(request_data: Dict, project_id: str) -> Tuple[bool, List[str]]:
    """
    Comprehensive validation of a shift request.
    
    Args:
        request_data: Dictionary containing shift request data
        project_id: Supabase project ID
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Extract required fields
    employee_email = request_data.get('employee_email', '')
    flight_number = request_data.get('flight_number', '')
    date = request_data.get('date', '')
    supervisor_email = request_data.get('supervisor_email', '')
    
    # Validation 1: Business email
    is_valid, error = validate_business_email(employee_email)
    if not is_valid:
        errors.append(f"Email empleado: {error}")
    
    # Validation 2: Flight number
    is_valid, error = validate_flight_number(flight_number)
    if not is_valid:
        errors.append(f"Número de vuelo: {error}")
    
    # Validation 3: Request date
    is_valid, error = validate_request_date(date)
    if not is_valid:
        errors.append(f"Fecha: {error}")
    
    # Validation 4: Duplicate request
    is_duplicate, error = check_duplicate_request(employee_email, flight_number, date, project_id)
    if is_duplicate:
        errors.append(f"Solicitud duplicada: {error}")
    
    # Validation 5: Shift overlap
    has_overlap, error = check_shift_overlap(employee_email, date, project_id)
    if has_overlap:
        errors.append(f"Conflicto de turnos: {error}")
    
    # Validation 6: Supervisor authorization (if provided)
    if supervisor_email:
        is_authorized, error = validate_supervisor_authorization(supervisor_email, employee_email, project_id)
        if not is_authorized:
            errors.append(f"Autorización: {error}")
    
    return len(errors) == 0, errors


def get_validation_summary() -> Dict[str, str]:
    """
    Get a summary of all business validation rules.
    
    Returns:
        Dictionary with validation rule descriptions
    """
    return {
        "Fechas": "No se permiten fechas pasadas ni más de 90 días de anticipación",
        "Duplicados": "Un empleado no puede solicitar el mismo vuelo en la misma fecha",
        "Supervisor": "Solo supervisores autorizados pueden aprobar/rechazar solicitudes",
        "Solapamiento": "Un empleado no puede tener múltiples turnos en la misma fecha",
        "Vuelos": "Solo se permiten vuelos: AV205, AV255, AV625, AV627",
        "Email": "Solo correos corporativos @avianca.com",
        "Estados": "Transiciones: pending→approved/rejected, approved→completed, rejected→pending"
    }
