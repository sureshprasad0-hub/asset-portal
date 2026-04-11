import streamlit as st
from supabase import create_client
# Import the modular reports
from modules import agreement_report, financial_report, customer_report, fleet_report 

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or st.session_state.get('user_role') not in ['Admin', 'Manager']:
    st.error("Access Restricted: Financial & Customer Reports require Manager or Admin privileges.")
    st.stop()

# --- 2. INITIALIZATION ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
branding_res = supabase.table("settings").select("*").execute()
branding = {item['config_key']: item['config_value'] for item in branding_res.data}

st.title("📊 Business Intelligence & Reports")
st.caption(f"📍 {branding.get('company_name', 'YOUR RENTAL & TOURS')}")

# --- 3. VISUAL NAVIGATION ---
if 'selected_report' not in st.session_state:
    st.session_state.selected_report = None

if st.session_state.selected_report is None:
    st.write("### Select a Report to Generate")
    
    col1, col2, col3, col4 = st.columns(4) # Added a 4th column
    
    with col1:
        if st.button("💰\n\nRevenue &\nFinancials", use_container_width=True):
            st.session_state.selected_report = "Financials"
            st.rerun()
    with col2:
        if st.button("👥\n\nAll\nCustomers", use_container_width=True):
            st.session_state.selected_report = "Customers"
            st.rerun()
    with col3:
        if st.button("📄\n\nAgreement\nTemplate", use_container_width=True):
            st.session_state.selected_report = "Agreement"
            st.rerun()
    with col4:
        # NEW BUTTON: Fleet Inventory Report
        if st.button("🚗\n\nFleet\nInventory", use_container_width=True):
            st.session_state.selected_report = "Fleet"
            st.rerun()
else:
    if st.button("⬅️ Back To Reports Menu"):
        st.session_state.selected_report = None
        st.session_state.view_agreement_id = None 
        st.rerun()

st.divider()

# --- 4. DYNAMIC MODULE LOADING ---
if st.session_state.selected_report == "Financials":
    financial_report.show(supabase)
elif st.session_state.selected_report == "Customers":
    customer_report.show(supabase)
elif st.session_state.selected_report == "Agreement":
    agreement_report.show(supabase, branding)
elif st.session_state.selected_report == "Fleet":
    # Call the new fleet report module
    fleet_report.show(supabase)