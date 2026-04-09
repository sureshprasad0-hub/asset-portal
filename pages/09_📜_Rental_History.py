import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. GATEKEEPER & CONNECTION ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("📜 Rental History")
st.caption("Completed and past rental records.")

# Fetch Company Name for the Header
c_res_settings = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res_settings.data[0]['config_value'] if c_res_settings.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 2. SEARCH & FILTERS ---
search = st.text_input("🔍 Search by Number Plate or Customer Name", placeholder="e.g. JL 101").strip().lower()

# --- 3. FETCH COMPLETED RECORDS ---
try:
    # FIXED: Changed ordering from 'created_at' to 'date_out' 
    # to resolve the 'column does not exist' error.
    hist_res = supabase.table("rentals") \
        .select("*, fleet!fk_rentals_fleet(plate, model, brand), customers!fk_rentals_customers(name)") \
        .eq("status", "Completed") \
        .order("date_out", desc=True) \
        .execute()

    if hist_res.data:
        # Filter logic
        filtered_data = [
            h for h in hist_res.data 
            if search in h['fleet']['plate'].lower() or search in h['customers']['name'].lower()
        ]

        if filtered_data:
            for h in filtered_data:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
                    
                    fleet_info = h.get('fleet', {})
                    cust_info = h.get('customers', {})
                    
                    c1.write(f"🚗 **{fleet_info.get('plate', 'N/A')}**")
                    c1.caption(f"{fleet_info.get('brand', '')} {fleet_info.get('model', '')}")
                    
                    c2.write(f"👤 **{cust_info.get('name', 'N/A')}**")
                    # Using get() for date_returned as it might be null
                    c2.caption(f"Check-in: {h.get('date_returned', 'N/A')}")
                    
                    c3.write(f"💵 **${float(h.get('total') or 0):,.2f}**")
                    c3.caption(f"Status: {h['status']}")
                    
                    # Detailed View
                    if c4.button("View", key=f"hist_{h['id']}"):
                        st.json(h)
        else:
            st.info("No matching records found.")
    else:
        st.info("No completed rentals in the database.")
        
except Exception as e:
    st.error("Could not load history.")
    with st.expander("Show Error Details"):
        st.code(str(e))