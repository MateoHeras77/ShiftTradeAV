import streamlit as st
import re
import utils

# Project ID for Supabase calls
PROJECT_ID = "lperiyftrgzchrzvutgx"

# Function to validate email format
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

st.set_page_config(
    page_title="Admin Empleados",
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

st.title("👥 Administración de Empleados")
st.caption("Gestiona la base de datos de empleados del sistema")

# Password protection for admin features
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.warning("🔒 Área restringida - Se requiere contraseña de administrador")
    admin_password = st.text_input("Contraseña de administrador", type="password")
    
    if st.button("Acceder"):
        if admin_password == "admin123":  # You should use a more secure password
            st.session_state.admin_authenticated = True
            st.success("✅ Acceso concedido")
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")
    st.stop()

# Load employees data
if 'employees_data' not in st.session_state:
    st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)

# Refresh employees data
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Actualizar Lista"):
        st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
        st.rerun()

employees = st.session_state.employees_data

# Tabs for different actions
tab1, tab2, tab3 = st.tabs(["📋 Lista de Empleados", "➕ Agregar Empleado", "✏️ Editar/Desactivar"])

with tab1:
    st.header("Lista de Empleados Activos")
    
    if employees:
        st.write(f"**Total de empleados activos:** {len(employees)}")
        
        # Display employees in a table format
        for i, emp in enumerate(employees, 1):
            with st.expander(f"{i}. {emp['full_name']} - {emp['raic_color']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Nombre:** {emp['full_name']}")
                with col2:
                    st.write(f"**RAIC:** {emp['raic_color']}")
                with col3:
                    st.write(f"**Email:** {emp['email']}")
                
                st.write(f"**Creado:** {utils.format_date(emp['created_at'])}")
                if emp['updated_at'] != emp['created_at']:
                    st.write(f"**Actualizado:** {utils.format_date(emp['updated_at'])}")
    else:
        st.info("No hay empleados registrados en el sistema.")

with tab2:
    st.header("Agregar Nuevo Empleado")
    
    with st.form("add_employee_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez García")
            new_raic = st.text_input("Color del RAIC", placeholder="Ej: Azul, Verde, Rojo, etc.")
        
        with col2:
            new_email = st.text_input("Email", placeholder="juan.perez@avianca.com")
        
        submit_add = st.form_submit_button("➕ Agregar Empleado")
        
        if submit_add:
            if not all([new_name, new_raic, new_email]):
                st.error("Por favor, completa todos los campos.")
            elif not validate_email(new_email):
                st.error("❌ El email no tiene un formato válido.")
            elif utils.check_employee_exists(full_name=new_name, project_id=PROJECT_ID):
                st.error("❌ Ya existe un empleado con ese nombre.")
            elif utils.check_employee_exists(email=new_email, project_id=PROJECT_ID):
                st.error("❌ Ya existe un empleado con ese email.")
            else:
                with st.spinner("Agregando empleado..."):
                    success = utils.add_employee(new_name, new_raic, new_email, PROJECT_ID)
                    if success:
                        st.success(f"✅ Empleado {new_name} agregado exitosamente.")
                        st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
                        st.rerun()
                    else:
                        st.error("❌ Error al agregar el empleado.")

with tab3:
    st.header("Editar o Desactivar Empleado")
    
    # Initialize session state for deactivation confirmation
    if 'show_deactivate_confirm' not in st.session_state:
        st.session_state.show_deactivate_confirm = False
    if 'employee_to_deactivate' not in st.session_state:
        st.session_state.employee_to_deactivate = None
    
    if employees:
        employee_options = [f"{emp['full_name']} - {emp['raic_color']}" for emp in employees]
        selected_emp = st.selectbox("Seleccionar empleado", ["Seleccionar..."] + employee_options)
        
        if selected_emp != "Seleccionar...":
            # Find the selected employee
            emp_name = selected_emp.split(" - ")[0]
            selected_employee = next((emp for emp in employees if emp['full_name'] == emp_name), None)
            
            if selected_employee:
                st.subheader("Editar Información")
                
                with st.form("edit_employee_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_name = st.text_input("Nombre completo", value=selected_employee['full_name'])
                        edit_raic = st.text_input("Color del RAIC", value=selected_employee['raic_color'])
                    
                    with col2:
                        edit_email = st.text_input("Email", value=selected_employee['email'])
                    
                    col_update, col_deactivate = st.columns(2)
                    
                    with col_update:
                        submit_update = st.form_submit_button("💾 Actualizar", type="primary")
                    
                    with col_deactivate:
                        submit_deactivate = st.form_submit_button("🗑️ Solicitar Desactivación", type="secondary")
                
                # Handle form submissions
                if submit_update:
                    if not all([edit_name, edit_raic, edit_email]):
                        st.error("Por favor, completa todos los campos.")
                    elif not validate_email(edit_email):
                        st.error("❌ El email no tiene un formato válido.")
                    elif edit_name != selected_employee['full_name'] and utils.check_employee_exists(full_name=edit_name, project_id=PROJECT_ID):
                        st.error("❌ Ya existe un empleado con ese nombre.")
                    elif edit_email != selected_employee['email'] and utils.check_employee_exists(email=edit_email, project_id=PROJECT_ID):
                        st.error("❌ Ya existe un empleado con ese email.")
                    else:
                        with st.spinner("Actualizando empleado..."):
                            success = utils.update_employee(selected_employee['id'], edit_name, edit_raic, edit_email, PROJECT_ID)
                            if success:
                                st.success(f"✅ Empleado {edit_name} actualizado exitosamente.")
                                st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
                                st.rerun()
                            else:
                                st.error("❌ Error al actualizar el empleado.")
                
                if submit_deactivate:
                    st.session_state.show_deactivate_confirm = True
                    st.session_state.employee_to_deactivate = selected_employee
                    st.rerun()
                
                # Show confirmation dialog outside of form
                if st.session_state.show_deactivate_confirm and st.session_state.employee_to_deactivate:
                    st.warning(f"⚠️ ¿Estás seguro de que quieres desactivar al empleado **{st.session_state.employee_to_deactivate['full_name']}**?")
                    st.write("Esta acción ocultará al empleado de las listas desplegables en futuras solicitudes.")
                    
                    col_confirm, col_cancel = st.columns(2)
                    
                    with col_confirm:
                        if st.button("✅ Confirmar Desactivación", type="primary"):
                            with st.spinner("Desactivando empleado..."):
                                success = utils.deactivate_employee(st.session_state.employee_to_deactivate['id'], PROJECT_ID)
                                if success:
                                    st.success(f"✅ Empleado {st.session_state.employee_to_deactivate['full_name']} desactivado exitosamente.")
                                    st.session_state.employees_data = utils.get_all_employees(PROJECT_ID)
                                    st.session_state.show_deactivate_confirm = False
                                    st.session_state.employee_to_deactivate = None
                                    st.rerun()
                                else:
                                    st.error("❌ Error al desactivar el empleado.")
                    
                    with col_cancel:
                        if st.button("❌ Cancelar"):
                            st.session_state.show_deactivate_confirm = False
                            st.session_state.employee_to_deactivate = None
                            st.rerun()
    else:
        st.info("No hay empleados para editar.")

st.markdown("---")
st.caption("⚠️ **Nota importante:** Los cambios en la base de datos de empleados afectarán todas las futuras solicitudes de cambio de turno.")
st.caption("ShiftTradeAV - Administración de Empleados")
