import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from supabase import create_client
import urllib.parse

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or st.session_state.get('user_role') not in ['Admin', 'Manager']:
    st.error("Access Restricted: Financial & Customer Reports require Manager or Admin privileges.")
    st.stop()

# --- 2. CONNECTION ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Business Intelligence & Reports")

# Fetch Company Branding from Settings
branding_res = supabase.table("settings").select("*").execute()
branding = {item['config_key']: item['config_value'] for item in branding_res.data}
st.caption(f"📍 {branding.get('company_name', 'YOUR RENTAL & TOURS')}")

# --- 3. VISUAL REPORT NAVIGATION (Replacing Dropdown) ---
st.write("### Select a Report to Generate")

# Create a 3-column grid for the report buttons
col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

# Initialize report selection in session state if not present
if 'selected_report' not in st.session_state:
    st.session_state.selected_report = None

# Row 1
with col1:
    if st.button("💰\n\nRevenue &\nFinancials", use_container_width=True):
        st.session_state.selected_report = "Revenue"
with col2:
    if st.button("👥\n\nAll\nCustomers", use_container_width=True):
        st.session_state.selected_report = "Customers"
with col3:
    if st.button("🚗\n\nActive\nRentals", use_container_width=True):
        st.session_state.selected_report = "Active"

# Row 2
with col4:
    if st.button("⏳\n\nOverdue\nAudit", use_container_width=True):
        st.session_state.selected_report = "Overdue"
with col5:
    if st.button("⚠️\n\nCompliance\nRisk", use_container_width=True):
        st.session_state.selected_report = "Compliance"
with col6:
    if st.button("📄\n\nAgreement\nTemplate", use_container_width=True):
        st.session_state.selected_report = "Agreement"

st.divider()

# --- 4. DYNAMIC REPORT CONTENT ---
report_mode = st.session_state.selected_report

if not report_mode:
    st.info("Please click a button above to view a specific report.")

# Logic for Rental Agreement Template
elif report_mode == "Agreement":
    st.subheader("📄 Rental Agreement Template")
    try:
        rentals_query = supabase.table("rentals") \
            .select("id, date_out, fleet!fk_rentals_fleet(plate), customers!fk_rentals_customers(name)") \
            .order("date_out", desc=True).limit(20).execute()
        
        if rentals_query.data:
            options = {f"{r['date_out']} | {r['fleet']['plate']} | {r['customers']['name']}": r['id'] for r in rentals_query.data}
            selected_label = st.selectbox("Search Rental Record", options.keys())
            rental_id = options[selected_label]
            
            if st.button("View Agreement"):
                # ... [Existing logic to display agreement details, signature, and terms]
                st.success(f"Displaying Agreement for {selected_label}")
    except Exception as e:
        st.error(f"Error: {e}")

# Logic for Revenue Report
elif report_mode == "Revenue":
    st.subheader("💰 Revenue & Financial Performance")
    # ... [Existing revenue logic from original file]

# Logic for Compliance Risk
elif report_mode == "Compliance":
    st.subheader("⚠️ Compliance Risk Audit")
    # ... [Existing compliance logic from original file]

# Add a "Close Report" button at the bottom
if report_mode:
    st.write("---")
    if st.button("Close Report"):
        st.session_state.selected_report = None
        st.rerun()