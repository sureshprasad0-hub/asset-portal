import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. SECURE CLOUD CONNECTION ---
# This pulls directly from Streamlit Cloud > Settings > Secrets
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("🔒 Security Hold: Supabase credentials not found in Secrets.")
    st.info("Action: Go to Streamlit Cloud Settings > Secrets and add SUPABASE_URL and SUPABASE_KEY.")
    st.stop()

# --- 2. BRANDING & INITIALIZATION ---
def get_company_name():
    try:
        res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
        return res.data[0]['config_value'] if res.data else None
    except:
        return None

company_name = get_company_name()

if not company_name:
    st.set_page_config(page_title="System Setup", layout="centered")
    st.title("🚢 Private Asset Portal Initialization")
    with st.form("setup_form"):
        new_name = st.text_input("Enter Project/Venture Name:", placeholder="e.g., Sankylam Asset Management")
        if st.form_submit_button("Initialize Cloud Database"):
            if new_name:
                supabase.table("settings").insert({"config_key": "company_name", "config_value": new_name}).execute()
                st.rerun()
else:
    # --- MAIN APPLICATION INTERFACE ---
    st.set_page_config(page_title=f"{company_name} | Portal", layout="wide")
    st.sidebar.title(f"🚢 {company_name}")
    
    menu = ["📊 Dashboard", "🔑 Check-Out", "🚗 Fleet Inventory", "👥 Customers"]
    choice = st.sidebar.radio("Navigation", menu)

    # --- 3. DASHBOARD (Live Oversight) ---
    if choice == "📊 Dashboard":
        st.header("Real-Time Fleet Status")
        
        # Fetch Fleet from Postgres
        f_res = supabase.table("fleet").select("*").execute()
        df_f = pd.DataFrame(f_res.data)
        
        if not df_f.empty:
            def color_status(val):
                if val == 'Available': return 'background-color: #d4edda; color: #155724'
                if val == 'Rented': return 'background-color: #f8d7da; color: #721c24'
                return 'background-color: #fff3cd; color: #856404'

            # Reordering columns for clarity
            display_cols = ['plate', 'brand', 'model', 'status', 'return_date']
            st.dataframe(df_f[display_cols].style.map(color_status, subset=['status']), use_container_width=True)
        else:
            st.info("Fleet is empty. Add your first vehicle in 'Fleet Inventory'.")

        # Active Rentals View
        st.divider()
        st.subheader("Current Active Agreements")
        r_res = supabase.table("rentals").select("id, total, date_out, date_in, fleet(plate), customers(name)").eq("status", "Active").execute()
        if r_res.data:
            # Flattening the join for a clean table
            flat_data = []
            for r in r_res.data:
                flat_data.append({
                    "ID": r['id'],
                    "Vehicle": r['fleet']['plate'],
                    "Customer": r['customers']['name'],
                    "Total ($)": f"{r['total']:,.2f}",
                    "Due Back": r['date_in']
                })
            st.table(flat_data)

    # --- 4. CHECK-OUT (Reactive Calculator) ---
    elif choice == "🔑 Check-Out":
        st.header("New Agreement")
        v_data = supabase.table("fleet").select("id, plate").eq("status", "Available").execute().data
        c_data = supabase.table("customers").select("id, name").execute().data

        if not v_data or not c_data:
            st.error("Action Required: Add available vehicles and register customers first.")
        else:
            col1, col2 = st.columns(2)
            v_plate = col1.selectbox("Select Vehicle", [x['plate'] for x in v_data])
            c_name = col2.selectbox("Select Customer", [x['name'] for x in c_data])
            
            col3, col4 = st.columns(2)
            d_out = col3.date_input("Out Date", datetime.now())
            d_in = col4.date_input("Return Date", datetime.now())
            
            # Auto-calculate duration
            days = max((d_in - d_out).days, 1)
            
            col5, col6 = st.columns(2)
            rate = col5.number_input("Daily Rate ($)", min_value=0.0, value=100.0)
            bond = col6.number_input("Security Bond ($)", min_value=0.0, value=500.0)
            
            total_due = (rate * days) + bond
            
            st.divider()
            ma, mb, mc = st.columns(3)
            ma.metric("Duration", f"{days} Days")
            mb.metric("Subtotal", f"${rate * days:,.2f}")
            mc.subheader(f"Total to Collect: :blue[${total_due:,.2f}]")
            
            if st.button("Confirm & Sync to Cloud", use_container_width=True):
                vid = [x['id'] for x in v_data if x['plate'] == v_plate][0]
                cid = [x['id'] for x in c_data if x['name'] == c_name][0]
                
                # Update Database
                supabase.table("rentals").insert({
                    "vehicle_id": vid, "customer_id": cid, "rate": rate, 
                    "days": days, "bond": bond, "total": total_due, 
                    "date_out": str(d_out), "date_in": str(d_in), "status": "Active"
                }).execute()
                
                supabase.table("fleet").update({"status": "Rented", "return_date": str(d_in)}).eq("id", vid).execute()
                st.success(f"Agreement confirmed for {v_plate}!")
                st.balloons()

    # --- 5. FLEET & CUSTOMER MANAGEMENT ---
    elif choice == "🚗 Fleet Inventory":
        st.header("Asset Management")
        with st.expander("Add New Vehicle"):
            with st.form("v_add", clear_on_submit=True):
                p, b, m = st.text_input("Plate"), st.text_input("Brand"), st.text_input("Model")
                if st.form_submit_button("Save to Cloud"):
                    supabase.table("fleet").insert({"plate": p, "brand": b, "model": m, "status": "Available", "return_date": "-"}).execute()
                    st.rerun()
        
        # Edit Status logic
        st.subheader("Update Vehicle Status")
        f_res = supabase.table("fleet").select("*").execute()
        for row in f_res.data:
            with st.expander(f"Edit {row['plate']}"):
                new_s = st.selectbox("Status", ["Available", "Rented", "Maintenance"], 
                                   index=["Available", "Rented", "Maintenance"].index(row['status']), key=f"s_{row['id']}")
                if st.button("Apply", key=f"b_{row['id']}"):
                    supabase.table("fleet").update({"status": new_s}).eq("id", row['id']).execute()
                    st.rerun()

    elif choice == "👥 Customers":
        st.header("Customer Directory")
        with st.expander("Register New Customer"):
            with st.form("c_add", clear_on_submit=True):
                n, d, ph = st.text_input("Full Name"), st.text_input("DL No"), st.text_input("Phone")
                if st.form_submit_button("Register"):
                    supabase.table("customers").insert({"name": n, "dl_no": d, "phone": ph}).execute()
                    st.rerun()