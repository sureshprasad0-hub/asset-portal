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
v_res = supabase.table("fleet").select("id, plate").eq("status", "Available").execute()
c_res = supabase.table("customers").select("id, name").order("name").execute()
vat_setting = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
vat_pct = float(vat_setting.data[0]['config_value']) if vat_setting.data else 15.0

# Fetch Active Rentals for the Registry
active_rentals_res = supabase.table("rentals").select("*, fleet(plate, model), customers(name)").eq("status", "Active").order("date_out", desc=True).execute()

# --- 4. QUICK CUSTOMER REGISTER ---
with st.expander("👤 Quick Register New Customer", expanded=False):
    with st.form("quick_cust"):
        nc_name = st.text_input("Full Legal Name")
        nc_dl = st.text_input("License No.")
        if st.form_submit_button("Register & Refresh List"):
            if nc_name and nc_dl:
                supabase.table("customers").insert({"name": nc_name, "dl_no": nc_dl}).execute()
                st.success(f"{nc_name} registered!")
                st.rerun()

# --- 5. RENTAL FORM ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    v_choice = col1.selectbox("Select Available Vehicle", options=[v['plate'] for v in v_res.data], index=None, placeholder="Choose Plate...")
    c_choice = col2.selectbox("Select Customer", options=[c['name'] for c in c_res.data] if c_res.data else ["No Customers Found"], index=None, placeholder="Choose Name...")
    
    col3, col4 = st.columns(2)
    date_out = col3.datetime_input("Departure Date & Time", value=datetime.now())
    date_in = col4.datetime_input("Expected Return Date & Time", value=datetime.now() + timedelta(days=3))
    
    col5, col6 = st.columns(2)
    daily_rate = col5.number_input("Daily Rental Rate ($)", min_value=0.0, value=120.0)
    security_bond = col6.number_input("Security Deposit / Bond ($)", min_value=0.0, value=500.0)
    
    fuel_out = st.select_slider(
        "Departure Fuel Level",
        options=["Empty", "1/8", "1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "Full"],
        value="Full"
    )

    # Financial Calculations
    try:
        d_out = datetime.combine(date_out, datetime.min.time()) if isinstance(date_out, date) else date_out
        d_in = datetime.combine(date_in, datetime.min.time()) if isinstance(date_in, date) else date_in
        duration_delta = d_in - d_out
        days = max(1, duration_delta.days + (1 if duration_delta.seconds > 3600 else 0))
        
        subtotal = float((daily_rate * days) + security_bond)
        tax_total = float((daily_rate * days) * (vat_pct / 100))
        grand_total = float(subtotal + tax_total)

        st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:15px; border-radius:10px; border-left: 5px solid #ff4b4b;">
            <h4 style="margin:0; color:#31333F;">Live Quote Summary</h4>
            <p style="margin:5px 0; color:#31333F;">Duration: <b>{days} Day(s)</b> | Subtotal: <b>${subtotal:,.2f}</b></p>
            <p style="margin:0; color:#31333F;">VAT ({vat_pct}%): <b>${tax_total:,.2f}</b></p>
            <h3 style="margin:10px 0 0 0; color:#ff4b4b;">Grand Total: ${grand_total:,.2f}</h3>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        st.error("Select valid dates to calculate total.")
        days, subtotal, tax_total, grand_total = 1, 0.0, 0.0, 0.0

    st.divider()
    st.write("### ✍️ Customer Signature")
    canvas_result = st_canvas(
        stroke_width=3, stroke_color="#000000", background_color="#eeeeee",
        height=150, drawing_mode="freedraw", key="canvas_checkout",
    )

    if st.button("Finalize & Save Agreement", use_container_width=True, type="primary"):
        if not v_choice or not c_choice:
            st.error("Please select both a vehicle and a customer.")
        elif canvas_result.image_data is None:
            st.error("Customer signature is required.")
        else:
            try:
                vid = [v['id'] for v in v_res.data if v['plate'] == v_choice][0]
                cid = [c['id'] for c in c_res.data if c['name'] == c_choice][0]
                
                supabase.table("rentals").insert({
                    "vehicle_id": vid, "customer_id": cid, "rate": daily_rate,
                    "days": days, "subtotal": subtotal, "tax_amount": tax_total,
                    "total": grand_total, "fuel_out": fuel_out,
                    "date_out": date_out.isoformat(), "date_in": date_in.isoformat(),
                    "status": "Active"
                }).execute()
                
                supabase.table("fleet").update({"status": "Rented"}).eq("id", vid).execute()
                st.success("Agreement Finalized!")
                # Refresh page as a new blank form
                st.rerun()
            except Exception as e:
                st.error(f"Save Failed: {e}")

# --- 6. ACTIVE RENTALS REGISTRY (STYLE MATCH WITH CUSTOMER PAGE) ---
st.write("---")
st.subheader("📋 Active Rental Registry")

if active_rentals_res.data:
    # Header Row
    h1, h2, h3, h4 = st.columns([2, 3, 2, 1])
    h1.caption("**PLATE / VEHICLE**")
    h2.caption("**CUSTOMER / DATES**")
    h3.caption("**TOTAL / FUEL**")
    h4.caption("**ACTION**")

    for rent in active_rentals_res.data:
        with st.container():
            r1, r2, r3, r4 = st.columns([2, 3, 2, 1])
            
            # Column 1: Asset Details
            r1.write(f"🚗 **{rent['fleet']['plate']}**")
            r1.caption(f"{rent['fleet']['model']}")
            
            # Column 2: Customer and Timing
            r2.write(f"👤 **{rent['customers']['name']}**")
            d_out_str = datetime.fromisoformat(rent['date_out']).strftime("%d %b, %H:%M")
            r2.caption(f"Out: {d_out_str}")
            
            # Column 3: Financials and Status
            r3.write(f"💰 **${float(rent['total']):,.2f}**")
            r3.caption(f"Fuel: {rent['fuel_out']}")
            
            # Column 4: Drill-down Button
            if r4.button("View", key=f"view_{rent['id']}", use_container_width=True):
                st.session_state[f"detail_{rent['id']}"] = not st.session_state.get(f"detail_{rent['id']}", False)
            
            # Detailed Drill-down View
            if st.session_state.get(f"detail_{rent['id']}", False):
                with st.container(border=True):
                    st.markdown(f"**Agreement ID:** `{rent['id']}`")
                    sd1, sd2, sd3 = st.columns(3)
                    sd1.write(f"**Daily Rate:** ${rent['rate']}")
                    sd2.write(f"**Days:** {rent['days']}")
                    sd3.write(f"**Deposit:** ${float(rent['total']) - float(rent['subtotal']) + float(rent['tax_amount']):,.2f}")
                    st.caption(f"Full Return Expected: {rent['date_in']}")
            
            st.write("---")
else:
    st.info("No active rentals found.")