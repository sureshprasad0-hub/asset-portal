import streamlit as st
from datetime import datetime, timedelta, date
from supabase import create_client, Client
from streamlit_drawable_canvas import st_canvas

# --- 1. GATEKEEPER ---
# Ensuring the user is authenticated before accessing the rental form
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🔑 New Rental Agreement")

# Fetch Company Name for the Header from global settings
c_res_settings = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res_settings.data[0]['config_value'] if c_res_settings.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 3. DATA FETCHING ---
# Retrieve only available vehicles and registered customers
v_res = supabase.table("fleet").select("id, plate").eq("status", "Available").execute()
c_res = supabase.table("customers").select("id, name").order("name").execute()
vat_setting = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
vat_pct = float(vat_setting.data[0]['config_value']) if vat_setting.data else 15.0

if not v_res.data:
    st.error("No vehicles available in the fleet. Please update fleet status in Inventory.")
    st.stop()

# --- 4. QUICK CUSTOMER REGISTER ---
# Allows adding a customer without leaving the current form
with st.expander("👤 Quick Register New Customer", expanded=False):
    with st.form("quick_cust"):
        nc_name = st.text_input("Full Legal Name")
        nc_dl = st.text_input("License No.")
        if st.form_submit_button("Register & Refresh List"):
            if nc_name and nc_dl:
                supabase.table("customers").insert({"name": nc_name, "dl_no": nc_dl}).execute()
                st.success(f"{nc_name} registered!")
                st.rerun()

# --- 5. RENTAL FORM (AUTO-CALCULATING) ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    # Default to None to ensure intentional selection
    v_choice = col1.selectbox("Select Available Vehicle", options=[v['plate'] for v in v_res.data], index=None, placeholder="Choose Plate...")
    c_choice = col2.selectbox("Select Customer", options=[c['name'] for c in c_res.data] if c_res.data else ["No Customers Found"], index=None, placeholder="Choose Name...")
    
    col3, col4 = st.columns(2)
    # DateTime support for precise tracking
    date_out = col3.datetime_input("Departure Date & Time", value=datetime.now())
    date_in = col4.datetime_input("Expected Return Date & Time", value=datetime.now() + timedelta(days=3))
    
    col5, col6 = st.columns(2)
    daily_rate = col5.number_input("Daily Rental Rate ($)", min_value=0.0, value=120.0)
    security_bond = col6.number_input("Security Deposit / Bond ($)", min_value=0.0, value=500.0)
    
    # Granular fuel levels in 1/8 increments
    fuel_out = st.select_slider(
        "Departure Fuel Level",
        options=["Empty", "1/8", "1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "Full"],
        value="Full"
    )

    # --- LIVE FINANCIAL SUMMARY ---
    try:
        # Standardizing date objects to prevent TypeErrors in calculations
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

    except Exception as e:
        st.error("Select valid dates to calculate total.")
        days, subtotal, tax_total, grand_total = 1, 0.0, 0.0, 0.0

    st.divider()
    st.write("### ✍️ Customer Signature")
    canvas_result = st_canvas(
        stroke_width=3, stroke_color="#000000", background_color="#eeeeee",
        height=150, drawing_mode="freedraw", key="canvas_checkout",
    )

    if st.button("Finalize & Save Agreement", use_container_width=True, type="primary"):
        if not v_choice or not c_choice or c_choice == "No Customers Found":
            st.error("Please select both a vehicle and a customer.")
        elif canvas_result.image_data is None:
            st.error("Customer signature is required to proceed.")
        else:
            try:
                # Resolve IDs for database insertion
                vid = [v['id'] for v in v_res.data if v['plate'] == v_choice][0]
                cid = [c['id'] for c in c_res.data if c['name'] == c_choice][0]
                
                # Create Rental Record
                supabase.table("rentals").insert({
                    "vehicle_id": vid, 
                    "customer_id": cid, 
                    "rate": daily_rate,
                    "days": days, 
                    "subtotal": subtotal,
                    "tax_amount": tax_total,
                    "total": grand_total, 
                    "fuel_out": fuel_out,
                    "date_out": date_out.isoformat(), 
                    "date_in": date_in.isoformat(),
                    "status": "Active"
                }).execute()
                
                # Mark vehicle as Rented in Fleet table
                supabase.table("fleet").update({"status": "Rented"}).eq("id", vid).execute()
                st.success(f"Agreement Finalized for {v_choice}!")
                st.rerun()
            except Exception as e:
                st.error(f"Save Failed: {e}")