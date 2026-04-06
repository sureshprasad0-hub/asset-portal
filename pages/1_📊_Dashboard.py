import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

if not st.session_state.get('logged_in'):
    st.warning("Please log in first."); st.stop()

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
st.title("📊 Operations Dashboard")

# Overdue Logic
r_res = supabase.table("rentals").select("*, fleet(plate), customers(name)").eq("status", "Active").execute()
if r_res.data:
    df = pd.json_normalize(r_res.data)
    df['date_in'] = pd.to_datetime(df['date_in']).dt.date
    overdue = df[df['date_in'] < datetime.now().date()]
    if not overdue.empty:
        st.error(f"⚠️ {len(overdue)} Vehicles Overdue!")
        st.dataframe(overdue[['fleet.plate', 'customers.name', 'date_in']], use_container_width=True)

# Fleet Summary
st.subheader("Live Fleet Status")
f_res = supabase.table("fleet").select("plate, brand, model, status, location").execute()
if f_res.data:
    st.dataframe(pd.DataFrame(f_res.data), use_container_width=True, hide_index=True)