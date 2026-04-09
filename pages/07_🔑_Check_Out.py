import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from supabase import create_client, Client

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🔑 New Rental Agreement")

# Fetch Company Name
c_res_settings = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res_settings.data[0]['config_value'] if c_res_settings.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 3. DATA FETCHING ---
# CRITICAL: We fetch 'odometer' here so the UI can display it
v_res = supabase.table("fleet").select("id, plate, odometer").eq("status", "Available").execute()
c_res = supabase.table("customers").select("id, name").order("name").execute()
vat_setting = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
vat_pct = float(vat_setting.data[0]['config_value']) if vat_setting.data else 15.0

if not v_res.data:
    st.error("No vehicles are currently Available in the yard.")
    st.stop()

# --- 4. RENTAL FORM ---
# Use a form to group inputs, but keep calculations dynamic
with st.form("rental_form"):
    col_a, col_b = st.columns(2)
    
    with col_a:
        v_choice = st.selectbox("Select Vehicle", options=[v['plate'] for v in v_res.data], index=None, placeholder="Choose Plate...")
        c_choice = st.selectbox("Select Customer", options=[c['name'] for c in c_res.data], index=None, placeholder="Search Customer...")
        
        # Dynamic Odometer Display
        current_odo = 0
        if v_choice:
            current_odo = next((v['odometer'] for v in v_res.data if v['plate'] == v_choice), 0)
            st.info(f"📟 **Current Odometer:** {current_odo:,} km")

    with col_b:
        daily_rate = st.number_input("Daily Rate ($)", min_value=0.0, value=85.0, step=5.0)
        fuel_out = st.select_slider("Fuel Level Out", options=["Empty", "1/4", "1/2", "3/4", "Full"], value="Full")

    st.divider()
    
    # DATETIME INPUTS: Captures both Date and Time
    col1, col2 = st.columns(2)
    with col1:
        time_out = st.datetime_input("Date & Time Out", value=datetime.now(), step=timedelta(minutes=30))
    with col2:
        # Default return is 24 hours later
        time_in_target = st.datetime_input("Expected Return", value=datetime.now() + timedelta(days=1), step=timedelta(minutes=30))

    # --- 5. BILLING CALCULATION ---
    duration = time_in_target - time_out
    total_hours = duration.total_seconds() / 3600
    
    if total_hours < 0:
        st.error("Return time cannot be before departure time.")
        total_hours = 0

    # Logic: Total Days (including fractions) * Daily Rate
    # Example: 26 hours = 1.083 days. 1.083 * $85 = $92.08
    subtotal = (total_hours / 24) * daily_rate
    tax_total = subtotal * (vat_pct / 100)
    grand_total = subtotal + tax_total

    st.write(f"⏱️ **Total Duration:** {total_hours:.2f} Hours ({total_hours/24:.2f} Days)")
    st.markdown(f"**Subtotal:** ${subtotal:,.2f} | **VAT ({vat_pct}%):** ${tax_total:,.2f}")
    st.subheader(f"Grand Total: ${grand_total:,.2f}")

    submitted = st.form_submit_button("Finalize & Save Agreement", use_container_width=True, type="primary")

# --- 6. SUBMISSION LOGIC ---
if submitted:
    if not v_choice or not c_choice or total_hours <= 0:
        st.error("Please ensure vehicle, customer, and valid times are selected.")
    else:
        try:
            vid = next(v['id'] for v in v_res.data if v['plate'] == v_choice)
            cid = next(c['id'] for c in c_res.data if c['name'] == c_choice)
            
            payload = {
                "vehicle_id": vid, 
                "customer_id": cid, 
                "rate": daily_rate,
                "subtotal": round(subtotal, 2),
                "tax_amount": round(tax_total, 2),
                "total": round(grand_total, 2), 
                "fuel_out": fuel_out,
                "odo_out": current_odo,
                "date_out": time_out.isoformat(), 
                "date_in": time_in_target.isoformat(),
                "status": "Active"
            }
            
            supabase.table("rentals").insert(payload).execute()
            supabase.table("fleet").update({"status": "Rented"}).eq("id", vid).execute()
            
            st.success(f"Success! {v_choice} is now active.")
            st.rerun()
        except Exception as e:
            st.error(f"Error saving record: {e}")

# --- 7. ACTIVE REGISTRY ---
st.write("---")
st.subheader("📋 Active Rental Registry")
rent_res = supabase.table("rentals").select(
    "id, total, date_out, fuel_out, odo_out, fleet(plate, model), customers(name)"
).eq("status", "Active").execute()

if rent_res.data:
    for rent in rent_res.data:
        with st.container(border=True):
            r1, r2, r3 = st.columns([3, 3, 2])
            
            r1.write(f"🚗 **{rent['fleet']['plate']}**")
            r1.caption(f"{rent['fleet']['model']}")
            
            r2.write(f"👤 **{rent['customers']['name']}**")
            # Format the ISO timestamp for the UI
            d_out = datetime.fromisoformat(rent['date_out']).strftime("%d %b, %H:%M")
            r2.caption(f"Departure: {d_out}")
            
            r3.write(f"💰 **${float(rent['total']):,.2f}**")
            r3.caption(f"📟 Odo: {rent['odo_out']:,} km")
else:
    st.info("No active rentals found.")