"""
Módulo de gestión de empleados para ShiftTradeAV.
Contiene funciones para interactuar con registros de empleados en Supabase.
"""

import streamlit as st
from datetime import datetime, timezone
from .config import supabase

def get_all_employees(project_id: str):
    """Get all active employees from the database."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return []
    
    try:
        response = supabase.table('employees').select('*').eq('is_active', True).order('full_name').execute()
        
        if response.data:
            return response.data
        else:
            print("No employees found or error in response.")
            return []
            
    except Exception as e:
        print(f"Error fetching employees: {e}")
        st.error(f"Error al obtener la lista de empleados: {e}")
        return []

def get_employee_by_name(full_name: str, project_id: str):
    """Get employee details by full name."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return None
    
    try:
        response = supabase.table('employees').select('*').eq('full_name', full_name).eq('is_active', True).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching employee {full_name}: {e}")
        st.error(f"Error al obtener datos del empleado {full_name}: {e}")
        return None

def get_employee_by_email(email: str, project_id: str):
    """Get employee details by email."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return None
    
    try:
        response = supabase.table('employees').select('*').eq('email', email).eq('is_active', True).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            return None
            
    except Exception as e:
        print(f"Error fetching employee by email {email}: {e}")
        st.error(f"Error al obtener datos del empleado por email {email}: {e}")
        return None

def check_employee_exists(full_name: str = None, email: str = None, project_id: str = None):
    """Check if an employee with the given name or email already exists."""
    if not supabase:
        return False
    
    try:
        if full_name:
            response = supabase.table('employees').select('id').eq('full_name', full_name).eq('is_active', True).execute()
            if response.data and len(response.data) > 0:
                return True
        
        if email:
            response = supabase.table('employees').select('id').eq('email', email).eq('is_active', True).execute()
            if response.data and len(response.data) > 0:
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking if employee exists: {e}")
        return False

def add_employee(full_name: str, raic_color: str, email: str, project_id: str):
    """Add a new employee to the database."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    
    try:
        response = supabase.table('employees').insert({
            'full_name': full_name,
            'raic_color': raic_color,
            'email': email,
            'is_active': True
        }).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Employee {full_name} added successfully")
            return True
        else:
            print("Error adding employee or no data returned.")
            return False
            
    except Exception as e:
        print(f"Error adding employee: {e}")
        st.error(f"Error al agregar empleado: {e}")
        return False

def update_employee(employee_id: int, full_name: str, raic_color: str, email: str, project_id: str):
    """Update an existing employee."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    
    try:
        response = supabase.table('employees').update({
            'full_name': full_name,
            'raic_color': raic_color,
            'email': email,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', employee_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Employee {employee_id} updated successfully")
            return True
        else:
            print("Error updating employee or no data returned.")
            return False
            
    except Exception as e:
        print(f"Error updating employee: {e}")
        st.error(f"Error al actualizar empleado: {e}")
        return False

def deactivate_employee(employee_id: int, project_id: str):
    """Deactivate an employee (soft delete)."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    
    try:
        response = supabase.table('employees').update({
            'is_active': False,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', employee_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Employee {employee_id} deactivated successfully")
            return True
        else:
            print("Error deactivating employee or no data returned.")
            return False
            
    except Exception as e:
        print(f"Error deactivating employee: {e}")
        st.error(f"Error al desactivar empleado: {e}")
        return False

def reactivate_employee(employee_id: int, project_id: str):
    """Reactivate an employee."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return False
    
    try:
        response = supabase.table('employees').update({
            'is_active': True,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', employee_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Employee {employee_id} reactivated successfully")
            return True
        else:
            print("Error reactivating employee or no data returned.")
            return False
            
    except Exception as e:
        print(f"Error reactivating employee: {e}")
        st.error(f"Error al reactivar empleado: {e}")
        return False

def get_inactive_employees(project_id: str):
    """Get all inactive employees from the database."""
    if not supabase:
        st.error("Cliente Supabase no inicializado.")
        return []
    
    try:
        response = supabase.table('employees').select('*').eq('is_active', False).order('full_name').execute()
        
        if response.data:
            return response.data
        else:
            print("No inactive employees found or error in response.")
            return []
            
    except Exception as e:
        print(f"Error fetching inactive employees: {e}")
        st.error(f"Error al obtener la lista de empleados inactivos: {e}")
        return []
