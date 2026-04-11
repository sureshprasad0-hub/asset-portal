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
            height: 20px;
            background-color: #e0e0e0; 
            z-index: 999999;
        }}
        

        /* BOTTOM BORDER - Now contains Metadata */
        .bottom-frame {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 30px;
            background-color: #e0e0e0;
            z-index: 999999;
            display: flex;
            align-items: center;
            padding: 0 15px;
            color: black; /* Text color updated to black */
            font-family: sans-serif;
            font-size: 12px;
            font-weight: bold;
        }}

        /* Layout helpers for bottom border alignment */
        .bottom-left {{
            flex: 1;
            text-align: left;
        }}
        .bottom-center {{
            flex: 1;
            text-align: center;
        }}
        .bottom-right-spacer {{
            flex: 1;
        }}

        /* Push application content inside the frames */
        .main .block-container {{
            padding-top: 50px !important;
            padding-right: 2rem;
            padding-bottom: 50px !important; /* Added bottom padding for visibility */
        }}
        </style>
        
        <div class="top-frame"></div>
        <div class="right-frame"></div>
        <div class="bottom-frame">
            <div class="bottom-left">{now}</div>
            <div class="bottom-center">👤 {current_user}</div>
            <div class="bottom-right-spacer"></div>
        </div>
        """, unsafe_allow_html=True)