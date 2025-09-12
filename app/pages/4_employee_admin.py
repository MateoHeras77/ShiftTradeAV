import streamlit as st
import re
import sys
from pathlib import Path

# Allow running this page directly via Streamlit
sys.path.append(str(Path(__file__).resolve().parents[1]))
import utils
from utils.general_utils import format_date  # Direct import for format_date function


# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx"

# Function to validate email format
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

st.set_page_config(
    page_title="Employee Admin",
    page_icon="👥",
    layout="wide"
)

# Hide the sidebar navigation
st.markdown("""
<style>
    .css-1d391kg {display: none}
    .st-emotion-cache-1rtdyuf {display: none}
    .st-emotion-cache-1cypcdb {display: none}
</style>
""", unsafe_allow_html=True)

st.title("👥 Employee Administration")
st.caption("Manage the system's employee database")

# Password protection for admin features
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.warning("🔒 Restricted area - admin password required")
    admin_password = st.text_input("Admin password", type="password")
    
    if st.button("Access"):
        if admin_password == "admin123":  # You should use a more secure password
            st.session_state.admin_authenticated = True
            st.success("✅ Access granted")
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    st.stop()

# Load employees data
if 'employees_data' not in st.session_state:
    st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
if 'inactive_employees_data' not in st.session_state:
    st.session_state.inactive_employees_data = utils.get_inactive_employees(PROJECT_ID)

# Refresh employees data
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh List"):
        st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
        st.session_state.inactive_employees_data = utils.get_inactive_employees(PROJECT_ID)
        st.rerun()

employees = st.session_state.employees_data
inactive_employees = st.session_state.inactive_employees_data

# Tabs for different actions
tab1, tab2, tab3, tab4 = st.tabs(["📋 Employee List", "➕ Add Employee", "✏️ Edit/Deactivate", "🗂️ Deactivated"])

with tab1:
    st.header("Active Employees List")
    
    if employees:
        st.write(f"**Total active employees:** {len(employees)}")
        
        # Display employees in a table format
        for i, emp in enumerate(employees, 1):
            with st.expander(f"{i}. {emp['full_name']} - {emp['raic_color']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Name:** {emp['full_name']}")
                with col2:
                    st.write(f"**RAIC:** {emp['raic_color']}")
                with col3:
                    st.write(f"**Email:** {emp['email']}")
                
                st.write(f"**Created:** {format_date(emp['created_at'])}")
                if emp['updated_at'] != emp['created_at']:
                    st.write(f"**Updated:** {format_date(emp['updated_at'])}")
    else:
        st.info("No employees registered in the system.")

with tab2:
    st.header("Add New Employee")
    
    with st.form("add_employee_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Full name", placeholder="Ex: John Doe")
            new_raic = st.text_input("RAIC color", placeholder="Ex: Blue, Green, Red, etc.")
        
        with col2:
            new_email = st.text_input("Email", placeholder="john.doe@example.com")
        
        submit_add = st.form_submit_button("➕ Add Employee")
        
        if submit_add:
            if not all([new_name, new_raic, new_email]):
                st.error("Please complete all fields.")
            elif not validate_email(new_email):
                st.error("❌ Email format is invalid.")
            elif utils.check_employee_exists(full_name=new_name, project_id=PROJECT_ID):
                st.error("❌ An employee with that name already exists.")
            elif utils.check_employee_exists(email=new_email, project_id=PROJECT_ID):
                st.error("❌ An employee with that email already exists.")
            else:
                with st.spinner("Adding employee..."):
                    success = utils.add_employee(new_name, new_raic, new_email, PROJECT_ID)
                    if success:
                        st.success(f"✅ Employee {new_name} added successfully.")
                        st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
                        st.session_state.inactive_employees_data = utils.get_inactive_employees(PROJECT_ID)
                        st.rerun()
                    else:
                        st.error("❌ Error adding the employee.")

with tab3:
    st.header("Edit or Deactivate Employee")
    
    # Initialize session state for deactivation confirmation
    if 'show_deactivate_confirm' not in st.session_state:
        st.session_state.show_deactivate_confirm = False
    if 'employee_to_deactivate' not in st.session_state:
        st.session_state.employee_to_deactivate = None
    
    if employees:
        employee_options = [f"{emp['full_name']} - {emp['raic_color']}" for emp in employees]
        selected_emp = st.selectbox("Select employee", ["Select..."] + employee_options)
        
        if selected_emp != "Select...":
            # Find the selected employee
            emp_name = selected_emp.split(" - ")[0]
            selected_employee = next((emp for emp in employees if emp['full_name'] == emp_name), None)
            
            if selected_employee:
                st.subheader("Edit Information")
                
                with st.form("edit_employee_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_name = st.text_input("Full name", value=selected_employee['full_name'])
                        edit_raic = st.text_input("RAIC color", value=selected_employee['raic_color'])
                    
                    with col2:
                        edit_email = st.text_input("Email", value=selected_employee['email'])
                    
                    col_update, col_deactivate = st.columns(2)
                    
                    with col_update:
                        submit_update = st.form_submit_button("💾 Update", type="primary")
                    
                    with col_deactivate:
                        submit_deactivate = st.form_submit_button("🗑️ Request Deactivation", type="secondary")
                
                # Handle form submissions
                if submit_update:
                    if not all([edit_name, edit_raic, edit_email]):
                        st.error("Please complete all fields.")
                    elif not validate_email(edit_email):
                        st.error("❌ Email format is invalid.")
                    elif edit_name != selected_employee['full_name'] and utils.check_employee_exists(full_name=edit_name, project_id=PROJECT_ID):
                        st.error("❌ An employee with that name already exists.")
                    elif edit_email != selected_employee['email'] and utils.check_employee_exists(email=edit_email, project_id=PROJECT_ID):
                        st.error("❌ An employee with that email already exists.")
                    else:
                        with st.spinner("Updating employee..."):
                            success = utils.update_employee(selected_employee['id'], edit_name, edit_raic, edit_email, PROJECT_ID)
                            if success:
                                st.success(f"✅ Employee {edit_name} updated successfully.")
                                st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
                                st.session_state.inactive_employees_data = utils.get_inactive_employees(PROJECT_ID)
                                st.rerun()
                            else:
                                st.error("❌ Error updating the employee.")
                
                if submit_deactivate:
                    st.session_state.show_deactivate_confirm = True
                    st.session_state.employee_to_deactivate = selected_employee
                    st.rerun()
                
                # Show confirmation dialog outside of form
                if st.session_state.show_deactivate_confirm and st.session_state.employee_to_deactivate:
                    st.warning(f"⚠️ Are you sure you want to deactivate employee **{st.session_state.employee_to_deactivate['full_name']}**?")
                    st.write("This will hide the employee from dropdowns in future requests.")
                    
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("✅ Confirm Deactivation", type="primary"):
                            with st.spinner("Deactivating employee..."):
                                success = utils.deactivate_employee(st.session_state.employee_to_deactivate['id'], PROJECT_ID)
                                if success:
                                    st.success(f"✅ Employee {st.session_state.employee_to_deactivate['full_name']} deactivated successfully.")
                                    st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
                                    st.session_state.inactive_employees_data = utils.get_inactive_employees(PROJECT_ID)
                                    st.session_state.show_deactivate_confirm = False
                                    st.session_state.employee_to_deactivate = None
                                    st.rerun()
                                else:
                                    st.error("❌ Error deactivating the employee.")
                    
                    with col_cancel:
                        if st.button("❌ Cancel"):
                            st.session_state.show_deactivate_confirm = False
                            st.session_state.employee_to_deactivate = None
                            st.rerun()
    else:
        st.info("No employees to edit.")

with tab4:
    st.header("Deactivated Employees")
    
    # Initialize session state for reactivation confirmation
    if 'show_reactivate_confirm' not in st.session_state:
        st.session_state.show_reactivate_confirm = False
    if 'employee_to_reactivate' not in st.session_state:
        st.session_state.employee_to_reactivate = None
    
    if inactive_employees:
        st.write(f"**Total of deactivated employees:** {len(inactive_employees)}")
        st.caption("Deactivated employees do not appear in the main form dropdowns.")
        
        # Display inactive employees in a table format
        for i, emp in enumerate(inactive_employees, 1):
            with st.expander(f"{i}. {emp['full_name']} - {emp['raic_color']} (DEACTIVATED)"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**Name:** {emp['full_name']}")
                with col2:
                    st.write(f"**RAIC:** {emp['raic_color']}")
                with col3:
                    st.write(f"**Email:** {emp['email']}")
                with col4:
                    if st.button(f"🔄 Reactivate", key=f"reactivate_{emp['id']}"):
                        st.session_state.show_reactivate_confirm = True
                        st.session_state.employee_to_reactivate = emp
                        st.rerun()
                
                st.write(f"**Created:** {format_date(emp['created_at'])}")
                st.write(f"**Deactivated:** {format_date(emp['updated_at'])}")
        
        # Show confirmation dialog for reactivation
        if st.session_state.show_reactivate_confirm and st.session_state.employee_to_reactivate:
            st.success(f"🔄 Do you want to reactivate employee **{st.session_state.employee_to_reactivate['full_name']}**?")
            st.write("This will make the employee appear again in the main form dropdowns.")
            
            col_confirm, col_cancel = st.columns(2)
            
            with col_confirm:
                if st.button("✅ Confirm Reactivation", type="primary"):
                    with st.spinner("Reactivating employee..."):
                        success = utils.reactivate_employee(st.session_state.employee_to_reactivate['id'], PROJECT_ID)
                        if success:
                            st.success(f"✅ Employee {st.session_state.employee_to_reactivate['full_name']} reactivated successfully.")
                            st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
                            st.session_state.inactive_employees_data = utils.get_inactive_employees(PROJECT_ID)
                            st.session_state.show_reactivate_confirm = False
                            st.session_state.employee_to_reactivate = None
                            st.rerun()
                        else:
                            st.error("❌ Error reactivating the employee.")
            
            with col_cancel:
                if st.button("❌ Cancel Reactivation"):
                    st.session_state.show_reactivate_confirm = False
                    st.session_state.employee_to_reactivate = None
                    st.rerun()
    else:
        st.info("There are no deactivated employees.")
        st.write("✨ Great! All employees are active in the system.")

st.markdown("---")
st.caption("⚠️ **Important note:** Changes to the employee database will affect all future shift change requests.")
st.caption("ShiftTradeAV - Employee Administration")
