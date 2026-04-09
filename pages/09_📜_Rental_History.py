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
c_res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res.data[0]['config_value'] if c_res.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 2. SEARCH & FILTERS ---
search = st.text_input("🔍 Search by Number Plate or Customer Name", placeholder="e.g. JL 101").strip().lower()

# --- 3. FETCH COMPLETED RECORDS ---
try:
    hist_res = supabase.table("rentals") \
        .select("*, fleet(plate, model, brand), customers(name)") \
        .eq("status", "Completed") \
        .order("created_at", desc=True) \
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
                    
                    c1.write(f"🏁 **{h['fleet']['plate']}**")
                    c1.caption(f"{h['fleet']['brand']} {h['fleet']['model']}")
                    
                    c2.write(f"👤 **{h['customers']['name']}**")
                    c2.caption(f"Check-in: {h.get('date_returned', 'N/A')}")
                    
                    c3.write(f"💵 **${float(h['total']):,.2f}**")
                    c3.caption(f"Status: {h['status']}")
                    
                    # Detailed View
                    if c4.button("View", key=f"hist_{h['id']}"):
                        st.json(h)
        else:
            st.info("No matching records found.")
    else:
        st.info("No completed rentals in the database.")
        
except Exception as e:
    st.error(f"Could not load history. Ensure SQL foreign keys are set. Error: {e}")