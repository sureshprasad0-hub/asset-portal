import streamlit as st
import pandas as pd
from datetime import date

def show(supabase):
    st.subheader("💵 Detailed Rental Income Report")

    try:
        # 1. FETCH DATA
        res = supabase.table("rentals").select(
            "*, fleet!fk_rentals_fleet(plate)"
        ).execute()
        
        if not res.data:
            st.info("No rental income records found.")
            return

        df = pd.DataFrame(res.data)
        
        # --- 2. DEFINE REVENUE TYPES ---
        # Identify all potential revenue columns in your rentals table
        revenue_map = {
            'daily_rate': 'Rental Rate',
            'insurance_fee': 'Insurance',
            'delivery_fee': 'Delivery/Collection',
            'bond_amount': 'Security Bond',
            'tax_amount': 'Tax/VAT',
            'extra_charges': 'Extras'
        }
        
        # Find which of these exist in your actual database schema
        available_revenue_cols = [col for col in revenue_map.keys() if col in df.columns]
        
        # Identify the primary total column
        possible_totals = ['total_amount', 'amount', 'grand_total']
        total_col = next((col for col in possible_totals if col in df.columns), None)

        # Process and clean numeric data
        for col in available_revenue_cols + ([total_col] if total_col else []):
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Flatten vehicle data and format dates
        df['vehicle'] = df['fleet'].apply(lambda x: x['plate'] if isinstance(x, dict) else "N/A")
        df['date_out'] = pd.to_datetime(df['date_out']).dt.date

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

        # --- 4. APPLY FILTER LOGIC ---
        filtered_df = df.copy()
        if selected_v != "All Vehicles":
            filtered_df = filtered_df[filtered_df['vehicle'] == selected_v]
        if date_mode == "Custom Range" and start_dt and end_dt:
            filtered_df = filtered_df[(filtered_df['date_out'] >= start_dt) & (filtered_df['date_out'] <= end_dt)]

        # --- 5. REVENUE BREAKDOWN DISPLAY ---
        st.write("### 📈 Revenue Breakdown")
        
        # Create columns for the total metric and the breakdown table
        m1, m2 = st.columns([1, 2])
        
        with m1:
            overall_total = filtered_df[total_col].sum() if total_col else filtered_df[available_revenue_cols].sum().sum()
            st.metric(label="Total Gross Revenue", value=f"${overall_total:,.2f}")

        with m2:
            # Generate a summary of income by type
            breakdown_data = []
            for col in available_revenue_cols:
                breakdown_data.append({
                    "Revenue Type": revenue_map[col],
                    "Total Amount": filtered_df[col].sum()
                })
            
            breakdown_df = pd.DataFrame(breakdown_data)
            st.table(breakdown_df.set_index("Revenue Type").style.format("${:,.2f}"))

        # --- 6. DETAILED DATA TABLE ---
        st.write("### Transaction Details")
        display_cols = ['date_out', 'vehicle'] + available_revenue_cols + ([total_col] if total_col else [])
        st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

        st.download_button(
            "📥 Download Full Breakdown CSV", 
            filtered_df.to_csv(index=False), 
            "detailed_income_report.csv", 
            "text/csv", 
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error loading income report: {e}")