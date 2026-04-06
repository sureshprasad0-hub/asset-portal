import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Asset Portal | Login", layout="centered", initial_sidebar_state="collapsed")

# --- 1. CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

supabase = init_connection()

# --- 2. DEBUG TOGGLE (CFO USE ONLY) ---
# Turn this ON to see why the login is failing
debug_mode = st.sidebar.checkbox("Enable Login Debugging", value=False)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🚢 Private Asset Portal")
    st.write("Secure access for **YOUR RENTAL & TOURS** staff.")
    
    with st.form("login_gate"):
        u = st.text_input("Username").strip().lower()
        p = st.text_input("Password", type="password").strip()
        
        if st.form_submit_button("Log In to Dashboard", use_container_width=True):
            # STEP 1: Fetch the user by username ONLY to see if they exist
            res = supabase.table("portal_users").select("*").eq("username", u).execute()
            
            if debug_mode:
                st.write("### --- DEBUG INFO ---")
                st.write(f"Querying for Username: `{u}`")
                st.write("Data found in DB:", res.data)
            
            if res.data:
                user_record = res.data[0]
                
                # STEP 2: Check if 'password_hash' column exists or if it's named 'password'
                # We use a flexible check here to help you debug
                db_password = user_record.get('password_hash') or user_record.get('password')
                
                if debug_mode:
                    st.write(f"Password in DB: `{db_password}`")
                    st.write(f"Password entered: `{p}`")

                if db_password == p:
                    st.session_state.update({
                        "logged_in": True, 
                        "user_role": user_record.get('role', 'Staff'), 
                        "user_name": user_record.get('full_name', u)
                    })
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Invalid Credentials (Password Mismatch).")
            else:
                st.error("Invalid Credentials (User not found).")
else:
    st.title(f"👋 Bula, {st.session_state['user_name']}!")
    st.info("You are currently logged in.")
    if st.button("Secure Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
