import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from supabase import create_client

# --- 1. GATEKEEPER: ADMIN/MANAGER ONLY ---
if 'logged_in' not in st.session_state or st.session_state.get('user_role') not in ['Admin', 'Manager']:
    st.error("Access Restricted: Financial & Customer Reports require Manager or Admin privileges.")
    st.stop()

# --- 2. CONNECTION ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Business Intelligence & Reports")

# Fetch Company Branding for the Header
branding_res = supabase.table("settings").select("*").in_("config_key", ["company_name", "company_address", "company_phone", "company_email", "company_logo"]).execute()
branding = {item['config_key']: item['config_value'] for item in branding_res.data}
company_display = branding.get("company_name", "YOUR RENTAL & TOURS")
st.caption(f"📍 {company_display}")

# --- 3. REPORT SETTINGS ---
with st.expander("🛠️ Report Settings & Filters", expanded=True):
    report_mode = st.selectbox(
        "Select Report Category",
        [
            "💰 Revenue & Financials", 
            "👥 All Customers", 
            "🚗 Active Rental Customers", 
            "⏳ Overdue Rentals",
            "⚠️ Compliance Risk",
            "📄 Rental Agreement Template"
        ]
    )
st.divider()

def safe_date(date_val, default=date(1995, 1, 1)):
    if date_val is None or pd.isna(date_val) or str(date_val).strip() == "":
        return default
    try:
        return datetime.strptime(str(date_val), '%Y-%m-%d').date()
    except:
        return default

# --- 4. RENTAL AGREEMENT TEMPLATE ---
if report_mode == "📄 Rental Agreement Template":
    st.subheader("Generate Rental Out Report")
    
    try:
        rentals_query = supabase.table("rentals") \
            .select("id, date_out, fleet!fk_rentals_fleet(plate), customers!fk_rentals_customers(name)") \
            .order("date_out", desc=True) \
            .limit(50).execute()
        
        if rentals_query.data:
            options = {f"{r['date_out']} | {r['fleet']['plate']} | {r['customers']['name']}": r['id'] for r in rentals_query.data}
            selected_label = st.selectbox("Select Rental Record", options.keys())
            rental_id = options[selected_label]
            
            if st.button("Generate Full Page Report"):
                r_res = supabase.table("rentals") \
                    .select("*, fleet!fk_rentals_fleet(*), customers!fk_rentals_customers(*)") \
                    .eq("id", rental_id).single().execute()
                r = r_res.data
                
                with st.container(border=True):
                    h1, h2 = st.columns([1, 2])
                    with h1:
                        if branding.get("company_logo"):
                            st.image(branding.get("company_logo"), width=150)
                    with h2:
                        st.markdown(f"## {company_display}")
                        st.write(f"📍 {branding.get('company_address', 'Fiji')}")
                        st.write(f"📞 {branding.get('company_phone', '')} | ✉️ {branding.get('company_email', '')}")
                    
                    # FIXED: Changed unsafe_content_allowed to unsafe_allow_html
                    st.markdown("<h2 style='text-align: center;'>RENTAL AGREEMENT / VEHICLE OUT REPORT</h2>", unsafe_allow_html=True)
                    st.divider()
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 👤 CUSTOMER DETAILS")
                        st.write(f"**Name:** {r['customers']['name']}")
                        st.write(f"**License No:** {r['customers'].get('dl_no', 'N/A')}")
                    with c2:
                        st.markdown("### 🚙 VEHICLE DETAILS")
                        st.write(f"**Plate:** {r['fleet']['plate']}")
                        st.write(f"**Make/Model:** {r['fleet']['brand']} {r['fleet']['model']}")
                        st.write(f"**Odometer Out:** {r.get('odo_out', 0):,} km")

                    st.divider()
                    
                    st.markdown("### 📜 TERMS & CONDITIONS")
                    st.caption("1. Vehicle Usage: Hirer agrees to use vehicle solely for personal use. 2. Insurance: Hirer responsible for insurance excess. 3. Fuel: Return with same level as out. 4. Fines: Hirer responsible for all traffic violations.")
                    
                    st.divider()
                    
                    s1, s2 = st.columns(2)
                    with s1:
                        st.markdown("### ✍️ HIRER SIGNATURE")
                        sig_data = r.get('signature_url') or r.get('signature_data')
                        if sig_data:
                            st.image(sig_data, width=250)
                        else:
                            # FIXED: Changed unsafe_content_allowed to unsafe_allow_html
                            st.markdown("<br><br>__________________________", unsafe_allow_html=True)
                    with s2:
                        st.markdown("### 📝 REMARKS")
                        st.info(r.get('notes') or "No remarks.")
        else:
            st.info("No rental records found.")
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")

# --- 5. REVENUE & FINANCIALS ---
elif report_mode == "💰 Revenue & Financials":
    st.subheader("Revenue & Financial Performance")
    res = supabase.table("rentals").select("*, fleet!fk_rentals_fleet(plate, brand), customers!fk_rentals_customers(name)").execute()

    if res.data:
        df = pd.json_normalize(res.data)
        df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
        df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce').fillna(0)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Revenue", f"${df['total'].sum():,.2f}")
        m2.metric("VAT Collected", f"${df['tax_amount'].sum():,.2f}")
        m3.metric("Total Bookings", len(df))

        st.dataframe(df[['date_out', 'fleet!fk_rentals_fleet.plate', 'customers!fk_rentals_customers.name', 'total', 'status']], use_container_width=True, hide_index=True)

# --- 6. ALL CUSTOMERS ---
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

# --- 7. ACTIVE RENTAL CUSTOMERS ---
elif report_mode == "🚗 Active Rental Customers":
    st.subheader("Current Active Rentals")
    res = supabase.table("rentals").select("*, customers!fk_rentals_customers(name, phone), fleet!fk_rentals_fleet(plate, model)").execute()
    
    if res.data:
        df_active = pd.json_normalize(res.data)
        active_list = df_active[df_active['status'].isin(['Active', 'Out'])]
        
        if not active_list.empty:
            st.dataframe(active_list[['customers!fk_rentals_customers.name', 'customers!fk_rentals_customers.phone', 'fleet!fk_rentals_fleet.plate', 'date_out', 'total']], use_container_width=True, hide_index=True)
        else:
            st.info("There are no active rentals currently out.")
    else:
        st.info("No rental records found to analyze.")

# --- 8. OVERDUE RENTALS ---
elif report_mode == "⏳ Overdue Rentals":
    st.subheader("Overdue & Delinquent Audit")
    res = supabase.table("rentals").select("*, customers!fk_rentals_customers(name, phone), fleet!fk_rentals_fleet(plate)").execute()
    
    if res.data:
        df_overdue = pd.json_normalize(res.data)
        active_items = df_overdue[df_overdue['status'].isin(['Active', 'Out'])]
        
        if not active_items.empty:
            st.warning("Review these active contracts for return-date compliance.")
            st.dataframe(active_items[['customers!fk_rentals_customers.name', 'fleet!fk_rentals_fleet.plate', 'date_out', 'total']], use_container_width=True, hide_index=True)
        else:
            st.success("No active rentals found to review.")
    else:
        st.info("No rental history found to check for overdue items.")

# --- 9. COMPLIANCE RISK (EXPIRED IDs) ---
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