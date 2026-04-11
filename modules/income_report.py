import streamlit as st
import pandas as pd
from datetime import date

def show(supabase):
    st.subheader("💵 Detailed Rental Income Report")

    try:
        # 1. FETCH DATA
        # We fetch all columns to identify the correct financial field dynamically
        res = supabase.table("rentals").select(
            "*, fleet!fk_rentals_fleet(plate)"
        ).execute()
        
        if not res.data:
            st.info("No rental income records found.")
            return

        df = pd.DataFrame(res.data)
        
        # --- 2. DYNAMIC COLUMN MAPPING ---
        # Identify the income column (checking for total_amount, amount, or tax_amount)
        possible_income_cols = ['total_amount', 'amount', 'tax_amount', 'grand_total']
        income_col = next((col for col in possible_income_cols if col in df.columns), None)

        if not income_col:
            st.error(f"Could not find an income column. Available: {list(df.columns)}")
            return

        # Flatten nested vehicle data and format dates
        df['vehicle'] = df['fleet'].apply(lambda x: x['plate'] if isinstance(x, dict) else "N/A")
        df['date_out'] = pd.to_datetime(df['date_out']).dt.date
        df['income_display'] = pd.to_numeric(df[income_col], errors='coerce').fillna(0)

        # --- 3. FILTERS ---
        c1, c2 = st.columns(2)
        
        with c1:
            vehicle_list = ["All Vehicles"] + sorted(df['vehicle'].unique().tolist())
            selected_v = st.selectbox("Select Vehicle", vehicle_list)
        
        with c2:
            date_mode = st.radio("Date Range", ["All Dates", "Custom Range"], horizontal=True)
            start_dt, end_dt = None, None
            if date_mode == "Custom Range":
                date_range = st.date_input("Select Range", [date.today(), date.today()])
                if len(date_range) == 2:
                    start_dt, end_dt = date_range

        # --- 4. APPLY LOGIC ---
        filtered_df = df.copy()
        
        if selected_v != "All Vehicles":
            filtered_df = filtered_df[filtered_df['vehicle'] == selected_v]
            
        if date_mode == "Custom Range" and start_dt and end_dt:
            filtered_df = filtered_df[(filtered_df['date_out'] >= start_dt) & (filtered_df['date_out'] <= end_dt)]

        # --- 5. DISPLAY RESULTS ---
        total_income = filtered_df['income_display'].sum()
        st.metric(label=f"Total Income ({selected_v})", value=f"${total_income:,.2f}")
        
        # Display relevant columns only
        display_cols = ['date_out', 'vehicle', income_col, 'status']
        st.dataframe(
            filtered_df[display_cols], 
            use_container_width=True, 
            hide_index=True
        )

        st.download_button(
            "📥 Download CSV", 
            filtered_df.to_csv(index=False), 
            "income_report.csv", 
            "text/csv", 
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error loading income report: {e}")