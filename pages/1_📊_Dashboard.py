import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client

if not st.session_state.get('logged_in'): st.stop()
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Operations Dashboard")

# --- 1. OVERDUE RENTALS ---
r_res = supabase.table("rentals").select("*, fleet(plate), customers(name)").eq("status", "Active").execute()
overdue_count = 0
if r_res.data:
    df_r = pd.json_normalize(r_res.data)
    today = datetime.now().date()
    overdue = df_r[pd.to_datetime(df_r['date_in']).dt.date < today]
    overdue_count = len(overdue)
    if overdue_count > 0:
        st.error(f"⚠️ {overdue_count} Overdue Rentals!")
        st.dataframe(overdue[['fleet.plate', 'customers.name', 'date_in']], use_container_width=True, hide_index=True)

# --- 2. UPCOMING MAINTENANCE ---
next_week = (datetime.now() + timedelta(days=7)).date()
m_res = supabase.table("maintenance_logs").select("*, fleet(plate)").execute()
maint_count = 0
if m_res.data:
    df_m = pd.json_normalize(m_res.data)
    upcoming = df_m[(pd.to_datetime(df_m['next_service_date']).dt.date >= datetime.now().date()) & 
                    (pd.to_datetime(df_m['next_service_date']).dt.date <= next_week)]
    maint_count = len(upcoming)
    if maint_count > 0:
        st.warning(f"🔧 {maint_count} Vehicles Due for Service Soon")

# --- 3. FLEET SUMMARY TABLE ---
st.divider()
st.subheader("Current Fleet Status")
f_res = supabase.table("fleet").select("plate, brand, model, status").order("plate").execute()
if f_res.data:
    df_f = pd.DataFrame(f_res.data)
    st.dataframe(df_f, use_container_width=True, hide_index=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Available", len(df_f[df_f['status'] == 'Available']))
    c2.metric("Rented", len(df_f[df_f['status'] == 'Rented']))
    c3.metric("Overdue", overdue_count, delta_color="inverse")