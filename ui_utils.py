import streamlit as st
from datetime import datetime

# --- 1. PREPARE DYNAMIC DATA ---
now = datetime.now().strftime("%d %b %Y | %H:%M")
current_user = st.session_state.get('user_name', 'Guest User')

# --- 2. GLOBAL UI BORDERS & BANNER ---
st.markdown(f"""
    <style>
    /* TOP BORDER/BANNER */
    .top-frame {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 30px; /* Increased height to accommodate text */
        background-color: #e0e0e0; 
        z-index: 999999;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 15px;
        color: black;
        font-family: sans-serif;
        font-size: 12px;
        font-weight: bold;
    }}

    /* RIGHT BORDER */
    .right-frame {{
        position: fixed;
        right: 0;
        top: 0;
        width: 20px;
        height: 100vh;
        background-color: #e0e0e0;
        z-index: 999999;
    }}

    /* BOTTOM BORDER */
    .bottom-frame {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 20px;
        background-color: #e0e0e0;
        z-index: 999999;
    }}

    /* Adjust main content padding to account for thicker top banner */
    .main .block-container {{
        padding-top: 45px !important;
        padding-right: 2rem;
        padding-bottom: 2rem;
    }}
    </style>
    
    <div class="top-frame">
        <div class="top-left">{now}</div>
        <div class="top-right">👤 {current_user}</div>
    </div>
    <div class="right-frame"></div>
    <div class="bottom-frame"></div>
    """, unsafe_allow_html=True)