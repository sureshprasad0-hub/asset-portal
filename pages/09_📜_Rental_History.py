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

# Fetch Company Name
c_res_settings = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res_settings.data[0]['config_value'] if c_res_settings.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# Helper to convert "1/8" strings to percentage for the progress bar
def fuel_to_percent(fuel_str):
    mapping = {
        "Empty": 0.0, "1/8": 0.125, "1/4": 0.25, "3/8": 0.375, 
        "1/2": 0.5, "5/8": 0.625, "3/4": 0.75, "7/8": 0.875, "Full": 1.0
    }
    return mapping.get(fuel_str, 0.0)

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
                    
                    # --- DETAILED GRAPHICAL VIEW ---
                    if c4.button("View", key=f"hist_{h['id']}"):
                        with st.expander("📄 Complete Rental Record", expanded=True):
                            # Section 1: Vehicle & Customer
                            v1, v2 = st.columns(2)
                            with v1:
                                st.markdown("### 🚙 Vehicle Details")
                                st.write(f"**Plate:** {fleet_info.get('plate')}")
                                st.write(f"**Model:** {fleet_info.get('brand')} {fleet_info.get('model')}")
                                st.write(f"**Odo Out:** {h.get('odo_out'):,} km")
                                st.write(f"**Odo In:** {h.get('odo_in'):,} km")
                            with v2:
                                st.markdown("### 👤 Customer Details")
                                st.write(f"**Name:** {cust_info.get('name')}")
                                st.write(f"**Out:** {h.get('date_out')}")
                                st.write(f"**In:** {h.get('return_date_actual')}")
                                st.write(f"**Bond:** ${h.get('bond') or 0}")

                            st.divider()

                            # Section 2: Fuel Graphical Display
                            st.markdown("### ⛽ Fuel Status")
                            f1, f2 = st.columns(2)
                            with f1:
                                st.write(f"**Fuel Out: {h.get('fuel_out')}**")
                                st.progress(fuel_to_percent(h.get('fuel_out')), text=None)
                            with f2:
                                st.write(f"**Fuel In: {h.get('fuel_in')}**")
                                st.progress(fuel_to_percent(h.get('fuel_in')), text=None)

                            st.divider()

                            # Section 3: Financials
                            st.markdown("### 💰 Financial Summary")
                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric("Daily Rate", f"${h.get('rate')}")
                            m2.metric("Subtotal", f"${h.get('subtotal')}")
                            m3.metric("VAT", f"${h.get('tax_amount')}")
                            m4.metric("Total Paid", f"${h.get('total')}")

                            st.divider()

                            # Section 4: Signature & Notes
                            s1, s2 = st.columns(2)
                            with s1:
                                st.markdown("### 🖋️ Customer Signature")
                                # This assumes signature is stored as a URL or base64. 
                                # If you haven't implemented storage yet, it shows a placeholder.
                                sig_data = h.get('signature_url') or h.get('signature_data')
                                if sig_data:
                                    st.image(sig_data, width=300)
                                else:
                                    st.warning("No digital signature captured for this record.")
                            with s2:
                                st.markdown("### 📝 Remarks")
                                st.info(h.get('notes') or "No notes provided.")
        else:
            st.info("No matching records found.")
    else:
        st.info("No completed rentals in the database.")
        
except Exception as e:
    st.error("Could not load history.")
    with st.expander("Show Error Details"):
        st.code(str(e))