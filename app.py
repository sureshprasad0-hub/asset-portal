import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. SECURE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("🔒 Security Hold: Check Streamlit Secrets.")
    st.stop()

# --- 2. DYNAMIC BRANDING ---
def get_setting(key_name, default):
    res = supabase.table("settings").select("config_value").eq("config_key", key_name).execute()
    return res.data[0]['config_value'] if res.data else default

company_name = get_setting("company_name", "YOUR RENTAL & TOURS")
st.set_page_config(page_title=company_name, layout="wide")

# --- 3. NAVIGATION ---
st.sidebar.title(f"🚢 {company_name}")
menu = ["📊 Dashboard", "🔑 Check-Out", "🚗 Fleet", "👥 Customers", "📈 Reports", "⚙️ Configuration"]
choice = st.sidebar.radio("Navigate", menu)

# --- 4. REPORTS TAB ---
if choice == "📈 Reports":
    st.header("Financial & Fleet Analytics")
    
    # Fetch all rentals
    r_res = supabase.table("rentals").select("total, date_out, status, fleet(brand)").execute()
    if r_res.data:
        df_r = pd.json_normalize(r_res.data)
        
        col1, col2, col3 = st.columns(3)
        total_rev = df_r['total'].sum()
        active_rentals = len(df_r[df_r['status'] == 'Active'])
        
        col1.metric("Total Revenue To Date", f"${total_rev:,.2f}")
        col2.metric("Active Contracts", active_rentals)
        col3.metric("Avg. Deal Size", f"${df_r['total'].mean():,.2f}")
        
        st.divider()
        st.subheader("Revenue Timeline")
        df_r['date_out'] = pd.to_datetime(df_r['date_out'])
        chart_data = df_r.groupby('date_out')['total'].sum()
        st.line_chart(chart_data)
    else:
        st.info("No rental data available for reporting yet.")

# --- 5. CONFIGURATION TAB ---
elif choice == "⚙️ Configuration":
    st.header("Portal Settings")
    
    tab1, tab2 = st.tabs(["Company Profile", "User Management"])
    
    with tab1:
        st.subheader("General Settings")
        new_comp_name = st.text_input("Change Company Name", value=company_name)
        if st.button("Update Branding"):
            supabase.table("settings").upsert({"config_key": "company_name", "config_value": new_comp_name}).execute()
            st.success("Branding updated! Refreshing...")
            st.rerun()
            
    with tab2:
        st.subheader("Authorized Portal Users")
        # Add User Form
        with st.expander("Add New User"):
            with st.form("add_user"):
                u, f, r = st.text_input("Username"), st.text_input("Full Name"), st.selectbox("Role", ["Admin", "Staff", "Manager"])
                if st.form_submit_button("Grant Access"):
                    supabase.table("portal_users").insert({"username": u, "full_name": f, "role": r}).execute()
                    st.rerun()
        
        # Display Users
        u_res = supabase.table("portal_users").select("*").execute()
        if u_res.data:
            st.table(pd.DataFrame(u_res.data)[['username', 'full_name', 'role', 'created_at']])

# --- 6. EXISTING LOGIC (DASHBOARD, CHECK-OUT, FLEET) ---
elif choice == "📊 Dashboard":
    st.header("Operations Overview")
    f_res = supabase.table("fleet").select("*").execute()
    if f_res.data:
        st.dataframe(pd.DataFrame(f_res.data)[['plate', 'brand', 'model', 'status', 'return_date']], use_container_width=True)

elif choice == "🔑 Check-Out":
    st.header("New Rental Agreement")
    # ... (Same checkout logic as previous code) ...

elif choice == "🚗 Fleet":
    st.header("Vehicle Inventory")
    # ... (Same inventory logic as previous code) ...

elif choice == "👥 Customers":
    st.header("Customer List")
    # ... (Same customer logic as previous code) ...