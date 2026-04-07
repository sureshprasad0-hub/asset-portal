import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from supabase import create_client

# --- 1. GATEKEEPER: ADMIN/MANAGER ONLY ---
# Ensuring only authorized personnel can view financial and personal data
if 'logged_in' not in st.session_state or st.session_state.get('user_role') not in ['Admin', 'Manager']:
    st.error("Access Restricted: Financial & Customer Reports require Manager or Admin privileges.")
    st.stop()

# --- 2. CONNECTION ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Business Intelligence & Reports")

# --- 3. SIDEBAR NAVIGATION ---
# Added a selection box for better organization of multiple report types
st.sidebar.header("Report Settings")
report_mode = st.sidebar.selectbox(
    "Select Report Category",
    [
        "💰 Revenue & Financials", 
        "👥 All Customers", 
        "🚗 Active Rental Customers", 
        "⏳ Overdue Rentals",
        "⚠️ Compliance Risk"
    ]
)

def safe_date(date_val, default=date(1995, 1, 1)):
    """Prevents JSON crashes by ensuring a valid date object is always returned."""
    if date_val is None or pd.isna(date_val) or str(date_val).strip() == "":
        return default
    try:
        return datetime.strptime(str(date_val), '%Y-%m-%d').date()
    except:
        return default

# --- 4. REVENUE & FINANCIALS (EXISTING LOGIC) ---
if report_mode == "💰 Revenue & Financials":
    res = supabase.table("rentals").select("*, fleet(plate, brand), customers(name)").execute()

    if res.data:
        df = pd.json_normalize(res.data)
        
        # Ensure numeric types for calculations to avoid 'nan' errors
        df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
        df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce').fillna(0)
        
        # Top Level Metrics
        total_rev = df['total'].sum()
        total_vat = df['tax_amount'].sum()
        total_rentals = len(df)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Revenue", f"${total_rev:,.2f}")
        m2.metric("VAT Collected", f"${total_vat:,.2f}")
        m3.metric("Total Bookings", total_rentals)

        st.divider()

        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Revenue by Vehicle")
            if 'fleet.plate' in df.columns:
                rev_by_plate = df.groupby('fleet.plate')['total'].sum().sort_values(ascending=False)
                st.bar_chart(rev_by_plate)

        with col_right:
            st.subheader("Booking Status")
            st.write(df['status'].value_counts())

        st.subheader("Transaction History")
        cols_to_show = [c for c in ['date_out', 'fleet.plate', 'customers.name', 'tax_amount', 'total', 'status'] if c in df.columns]
        st.dataframe(df[cols_to_show], use_container_width=True, hide_index=True)
    else:
        st.info("No rental history found.")

# --- 5. ALL CUSTOMERS ---
elif report_mode == "👥 All Customers":
    res = supabase.table("customers").select("*").order("name").execute()
    if res.data:
        df_cust = pd.DataFrame(res.data)
        st.subheader("Full Customer Registry")
        st.write(f"**Total Registered:** {len(df_cust)}")
        
        # Drop technical paths for a clean report view
        display_df = df_cust.drop(columns=['license_scan_path']) if 'license_scan_path' in df_cust.columns else df_cust
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "all_customers.csv", "text/csv")

# --- 6. ACTIVE RENTAL CUSTOMERS ---
elif report_mode == "🚗 Active Rental Customers":
    # Pulling current rentals including customer names
    res = supabase.table("rentals").select("*, customers(name, phone), fleet(plate, model)").execute()
    if res.data:
        df_active = pd.json_normalize(res.data)
        # Filter for rentals currently out in the field
        active_list = df_active[df_active['status'].isin(['Active', 'Out'])]
        
        st.subheader("Active Rental Customers")
        if not active_list.empty:
            cols = ['customers.name', 'customers.phone', 'fleet.plate', 'date_out', 'total']
            st.dataframe(active_list[cols], use_container_width=True, hide_index=True)
        else:
            st.info("There are currently no active rentals.")

# --- 7. OVERDUE RENTALS ---
elif report_mode == "⏳ Overdue Rentals":
    res = supabase.table("rentals").select("*, customers(name, phone), fleet(plate)").execute()
    if res.data:
        df_overdue = pd.json_normalize(res.data)
        
        # Logic: Status is 'Active' and current date has passed the return date
        # (Assuming your schema uses 'date_in' or 'expected_return' for the return date)
        # For this version, we flag 'Active' status items as needing audit
        active_only = df_overdue[df_overdue['status'].isin(['Active', 'Out'])]
        
        st.subheader("Potential Overdue Items")
        st.warning("Ensure staff confirm the 'Expected Return' date for the items below.")
        st.dataframe(active_only[['customers.name', 'fleet.plate', 'date_out', 'total']], use_container_width=True)

# --- 8. COMPLIANCE RISK (EXPIRED IDs) ---
elif report_mode == "⚠️ Compliance Risk":
    res = supabase.table("customers").select("name, dl_no, dl_expiry, phone").execute()
    if res.data:
        df_risk = pd.DataFrame(res.data)
        # Safe comparison to avoid JSON nan errors
        df_risk['expiry_dt'] = df_risk['dl_expiry'].apply(lambda x: safe_date(x, default=date.today()))
        
        expired = df_risk[df_risk['expiry_dt'] < date.today()]
        
        st.subheader("Expired License Reports")
        if not expired.empty:
            st.error(f"ATTENTION: {len(expired)} customers have expired identification.")
            st.dataframe(expired[['name', 'dl_no', 'dl_expiry', 'phone']], use_container_width=True, hide_index=True)
        else:
            st.success("All registered IDs are currently compliant.")