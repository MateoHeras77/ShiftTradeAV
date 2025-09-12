import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys
from pathlib import Path

# Allow running this page directly via Streamlit
sys.path.append(str(Path(__file__).resolve().parents[1]))
import utils


# Project ID (ensure this is consistent, or pass it around/get from a central config)
PROJECT_ID = "lperiyftrgzchrzvutgx"

st.set_page_config(
    page_title="Shift History",
    page_icon="📜",
    layout="wide"
)

st.title("📜 Shift Swap History")

# Function to load and prepare data
def load_data():
    with st.spinner("Loading request history..."):
        all_requests = utils.get_all_shift_requests(PROJECT_ID)
    if not all_requests:
        st.warning("No shift swap requests in history.")
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
    st.sidebar.header("Filters")

    # Create a copy for filtering
    filtered_df = data_df.copy()

    # 1. Filter by Date Range (date_request)
    if 'date_request' in filtered_df.columns:
        min_date = filtered_df['date_request'].min()
        max_date = filtered_df['date_request'].max()

        if pd.isna(min_date) or pd.isna(max_date) or min_date > max_date:  # Handle cases with no valid dates
            st.sidebar.warning("No valid dates to filter.")
        else:
            date_range = st.sidebar.date_input(
                "Shift Date (Range)",
                value=(min_date.date() if pd.notna(min_date) else date.today(), max_date.date() if pd.notna(max_date) else date.today()),
                min_value=min_date.date() if pd.notna(min_date) else None,
                max_value=max_date.date() if pd.notna(max_date) else None,
                key="date_filter_historial"
            )
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                start_date, end_date = date_range
                # Convert to datetime for comparison
                filtered_df = filtered_df[
                    (filtered_df['date_request'].dt.date >= start_date) &
                    (filtered_df['date_request'].dt.date <= end_date)
                ]

    # 2. Filter by Status
    status_options = ["All"] + filtered_df['supervisor_status'].unique().tolist()
    selected_status = st.sidebar.selectbox("Supervisor Status", options=status_options, index=0)
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df['supervisor_status'] == selected_status]

    if 'cover_status' in filtered_df.columns:
        cover_status_options = ["All"] + filtered_df['cover_status'].unique().tolist()
        selected_cover_status = st.sidebar.selectbox("Cover Status", options=cover_status_options, index=0)
        if selected_cover_status != "All":
            filtered_df = filtered_df[filtered_df['cover_status'] == selected_cover_status]
    else:
        st.sidebar.text("Filter 'Cover Status' not available (no data)")
        
    # 3. Filter by Requester Name
    if 'requester_name' in filtered_df.columns:
        requester_names = ["All"] + sorted(filtered_df['requester_name'].astype(str).unique().tolist())
        selected_requester = st.sidebar.selectbox("Requester", options=requester_names, index=0)
        if selected_requester != "All":
            filtered_df = filtered_df[filtered_df['requester_name'] == selected_requester]

    # 4. Filter by Cover Name
    if 'cover_name' in filtered_df.columns:
        cover_names = ["All"] + sorted(filtered_df['cover_name'].astype(str).unique().tolist())
        selected_cover = st.sidebar.selectbox("Covering Employee", options=cover_names, index=0)
        if selected_cover != "All":
            filtered_df = filtered_df[filtered_df['cover_name'] == selected_cover]
            
    # 5. Filter by Flight Number
    if 'flight_number' in filtered_df.columns:
        flight_numbers = ["All"] + sorted(filtered_df['flight_number'].astype(str).unique().tolist())
        selected_flight = st.sidebar.selectbox("Flight", options=flight_numbers, index=0)
        if selected_flight != "All":
            filtered_df = filtered_df[filtered_df['flight_number'] == selected_flight]

    st.subheader(f"Showing {len(filtered_df)} of {len(data_df)} requests")

    # Columns to display and their new names
    columns_to_display = {
        'created_at': 'Request Creation Date',
        'requester_name': 'Requester',
        'cover_name': 'Covering Employee',
        'flight_number': 'Flight',
        'date_request': 'Shift Date',
        'cover_status': 'Cover Status',
        'date_accepted_by_cover': 'Cover Acceptance Date',
        'supervisor_status': 'Supervisor Status',
        'supervisor_name': 'Supervisor',
        'supervisor_decision_date': 'Supervisor Decision Date',
        'rejection_reason': 'Rejection Reason'
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
        st.info("No requests match the selected filters.")

