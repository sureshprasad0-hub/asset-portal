import streamlit as st
from supabase import create_client
# Ensure the utility is imported
from ui_utils import apply_global_borders 

# 1. Page Config must be FIRST
st.set_page_config(page_title="RCA Fiji | Login", layout="centered", initial_sidebar_state="collapsed")

# 2. Apply Borders immediately after config
apply_global_borders()

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
            # Add your authentication logic here
            if user_input == "admin" and pass_input == "fiji2026":
                st.session_state.logged_in = True
                st.session_state.user_name = user_input
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    # CRITICAL: Stop the script here so the rest of the app doesn't run
    st.stop()

# If already logged in, show the rest of the application or redirect
st.success(f"Welcome back, {st.session_state.user_name}!")