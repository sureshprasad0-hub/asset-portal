import streamlit as st
from datetime import datetime

def apply_global_borders():
    # Prepare dynamic data
    now = datetime.now().strftime("%d %b %Y | %H:%M")
    current_user = st.session_state.get('user_name', 'Guest User')

    st.markdown(f"""
        <style>
        /* TOP BANNER */
        .top-frame {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 30px;
            background-color: #e0e0e0; 
            z-index: 999999;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 15px;
            color: white;
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

        /* Push application content inside the frames */
        .main .block-container {{
            padding-top: 50px !important;
            padding-right: 2rem;
            padding-bottom: 2rem;
        }}
        </style>
        
        <div class="top-frame">
            <div>{now}</div>
            <div>👤 {current_user}</div>
        </div>
        <div class="right-frame"></div>
        <div class="bottom-frame"></div>
        """, unsafe_allow_html=True)