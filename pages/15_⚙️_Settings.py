import streamlit as st
from supabase import create_client
import base64

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
    # Fetch all branding settings at once
    set_res = supabase.table("settings").select("*").in_("config_key", ["company_name", "company_address", "company_phone", "company_email", "company_logo"]).execute()
    settings_dict = {item['config_key']: item['config_value'] for item in set_res.data}
    
    col_branding1, col_branding2 = st.columns(2)
    
    with col_branding1:
        new_name = st.text_input("Organisation Name", value=settings_dict.get("company_name", "YOUR RENTAL & TOURS")).strip().upper()
        new_address = st.text_input("Physical Address", value=settings_dict.get("company_address", "Suva, Fiji")).strip()
        
        # LOGO UPLOADER
        st.write("**Company Logo**")
        uploaded_logo = st.file_uploader("Upload Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        current_logo = settings_dict.get("company_logo")
        if current_logo:
            st.image(current_logo, width=100, caption="Current Logo")
        
    with col_branding2:
        new_email = st.text_input("Business Email", value=settings_dict.get("company_email", "info@rental.com.fj")).strip()
        new_phone = st.text_input("Phone Number", value=settings_dict.get("company_phone", "+679")).strip()
    
    if st.button("Update Organisation Details"):
        payload = [
            {"config_key": "company_name", "config_value": new_name},
            {"config_key": "company_address", "config_value": new_address},
            {"config_key": "company_email", "config_value": new_email},
            {"config_key": "company_phone", "config_value": new_phone}
        ]
        
        # Handle Logo conversion to Base64 for easy storage in Settings table
        if uploaded_logo:
            encoded_logo = base64.b64encode(uploaded_logo.read()).decode()
            logo_data_url = f"data:image/png;base64,{encoded_logo}"
            payload.append({"config_key": "company_logo", "config_value": logo_data_url})

        supabase.table("settings").upsert(payload).execute()
        st.success("Organisation details updated successfully.")
        st.rerun()

# --- 4. VAT & FINANCIAL CONFIGURATION ---
with st.expander("💰 VAT & Financials", expanded=False):
    res_vat = supabase.table("settings").select("config_value").eq("config_key", "vat_rate").execute()
    current_vat = float(res_vat.data[0]['config_value']) if res_vat.data else 15.0
    new_vat = st.number_input("Global Fiji VAT Rate (%)", value=current_vat, step=0.5)

    if st.button("Update VAT Rate"):
        supabase.table("settings").upsert({"config_key": "vat_rate", "config_value": str(new_vat)}).execute()
        st.success(f"VAT updated to {new_vat}%")

    st.divider()

    res_fuel = supabase.table("settings").select("config_value").eq("config_key", "fuel_surcharge").execute()
    current_fuel = float(res_fuel.data[0]['config_value']) if res_fuel.data else 0.00
    new_fuel = st.number_input("Fuel Surcharge per Litre ($)", value=current_fuel, min_value=0.00, step=0.01, format="%.2f")

    if st.button("Update Fuel Surcharge"):
        supabase.table("settings").upsert({"config_key": "fuel_surcharge", "config_value": str(new_fuel)}).execute()
        st.success(f"Fuel surcharge updated to ${new_fuel:.2f} per litre")

# --- 5. STAFF ACCOUNT MANAGEMENT ---
with st.expander("👥 Staff Account Management", expanded=False):
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
            user_data = next(u for u in user_list if u['username'] == selected_u)
            current_role_idx = ["Staff", "Manager", "Admin"].index(user_data['role'])
            new_role = st.selectbox("Update Role", ["Staff", "Manager", "Admin"], index=current_role_idx)
            
            if st.button("Update User Role"):
                supabase.table("portal_users").update({"role": new_role}).eq("username", selected_u).execute()
                st.success(f"Updated {selected_u} to {new_role}")
                st.rerun()

            st.divider()
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