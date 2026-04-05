import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. SUPABASE CONNECTION ---
# In production, these should be in st.secrets
url = st.sidebar.text_input("Supabase URL", type="password")
key = st.sidebar.text_input("Supabase API Key", type="password")

if not url or not key:
    st.warning("Please enter your Supabase credentials in the sidebar to begin.")
    st.stop()

supabase: Client = create_client(url, key)

# --- 2. BRANDING ---
def get_company_name():
    res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
    return res.data[0]['config_value'] if res.data else None

company_name = get_company_name()

# --- 3. SYSTEM INITIALIZATION ---
if not company_name:
    st.title("🚢 Private Asset Portal Setup")
    new_name = st.text_input("Project Name:")
    if st.button("Initialize Cloud Database"):
        supabase.table("settings").insert({"config_key": "company_name", "config_value": new_name}).execute()
        st.rerun()
else:
    st.set_page_config(page_title=company_name, layout="wide")
    st.sidebar.title(f"🚢 {company_name}")
    menu = ["📊 Dashboard", "🔑 Check-Out", "🚗 Fleet Inventory", "👥 Customers"]
    choice = st.sidebar.radio("Navigation", menu)

    # --- 4. DASHBOARD (Multi-User Live View) ---
    if choice == "📊 Dashboard":
        st.header("Real-Time Fleet Oversight")
        # Fetch data from Postgres
        res = supabase.table("fleet").select("*").execute()
        df_f = pd.DataFrame(res.data)
        
        if not df_f.empty:
            def color_status(val):
                if val == 'Available': return 'background-color: #d4edda; color: #155724'
                if val == 'Rented': return 'background-color: #f8d7da; color: #721c24'
                return 'background-color: #fff3cd; color: #856404'
            
            st.dataframe(df_f[['plate', 'brand', 'status', 'return_date']].style.map(color_status, subset=['status']), use_container_width=True)
        
        st.divider()
        st.subheader("Active Rental Contracts")
        # Join logic handled via Supabase select
        rent_res = supabase.table("rentals").select("id, total, date_out, date_in, fleet(plate), customers(name)").eq("status", "Active").execute()
        if rent_res.data:
            st.table(rent_res.data)

    # --- 5. CHECK-OUT (The Cloud Calculator) ---
    elif choice == "🔑 Check-Out":
        st.header("New Cloud Agreement")
        v_data = supabase.table("fleet").select("id, plate").eq("status", "Available").execute().data
        c_data = supabase.table("customers").select("id, name").execute().data

        if not v_data or not c_data:
            st.error("Ensure you have Available Vehicles and Registered Customers.")
        else:
            col1, col2 = st.columns(2)
            v_plate = col1.selectbox("Vehicle", [x['plate'] for x in v_data])
            c_name = col2.selectbox("Customer", [x['name'] for x in c_data])
            
            col3, col4 = st.columns(2)
            d_out = col3.date_input("Start Date", datetime.now())
            d_in = col4.date_input("End Date", datetime.now())
            
            days = max((d_in - d_out).days, 1)
            rate = st.number_input("Daily Rate ($)", value=100.0)
            bond = st.number_input("Bond ($)", value=500.0)
            total = (rate * days) + bond
            
            st.metric("Total to Collect", f"${total:,.2f}")
            
            if st.button("Finalize & Sync to Cloud"):
                vid = [x['id'] for x in v_data if x['plate'] == v_plate][0]
                cid = [x['id'] for x in c_data if x['name'] == c_name][0]
                
                # Insert Rental
                supabase.table("rentals").insert({
                    "vehicle_id": vid, "customer_id": cid, "rate": rate, 
                    "days": days, "bond": bond, "total": total, 
                    "date_out": str(d_out), "date_in": str(d_in), "status": "Active"
                }).execute()
                
                # Update Fleet
                supabase.table("fleet").update({"status": "Rented", "return_date": str(d_in)}).eq("id", vid).execute()
                st.success("Synchronized successfully!")

    # --- 6. INVENTORY & CUSTOMERS ---
    elif choice == "🚗 Fleet Inventory":
        with st.form("add_v", clear_on_submit=True):
            p, b, m = st.text_input("Plate"), st.text_input("Brand"), st.text_input("Model")
            if st.form_submit_button("Save to Cloud"):
                supabase.table("fleet").insert({"plate": p, "brand": b, "model": m, "status": "Available", "return_date": "-"}).execute()
                st.rerun()

    elif choice == "👥 Customers":
        with st.form("add_c", clear_on_submit=True):
            n, d, ph = st.text_input("Name"), st.text_input("DL No"), st.text_input("Phone")
            if st.form_submit_button("Register Customer"):
                supabase.table("customers").insert({"name": n, "dl_no": d, "phone": ph}).execute()
                st.rerun()