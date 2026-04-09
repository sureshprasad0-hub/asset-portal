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
    hist_res = supabase.table("rentals") \
        .select("*, fleet!fk_rentals_fleet(plate, model, brand), customers!fk_rentals_customers(name)") \
        .eq("status", "Completed") \
        .order("date_out", desc=True) \
        .execute()

    if hist_res.data:
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
                    c2.caption(f"Checked in: {h.get('return_date_actual', 'N/A')}")
                    
                    c3.write(f"💵 **${float(h.get('total') or 0):,.2f}**")
                    c3.caption(f"Status: {h['status']}")
                    
                    # --- IMPROVED DETAILED VIEW ---
                    if c4.button("View", key=f"hist_{h['id']}"):
                        with st.expander("📄 Full Rental Details", expanded=True):
                            v1, v2 = st.columns(2)
                            with v1:
                                st.markdown(f"**Vehicle:** {fleet_info.get('brand')} {fleet_info.get('model')} ({fleet_info.get('plate')})")
                                st.markdown(f"**Customer:** {cust_info.get('name')}")
                                st.markdown(f"**Period:** {h.get('date_out')} to {h.get('return_date_actual')}")
                                st.markdown(f"**Odometer:** {h.get('odo_out')} → {h.get('odo_in')} km")
                            with v2:
                                st.markdown(f"**Daily Rate:** ${h.get('rate')}")
                                st.markdown(f"**Subtotal:** ${h.get('subtotal')}")
                                st.markdown(f"**VAT:** ${h.get('tax_amount')}")
                                st.markdown(f"**Grand Total:** ${h.get('total')}")
                            
                            st.divider()
                            st.markdown(f"**Fuel Out/In:** {h.get('fuel_out')} / {h.get('fuel_in')}")
                            st.info(f"**Notes:** {h.get('notes') or 'No notes provided.'}")
        else:
            st.info("No matching records found.")
    else:
        st.info("No completed rentals in the database.")
        
except Exception as e:
    st.error("Could not load history.")
    with st.expander("Show Error Details"):
        st.code(str(e))