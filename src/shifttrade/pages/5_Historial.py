import streamlit as st
import pandas as pd
from datetime import datetime, date
from shifttrade import utils
from shifttrade import supabase_client

# Project ID (ensure this is consistent, or pass it around/get from a central config)
PROJECT_ID = "lperiyftrgzchrzvutgx"

st.set_page_config(
    page_title="Historial de Cambios",
    page_icon="📜",
    layout="wide"
)

st.title("📜 Historial de Intercambios de Turno")

# Function to load and prepare data
def load_data():
    with st.spinner("Cargando historial de solicitudes..."):
        all_requests = supabase_client.get_all_shift_requests(PROJECT_ID)
    if not all_requests:
        st.warning("No hay solicitudes de intercambio en el historial.")
        return pd.DataFrame()

    df = pd.DataFrame(all_requests)

    # Convert relevant date columns
    date_cols_to_convert = ['created_at', 'date_request', 'date_accepted_by_cover', 'supervisor_decision_date']
    for col in date_cols_to_convert:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.tz_localize(None) # Remove timezone for simplicity in display

    return df

data_df = load_data()

if not data_df.empty:
    st.sidebar.header("Filtros")

    # Create a copy for filtering
    filtered_df = data_df.copy()

    # 1. Filter by Date Range (date_request)
    if 'date_request' in filtered_df.columns:
        min_date = filtered_df['date_request'].min()
        max_date = filtered_df['date_request'].max()

        if pd.isna(min_date) or pd.isna(max_date) or min_date > max_date: # Handle cases with no valid dates
             st.sidebar.warning("No hay fechas válidas para filtrar.")
        else:
            date_range = st.sidebar.date_input(
                "Fecha del Turno (Rango)",
                value=(min_date.date() if pd.notna(min_date) else date.today(), max_date.date() if pd.notna(max_date) else date.today()),
                min_value=min_date.date() if pd.notna(min_date) else None,
                max_value=max_date.date() if pd.notna(max_date) else None,
                key="date_filter_historial"
            )
            if len(date_range) == 2:
                start_date, end_date = date_range
                # Convert to datetime for comparison
                filtered_df = filtered_df[
                    (filtered_df['date_request'].dt.date >= start_date) &
                    (filtered_df['date_request'].dt.date <= end_date)
                ]

    # 2. Filter by Status
    status_options = ["Todos"] + filtered_df['supervisor_status'].unique().tolist()
    selected_status = st.sidebar.selectbox("Estado Supervisor", options=status_options, index=0)
    if selected_status != "Todos":
        filtered_df = filtered_df[filtered_df['supervisor_status'] == selected_status]

    if 'cover_status' in filtered_df.columns:
        cover_status_options = ["Todos"] + filtered_df['cover_status'].unique().tolist()
        selected_cover_status = st.sidebar.selectbox("Estado Compañero", options=cover_status_options, index=0)
        if selected_cover_status != "Todos":
            filtered_df = filtered_df[filtered_df['cover_status'] == selected_cover_status]
    else:
        st.sidebar.text("Filtro 'Estado Compañero' no disponible (sin datos)")
        
    # 3. Filter by Requester Name
    if 'requester_name' in filtered_df.columns:
        requester_names = ["Todos"] + sorted(filtered_df['requester_name'].astype(str).unique().tolist())
        selected_requester = st.sidebar.selectbox("Solicitante", options=requester_names, index=0)
        if selected_requester != "Todos":
            filtered_df = filtered_df[filtered_df['requester_name'] == selected_requester]

    # 4. Filter by Cover Name
    if 'cover_name' in filtered_df.columns:
        cover_names = ["Todos"] + sorted(filtered_df['cover_name'].astype(str).unique().tolist())
        selected_cover = st.sidebar.selectbox("Compañero que Cubre", options=cover_names, index=0)
        if selected_cover != "Todos":
            filtered_df = filtered_df[filtered_df['cover_name'] == selected_cover]
            
    # 5. Filter by Flight Number
    if 'flight_number' in filtered_df.columns:
        flight_numbers = ["Todos"] + sorted(filtered_df['flight_number'].astype(str).unique().tolist())
        selected_flight = st.sidebar.selectbox("Vuelo", options=flight_numbers, index=0)
        if selected_flight != "Todos":
            filtered_df = filtered_df[filtered_df['flight_number'] == selected_flight]

    st.subheader(f"Mostrando {len(filtered_df)} de {len(data_df)} solicitudes")

    # Columns to display and their new names
    columns_to_display = {
        'created_at': 'Fecha Creación Solicitud',
        'requester_name': 'Solicitante',
        'cover_name': 'Compañero Cubre',
        'flight_number': 'Vuelo',
        'date_request': 'Fecha Turno',
        'cover_status': 'Estado Compañero',
        'date_accepted_by_cover': 'Fecha Aceptación Compañero',
        'supervisor_status': 'Estado Supervisor',
        'supervisor_name': 'Supervisor',
        'supervisor_decision_date': 'Fecha Decisión Supervisor',
        'rejection_reason': 'Motivo Rechazo'
    }

    # Filter out columns that might not exist if no requests have reached that stage
    display_df_cols = {k: v for k, v in columns_to_display.items() if k in filtered_df.columns}
    
    display_df = filtered_df[list(display_df_cols.keys())].rename(columns=display_df_cols)

    # Format date columns for display
    for col_original, col_display in display_df_cols.items():
        if col_original in ['created_at', 'date_request', 'date_accepted_by_cover', 'supervisor_decision_date']:
            if col_display in display_df.columns: # Check if column exists after rename
                 display_df[col_display] = pd.to_datetime(display_df[col_display]).dt.strftime('%Y-%m-%d %H:%M')


    st.dataframe(display_df, use_container_width=True)

else:
    if not data_df.empty: # Only show if initial load had data but filters cleared it
        st.info("No hay solicitudes que coincidan con los filtros seleccionados.")

