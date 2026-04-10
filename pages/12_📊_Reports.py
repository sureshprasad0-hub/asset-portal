import streamlit as st
from supabase import create_client
# Import your modules
from modules import agreement_report 

# ... (Connection and Gatekeeper logic)

# 1. Initialize session state for report persistence
if 'selected_report' not in st.session_state:
    st.session_state.selected_report = None

# 2. Navigation Logic
if st.session_state.selected_report is None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄\n\nRental Agreement", use_container_width=True):
            st.session_state.selected_report = "Agreement"
            st.rerun()
else:
    if st.button("⬅️ Back to Reports"):
        st.session_state.selected_report = None
        st.session_state.view_agreement_id = None # Clear sub-state
        st.rerun()

# 3. Route to Module
if st.session_state.selected_report == "Agreement":
    agreement_report.show(supabase, branding)