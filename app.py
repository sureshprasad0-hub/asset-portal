import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONFIG & MOBILE RESPONSIVENESS ---
st.set_page_config(page_title="Asset Portal", layout="wide", initial_sidebar_state="expanded")

# --- 2. SECURE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error. Check Secrets.")
    st.stop()

# --- 3. CUSTOM STYLING (Watermark & Mobile UI) ---
st.markdown("""
    <style>
    /* Watermark for all pages */
    .main {
        background-image: url("https://www.svgrepo.com/show/490653/car.svg");
        background-repeat: no-repeat;
        background-position: center;
        background-attachment: fixed;
        background-size: 40% auto;
        opacity: 0.05;
    }
    /* Mobile-friendly buttons */
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
    </style>
    """, unsafe_allow_value=True)

# --- 4. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login_page():
    st.title("🚗 Business Portal Login")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            res = supabase.table("portal_users").select("*").eq("username", u).eq("password_hash", p).execute()
            if res.data:
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = res.data[0]['role']
                st.session_state['user_name'] = res.data[0]['full_name']
                st.rerun()
            else:
                st.error("Invalid credentials.")

if not st.session_state['logged_in']:
    login_page()
    st.stop()

# --- 5. SHARED LOGIC & NAVIGATION ---
def get_setting(k, d):
    res = supabase.table("settings").select("config_value").eq("config_key", k).execute()
    return res.data[0]['config_value'] if res.data else d

company_name = get_setting("company_name", "YOUR RENTAL & TOURS")
role = st.session_state['user_role']

st.sidebar.title(f"🚢 {company_name}")
st.sidebar.info(f"Logged in as: {st.session_state['user_name']} ({role})")

menu = ["📊 Dashboard", "🔑 Check-Out", "🚗 Fleet", "👥 Customers", "📈 Reports", "⚙️ Configuration"]
choice = st.sidebar.radio("Navigate", menu)

# --- GLOBAL "ADD" BUTTONS (Requirement 3) ---
with st.sidebar:
    st.divider()
    st.subheader("Quick Actions")
    if st.button("➕ New Rental"): st.session_state['nav'] = "🔑 Check-Out"
    if st.button("➕ Add Vehicle"): st.session_state['nav'] = "🚗 Fleet"
    if st.button("➕ Add Customer"): st.session_state['nav'] = "👥 Customers"

# --- 6. PAGE CONTENT ---

if choice == "📈 Reports":
    st.header("Business Performance Reports")
    r_res = supabase.table("rentals").select("*, fleet(brand, plate), customers(name)").execute()
    if r_res.data:
        df = pd.json_normalize(r_res.data)
        
        # Report 1: Revenue by Vehicle
        st.subheader("💰 Revenue by Asset")
        rev_by_car = df.groupby('fleet.plate')['total'].sum().sort_values(ascending=False)
        st.bar_chart(rev_by_car)
        
        # Report 2: Utilization Status
        st.subheader("🔄 Fleet Utilization")
        f_res = supabase.table("fleet").select("status").execute()
        df_f = pd.DataFrame(f_res.data)
        st.write(df_f['status'].value_counts())
        
        # Report 3: Monthly Growth
        df['date_out'] = pd.to_datetime(df['date_out'])
        monthly = df.set_index('date_out').resample('M')['total'].sum()
        st.line_chart(monthly)
    else:
        st.info("Insufficient data for reports.")

elif choice == "⚙️ Configuration":
    st.header("System Configuration")
    if role != "Admin":
        st.warning("Access Restricted to Admins only.")
    else:
        # Requirement 4: Logo and Company Modification
        col1, col2 = st.columns([1, 3])
        col1.image("https://www.svgrepo.com/show/490653/car.svg", width=100) # Logo placeholder
        with col2:
            new_name = st.text_input("Modify Company Name", value=company_name)
            if st.button("Save Changes"):
                supabase.table("settings").upsert({"config_key": "company_name", "config_value": new_name}).execute()
                st.rerun()
        
        st.divider()
        st.subheader("Manage Staff Access")
        with st.expander("Add New User"):
            with st.form("new_user"):
                nu, np, nr = st.text_input("Username"), st.text_input("Password"), st.selectbox("Role", ["Staff", "Manager", "Admin"])
                if st.form_submit_button("Create User"):
                    supabase.table("portal_users").insert({"username": nu, "password_hash": np, "role": nr}).execute()
                    st.success("User created.")

# (Other pages: Dashboard, Check-Out, Fleet, Customers remain as per previous functional logic)