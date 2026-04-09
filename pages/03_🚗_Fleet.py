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
            
            # Index safety for dynamic selectboxes
            b_idx = brand_options.index(v['brand']) if v.get('brand') in brand_options else 0
            brand = st.selectbox("Brand", options=brand_options, index=b_idx)
            
            model = st.text_input("Model", value=v.get('model', ""))
            
            # ODOMETER BUTTON/FIELD
            odometer = st.number_input("Odometer Reading (km)", value=int(v.get('odometer', 0)), min_value=0, help="Initial or corrected mileage.")
            
        with col2:
            v_types = ["Sedan", "SUV", "4WD", "Van", "Truck"]
            vt_idx = v_types.index(v['type']) if v.get('type') in v_types else 0
            v_type = st.selectbox("Vehicle Type", v_types, index=vt_idx)
            
            l_idx = loc_options.index(v['location']) if v.get('location') in loc_options else 0
            location = st.selectbox("Current Location", options=loc_options, index=l_idx)
            
            status_list = ["Available", "Maintenance", "Rented"]
            s_idx = status_list.index(v['status']) if v.get('status') in status_list else 0