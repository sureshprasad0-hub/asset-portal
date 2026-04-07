import streamlit as st
from supabase import create_client

if st.session_state.get('user_role') != 'Admin':
    st.error("Admin Access Required."); st.stop()

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
st.title("⚙️ System Settings")

# VAT Configuration
res = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
current_vat = float(res.data[0]['config_value']) if res.data else 15.0
new_vat = st.number_input("Global Fiji VAT Rate (%)", value=current_vat, step=0.5)

if st.button("Update VAT Rate"):
    supabase.table("settings").upsert({"config_key": "vat_rate", "config_value": str(new_vat)}).execute()
    st.success(f"VAT updated to {new_vat}%")

# User Management
st.divider()
st.subheader("Add Staff Account")
with st.form("new_user"):
    u, p = st.text_input("Username"), st.text_input("Password")
    r = st.selectbox("Role", ["Staff", "Manager", "Admin"])
    if st.form_submit_button("Create User"):
        supabase.table("portal_users").insert({"username":u, "password_hash":p, "role":r, "full_name":u.title()}).execute()
        st.success("User added.")
        
        # --- BRAND MANAGEMENT SECTION ---
st.divider()
st.subheader("📋 Fleet Brand Setup")

# Fetch current brands
b_res = supabase.table("vehicle_brands").select("*").order("brand_name").execute()
brands = [b['brand_name'] for b in b_res.data] if b_res.data else []

col_a, col_b = st.columns(2)

with col_a:
    new_brand = st.text_input("Add New Brand", placeholder="e.g. Suzuki").strip().title()
    if st.button("Save Brand"):
        if new_brand and new_brand not in brands:
            supabase.table("vehicle_brands").insert({"brand_name": new_brand}).execute()
            st.success(f"Added {new_brand}")
            st.rerun()

with col_b:
    if brands:
        remove_brand = st.selectbox("Remove Existing Brand", options=brands)
        if st.button("Delete Brand", type="secondary"):
            supabase.table("vehicle_brands").delete().eq("brand_name", remove_brand).execute()
            st.warning(f"Removed {remove_brand}")
            st.rerun()

# --- LOCATION MANAGEMENT SECTION ---
st.divider()
st.subheader("📍 Branch Location Setup")

# Fetch current locations
loc_res = supabase.table("operating_locations").select("*").order("location_name").execute()
locations = [l['location_name'] for l in loc_res.data] if loc_res.data else []

col_c, col_d = st.columns(2)

with col_c:
    new_loc = st.text_input("Add New Branch", placeholder="e.g. Rakiraki").strip().title()
    if st.button("Save Location"):
        if new_loc and new_loc not in locations:
            supabase.table("operating_locations").insert({"location_name": new_loc}).execute()
            st.success(f"Added {new_loc} Branch")
            st.rerun()

with col_d:
    if locations:
        remove_loc = st.selectbox("Remove Branch", options=locations)
        if st.button("Delete Location", type="secondary"):
            supabase.table("operating_locations").delete().eq("location_name", remove_loc).execute()
            st.warning(f"Removed {remove_loc}")
            st.rerun()