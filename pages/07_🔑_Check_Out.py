import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas  # Ensure this is installed

# --- 1. GATEKEEPER & CONNECTION ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🔑 New Rental Agreement")

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
    
    db_odo = 0
    if v_choice:
        v_data = next((v for v in v_res.data if v['plate'] == v_choice), None)
        db_odo = v_data['odometer'] if v_data else 0
    
    current_odo = st.number_input("Odometer Reading (km)", value=db_odo)

with col_b:
    daily_rate = st.number_input("Daily Rate ($)", min_value=0.0, value=85.0, step=5.0)
    fuel_options = ["Empty", "1/8", "1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "Full"]
    fuel_out = st.select_slider("Fuel Level Out", options=fuel_options, value="Full")
    bond_amount = st.number_input("Bond Deposit ($)", min_value=0.0, value=500.0, step=50.0)

st.divider()

col1, col2 = st.columns(2)
with col1:
    time_out = st.datetime_input("Date & Time Out", value=datetime.now(), step=timedelta(minutes=15))
with col2:
    time_in_target = st.datetime_input("Expected Return", value=datetime.now() + timedelta(days=1), step=timedelta(minutes=15))

# --- 4. CALCULATION (VAT INCLUSIVE) ---
duration = time_in_target - time_out
total_hours = max(0.0, duration.total_seconds() / 3600)

gross_total = (total_hours / 24) * daily_rate
subtotal = gross_total / (1 + (vat_pct / 100))
tax_amount = gross_total - subtotal
total_payable = gross_total + bond_amount

with st.container(border=True):
    st.write("### 📊 Live Quote (VAT Inclusive)")
    q1, q2, q3 = st.columns(3)
    q1.metric("Rental Subtotal", f"${subtotal:,.2f}")
    q2.metric(f"VAT ({vat_pct}%)", f"${tax_amount:,.2f}")
    q3.metric("Rental Total", f"${gross_total:,.2f}")
    st.write(f"**Security Bond:** ${bond_amount:,.2f}")
    st.subheader(f"Total Due Now: ${total_payable:,.2f}")

# --- 5. SIGNATURE FIELD ---
st.write("### 🖋️ Customer Signature")
signature_canvas = st_canvas(
    fill_color="rgba(255, 255, 255, 0)",
    stroke_width=3,
    stroke_color="#000000",
    background_color="#eeeeee",
    height=150,
    drawing_mode="freedraw",
    key="canvas",
)

# --- 6. SUBMISSION ---
if st.button("Finalize & Save Agreement", type="primary", use_container_width=True):
    # Basic check to see if signature has been attempted (optional but recommended)
    if not v_choice or not c_choice or total_hours <= 0:
        st.error("Please complete all selections and ensure the return time is valid.")
    elif signature_canvas.image_data is None:
        st.warning("Please provide a customer signature before finalizing.")
    else:
        try:
            vid = next(v['id'] for v in v_res.data if v['plate'] == v_choice)
            cid = next(c['id'] for c in c_res.data if c['name'] == c_choice)
            
            payload = {
                "vehicle_id": vid, 
                "customer_id": cid, 
                "rate": daily_rate,
                "bond": bond_amount,
                "subtotal": round(subtotal, 2), 
                "tax_amount": round(tax_amount, 2),
                "total": round(gross_total, 2), 
                "fuel_out": fuel_out,
                "odo_out": current_odo, 
                "date_out": time_out.isoformat(), 
                "date_in": time_in_target.isoformat(), 
                "status": "Active"
            }
            
            supabase.table("rentals").insert(payload).execute()
            supabase.table("fleet").update({"status": "Rented"}).eq("id", vid).execute()
            st.success("Rental Agreement Active & Signature Captured!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# --- 7. ACTIVE REGISTRY ---
st.write("---")
st.subheader("📋 Currently Out (Active)")
try:
    rent_res = supabase.table("rentals") \
        .select("id, total, bond, date_out, odo_out, fleet!fk_rentals_fleet(plate), customers!fk_rentals_customers(name)") \
        .eq("status", "Active") \
        .execute()

    if rent_res.data:
        for r in rent_res.data:
            with st.container(border=True):
                r1, r2, r3 = st.columns([3, 3, 2])
                r1.write(f"🚗 **{r['fleet']['plate']}**")
                r2.write(f"👤 {r['customers']['name']}")
                r3.write(f"💰 **${float(r['total']):,.2f}**")
                st.caption(f"Bond: ${r['bond']} | Out since: {r['date_out']}")
    else:
        st.info("No active rentals.")
except:
    st.warning("Active list view limited.")