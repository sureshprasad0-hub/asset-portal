import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client

# --- 1. GATEKEEPER & CONNECTION ---
if not st.session_state.get('logged_in'): 
    st.warning("Please log in on the Home page first.")
    st.stop()

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Dashboard")

# Fetch Company Name for the Header
c_res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res.data[0]['config_value'] if c_res.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 2. DATA RETRIEVAL (FIXED FOR ERROR) ---
try:
    # FIXED: Added explicit foreign key relationships !fk_rentals_fleet and !fk_rentals_customers
    r_res = supabase.table("rentals").select(
        "*, fleet!fk_rentals_fleet(plate), customers!fk_rentals_customers(name)"
    ).eq("status", "Active").execute()
    
    overdue_count = 0
    if r_res.data:
        df_r = pd.json_normalize(r_res.data)
        today = datetime.now().date()
        # Ensure column names match the flattened JSON structure
        overdue = df_r[pd.to_datetime(df_r['date_in']).dt.date < today]
        overdue_count = len(overdue)
        if overdue_count > 0:
            with st.container(border=True):
                st.error(f"⚠️ {overdue_count} Overdue Rentals!")
                # Matching styling with simplified dataframes
                st.dataframe(
                    overdue[['fleet.plate', 'customers.name', 'date_in']], 
                    use_container_width=True, 
                    hide_index=True
                )

    # --- 3. UPCOMING MAINTENANCE ---
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

    # --- 4. FLEET SUMMARY TABLE ---
    st.divider()
    with st.container(border=True):
        st.subheader("Current Fleet Status")
        f_res = supabase.table("fleet").select("plate, brand, model, status").order("plate").execute()
        if f_res.data:
            df_f = pd.DataFrame(f_res.data)
            st.dataframe(df_f, use_container_width=True, hide_index=True)
            
            # Metric styling matching Check-Out performance indicators
            c1, c2, c3 = st.columns(3)
            c1.metric("Available", len(df_f[df_f['status'] == 'Available']))
            c2.metric("Rented", len(df_f[df_f['status'] == 'Rented']))
            c3.metric("Overdue", overdue_count, delta_color="inverse")

except Exception as e:
    st.error(f"PostgreSQL Connection Error: {e}")
    st.info("Ensure foreign key relationships (fk_rentals_fleet, fk_rentals_customers) are correctly named in your database.")