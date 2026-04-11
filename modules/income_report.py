import streamlit as st
import pandas as pd
from datetime import date

def show(supabase):
    st.subheader("💵 Detailed Rental Income Report")

    try:
        # 1. FETCH DATA
        # Fetching rentals with vehicle plate info
        res = supabase.table("rentals").select(
            "id, date_out, total_amount, status, fleet!fk_rentals_fleet(plate)"
        ).execute()
        
        if not res.data:
            st.info("No rental income records found.")
            return

        df = pd.DataFrame(res.data)
        # Flatten the nested fleet plate data
        df['vehicle'] = df['fleet'].apply(lambda x: x['plate'] if x else "N/A")
        df['date_out'] = pd.to_datetime(df['date_out']).dt.date

        # --- 2. FILTERS ---
        c1, c2 = st.columns(2)
        
        with c1:
            # Vehicle Filter
            vehicle_list = ["All Vehicles"] + sorted(df['vehicle'].unique().tolist())
            selected_v = st.selectbox("Select Vehicle", vehicle_list)
        
        with c2:
            # Date Filter Type
            date_mode = st.radio("Date Range", ["All Dates", "Custom Range"], horizontal=True)
            
            start_dt, end_dt = None, None
            if date_mode == "Custom Range":
                date_range = st.date_input("Select Range", [date.today(), date.today()])
                if len(date_range) == 2:
                    start_dt, end_dt = date_range

        # --- 3. APPLY LOGIC ---
        filtered_df = df.copy()
        
        if selected_v != "All Vehicles":
            filtered_df = filtered_df[filtered_df['vehicle'] == selected_v]
            
        if date_mode == "Custom Range" and start_dt and end_dt:
            filtered_df = filtered_df[(filtered_df['date_out'] >= start_dt) & (filtered_df['date_out'] <= end_dt)]

        # --- 4. DISPLAY RESULTS ---
        total_income = filtered_df['total_amount'].sum()
        st.metric(label=f"Total Income ({selected_v})", value=f"${total_income:,.2f}")
        
        st.dataframe(
            filtered_df[['date_out', 'vehicle', 'total_amount', 'status']], 
            use_container_width=True, 
            hide_index=True
        )

        # Export option
        st.download_button(
            "📥 Download CSV", 
            filtered_df.to_csv(index=False), 
            "income_report.csv", 
            "text/csv", 
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error loading income report: {e}")