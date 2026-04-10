import streamlit as st
from supabase import create_client
# Import the modular reports
from modules import agreement_report, financial_report 

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or st.session_state.get('user_role') not in ['Admin', 'Manager']:
    st.error("Access Restricted.")
    st.stop()

# --- 2. INITIALIZATION (Must happen before calling modules) ---
# Define supabase globally within this script so modules can receive it
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Fetch Branding details
branding_res = supabase.table("settings").select("*").execute()
branding = {item['config_key']: item['config_value'] for item in branding_res.data}

st.title("📊 Business Intelligence & Reports")

# --- 3. NAVIGATION ---
if 'selected_report' not in st.session_state:
    st.session_state.selected_report = None

if st.session_state.selected_report is None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄\n\nRental Agreement", use_container_width=True):
            st.session_state.selected_report = "Agreement"
            st.rerun()
    with col2:
        if st.button("💰\n\nFinancials", use_container_width=True):
            st.session_state.selected_report = "Financials"
            st.rerun()
else:
    if st.button("⬅️ Back to Menu"):
        st.session_state.selected_report = None
        st.session_state.view_agreement_id = None
        st.rerun()

# --- 4. MODULE EXECUTION ---
# Now 'supabase' and 'branding' are guaranteed to exist
if st.session_state.selected_report == "Agreement":
    agreement_report.show(supabase, branding)
elif st.session_state.selected_report == "Financials":
    financial_report.show(supabase)