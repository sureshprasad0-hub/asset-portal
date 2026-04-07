import streamlit as st
from supabase import create_client

# --- 1. GATEKEEPER: ADMIN ONLY ---
if st.session_state.get('user_role') != 'Admin':
    st.error("Admin Access Required."); st.stop()

# --- 2. CONNECTION ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
st.title("⚙️ System Settings")

# Fetch Company Name for the Header
c_res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res.data[0]['config_value'] if c_res.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 3. COMPANY CONFIGURATION ---
with st.expander("🏢 Company Branding", expanded=True):
    c_res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
    current_name = c_res.data[0]['config_value'] if c_res.data else "YOUR RENTAL & TOURS"
    
    new_name = st.text_input("Organisation Name", value=current_name).strip().upper()
    
    if st.button("Update Company Name"):
        supabase.table("settings").upsert({"config_key": "company_name", "config_value": new_name}).execute()
        st.success(f"Company name updated to: {new_name}")
        st.rerun()

# --- 4. VAT CONFIGURATION ---
with st.expander("💰 VAT & Financials", expanded=False):
    res = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
    current_vat = float(res.data[0]['config_value']) if res.data else 15.0
    new_vat = st.number_input("Global Fiji VAT Rate (%)", value=current_vat, step=0.5)

    if st.button("Update VAT Rate"):
        supabase.table("settings").upsert({"config_key": "vat_rate", "config_value": str(new_vat)}).execute()
        st.success(f"VAT updated to {new_vat}%")

# --- 5. STAFF ACCOUNT MANAGEMENT (UPDATED) ---
with st.expander("👥 Staff Account Management", expanded=False):
    # Fetch current users
    u_res = supabase.table("portal_users").select("*").order("username").execute()
    user_list = u_res.data if u_res.data else []
    usernames = [u['username'] for u in user_list]

    col_u1, col_u2 = st.columns(2)

    with col_u1:
        st.subheader("Add New Staff")
        with st.form("new_user_form", clear_on_submit=True):
            new_u = st.text_input("Username").strip().lower()
            new_p = st.text_input("Password", type="password")
            new_r = st.selectbox("Assign Role", ["Staff", "Manager", "Admin"])
            if st.form_submit_button("Create Account"):
                if new_u and new_p:
                    if new_u not in usernames:
                        supabase.table("portal_users").insert({
                            "username": new_u, 
                            "password_hash": new_p, 
                            "role": new_r, 
                            "full_name": new_u.title()
                        }).execute()
                        st.success(f"Account created for {new_u}")
                        st.rerun()
                    else:
                        st.error("Username already exists.")
                else:
                    st.error("Please provide both username and password.")

    with col_u2:
        st.subheader("Modify / Delete Staff")
        if usernames:
            selected_u = st.selectbox("Select Account", options=usernames)
            # Find the data for the selected user
            user_data = next(u for u in user_list if u['username'] == selected_u)
            
            # Change Role
            current_role_idx = ["Staff", "Manager", "Admin"].index(user_data['role'])
            new_role = st.selectbox("Update Role", ["Staff", "Manager", "Admin"], index=current_role_idx)
            
            if st.button("Update User Role"):
                supabase.table("portal_users").update({"role": new_role}).eq("username", selected_u).execute()
                st.success(f"Updated {selected_u} to {new_role}")
                st.rerun()

            st.divider()
            # Delete account (with safety check)
            if st.button(f"🗑️ Delete {selected_u}", type="secondary"):
                if selected_u == st.session_state.get('username'):
                    st.error("You cannot delete your own account.")
                else:
                    supabase.table("portal_users").delete().eq("username", selected_u).execute()
                    st.warning(f"Account {selected_u} has been removed.")
                    st.rerun()
        else:
            st.info("No other accounts found.")

# --- 6. BRAND MANAGEMENT ---
with st.expander("📋 Fleet Brand Setup", expanded=False):
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
            if st.button("Delete Brand", key="del_brand", type="secondary"):
                supabase.table("vehicle_brands").delete().eq("brand_name", remove_brand).execute()
                st.warning(f"Removed {remove_brand}")
                st.rerun()

# --- 7. LOCATION MANAGEMENT ---
with st.expander("📍 Branch Location Setup", expanded=False):
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
            if st.button("Delete Location", key="del_loc", type="secondary"):
                supabase.table("operating_locations").delete().eq("location_name", remove_loc).execute()
                st.warning(f"Removed {remove_loc}")
                st.rerun()