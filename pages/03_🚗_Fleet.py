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
    loc_options = [l['location_name'] for l in loc_res.data] if l_res.data else ["Main Yard"]
except:
    brand_options = ["Standard"]
    loc_options = ["Main Yard"]

# --- 5. VIEW: ADD / EDIT FORM ---
if st.session_state.fleet_view in ["add", "edit"]:
    mode = st.session_state.fleet_view
    v = st.session_state.selected_vehicle if mode == "edit" else {}
    
    st.subheader("🛠️ Asset Details" if mode == "edit" else "➕ Register New Asset")
    
    # Use the form block
    with st.form("vehicle_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            plate = st.text_input("Number Plate", value=v.get('plate', "")).strip().upper()
            brand = st.selectbox("Brand", options=brand_options, index=brand_options.index(v['brand']) if v.get('brand') in brand_options else 0)
            model = st.text_input("Model", value=v.get('model', ""))
            # ODOMETER OVERRIDE FIELD
            odometer = st.number_input("Odometer Reading (km)", value=int(v.get('odometer', 0)), min_value=0, help="This is updated automatically during Check-In, but can be overridden here.")
            
        with col2:
            v_type = st.selectbox("Vehicle Type", ["Sedan", "SUV", "4WD", "Van", "Truck"], index=0)
            location = st.selectbox("Current Location", options=loc_options)
            status = st.selectbox("Status", ["Available", "Maintenance", "Rented"], disabled=(v.get('status') == "Rented"))
            color = st.color_picker("Display Color", value=v.get('color', "#ff4b4b"))

        # The submit button MUST be inside the 'with st.form' block
        submitted = st.form_submit_button("Save Asset Details", use_container_width=True, type="primary")
        
        if submitted:
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
                    st.success("Asset added to registry.")
                else:
                    supabase.table("fleet").update(payload).eq("id", v['id']).execute()
                    st.success("Asset details updated successfully.")
                
                st.session_state.fleet_view = "list"
                st.rerun()
            except Exception as e:
                st.error(f"Error saving asset: {e}")

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
            
            # Search Filter
            if search and search.lower() not in s_plate.lower() and search.lower() not in s_model.lower():
                continue
                
            with st.container(border=True):
                r1, r2, r3, r4 = st.columns([3, 2, 2, 1])
                
                status = row['status']
                icon = "🟢" if status == "Available" else "🔴" if status == "Rented" else "🟡"
                
                # Column 1: Plate and Odometer
                r1.write(f"{icon} **{s_plate}**")
                r1.caption(f"📟 {row.get('odometer', 0):,} km")
                
                # Column 2: Location and Status
                r2.write(f"{row['location']}")
                r2.caption(f"Status: {status}")
                
                # Column 3: Brand, Model, and Color
                r3.write(f"{row['brand']}")
                r3.caption(f"{s_model} | {row.get('color', 'N/A')}")
                
                # Column 4: Edit Button
                if r4.button("Edit", key=f"v_ed_{row['id']}", use_container_width=True):
                    st.session_state.selected_vehicle = row
                    st.session_state.fleet_view = "edit"
                    st.rerun()
    else:
        st.info("No vehicles currently in the database.")