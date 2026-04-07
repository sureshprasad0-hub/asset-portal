import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("👥 Customer Information")

# --- 3. ACTION: REGISTER & VERIFY ---
# Note: clear_on_submit is now FALSE so data stays if there is an error
with st.expander("➕ Register New Customer (ID Verification)", expanded=True):
    with st.form("add_customer", clear_on_submit=False):
        st.subheader("Personal Details")
        full_name = st.text_input("Full Legal Name (as per Government ID)").strip()
        dob = st.date_input("Date of Birth", value=date(1995, 1, 1))
        
        col1, col2 = st.columns(2)
        email = col1.text_input("Verified Email Address")
        phone = col2.text_input("Mobile Phone Number")
        address = st.text_area("Physical Address (Billing/Legal Notices)")

        st.divider()
        st.subheader("Driver's License Compliance")
        col3, col4 = st.columns(2)
        dl_no = col3.text_input("License Number").strip().upper()
        dl_expiry = col4.date_input("License Expiry Date")
        
        country = st.selectbox("Country/State of Issue", ["Fiji", "Australia", "New Zealand", "USA", "Other"])
        license_file = st.file_uploader("Upload ID/License Scan", type=['png', 'jpg', 'jpeg', 'pdf'])

        if st.form_submit_button("Verify & Save Customer", use_container_width=True):
            # Compliance Logic
            age = (date.today() - dob).days // 365
            
            if not full_name or not dl_no or not email:
                st.error("Missing required fields: Name, License No, or Email.")
            elif age < 21:
                st.error(f"Compliance Violation: Customer age ({age}) is below the minimum requirement of 21.")
            elif dl_expiry < date.today():
                # DATA PERSISTENCE: Because clear_on_submit=False, 
                # the user can now just change this date and click save again.
                st.error("Compliance Violation: The Driver's License has expired. Please update the date if this was a typo.")
            else:
                try:
                    file_path = None
                    if license_file:
                        file_ext = license_file.name.split('.')[-1]
                        file_path = f"licenses/{dl_no}_{datetime.now().strftime('%Y%m%d')}.{file_ext}"
                        supabase.storage.from_("license-docs").upload(file_path, license_file.getvalue())

                    # Insert Record
                    supabase.table("customers").insert({
                        "name": full_name,
                        "dob": str(dob),
                        "email": email,
                        "phone": phone,
                        "physical_address": address,
                        "dl_no": dl_no,
                        "dl_expiry": str(dl_expiry),
                        "country_of_issue": country,
                        "license_scan_path": file_path
                    }).execute()
                    
                    st.success(f"Customer {full_name} successfully verified.")
                    # Only rerun (and thus clear the form) on SUCCESS
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")

# --- 4. CUSTOMER SEARCH & AUDIT ---
st.divider()
# ... (Search logic remains the same as previous version)