import streamlit as st
import pandas as pd
import numpy as np # Added for NaN handling
from datetime import datetime, date
from supabase import create_client, Client

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("👥 Customer Information")

# --- 3. SESSION STATE & HELPERS ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "list"
if 'selected_customer' not in st.session_state:
    st.session_state.selected_customer = None

def safe_date(date_val, default=date(1995, 1, 1)):
    if date_val is None or pd.isna(date_val): return default
    try:
        return datetime.strptime(str(date_val), '%Y-%m-%d').date()
    except:
        return default

# --- 4. DATA FETCHING ---
res = supabase.table("customers").select("*").order("name").execute()
# Ensure we handle empty data or NaN values immediately
df_all = pd.DataFrame(res.data) if res.data else pd.DataFrame()

# --- 5. TOP SECTION: STATS (FIXED FOR NaN) ---
if st.session_state.view_mode == "list":
    if not df_all.empty:
        st.write("### 📊 Registry Overview")
        col_a, col_b, col_c = st.columns(3)
        
        total_cust = len(df_all)
        
        # Clean date column for calculation: replace NaNs with today to avoid crash
        df_all['temp_expiry'] = df_all['dl_expiry'].apply(lambda x: safe_date(x, default=date.today()))
        expired_count = len(df_all[df_all['temp_expiry'] < date.today()])
        
        intl_count = len(df_all[df_all['country_of_issue'] != 'Fiji'])

        col_a.metric("Total Customers", total_cust)
        col_b.metric("Expired Licenses", expired_count)
        col_c.metric("International IDs", intl_count)
    st.divider()

# --- 6. FORM VIEW (ADD / EDIT) ---
if st.session_state.view_mode in ["add", "edit"]:
    cust = st.session_state.selected_customer
    with st.container(border=True):
        st.subheader("📝 Edit Profile" if cust else "➕ New Registration")
        with st.form("customer_form", clear_on_submit=False):
            f_name = st.text_input("Full Legal Name", value=cust['name'] if cust and not pd.isna(cust['name']) else "").strip()
            f_dob = st.date_input("Date of Birth", value=safe_date(cust['dob'] if cust else None))
            
            c1, c2 = st.columns(2)
            f_email = c1.text_input("Email", value=cust['email'] if cust and not pd.isna(cust['email']) else "")
            f_phone = c2.text_input("Mobile", value=cust['phone'] if cust and not pd.isna(cust['phone']) else "")
            f_address = st.text_area("Physical Address", value=cust['physical_address'] if cust and not pd.isna(cust['physical_address']) else "")

            st.divider()
            c3, c4 = st.columns(2)
            f_dl = c3.text_input("License No.", value=cust['dl_no'] if cust and not pd.isna(cust['dl_no']) else "").upper()
            f_expiry = c4.date_input("License Expiry", value=safe_date(cust['dl_expiry'] if cust else None, default=date.today()))
            
            f_country = st.selectbox("Issue Country", ["Fiji", "Australia", "NZ", "USA", "Other"], 
                                     index=0 if not cust else ["Fiji", "Australia", "NZ", "USA", "Other"].index(cust.get('country_of_issue', 'Fiji')))

            sub_col, can_col = st.columns(2)
            if sub_col.form_submit_button("💾 Save Record", use_container_width=True):
                if not f_name or not f_dl:
                    st.error("Name and License are required.")
                else:
                    try:
                        # Ensure no None/NaN values are sent to Supabase
                        payload = {
                            "name": f_name or "Unknown",
                            "dob": str(f_dob),
                            "email": f_email or "",
                            "phone": f_phone or "",
                            "physical_address": f_address or "",
                            "dl_no": f_dl,
                            "dl_expiry": str(f_expiry),
                            "country_of_issue": f_country
                        }

                        if cust:
                            supabase.table("customers").update(payload).eq("id", cust['id']).execute()
                        else:
                            supabase.table("customers").insert(payload).execute()
                        
                        st.session_state.view_mode = "list"
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

            if can_col.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.view_mode = "list"
                st.rerun()

# --- 7. LIST VIEW (SINGLE LINE FORMAT) ---
if st.session_state.view_mode == "list":
    st.button("➕ Add New Customer", on_click=lambda: st.session_state.update({"view_mode": "add"}), use_container_width=True)
    
    search = st.text_input("🔍 Search", placeholder="Name or License...")
    
    if not df_all.empty:
        st.write("---")
        for _, row in df_all.iterrows():
            # Handle NaN in search
            name_val = str(row['name']) if not pd.isna(row['name']) else ""
            dl_val = str(row['dl_no']) if not pd.isna(row['dl_no']) else ""
            
            if search and search.lower() not in name_val.lower() and search.lower() not in dl_val.lower():
                continue
                
            with st.container():
                r1, r2, r3, r4 = st.columns([3, 2, 2, 1])
                
                exp_date = safe_date(row['dl_expiry'])
                status_icon = "🔴" if exp_date < date.today() else "🟢"
                
                r1.write(f"{status_icon} {name_val}")
                r2.write(f"`{dl_val}` | {row['dl_expiry']}")
                r3.write(f"{row['phone'] if not pd.isna(row['phone']) else ''}")
                
                if r4.button("Edit", key=f"ed_{row['id']}", use_container_width=True):
                    st.session_state.selected_customer = row.to_dict()
                    st.session_state.view_mode = "edit"
                    st.rerun()
                st.write("---")