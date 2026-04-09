import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🔑 New Rental Agreement")

# Fetch Company Name for the Header
c_res_settings = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res_settings.data[0]['config_value'] if c_res_settings.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 3. DATA FETCHING (Updated to include odometer) ---
v_res = supabase.table("fleet").select("id, plate, odometer").eq("status", "Available").execute()
c_res = supabase.table("customers").select("id, name").order("name").execute()
vat_setting = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
vat_pct = float(vat_setting.data[0]['config_value']) if vat_setting.data else 15.0

if not v_res.data:
    st.error("No vehicles are currently Available in the yard.")
    st.stop()

# --- 4. RENTAL FORM ---
with st.form("rental_form"):
    v_choice = st.selectbox("Select Vehicle", options=[v['plate'] for v in v_res.data])
    c_choice = st.selectbox("Select Customer", options=[c['name'] for c in c_res.data])
    
    # --- ODOMETER DISPLAY (Added) ---
    # Fetch mileage for the currently selected plate
    current_odo = next((v['odometer'] for v in v_res.data if v['plate'] == v_choice), 0)
    st.info(f"📟 **Departure Odometer Reading:** {current_odo:,} km")

    col1, col2 = st.columns(2)
    with col1:
        date_out = st.date_input("Date Out", value=date.today())
        daily_rate = st.number_input("Daily Rate ($)", min_value=0.0, value=85.0, step=5.0)
    with col2:
        date_in = st.date_input("Target Return", value=date.today() + timedelta(days=3))
        fuel_out = st.select_slider("Fuel Level Out", options=["Empty", "1/4", "1/2", "3/4", "Full"], value="Full")

    st.write("### Customer Signature")
    canvas_result = st_canvas(
        stroke_width=2, stroke_color="#000", background_color="#eee",
        height=150, update_streamlit=True, key="sig_checkout"
    )

    # Calculation logic for UI preview
    days = (date_in - date_out).days or 1
    subtotal = daily_rate * days
    tax_total = subtotal * (vat_pct / 100)
    grand_total = subtotal + tax_total

    st.divider()
    st.markdown(f"**Total Days:** {days} | **Subtotal:** ${subtotal:,.2f} | **VAT ({vat_pct}%):** ${tax_total:,.2f}")
    st.subheader(f"Grand Total: ${grand_total:,.2f}")

    if st.form_submit_button("Finalize & Save Agreement", use_container_width=True, type="primary"):
        if canvas_result.image_data is not None:
            try:
                # Resolve IDs
                vid = next(v['id'] for v in v_res.data if v['plate'] == v_choice)
                cid = next(c['id'] for c in c_res.data if c['name'] == c_choice)
                
                # Create Rental Record (Including odo_out)
                supabase.table("rentals").insert({
                    "vehicle_id": vid, 
                    "customer_id": cid, 
                    "rate": daily_rate,
                    "days": days, 
                    "subtotal": subtotal,
                    "tax_amount": tax_total,
                    "total": grand_total, 
                    "fuel_out": fuel_out,
                    "odo_out": current_odo, # Recorded departure mileage
                    "date_out": date_out.isoformat(), 
                    "date_in": date_in.isoformat(),
                    "status": "Active"
                }).execute()
                
                # Mark as Rented
                supabase.table("fleet").update({"status": "Rented"}).eq("id", vid).execute()
                
                st.success(f"Success! {v_choice} has been checked out.")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving agreement: {e}")
        else:
            st.warning("Please provide a signature before finalizing.")

# --- 5. ACTIVE AGREEMENTS REGISTRY ---
st.write("---")
st.subheader("📋 Currently Active Agreements")
rent_res = supabase.table("rentals").select(
    "id, total, date_out, fuel_out, fleet(plate, model), customers(name)"
).eq("status", "Active").execute()

if rent_res.data:
    for rent in rent_res.data:
        with st.container(border=True):
            r1, r2, r3, r4 = st.columns([3, 3, 2, 1])
            r1.write(f"🚗 **{rent['fleet']['plate']}**")
            r1.caption(f"{rent['fleet']['model']}")
            
            r2.write(f"👤 **{rent['customers']['name']}**")
            r2.caption(f"Out: {rent['date_out']}")
            
            r3.write(f"💰 **${float(rent['total']):,.2f}**")
            r3.caption(f"Fuel: {rent['fuel_out']}")
            
            if r4.button("View", key=f"v_{rent['id']}", use_container_width=True):
                st.session_state[f"detail_{rent['id']}"] = not st.session_state.get(f"detail_{rent['id']}", False)
            
            if st.session_state.get(f"detail_{rent['id']}", False):
                st.info(f"Agreement ID: {rent['id']}")