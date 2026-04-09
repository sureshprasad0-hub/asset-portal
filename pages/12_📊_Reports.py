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
            "📄 Rental Agreement Template" # NEW CATEGORY
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

# --- [CATEGORIES 4-8 REMAIN UNCHANGED IN YOUR ORIGINAL FILE] ---
# (Logic for Revenue, Customers, Active, Overdue, and Compliance Risk stays intact)

# --- 9. RENTAL AGREEMENT TEMPLATE (NEW) ---
if report_mode == "📄 Rental Agreement Template":
    st.subheader("Generate Rental Out Report")
    
    # Selection logic to pick a specific rental to generate a report for
    rentals_query = supabase.table("rentals").select("id, date_out, fleet(plate), customers(name)").order("date_out", desc=True).limit(50).execute()
    
    if rentals_query.data:
        options = {f"{r['date_out']} | {r['fleet']['plate']} | {r['customers']['name']}": r['id'] for r in rentals_query.data}
        selected_label = st.selectbox("Select Rental Record to View Report", options.keys())
        rental_id = options[selected_label]
        
        if st.button("Generate Full Page Report"):
            # Fetch full details for the specific rental
            r = supabase.table("rentals").select("*, fleet(*), customers(*)").eq("id", rental_id).single().execute().data
            
            # --- START OF FULL PAGE TEMPLATE ---
            st.container(border=True)
            with st.container():
                # Header with Logo and Branding
                h1, h2 = st.columns([1, 2])
                with h1:
                    if branding.get("company_logo"):
                        st.image(branding.get("company_logo"), width=150)
                with h2:
                    st.markdown(f"## {company_display}")
                    st.write(f"📍 {branding.get('company_address', 'Fiji')}")
                    st.write(f"📞 {branding.get('company_phone', '')} | ✉️ {branding.get('company_email', '')}")
                
                st.markdown("<h1 style='text-align: center;'>RENTAL AGREEMENT / VEHICLE OUT REPORT</h1>", unsafe_content_allowed=True)
                st.divider()
                
                # Customer & Vehicle Details
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("### 👤 CUSTOMER DETAILS")
                    st.write(f"**Name:** {r['customers']['name']}")
                    st.write(f"**License No:** {r['customers'].get('dl_no', 'N/A')}")
                    st.write(f"**Contact:** {r['customers'].get('phone', 'N/A')}")
                with c2:
                    st.markdown("### 🚙 VEHICLE DETAILS")
                    st.write(f"**Plate:** {r['fleet']['plate']}")
                    st.write(f"**Make/Model:** {r['fleet']['brand']} {r['fleet']['model']}")
                    st.write(f"**Odometer Out:** {r.get('odo_out', 0):,} km")

                st.divider()
                
                # Financials & Rental Period
                f1, f2 = st.columns(2)
                with f1:
                    st.markdown("### ⏳ RENTAL PERIOD")
                    st.write(f"**Date Out:** {r.get('date_out')}")
                    st.write(f"**Expected In:** {r.get('date_in')}")
                    st.write(f"**Fuel Level Out:** {r.get('fuel_out', 'N/A')}")
                with f2:
                    st.markdown("### 💰 FINANCIAL SUMMARY")
                    st.write(f"**Daily Rate:** ${float(r.get('rate', 0)):,.2f}")
                    st.write(f"**Bond/Deposit:** ${float(r.get('bond', 0)):,.2f}")
                    st.write(f"**Total Estimated:** ${float(r.get('total', 0)):,.2f}")

                st.divider()
                
                # Disclaimer Section
                st.markdown("### 📜 TERMS & CONDITIONS")
                st.caption("""
                1. **Vehicle Usage:** The hirer agrees to use the vehicle solely for personal use and not for hire, racing, or illegal activities.
                2. **Insurance:** The vehicle is covered by third-party insurance. In the event of an accident, the hirer is responsible for the insurance excess as specified.
                3. **Fuel:** The vehicle must be returned with the same level of fuel as recorded at the time of check-out. A surcharge may apply for refueling.
                4. **Traffic Violations:** All traffic fines, parking tickets, and tolls incurred during the rental period are the sole responsibility of the hirer.
                5. **Cleanliness:** A cleaning fee may be charged if the vehicle is returned in an excessively dirty condition.
                """)
                
                st.divider()
                
                # Signature Section
                s1, s2 = st.columns(2)
                with s1:
                    st.markdown("### ✍️ HIRER SIGNATURE")
                    sig_data = r.get('signature_url') or r.get('signature_data')
                    if sig_data:
                        st.image(sig_data, width=300)
                    else:
                        st.markdown("<br><br>__________________________", unsafe_content_allowed=True)
                        st.caption("Authorized Signature Required")
                with s2:
                    st.markdown("### 📝 AGENT REMARKS")
                    st.info(r.get('notes') or "No additional remarks recorded.")
            
            # Print Helper
            st.button("🖨️ Print Report", on_click=lambda: st.write("Tip: Use Browser Print (Ctrl+P) to save as PDF"))
    else:
        st.info("No rental records found to generate reports.")

# --- REST OF ORIGINAL CATEGORIES ---
elif report_mode == "💰 Revenue & Financials":
    # ... [Existing code for Revenue] ...
    pass
elif report_mode == "👥 All Customers":
    # ... [Existing code for Customers] ...
    pass
# ... (and so on)