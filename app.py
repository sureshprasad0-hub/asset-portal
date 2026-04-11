import streamlit as st
from supabase import create_client
from ui_utils import apply_global_borders 

# 1. Page Config must be FIRST
st.set_page_config(page_title="RCA Fiji | Login", layout="centered", initial_sidebar_state="collapsed")

# 2. Apply Borders immediately after config
apply_global_borders()

# --- CSS FIX FOR CLICKABILITY ---
st.markdown("""
    <style>
    .stApp { z-index: 1; }
    [data-testid="stForm"] { position: relative; z-index: 1000000; }
    </style>
    """, unsafe_allow_html=True)

# --- GLOBAL NAVIGATION LOGIC ---
# Initialize login state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Function to logout from anywhere
def logout():
    st.session_state.logged_in = False
    st.session_state.user_name = None
    st.session_state.user_role = None
    st.switch_page("app.py")

# --- LOGIN PAGE UI ---
if not st.session_state.logged_in:
    st.title("🔐 Secure Login")
    
    with st.form("login_form"):
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            # Replace with your actual authentication logic
            if user_input == "admin" and pass_input == "fiji2026":
                st.session_state.logged_in = True
                st.session_state.user_name = user_input
                st.session_state.user_role = "Admin"
                
                # SUCCESSFUL REDIRECT TO DASHBOARD
                st.switch_page("pages/01_📊_Dashboard.py")
            else:
                st.error("Invalid credentials")
    
    st.stop()

# Fallback: If logged in and on app.py, go to Dashboard
st.switch_page("pages/01_📊_Dashboard.py")