import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas

# --- GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🔑 New Rental Agreement")

# Fetch Company Name for the Header
c_res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res.data[0]['config_value'] if c_res.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- DATA FETCHING ---
v_res = supabase.table("fleet").select("id, plate").eq("status", "Available").execute()
c_res = supabase.table("customers").select("id, name").execute()
vat_setting = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
vat_pct = float(vat_setting.data[0]['config_value']) if vat_setting.data else 15.0

if not v_res.data:
    st.error("No vehicles available in the fleet.")
    st.stop()

# --- RENTAL FORM ---
with st.form("checkout_form"):
    col1, col2 = st.columns(2)
    v_choice = col1.selectbox("Vehicle", options=[v['plate'] for v in v_res.data])
    c_choice = col2.selectbox("Customer", options=[c['name'] for c in c_res.data] if c_res.data else ["No Customers Found"])
    
    col3, col4 = st.columns(2)
    date_out = col3.date_input("Out Date", datetime.now())
    date_in = col4.date_input("Return Date", datetime.now() + timedelta(days=3))
    
    daily_rate = st.number_input("Daily Rate ($)", min_value=0.0, value=120.0)
    security_bond = st.number_input("Security Bond ($)", min_value=0.0, value=500.0)
    
    fuel_out = st.select_slider(
        "Departure Fuel Level",
        options=["Empty", "1/4", "1/2", "3/4", "Full"],
        value="Full"
    )

    st.write("### ✍️ Customer Signature")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#eeeeee",
        height=150,
        drawing_mode="freedraw",
        key="canvas",
    )

    # Calculate Totals
    duration = (date_in - date_out).days
    if duration < 1: duration = 1
    subtotal = (daily_rate * duration) + security_bond
    tax_total = (daily_rate * duration) * (vat_pct / 100)
    grand_total = subtotal + tax_total

    st.divider()
    st.write(f"**Subtotal:** ${subtotal:,.2f} | **VAT ({vat_pct}%):** ${tax_total:,.2f}")
    st.subheader(f"Grand Total: ${grand_total:,.2f}")

    if st.form_submit_button("Finalize & Save Agreement", use_container_width=True):
        if canvas_result.image_data is not None and c_choice != "No Customers Found":
            vid = [v['id'] for v in v_res.data if v['plate'] == v_choice][0]
            cid = [c['id'] for c in c_res.data if c['name'] == c_choice][0]
            
            supabase.table("rentals").insert({
                "vehicle_id": vid, 
                "customer_id": cid, 
                "rate": daily_rate,
                "days": duration, 
                "subtotal": subtotal,
                "tax_amount": tax_total,
                "total": grand_total, 
                "fuel_out": fuel_out,
                "date_out": str(date_out), 
                "date_in": str(date_in),
                "status": "Active"
            }).execute()
            
            supabase.table("fleet").update({"status": "Rented"}).eq("id", vid).execute()
            st.success("Agreement Saved!")
            st.rerun()
        else:
            st.error("Signature required and a valid customer must be selected.")