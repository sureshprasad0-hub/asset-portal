import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas # New Import

# --- GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🔑 New Rental Agreement")

# --- DATA FETCHING ---
v_res = supabase.table("fleet").select("id, plate").eq("status", "Available").execute()
c_res = supabase.table("customers").select("id, name").execute()

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

# --- FETCH TAX RATE ---
vat_setting = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
vat_pct = float(vat_setting.data[0]['config_value']) if vat_setting.data else 15.0

# --- DYNAMIC CALCULATION ---
duration = (date_in - date_out).days
if duration < 1: duration = 1

subtotal = (daily_rate * duration) + security_bond
tax_total = (daily_rate * duration) * (vat_pct / 100) # Tax only applies to the rental, not the bond
grand_total = subtotal + tax_total

st.divider()
col_a, col_b, col_c = st.columns(3)
col_a.metric("Subtotal", f"${subtotal:,.2f}")
col_b.metric(f"VAT ({vat_pct}%)", f"${tax_total:,.2f}")
col_c.metric("Grand Total", f"${grand_total:,.2f}")

# --- SAVE TO DATABASE ---
# When you run your .insert(), make sure to include these:
# "subtotal": subtotal, "tax_amount": tax_total, "total": grand_total

    fuel_out = st.select_slider(
    "Departure Fuel Level",
    options=["Empty", "1/4", "1/2", "3/4", "Full"],
    value="Full"
)

# Remember to include "fuel_out": fuel_out in your .insert() dictionary later in that file!
    # Signature Section
    st.write("### ✍️ Customer Signature")
    st.caption("Sign inside the box below using your finger or stylus")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#eeeeee",
        height=150,
        drawing_mode="freedraw",
        key="canvas",
    )

    if st.form_submit_button("Finalize & Save Agreement", use_container_width=True):
        if canvas_result.image_data is not None:
            # Logic to save the data
            vid = [v['id'] for v in v_res.data if v['plate'] == v_choice][0]
            cid = [c['id'] for c in c_res.data if c['name'] == c_choice][0]
            
            duration = (date_in - date_out).days
            total = daily_rate * (duration if duration > 0 else 1)
            
            # 1. Save Rental Record
            supabase.table("rentals").insert({
                "vehicle_id": vid, "customer_id": cid, "rate": daily_rate,
                "days": duration, "total": total, "date_out": str(date_out), 
                "status": "Active"
            }).execute()
            
            # 2. Update Fleet Status
            supabase.table("fleet").update({"status": "Rented"}).eq("id", vid).execute()
            
            st.success(f"Agreement Signed & Saved for {v_choice}!")
            st.balloons()
        else:
            st.error("Please provide a signature to proceed.")