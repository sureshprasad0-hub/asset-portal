import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🚗 Fleet Inventory")

# Fetch Company Name for the Header
c_res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res.data[0]['config_value'] if c_res.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 3. FETCH DYNAMIC DROPDOWNS FROM SETTINGS ---
# Fetch Brands
try:
    brand_res = supabase.table("vehicle_brands").select("brand_name").order("brand_name").execute()
    brand_options = [b['brand_name'] for b in brand_res.data] if brand_res.data else ["Other"]
except:
    brand_options = ["Standard"]

# Fetch Locations
try:
    loc_res = supabase.table("operating_locations").select("location_name").order("location_name").execute()
    loc_options = [l['location_name'] for l in loc_res.data] if loc_res.data else ["Main Office"]
except:
    loc_options = ["Suva"]

# --- 4. ACTION: REGISTER NEW ASSET ---
with st.expander("➕ Register New Vehicle", expanded=False):
    with st.form("add_vehicle", clear_on_submit=True):
        col1, col2 = st.columns(2)
        plate = col1.text_input("License Plate").strip().upper()
        brand = col2.selectbox("Brand/Make", options=brand_options)
        
        col3, col4 = st.columns(2)
        model = col3.text_input("Model (e.g. Hilux)")
        location = col4.selectbox("Primary Location", options=loc_options)
        
        if st.form_submit_button("Add to Fleet", use_container_width=True):
            if plate and brand:
                try:
                    supabase.table("fleet").insert({
                        "plate": plate, 
                        "brand": brand, 
                        "model": model, 
                        "location": location,
                        "status": "Available"
                    }).execute()
                    st.success(f"Vehicle {plate} successfully added!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Database Error: {e}")
            else:
                st.warning("Please provide the Plate and Brand.")

# --- 5. DISPLAY & EDIT FLEET ---
st.subheader("Current Asset Registry")

f_res = supabase.table("fleet").select("*").order("plate").execute()

if f_res.data:
    df = pd.DataFrame(f_res.data)
    for index, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**{row['plate']}**")
            c1.caption(f"{row['brand']} {row['model']} | {row['location']}")
            
            status = row['status']
            color = "🟢" if status == "Available" else "🔴" if status == "Rented" else "🟡"
            c2.write(f"{color} {status}")
            
            if st.session_state.get('user_role') in ['Admin', 'Manager']:
                if status != "Rented":
                    options = ["Available", "Maintenance"]
                    idx = options.index(status) if status in options else 0
                    new_status = c3.selectbox("Update", options, index=idx, key=f"st_{row['id']}", label_visibility="collapsed")
                    if new_status != status:
                        supabase.table("fleet").update({"status": new_status}).eq("id", row['id']).execute()
                        st.rerun()
                else:
                    c3.caption("Locked (Active)")
else:
    st.info("No vehicles registered.")