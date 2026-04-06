import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. DATABASE CONNECTION ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

st.title("🚗 Fleet Inventory")

# --- 3. FETCH DATA FOR FORM (BRANDS & LOCATIONS) ---
# We fetch brands from the new lookup table we discussed for Settings
try:
    brand_res = supabase.table("vehicle_brands").select("brand_name").order("brand_name").execute()
    brand_list = [b['brand_name'] for b in brand_res.data] if brand_res.data else ["Other"]
except:
    brand_list = ["Toyota", "Hyundai", "Isuzu", "Kia", "Mazda"] # Fallback defaults

# --- 4. ACTION: REGISTER NEW ASSET ---
with st.expander("➕ Register New Vehicle", expanded=False):
    with st.form("add_vehicle", clear_on_submit=True):
        col1, col2 = st.columns(2)
        plate = col1.text_input("License Plate (e.g. LR1234)").strip().upper()
        # CHANGED: Now a selectbox instead of text_input
        brand = col2.selectbox("Make/Brand", options=brand_list)
        
        col3, col4 = st.columns(2)
        model = col3.text_input("Model (e.g. Hilux)")
        location = col4.selectbox("Primary Location", ["Suva", "Nadi", "Lautoka", "Pacific Harbor", "Savusavu"])
        
        if st.form_submit_button("Add to Fleet", use_container_width=True):
            if plate:
                try:
                    supabase.table("fleet").insert({
                        "plate": plate, 
                        "brand": brand, 
                        "model": model, 
                        "location": location,
                        "status": "Available"
                    }).execute()
                    st.success(f"Vehicle {plate} ({brand}) added to inventory!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding vehicle: {e}")
            else:
                st.warning("Please provide the License Plate number.")

# --- 5. DISPLAY & MANAGEMENT ---
st.subheader("Current Asset Registry")

# Fetch full fleet data
f_res = supabase.table("fleet").select("*").order("plate").execute()

if f_res.data:
    df = pd.DataFrame(f_res.data)
    
    for index, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            
            # Column 1: Identity
            c1.write(f"**{row['plate']}**")
            c1.caption(f"{row['brand']} {row['model']} | {row['location']}")
            
            # Column 2: Status with Color Indicators
            status = row['status']
            if status == "Available":
                c2.write("🟢 Available")
            elif status == "Rented":
                c2.write("🔴 Rented")
            else:
                c2.write("🟡 Maintenance")
            
            # Column 3: Quick Admin Update (Role-based)
            if st.session_state.get('user_role') in ['Admin', 'Manager']:
                if status != "Rented":
                    options = ["Available", "Maintenance"]
                    # Ensure current status is in the options list to avoid index errors
                    current_idx = options.index(status) if status in options else 0
                    
                    new_status = c3.selectbox(
                        "Set Status", 
                        options, 
                        index=current_idx, 
                        key=f"status_{row['id']}",
                        label_visibility="collapsed"
                    )
                    
                    if new_status != status:
                        supabase.table("fleet").update({"status": new_status}).eq("id", row['id']).execute()
                        st.rerun()
                else:
                    c3.caption("Locked (Active)")

else:
    st.info("No vehicles registered. Use the 'Register' box above to start.")