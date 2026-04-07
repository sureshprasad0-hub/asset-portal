import streamlit as st
import pandas as pd
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
    if not date_val: return default
    try:
        return datetime.strptime(str(date_val), '%Y-%m-%d').date()
    except:
        return default

# --- 4. DATA FETCHING (PRE-LOAD FOR STATS) ---
res = supabase.table("customers").select("*").order("name").execute()
df_all = pd.DataFrame(res.data) if res.data else pd.DataFrame()

# --- 5. TOP SECTION: CUSTOMER STATS ---
if st.session_state.view_mode == "list":
    if not df_all.empty:
        st.write("### 📊 Registry Overview")
        col_a, col_b, col_c = st.columns(3)
        
        total_cust = len(df_all)
        # Convert to date objects for comparison
        df_all['expiry_dt'] = pd.to_datetime(df_all['dl_expiry']).dt.date
        expired_count = len(df_all[df_all['expiry_dt'] < date.today()])
        intl_count = len(df_all[df_all['country_of_issue'] != 'Fiji'])

        col_a.metric("Total Customers", total_cust)
        col_b.metric("Expired Licenses", expired_count, delta="-Risk" if expired_count > 0 else None, delta_color="inverse")
        col_c.metric("International IDs", intl_count)
    st.divider()

# --- 6. FORM VIEW (ADD / EDIT) ---
if st.session_state.view_mode in ["add", "edit"]:
    cust = st.session_state.selected_customer
    with st.container(border=True):
        st.subheader("📝 Edit Profile" if cust else "➕ New Registration")
        with st.form("customer_form", clear_on_submit=False):
            f_name = st.text_input("Full Legal Name", value=cust['name'] if cust else "").strip()
            f_dob = st.date_input("Date of Birth", value=safe_date(cust['dob'] if cust else None))
            
            c1, c2 = st.columns(2)
            f_email = c1.text_input("Email", value=cust['email'] if cust else "")
            f_phone = c2.text_input("Mobile", value=cust['phone'] if cust else "")
            f_address = st.text_area("Physical Address", value=cust['physical_address'] if cust else "")

            st.divider()
            c3, c4 = st.columns(2)
            f_dl = c3.text_input("License No.", value=cust['dl_no'] if cust else "").upper()
            f_expiry = c4.date_input("License Expiry", value=safe_date(cust['dl_expiry'] if cust else None, default=date.today()))
            
            f_country = st.selectbox("Issue Country", ["Fiji", "Australia", "NZ", "USA", "Other"], 
                                     index=0 if not cust else ["Fiji", "Australia", "NZ", "USA", "Other"].index(cust.get('country_of_issue', 'Fiji')))
            
            license_file = st.file_uploader("Upload ID Scan", type=['png', 'jpg', 'jpeg', 'pdf'])

            sub_col, can_col = st.columns(2)
            if sub_col.form_submit_button("💾 Save Record", use_container_width=True):
                # Age & Expiry Logic
                age = (date.today() - f_dob).days // 365
                if not f_name or not f_dl:
                    st.error("Name and License are required.")
                elif age < 21:
                    st.error(f"Underage Violation ({age} yrs)")
                elif f_expiry < date.today():
                    st.error("License Expired")
                else:
                    try:
                        f_path = cust.get('license_scan_path') if cust else None
                        if license_file:
                            f_path = f"licenses/{f_dl}_{datetime.now().strftime('%Y%m%d')}.{license_file.name.split('.')[-1]}"
                            supabase.storage.from_("license-docs").upload(f_path, license_file.getvalue(), {"upsert": "true"})

                        payload = {"name": f_name, "dob": str(f_dob), "email": f_email, "phone": f_phone, 
                                   "physical_address": f_address, "dl_no": f_dl, "dl_expiry": str(f_expiry), 
                                   "country_of_issue": f_country, "license_scan_path": f_path}

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
        # Header Row for the single-line list
        st.write("---")
        h1, h2, h3, h4 = st.columns([3, 2, 2, 1])
        h1.caption("**NAME**")
        h2.caption("**LICENSE / EXPIRY**")
        h3.caption("**CONTACT**")
        h4.caption("**ACTION**")

        for _, row in df_all.iterrows():
            if search and search.lower() not in row['name'].lower() and search.lower() not in row['dl_no'].lower():
                continue
                
            # Single Line Display
            with st.container():
                r1, r2, r3, r4 = st.columns([3, 2, 2, 1])
                
                # Name & Status Indicator
                is_expired = safe_date(row['dl_expiry']) < date.today()
                status_icon = "🔴" if is_expired else "🟢"
                r1.write(f"{status_icon} {row['name']}")
                
                # License Details
                r2.write(f"`{row['dl_no']}` | {row['dl_expiry']}")
                
                # Contact info condensed
                r3.write(f"{row['phone']}")
                
                # Action Button
                if r4.button("Edit", key=f"ed_{row['id']}", use_container_width=True):
                    st.session_state.selected_customer = row.to_dict()
                    st.session_state.view_mode = "edit"
                    st.rerun()
                st.write("---")
    else:
        st.info("No customers found.")