"""
Integration Demo: How to use Business Validation in ShiftTradeAV
This file demonstrates how to integrate the new business validation functions
into the main application pages.
"""

import streamlit as st
from utils.business_validation import (
    validate_shift_request,
    validate_request_date,
    check_duplicate_request,
    validate_supervisor_authorization,
    check_shift_overlap,
    get_validation_summary
)


def demo_employee_request_validation():
    """Demo: How to validate an employee shift request."""
    st.subheader("🔍 Employee Request Validation Demo")
    
    # Sample request data (this would come from the form)
    request_data = {
        'employee_email': 'pilot@avianca.com',
        'employee_name': 'Juan Pérez',
        'flight_number': 'AV205',
        'date': '2025-09-18',
        'supervisor_email': 'supervisor@avianca.com'
    }
    
    # Validate the complete request
    project_id = "your_project_id"  # This would come from your config
    is_valid, errors = validate_shift_request(request_data, project_id)
    
    st.code(f"""
# Example usage in app/main.py or employee request page:

request_data = {{
    'employee_email': employee_email,
    'employee_name': employee_name,
    'flight_number': flight_number,
    'date': selected_date,
    'supervisor_email': supervisor_email
}}

is_valid, errors = validate_shift_request(request_data, project_id)

if not is_valid:
    for error in errors:
        st.error(error)
    return False
else:
    # Proceed with saving the request
    save_shift_request(request_data, project_id)
    st.success("Solicitud enviada exitosamente!")
    """)
    
    if is_valid:
        st.success("✅ Request would be valid!")
    else:
        st.error("❌ Request validation failed:")
        for error in errors:
            st.error(f"  • {error}")


def demo_supervisor_approval_validation():
    """Demo: How to validate supervisor approval."""
    st.subheader("👨‍💼 Supervisor Approval Validation Demo")
    
    st.code(f"""
# Example usage in app/pages/3_supervisor.py:

def approve_request(request_id, supervisor_email):
    # Get request details
    request = get_shift_request_details(request_id, project_id)
    employee_email = request['employee_email']
    
    # Validate supervisor authorization
    is_authorized, error = validate_supervisor_authorization(
        supervisor_email, employee_email, project_id
    )
    
    if not is_authorized:
        st.error(f"No autorizado: {{error}}")
        return False
    
    # Proceed with approval
    update_shift_request_status(request_id, {{'status': 'approved'}}, project_id)
    st.success("Solicitud aprobada exitosamente!")
    """)


def demo_date_validation():
    """Demo: How to validate dates in forms."""
    st.subheader("📅 Date Validation Demo")
    
    st.code(f"""
# Example usage in date input forms:

selected_date = st.date_input("Fecha del vuelo")
date_str = selected_date.strftime('%Y-%m-%d')

is_valid, error = validate_request_date(date_str)

if not is_valid:
    st.error(error)
    st.stop()  # Prevent form submission
    """)


def demo_real_time_validation():
    """Demo: Real-time validation as user types."""
    st.subheader("⚡ Real-time Validation Demo")
    
    st.write("Try entering different values to see validation in action:")
    
    # Email validation
    email = st.text_input("Email del empleado", placeholder="nombre@avianca.com")
    if email:
        from utils.business_validation import validate_business_email
        is_valid, error = validate_business_email(email)
        if is_valid:
            st.success("✅ Email válido")
        else:
            st.error(f"❌ {error}")
    
    # Flight validation
    flight = st.text_input("Número de vuelo", placeholder="AV205")
    if flight:
        from utils.business_validation import validate_flight_number
        is_valid, error = validate_flight_number(flight)
        if is_valid:
            st.success("✅ Vuelo válido")
        else:
            st.error(f"❌ {error}")
    
    # Date validation
    selected_date = st.date_input("Fecha del vuelo")
    if selected_date:
        date_str = selected_date.strftime('%Y-%m-%d')
        is_valid, error = validate_request_date(date_str)
        if is_valid:
            st.success("✅ Fecha válida")
        else:
            st.error(f"❌ {error}")


def show_validation_rules():
    """Display all validation rules."""
    st.subheader("📋 Business Validation Rules")
    
    summary = get_validation_summary()
    
    for rule, description in summary.items():
        st.info(f"**{rule}**: {description}")


def main():
    """Main demo application."""
    st.title("🔧 Business Validation Integration Demo")
    st.write("This demo shows how to integrate business validation into your ShiftTradeAV application.")
    
    # Tabs for different demo sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Employee Request", 
        "Supervisor Approval", 
        "Date Validation", 
        "Real-time Validation",
        "Validation Rules"
    ])
    
    with tab1:
        demo_employee_request_validation()
    
    with tab2:
        demo_supervisor_approval_validation()
    
    with tab3:
        demo_date_validation()
    
    with tab4:
        demo_real_time_validation()
    
    with tab5:
        show_validation_rules()
    
    st.markdown("---")
    st.subheader("🚀 Next Steps")
    st.write("""
    To integrate these validations into your application:
    
    1. **Import the validation functions** in your page files:
       ```python
       from utils.business_validation import validate_shift_request, validate_request_date
       ```
    
    2. **Add validation to forms** before saving data:
       ```python
       if not is_valid:
           for error in errors:
               st.error(error)
           return
       ```
    
    3. **Use real-time validation** for better user experience:
       ```python
       if user_input and not validate_function(user_input)[0]:
           st.error("Invalid input")
       ```
    
    4. **Add validation to approval workflows** to ensure supervisors are authorized.
    
    5. **Test thoroughly** with the test files we created.
    """)


if __name__ == "__main__":
    main()
