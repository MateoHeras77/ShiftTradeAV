import streamlit as st
import pandas as pd
from datetime import datetime
import utils # Your utility functions
import locale

# Project ID for Supabase calls (ensure this is consistent with your project)
PROJECT_ID = "lperiyftrgzchrzvutgx" 

# Configurar locale para manejo correcto de caracteres especiales
try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')  # Para Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Spanish_Spain.1252')  # Para Windows
    except:
        pass  # Si falla, seguimos sin cambiar el locale

st.set_page_config(
    page_title="Historial de Solicitudes",
    page_icon="📜",
    layout="wide"
)

st.title("📜 Historial de Todas las Solicitudes")

# Function to refresh data
def refresh_data():
    if 'all_requests_for_history_page' in st.session_state:
        del st.session_state.all_requests_for_history_page
    st.rerun()

# Sidebar for actions
st.sidebar.header("Acciones")
if st.sidebar.button("Refrescar Datos", key="refresh_hist_page"):
    refresh_data()

st.sidebar.markdown("---")

# Fetch all requests for history, cache in session state
if 'all_requests_for_history_page' not in st.session_state:
    with st.spinner("Cargando historial de solicitudes..."):
        st.session_state.all_requests_for_history_page = utils.get_all_shift_requests(PROJECT_ID)

all_requests_for_history = st.session_state.all_requests_for_history_page

if not all_requests_for_history:
    st.info("No hay historial de solicitudes disponible.")
else:
    # Convertir la lista de solicitudes a DataFrame para facilitar manipulación
    df_history = pd.DataFrame(all_requests_for_history)
    
    # Ordenar por fecha de vuelo (convertir a datetime para ordenamiento correcto)
    try:
        # Convertir fecha_request a datetime para ordenar correctamente
        df_history['date_request_dt'] = pd.to_datetime(df_history['date_request'], errors='coerce')
        # Ordenar por fecha ascendente (más cercanas primero)
        df_history = df_history.sort_values(by='date_request_dt', ascending=True).reset_index(drop=True) # Changed to ascending=True
        # Eliminar columna auxiliar usada para ordenar
        df_history = df_history.drop('date_request_dt', axis=1)
    except Exception as e:
        st.warning(f"No se pudo ordenar el historial por fecha: {e}")
    
    columns_to_display = [
        'id', 'date_request', 'flight_number', 'requester_name', 
        'cover_name', 'supervisor_status', 'supervisor_name', 
        'supervisor_decision_date', 'supervisor_comments',
        'requester_employee_number', 'cover_employee_number', # Added RAIC/Employee numbers
        'date_accepted_by_cover' # Added date cover accepted
    ]
    existing_columns_in_df = [col for col in columns_to_display if col in df_history.columns]
    
    df_display_full = df_history[existing_columns_in_df].copy()

    # Convert relevant date columns to datetime objects and format
    if 'date_request' in df_display_full.columns:
        df_display_full['date_request'] = df_display_full['date_request'].apply(utils.format_date)
    if 'supervisor_decision_date' in df_display_full.columns:
        df_display_full['supervisor_decision_date'] = df_display_full['supervisor_decision_date'].apply(utils.format_date)
    if 'date_accepted_by_cover' in df_display_full.columns:
        df_display_full['date_accepted_by_cover'] = df_display_full['date_accepted_by_cover'].apply(utils.format_date)
    rename_map = {
        'id': 'ID',
        'date_request': 'Fecha Vuelo Orig.',
        'flight_number': 'Vuelo',
        'requester_name': 'Solicitante',
        'requester_employee_number': 'RAIC Solicitante',
        'cover_name': 'Cubridor',
        'cover_employee_number': 'RAIC Cubridor',
        'date_accepted_by_cover': 'Fecha Acept. Cubridor',
        'supervisor_status': 'Estado Sup.',
        'supervisor_name': 'Supervisor',
        'supervisor_decision_date': 'Fecha Decisión Sup.',
        'supervisor_comments': 'Comentarios Sup.'
    }
    # Asegurarnos de que los nombres de columnas con acentos se muestran correctamente
    df_display_filtered = df_display_full.rename(columns={k: v for k, v in rename_map.items() if k in df_display_full.columns})
    
    # Ensure the order of columns after renaming
    ordered_renamed_columns = [rename_map[col] for col in existing_columns_in_df if col in rename_map and rename_map[col] in df_display_filtered.columns]
    df_display_filtered = df_display_filtered[ordered_renamed_columns]

    st.markdown("### Filtrar Historial")
    filter_cols = st.columns(4) # Increased to 4 for new date filter
    
    with filter_cols[0]:
        if 'Solicitante' in df_display_filtered.columns:
            requester_names = sorted(df_display_filtered['Solicitante'].dropna().unique().tolist())
            selected_requester = st.selectbox("Por Solicitante", ["Todos"] + requester_names, key="hist_requester_filter")
            if selected_requester != "Todos":
                df_display_filtered = df_display_filtered[df_display_filtered['Solicitante'] == selected_requester]
    
    with filter_cols[1]:
        if 'Cubridor' in df_display_filtered.columns:
            cover_names = sorted(df_display_filtered['Cubridor'].dropna().unique().tolist())
            selected_cover = st.selectbox("Por Cubridor", ["Todos"] + cover_names, key="hist_cover_filter")
            if selected_cover != "Todos":
                df_display_filtered = df_display_filtered[df_display_filtered['Cubridor'] == selected_cover]

    with filter_cols[2]:
        if 'Estado Sup.' in df_display_filtered.columns:
            status_options = sorted(df_display_filtered['Estado Sup.'].dropna().unique().tolist())
            selected_status = st.selectbox("Por Estado Sup.", ["Todos"] + status_options, key="hist_status_filter")
            if selected_status != "Todos":
                df_display_filtered = df_display_filtered[df_display_filtered['Estado Sup.'] == selected_status]
    
    with filter_cols[3]:
        # Date range filter for 'Fecha Vuelo Orig.'
        # We need to use the original date column for filtering before it's formatted.
        # This requires having the original date data available or re-parsing.
        # For simplicity, if 'Fecha Vuelo Orig.' is already formatted, this filter might not be precise.
        # A more robust solution would keep original dates for filtering and formatted for display.
        
        # Assuming 'date_request' still holds original sortable dates in df_history for this filter
        if 'date_request' in df_history.columns:
            try:
                # Convert to datetime, coercing errors for non-date strings
                date_series = pd.to_datetime(df_history['date_request'], errors='coerce').dropna()
                if not date_series.empty:
                    min_date = date_series.min().date()
                    max_date = date_series.max().date()
                    
                    selected_date_range = st.date_input(
                        "Por Fecha Vuelo Orig.",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        key="hist_date_filter"
                    )
                    
                    if selected_date_range and len(selected_date_range) == 2:
                        start_date, end_date = selected_date_range
                        # Filter the original df_history based on the unformatted 'date_request'
                        # Then apply this filter to df_display_filtered by index
                        original_indices = df_history[
                            (pd.to_datetime(df_history['date_request'], errors='coerce').dt.date >= start_date) &
                            (pd.to_datetime(df_history['date_request'], errors='coerce').dt.date <= end_date)
                        ].index
                        df_display_filtered = df_display_filtered.loc[original_indices]

            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de fecha: {e}")
    # Asegurar que los caracteres especiales (tildes, ñ, etc.) se muestren correctamente
    # Convertir cualquier valor NaN/None a cadenas vacías para evitar problemas
    df_display_filtered = df_display_filtered.fillna('')
    
    # Aplicar formato HTML si es necesario para los caracteres especiales
    st.dataframe(
        df_display_filtered,
        use_container_width=True,
        height=600,
        column_config={col: st.column_config.TextColumn(col) for col in df_display_filtered.columns}
    )

st.markdown("---")
st.caption("ShiftTradeAV - Historial de Solicitudes")
