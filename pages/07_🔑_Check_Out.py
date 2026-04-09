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

# --- 3. DATA FETCHING ---
# Updated to include 'odometer' from the fleet table
v_res = supabase.table("fleet").select("id, plate, odometer").eq("status", "Available").execute()
c_res = supabase.table("customers").select("id, name").order("name").execute()
vat_setting = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
vat_pct = float(vat_setting.data[0]['config_value']) if vat_setting.data else 15.0

if not v_res.data:
    st.error("No vehicles are currently Available in the yard.")
    st.stop()

# --- 4. RENTAL FORM ---
with st.form("rental_form", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    
    with col_a:
        v_choice = st.selectbox("Select Vehicle", options=[v['plate'] for v in v_res.data], index=None, placeholder="Choose Plate...")
        c_choice = st.selectbox("Select Customer", options=[c['name'] for c in c_res.data], index=None, placeholder="Search Customer...")
        
        # Dynamic Odometer Display
        if v_choice:
            current_odo = next((v['odometer'] for v in v_res.data if v['plate'] == v_choice), 0)
            st.info(f"📟 **Current Odometer:** {current_odo:,} km")
        else:
            current_odo = 0

    with col_b:
        daily_rate = st.number_input("Daily Rate ($)", min_value=0.0, value=85.0, step=5.0)
        fuel_out = st.select_slider("Fuel Level Out", options=["Empty", "1/4", "1/2", "3/4", "Full"], value="Full")

    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        date_out = st.date_input("Date Out", value=date.today())
    with col2:
        date_in = st.date_input("Target Return", value=date.today() + timedelta(days=3))

    st.write("### Customer Signature")
    canvas_result = st_canvas(
        stroke_width=2, stroke_color="#000", background_color="#eee",
        height=150, update_streamlit=True, key="sig_checkout"
    )

    # Calculation logic for UI preview
    days = (date_in - date_out).days
    if days <= 0: days = 1 # Minimum 1 day charge
    
    subtotal = daily_rate * days
    tax_total = subtotal * (vat_pct / 100)
    grand_total = subtotal + tax_total

    st.markdown(f"**Total Days:** {days} | **Subtotal:** ${subtotal:,.2f} | **VAT ({vat_pct}%):** ${tax_total:,.2f}")
    st.subheader(f"Grand Total: ${grand_total:,.2f}")

    # Submit Button
    submitted = st.form_submit_button("Finalize & Save Agreement", use_container_width=True, type="primary")

# --- 5. FORM SUBMISSION LOGIC ---
if submitted:
    if not v_choice or not c_choice:
        st.error("Please select both a vehicle and a customer.")
    elif canvas_result.image_data is None:
        st.warning("Please provide a signature before finalizing.")
    else:
        try:
            # Resolve IDs
            vid = next(v['id'] for v in v_res.data if v['plate'] == v_choice)
            cid = next(c['id'] for c in c_res.data if c['name'] == c_choice)
            
            # 1. Create Rental Record (Including odo_out)
            supabase.table("rentals").insert({
                "vehicle_id": vid, 
                "customer_id": cid, 
                "rate": daily_rate,
                "days": days, 
                "subtotal": subtotal,
                "tax_amount": tax_total,
                "total": grand_total, 
                "fuel_out": fuel_out,
                "odo_out": current_odo, # Recorded starting mileage
                "date_out": date_out.isoformat(), 
                "