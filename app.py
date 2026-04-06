import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Asset Portal | Login", layout="centered", initial_sidebar_state="collapsed")

@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        st.error("Connection Error: Check Streamlit Secrets.")
        return None

supabase = init_connection()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🚢 Private Asset Portal")
    st.write("Secure access for **YOUR RENTAL & TOURS** staff.")
    with st.form("login_gate"):
        u = st.text_input("Username").strip().lower()
        p = st.text_input("Password", type="password").strip()
        if st.form_submit_button("Log In to Dashboard", use_container_width=True):
            # TEMPORARY DEBUG ONLY - DELETE AFTER TESTING
            res = supabase.table("portal_users").select("*").eq("username", u).execute()
            'res = supabase.table("portal_users").select("*").eq("username", u).eq("password_hash", p).execute()'
            if res.data:
                st.session_state.update({
                    "logged_in": True, 
                    "user_role": res.data[0]['role'], 
                    "user_name": res.data[0]['full_name']
                })
                st.rerun()
            else:
                st.error("Invalid Credentials.")
else:
    st.title(f"👋 Bula, {st.session_state['user_name']}!")
    st.info("The system is live. Please use the sidebar to navigate.")
    if st.button("Secure Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
