import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client

# --- 1. GATEKEEPER ---
if not st.session_state.get('logged_in'): 
    st.warning("Please log in first.")
    st.stop()

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("🛠️ Fleet Maintenance Log")

# Fetch Company Name for the Header
c_res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res.data[0]['config_value'] if c_res.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 2. ADD NEW LOG ---
with st.expander("📝 Log New Service/Repair", expanded=False):
    # Fetch available vehicles for the dropdown
    v_res = supabase.table("fleet").select("id, plate").execute()
    if v_res.data:
        v_options = {v['plate']: v['id'] for v in v_res.data}
        
        with st.form("maint_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            v_plate = col1.selectbox("Select Vehicle", options=list(v_options.keys()))
            s_type = col2.selectbox("Service Type", ["Oil Change", "Tire Rotation", "Brake Repair", "General Inspection", "Body Work", "Electrical"])
            
            col3, col4 = st.columns(2)
            cost = col3.number_input("Cost ($)", min_value=0.0)
            provider = col4.text_input("Service Provider", placeholder="e.g. Workshop Name")
            
            notes = st.text_area("Detailed Work Notes")
            next_due = st.date_input("Next Service Due", datetime.now() + timedelta(days=180))
            
            decommission = st.checkbox("Move vehicle to 'Maintenance' status")

            if st.form_submit_button("Save Maintenance Record", use_container_width=True):
                try:
                    vid = v_options[v_plate]
                    # Insert Log
                    supabase.table("maintenance_logs").insert({
                        "vehicle_id": vid, 
                        "service_type": s_type, 
                        "cost": cost,
                        "provider": provider, 
                        "notes": notes, 
                        "next_service_date": str(next_due)
                    }).execute()
                    
                    # Update Fleet Status if requested
                    if decommission:
                        supabase.table("fleet").update({"status": "Maintenance"}).eq("id", vid).execute()
                    
                    st.success(f"Log saved for {v_plate}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save: {e}")
    else:
        st.info("No vehicles found in fleet to log maintenance for.")

# --- 3. HISTORY VIEW ---
st.divider()
st.subheader("Service History")
m_res = supabase.table("maintenance_logs").select("*, fleet(plate)").order("service_date", desc=True).execute()

if m_res.data:
    df = pd.json_normalize(m_res.data)
    # Formatting for clarity
    df_display = df[['service_date', 'fleet.plate', 'service_type', 'provider', 'cost', 'next_service_date']]
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Financial Insight
    total_maint = pd.to_numeric(df['cost']).sum()
    st.info(f"Total Maintenance Spend to Date: **${total_maint:,.2f}**")