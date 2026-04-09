import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- 1. GATEKEEPER & CONNECTION ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🔑 New Rental Agreement")

# Fetch Company Name for the Header
c_res_settings = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res_settings.data[0]['config_value'] if c_res_settings.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 2. DATA FETCHING ---
v_res = supabase.table("fleet").select("id, plate, odometer, model").eq("status", "Available").execute()
c_res = supabase.table("customers").select("id, name").order("name").execute()
vat_setting = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
vat_pct = float(vat_setting.data[0]['config_value']) if vat_setting.data else 15.0

# --- 3. DYNAMIC INPUTS ---
col_a, col_b = st.columns(2)

with col_a:
    v_choice = st.selectbox("Select Vehicle", options=[v['plate'] for v in v_res.data], index=None)
    c_choice = st.selectbox("Select Customer", options=[c['name'] for c in c_res.data], index=None)
    
    current_odo = 0
    if v_choice:
        v_data = next((v for v in v_res.data if v['plate'] == v_choice), None)
        current_odo = v_data['odometer'] if v_data else 0
        st.info(f"📟 **Current Odometer:** `{current_odo:,} km`")

with col_b:
    daily_rate = st.number_input("Daily Rate ($)", min_value=0.0, value=85.0, step=5.0)
    fuel_out = st.select_slider("Fuel Level Out", options=["Empty", "1/4", "1/2", "3/4", "Full"], value="Full")

st.divider()

col1, col2 = st.columns(2)
with col1:
    time_out = st.datetime_input("Date & Time Out", value=datetime.now(), step=timedelta(minutes=15))
with col2:
    time_in_target = st.datetime_input("Expected Return", value=datetime.now() + timedelta(days=1), step=timedelta(minutes=15))

# --- 4. REAL-TIME CALCULATION ---
duration = time_in_target - time_out
total_hours = max(0.0, duration.total_seconds() / 3600)
subtotal = (total_hours / 24) * daily_rate
tax_total = subtotal * (vat_pct / 100)
grand_total = subtotal + tax_total

with st.container(border=True):
    st.write("### 📊 Live Quote Summary")
    q1, q2, q3 = st.columns(3)
    q1.metric("Duration", f"{total_hours:.2f} Hrs")
    q2.metric("Subtotal", f"${subtotal:,.2f}")
    q3.metric("Grand Total", f"${grand_total:,.2f}")

# --- 5. SUBMISSION ---
if st.button("Finalize & Save Rental Agreement", type="primary", use_container_width=True):
    if not v_choice or not c_choice or total_hours <= 0:
        st.error("Please check vehicle selection and valid return time.")
    else:
        try:
            vid = next(v['id'] for v in v_res.data if v['plate'] == v_choice)
            cid = next(c['id'] for c in c_res.data if c['name'] == c_choice)
            
            payload = {
                "vehicle_id": vid, "customer_id": cid, "rate": daily_rate,
                "subtotal": round(subtotal, 2), "tax_amount": round(tax_total, 2),
                "total": round(grand_total, 2), "fuel_out": fuel_out,
                "odo_out": current_odo, "date_out": time_out.isoformat(), 
                "date_in": time_in_target.isoformat(), "status": "Active"
            }
            
            supabase.table("rentals").insert(payload).execute()
            supabase.table("fleet").update({"status": "Rented"}).eq("id", vid).execute()
            st.success("Rental Agreement Active!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# --- 6. CURRENTLY ACTIVE REGISTRY ---
st.write("---")
st.subheader("📋 Currently Out (Active)")

try:
    # We add !fk_rentals_fleet to tell Supabase exactly which relationship to use
    rent_res = supabase.table("rentals") \
        .select("id, total, date_out, odo_out, fleet!fk_rentals_fleet(plate, model), customers!fk_rentals_customers(name)") \
        .eq("status", "Active") \
        .execute()

    if rent_res.data:
        for r in rent_res.data:
            with st.container(border=True):
                r1, r2, r3 = st.columns([3, 3, 2])
                
                # Extracting data safely using the explicit relationship key
                fleet_info = r.get('fleet', {})
                cust_info = r.get('customers', {})
                
                plate = fleet_info.get('plate', 'Unknown')
                model = fleet_info.get('model', '')
                cust_name = cust_info.get('name', 'Unknown')
                
                r1.write(f"🚗 **{plate}**")
                r1.caption(f"{model}")
                
                r2.write(f"👤 {cust_name}")
                
                r3.write(f"💰 **${float(r['total']):,.2f}**")
                
                # Formatting the date for Fiji standard
                d_out = datetime.fromisoformat(r['date_out']).strftime("%d %b, %I:%M %p")
                st.caption(f"Departure: {d_out} | Odo Out: {r['odo_out']:,} km")
    else:
        st.info("No vehicles are currently out.")

except Exception as e:
    st.error("Relationship Ambiguity Error")
    st.info("Try updating the join syntax in your code as shown above.")
    st.expander("Show Technical Error").code(str(e))