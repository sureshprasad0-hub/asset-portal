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