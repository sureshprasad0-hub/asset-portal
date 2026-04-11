import streamlit as st
from supabase import create_client
from ui_utils import apply_global_borders 

# 1. Page Config must be FIRST
st.set_page_config(page_title="RCA Fiji | Login", layout="centered", initial_sidebar_state="collapsed")

# 2. Apply Borders immediately after config
apply_global_borders()

# --- CSS FIX FOR CLICKABILITY ---
# This ensures the main content area is not blocked by the fixed frames
st.markdown("""
    <style>
    .stApp {
        z-index: 1;
    }
    /* Ensure the form container is above the background frames */
    [data-testid="stForm"] {
        position: relative;
        z-index: 1000000; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

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
                
                # SUCCESSFUL REDIRECT
                st.switch_page("pages/01_📊_Dashboard.py")
            else:
                st.error("Invalid credentials")
    
    st.stop()

# Fallback: If someone navigates to app.py while already logged in
st.switch_page("pages/01_📊_Dashboard.py")