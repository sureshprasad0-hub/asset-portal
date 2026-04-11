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
        revenue_map = {
            'daily_rate': 'Rental Rate',
            'insurance_fee': 'Insurance',
            'delivery_fee': 'Delivery/Collection',
            'bond_amount': 'Security Bond',
            'tax_amount': 'Tax/VAT',
            'extra_charges': 'Extras'
        }
        
        # Identify existing revenue columns
        available_revenue_cols = [col for col in revenue_map.keys() if col in df.columns]
        
        # Process numeric data and create a reliable Total
        for col in available_revenue_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # CRITICAL FIX: Manually calculate the true total to avoid tax-only errors
        df['calculated_total'] = df[available_revenue_cols].sum(axis=1)

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
        
        m1, m2 = st.columns([1, 2])
        
        with m1:
            # Display the calculated total instead of the database column
            overall_total = filtered_df['calculated_total'].sum()
            st.metric(label=f"Total Gross Revenue ({selected_v})", value=f"${overall_total:,.2f}")

        with m2:
            # Generate summary by type
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
        # Include the calculated total in the view
        display_cols = ['date_out', 'vehicle'] + available_revenue_cols + ['calculated_total']
        
        # Rename 'calculated_total' for the user display
        final_table = filtered_df[display_cols].rename(columns={'calculated_total': 'Total Income'})
        st.dataframe(final_table, use_container_width=True, hide_index=True)

        st.download_button(
            "📥 Download Full Breakdown CSV", 
            filtered_df.to_csv(index=False), 
            "detailed_income_report.csv", 
            "text/csv", 
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Error loading income report: {e}")