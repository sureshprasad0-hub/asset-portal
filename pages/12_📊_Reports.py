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

# Fetch Company Branding & Terms for the Header
# Updated query to include 'rental_terms' (Standard Terms & Conditions)
branding_res = supabase.table("settings").select("*").in_("config_key", [
    "company_name", "company_address", "company_phone", "company_email", "company_logo", "rental_terms"
]).execute()
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
                    
                    # UPDATED: Pulling dynamic terms from Settings table
                    st.markdown("### 📜 TERMS & CONDITIONS")
                    terms_text = branding.get("rental_terms", "Standard terms and conditions apply. Contact administration for details.")
                    st.caption(terms_text)
                    
                    st.divider()
                    
                    s1, s2 = st.columns(2)
                    with s1:
                        st.markdown("### ✍️ HIRER SIGNATURE")
                        sig_data = r.get('signature_url') or r.get('signature_data')
                        if sig_data:
                            st.image(sig_data, width=250)
                        else:
                            st.markdown("<br><br>__________________________", unsafe_allow_html=True)
                    with s2:
                        st.markdown("### 📝 REMARKS")
                        st.info(r.get('notes') or "No remarks.")
        else:
            st.info("No rental records found.")
    except Exception as e:
        st.error(f"Data Fetch Error: {e}")

# ... (Keep all other report modes: Revenue, Customers, etc. as per original file)