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
# Fetch Dropdown Options
try:
    brand_res = supabase.table("vehicle_brands").select("brand_name").order("brand_name").execute()
    brand_options = [b['brand_name'] for b in brand_res.data] if brand_res.data else ["Other"]
except: brand_options = ["Standard"]

try:
    loc_res = supabase.table("operating_locations").select("location_name").order("location_name").execute()
    loc_options = [l['location_name'] for l in loc_res.data] if loc_res.data else ["Main Office"]
except: loc_options = ["Suva"]

type_options = ["Sedan", "SUV", "4WD Pickup", "Van", "Luxury", "Bus"]

# Fetch Fleet Data
f_res = supabase.table("fleet").select("*").order("plate").execute()
df_fleet = pd.DataFrame(f_res.data) if f_res.data else pd.DataFrame()

# --- 5. TOP SECTION: STATS DASHBOARD (List View only) ---
if st.session_state.fleet_view == "list":
    if not df_fleet.empty:
        st.markdown("### 📊 Fleet Intelligence")
        m1, m2, m3 = st.columns(3)
        
        total_v = len(df_fleet)
        avail_v = len(df_fleet[df_fleet['status'] == 'Available'])
        maint_v = len(df_fleet[df_fleet['status'] == 'Maintenance'])
        rent_v = len(df_fleet[df_fleet['status'] == 'Rented'])

        with m1:
            st.metric("Total Assets", f"{total_v} Units")
        with m2:
            st.metric("Operational Ready", f"{avail_v} Avail", delta=f"{rent_v} Rented")
        with m3:
            st.metric("In Workshop", f"{maint_v} Maintenance", delta_color="inverse")
    st.divider()

# --- 6. FORM VIEW (ADD / EDIT) ---
if st.session_state.fleet_view in ["add", "edit"]:
    v = st.session_state.selected_vehicle
    with st.container(border=True):
        st.subheader("📝 Edit Vehicle Details" if v else "➕ Register New Asset")
        
        with st.form("fleet_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            f_plate = col1.text_input("License Plate", value=v['plate'] if v else "").strip().upper()
            
            # Brand Selection
            b_idx = brand_options.index(v['brand']) if v and v['brand'] in brand_options else 0
            f_brand = col2.selectbox("Brand/Make", options=brand_options, index=b_idx)
            
            col3, col4 = st.columns(2)
            f_model = col3.text_input("Model Name", value=v['model'] if v else "")
            f_color = col4.text_input("Vehicle Color", value=v.get('color', '') if v else "")
            
            col5, col6 = st.columns(2)
            t_idx = type_options.index(v['type']) if v and v.get('type') in type_options else 0
            f_type = col5.selectbox("Vehicle Type", options=type_options, index=t_idx)
            
            l_idx = loc_options.index(v['location']) if v and v['location'] in loc_options else 0
            f_location = col6.selectbox("Current Location", options=loc_options, index=l_idx)
            
            st.divider()
            sub_col, can_col = st.columns(2)
            
            if sub_col.form_submit_button("💾 Save to Inventory", use_container_width=True):
                if not f_plate or not f_brand:
                    st.error("Plate and Brand are mandatory.")
                else:
                    try:
                        payload = {
                            "plate": f_plate, "brand": f_brand, "model": f_model,
                            "color": f_color, "type": f_type, "location": f_location
                        }
                        if not v: payload["status"] = "Available" # Set default for new items

                        if v:
                            supabase.table("fleet").update(payload).eq("id", v['id']).execute()
                        else:
                            supabase.table("fleet").insert(payload).execute()
                        
                        st.session_state.fleet_view = "list"
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

            if can_col.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.fleet_view = "list"
                st.rerun()

# --- 7. LIST VIEW (SINGLE LINE REGISTRY) ---
if st.session_state.fleet_view == "list":
    st.button("➕ Register New Vehicle", on_click=enter_fleet_add, use_container_width=True)
    
    search = st.text_input("🔍 Quick Search", placeholder="Search by plate, model, or location...")
    
    if not df_fleet.empty:
        st.write("---")
        # Header Row matching Customer Page style
        h1, h2, h3, h4 = st.columns([3, 2, 2, 1])
        h1.caption("**ASSET / TYPE**")
        h2.caption("**LOCATION / STATUS**")
        h3.caption("**COLOR / BRAND**")
        h4.caption("**ACTION**")

        for _, row in df_fleet.iterrows():
            s_plate = str(row['plate'])
            s_model = str(row['model'])
            
            # Search Filter
            if search and search.lower() not in s_plate.lower() and search.lower() not in s_model.lower():
                continue
                
            with st.container():
                r1, r2, r3, r4 = st.columns([3, 2, 2, 1])
                
                status = row['status']
                icon = "🟢" if status == "Available" else "🔴" if status == "Rented" else "🟡"
                
                # Column 1: Plate and Type
                r1.write(f"{icon} **{s_plate}**")
                r1.caption(f"{row.get('type', 'N/A')}")
                
                # Column 2: Location and Status
                r2.write(f"{row['location']}")
                r2.caption(f"Status: {status}")
                
                # Column 3: Color and Brand
                r3.write(f"{row.get('color', 'N/A')}")
                r3.caption(f"{row['brand']} {s_model}")
                
                # Column 4: Edit Button
                if r4.button("Edit", key=f"v_ed_{row['id']}", use_container_width=True):
                    st.session_state.selected_vehicle = row.to_dict()
                    st.session_state.fleet_view = "edit"
                    st.rerun()
                st.write("---")
    else:
        st.info("No vehicles registered in the fleet.")