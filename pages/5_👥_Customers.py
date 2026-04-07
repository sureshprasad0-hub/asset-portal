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

st.title("👥 Customer Compliance Registry")

# --- 3. ACTION: REGISTER NEW CUSTOMER ---
with st.expander("➕ Register New Customer (ID Verification Required)", expanded=False):
    with st.form("add_customer", clear_on_submit=True):
        st.subheader("Personal Details")
        full_name = st.text_input("Full Legal Name (as per ID)").strip()
        dob = st.date_input("Date of Birth", value=date(1995, 1, 1))
        
        col1, col2 = st.columns(2)
        email = col1.text_input("Email Address")
        phone = col2.text_input("Mobile Phone Number")
        address = st.text_area("Physical Address (for Billing/Legal)")

        st.divider()
        st.subheader("Driver's License Details")
        col3, col4 = st.columns(2)
        dl_no = col3.text_input("License Number").strip().upper()
        dl_expiry = col4.date_input("License Expiry Date")
        
        country = st.selectbox("Country/State of Issue", ["Fiji", "Australia", "New Zealand", "USA", "Other"])

        if st.form_submit_button("Verify & Register Customer", use_container_width=True):
            # LOGIC: Age Validation (Minimum 21)
            age = (date.today() - dob).days // 365
            
            if not full_name or not dl_no or not email:
                st.error("Full Name, License No, and Email are mandatory.")
            elif age < 21:
                st.error(f"Compliance Error: Customer is only {age} years old. Minimum requirement is 21.")
            elif dl_expiry < date.today():
                st.error("Compliance Error: Driver's License has expired.")
            else:
                try:
                    supabase.table("customers").insert({
                        "name": full_name,
                        "dob": str(dob),
                        "email": email,
                        "phone": phone,
                        "physical_address": address,
                        "dl_no": dl_no,
                        "dl_expiry": str(dl_expiry),
                        "country_of_issue": country
                    }).execute()
                    st.success(f"Customer {full_name} successfully verified and registered.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Registration Failed: {e}")

# --- 4. SEARCH & VIEW ---
st.divider()
search_query = st.text_input("🔍 Search Registry", placeholder="Search by name, email, or license number...")

c_res = supabase.table("customers").select("*").order("name").execute()

if c_res.data:
    df = pd.DataFrame(c_res.data)
    
    if search_query:
        df = df[
            df['name'].str.contains(search_query, case=False) | 
            df['dl_no'].str.contains(search_query, case=False) |
            df['email'].str.contains(search_query, case=False)
        ]

    if not df.empty:
        # We display the most critical info for the yard staff
        st.dataframe(
            df[['name', 'dl_no', 'dl_expiry', 'phone', 'email']], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Alert for expiring licenses
        today = str(date.today())
        expiring = df[df['dl_expiry'] <= today]
        if not expiring.empty:
            st.warning(f"⚠️ Notice: {len(expiring)} registered customers have expired licenses.")
    else:
        st.info("No matching customers found.")