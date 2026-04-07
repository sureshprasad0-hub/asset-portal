import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from supabase import create_client

# --- 1. GATEKEEPER: ADMIN/MANAGER ONLY ---
# Restricting access to sensitive financial and customer data
if 'logged_in' not in st.session_state or st.session_state.get('user_role') not in ['Admin', 'Manager']:
    st.error("Access Restricted: Financial & Customer Reports require Manager or Admin privileges.")
    st.stop()

# --- 2. CONNECTION ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Business Intelligence & Reports")

# --- 3. REPORT SETTINGS (MAIN TAB AREA) ---
# Moved from sidebar to the main page as requested
with st.expander("🛠️ Report Settings & Filters", expanded=True):
    report_mode = st.selectbox(
        "Select Report Category",
        [
            "💰 Revenue & Financials", 
            "👥 All Customers", 
            "🚗 Active Rental Customers", 
            "⏳ Overdue Rentals",
            "⚠️ Compliance Risk"
        ]
    )
st.divider()

def safe_date(date_val, default=date(1995, 1, 1)):
    """Prevents JSON crashes by ensuring a valid date object is always returned."""
    if date_val is None or pd.isna(date_val) or str(date_val).strip() == "":
        return default
    try:
        return datetime.strptime(str(date_val), '%Y-%m-%d').date()
    except:
        return default

# --- 4. REVENUE & FINANCIALS ---
if report_mode == "💰 Revenue & Financials":
    st.subheader("Revenue & Financial Performance")
    res = supabase.table("rentals").select("*, fleet(plate, brand), customers(name)").execute()

    if res.data:
        df = pd.json_normalize(res.data)
        df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
        df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce').fillna(0)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Revenue", f"${df['total'].sum():,.2f}")
        m2.metric("VAT Collected", f"${df['tax_amount'].sum():,.2f}")
        m3.metric("Total Bookings", len(df))

        col_l, col_r = st.columns(2)
        with col_l:
            st.caption("Revenue by Vehicle")
            st.bar_chart(df.groupby('fleet.plate')['total'].sum())
        with col_r:
            st.caption("Booking Status")
            st.write(df['status'].value_counts())

        st.dataframe(df[['date_out', 'fleet.plate', 'customers.name', 'total', 'status']], use_container_width=True, hide_index=True)
    else:
        st.info("No financial transactions found in the database.")

# --- 5. ALL CUSTOMERS ---
elif report_mode == "👥 All Customers":
    st.subheader("Complete Customer Registry")
    res = supabase.table("customers").select("*").order("name").execute()
    
    if res.data:
        df_cust = pd.DataFrame(res.data)
        display_df = df_cust.drop(columns=['license_scan_path']) if 'license_scan_path' in df_cust.columns else df_cust
        st.write(f"**Total Registered:** {len(display_df)}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "all_customers.csv", "text/csv")
    else:
        st.info("The customer registry is currently empty.")

# --- 6. ACTIVE RENTAL CUSTOMERS ---
elif report_mode == "🚗 Active Rental Customers":
    st.subheader("Current Active Rentals")
    res = supabase.table("rentals").select("*, customers(name, phone), fleet(plate, model)").execute()
    
    if res.data:
        df_active = pd.json_normalize(res.data)
        active_list = df_active[df_active['status'].isin(['Active', 'Out'])]
        
        if not active_list.empty:
            st.dataframe(active_list[['customers.name', 'customers.phone', 'fleet.plate', 'date_out', 'total']], use_container_width=True, hide_index=True)
        else:
            st.info("There are no active rentals currently out.")
    else:
        st.info("No rental records found to analyze.")

# --- 7. OVERDUE RENTALS ---
elif report_mode == "⏳ Overdue Rentals":
    st.subheader("Overdue & Delinquent Audit")
    res = supabase.table("rentals").select("*, customers(name, phone), fleet(plate)").execute()
    
    if res.data:
        df_overdue = pd.json_normalize(res.data)
        # Segments active items for manual audit
        active_items = df_overdue[df_overdue['status'].isin(['Active', 'Out'])]
        
        if not active_items.empty:
            st.warning("Review these active contracts for return-date compliance.")
            st.dataframe(active_items[['customers.name', 'fleet.plate', 'date_out', 'total']], use_container_width=True, hide_index=True)
        else:
            st.success("No active rentals found to review.")
    else:
        st.info("No rental history found to check for overdue items.")

# --- 8. COMPLIANCE RISK (EXPIRED IDs) ---
elif report_mode == "⚠️ Compliance Risk":
    st.subheader("Customer ID Compliance Audit")
    res = supabase.table("customers").select("name, dl_no, dl_expiry, phone").execute()
    
    if res.data:
        df_risk = pd.DataFrame(res.data)
        df_risk['expiry_dt'] = df_risk['dl_expiry'].apply(lambda x: safe_date(x, default=date.today()))
        expired = df_risk[df_risk['expiry_dt'] < date.today()]
        
        if not expired.empty:
            st.error(f"Alert: {len(expired)} customers have expired licenses.")
            st.dataframe(expired[['name', 'dl_no', 'dl_expiry', 'phone']], use_container_width=True, hide_index=True)
        else:
            st.success("All customer IDs in the system are currently valid and compliant.")
    else:
        st.info("No customer data available for compliance check.")