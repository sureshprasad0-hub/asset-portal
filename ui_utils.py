import streamlit as st

def apply_global_borders():
    st.markdown("""
        <style>
        .top-frame { position: fixed; top: 0; left: 0; width: 100%; height: 6px; background-color: #ff4b4b; z-index: 999999; }
        .right-frame { position: fixed; right: 0; top: 0; width: 10px; height: 100vh; background-color: #e0e0e0; z-index: 999999; }
        .bottom-frame { position: fixed; bottom: 0; left: 0; width: 100%; height: 20px; background-color: #e0e0e0; z-index: 999999; }
        .main .block-container { padding: 2rem; }
        </style>
        <div class="top-frame"></div><div class="right-frame"></div><div class="bottom-frame"></div>
    """, unsafe_allow_html=True)