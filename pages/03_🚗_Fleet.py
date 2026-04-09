import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from supabase import create_client, Client

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 3. SESSION STATE & NAVIGATION ---
if 'fleet_view' not in st.session_state:
    st.session_state.fleet_view = "list"
if 'selected_vehicle' not in st.session_state:
    st.session_state.selected_vehicle = None

def enter_fleet_add():
    st.session_state.selected_vehicle = None
    st.session_state.fleet_view = "add"

st.title("🚗 Fleet Inventory")

# Fetch Company Name for the Header
c_res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res.data[0]['config_value'] if c_res.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 4. DATA FETCHING ---
try:
    brand_res = supabase.table("vehicle_brands").select("brand_name").order("brand_name").execute()
    brand_options = [b['brand_name'] for b in brand_res.data] if brand_res.data else ["Other"]
    
    loc_res = supabase.table("operating_locations").select("location_name").order("location_name").execute()
    loc_options = [l['location_name'] for l in loc_res.data] if loc_res.data else ["Main Yard"]
except:
    brand_options = ["Standard"]
    loc_options = ["Main Yard"]

# --- 5. VIEW: ADD / EDIT FORM ---
if st.session_state.fleet_view in ["add", "edit"]:
    mode = st.session_state.fleet_view
    v = st.session_state.selected_vehicle if mode == "edit" else {}
    
    st.subheader("🛠️ Asset Details" if mode == "edit" else "➕ Register New Asset")
    
    with st.form("vehicle_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            plate = st.text_input("Number Plate", value=v.get('plate', "")).strip().upper()
            
            # Brand Index Safety
            b_val = v.get('brand', "Other")
            b_idx = brand_options.index(b_val) if b_val in brand_options else 0
            brand = st.selectbox("Brand", options=brand_options, index=b_idx)
            
            model = st.text_input("Model", value=v.get('model', ""))
            
            # ODOMETER: Default to 0 if blank to prevent crash
            odo_raw = v.get('odometer')
            current_odo = int(odo_raw) if odo_raw is not None else 0
            odometer = st.number_input("Odometer Reading (km)", value=current_odo, min_value=0)
            
        with col2:
            v_types = ["Sedan", "SUV", "4WD", "Van", "Truck"]
            vt_val = v.get('type', "Sedan")
            vt_idx = v_types.index(vt_val) if vt_val in v_types else 0
            v_type = st.selectbox("Vehicle Type", v_types, index=vt_idx)
            
            l_val = v.get('location', "Main Yard")
            l_idx = loc_options.index(l_val) if l_val in loc_options else 0
            location = st.selectbox("Current Location", options=loc_options, index=l_idx)
            
            status_list = ["Available", "Maintenance", "Rented"]
            s_val = v.get('status', "Available")
            s_idx = status_list.index(s_val) if s_val in status_list else 0
            status = st.selectbox("Status", status_list, index=s_idx, disabled=(s_val == "Rented"))
            
            # COLOR: Default to red if blank
            saved_color = v.get('color', "#ff4b4b")
            color = st.color_picker("Display Color", value=saved_color)

        # SUBMIT BUTTON: Must be inside form
        submitted = st.form_submit_button("Save Asset Details", use_container_width=True, type="primary")
        
    if submitted:
        if not plate:
            st.error("Number Plate is required.")
        else:
            payload = {
                "plate": plate, 
                "brand": brand, 
                "model": model, 
                "odometer": odometer, 
                "type": v_type, 
                "location": location, 
                "status": status, 
                "color": color
            }
            
            try:
                if mode == "add":
                    supabase.table("fleet").insert(payload).execute()
                    st.success("Asset added successfully.")
                else:
                    supabase.table("fleet").update(payload).eq("id", v['id']).execute()
                    st.success("Asset updated successfully.")
                
                st.session_state.fleet_view = "list"
                st.rerun()
            except Exception as e:
                st.error(f"Database Error: {e}")

    if st.button("⬅️ Back to List"):
        st.session_state.fleet_view = "list"
        st.rerun()

# --- 6. VIEW: LIST ASSETS ---
else:
    col_header, col_search = st.columns([1, 1])
    with col_header:
        st.button("➕ Add New Vehicle", on_click=enter_fleet_add)
    with col_search:
        search = st.text_input("🔍 Search Plate or Model", placeholder="e.g. JL 101").strip()

    f_res = supabase.table("fleet").select("*").order("plate").execute()
    
    if f_res.data:
        df_fleet = pd.DataFrame(f_res.data)
        st.write("---")
        
        # Table Header
        h1, h2, h3, h4 = st.columns([3, 2, 2, 1])
        h1.caption("**VEHICLE**")
        h2.caption("**LOCATION**")
        h3.caption("**DETAILS**")
        h4.caption("**ACTION**")

        for _, row in df_fleet.iterrows():
            s_plate = str(row['plate'])
            s_model = str(row['model'])
            
            if search and search.lower() not in s_plate.lower() and search.lower() not in s_model.lower():
                continue
                
            with st.container(border=True):
                r1, r2, r3, r4 = st.columns([3, 2, 2, 1])
                
                status = row['status']
                icon = "🟢" if status == "Available" else "🔴" if status == "Rented" else "🟡"
                
                r1.write(f"{icon} **{s_plate}**")
                r1.caption(f"📟 {row.get('odometer', 0):,} km")
                
                r2.write(f"{row['location']}")
                r2.caption(f"Status: {status}")
                
                # Show brand, model, and the selected color badge
                r3.write(f"{row['brand']}")
                r3.caption(f"{s_model} | {row.get('color', 'N/A')}")
                
                if r4.button("Edit", key=f"v_ed_{row['id']}", use_container_width=True):
                    st.session_state.selected_vehicle = row
                    st.session_state.fleet_view = "edit"
                    st.rerun()
    else:
        st.info("No vehicles found.")