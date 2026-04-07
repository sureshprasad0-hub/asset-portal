import streamlit as st
import pandas as pd
import numpy as np
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
    """Prevents JSON crashes by ensuring a valid date object is always returned."""
    if date_val is None or pd.isna(date_val) or str(date_val).strip() == "":
        return default
    try:
        return datetime.strptime(str(date_val), '%Y-%m-%d').date()
    except:
        return default

# --- 4. DATA FETCHING ---
res = supabase.table("customers").select("*").order("name").execute()
df_all = pd.DataFrame(res.data) if res.data else pd.DataFrame()

# --- 5. TOP SECTION: STATS DASHBOARD (List View only) ---
if st.session_state.view_mode == "list":
    if not df_all.empty:
        st.write("### 📊 Registry Overview")
        col_a, col_b, col_c = st.columns(3)
        
        total_cust = len(df_all)
        # Safe date conversion for metric calculation
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
            st.write("### Personal Details")
            f_name = st.text_input("Full Legal Name", value=cust['name'] if cust and not pd.isna(cust['name']) else "").strip()
            f_dob = st.date_input("Date of Birth", value=safe_date(cust['dob'] if cust else None))
            
            c1, c2 = st.columns(2)
            # EMAIL IS OPTIONAL
            f_email = c1.text_input("Email (Optional)", value=cust['email'] if cust and not pd.isna(cust['email']) else "")
            f_phone = c2.text_input("Mobile", value=cust['phone'] if cust and not pd.isna(cust['phone']) else "")
            f_address = st.text_area("Physical Address", value=cust['physical_address'] if cust and not pd.isna(cust['physical_address']) else "")

            st.divider()
            st.write("### Driver's License Compliance")
            c3, c4 = st.columns(2)
            f_dl = c3.text_input("License No.", value=cust['dl_no'] if cust and not pd.isna(cust['dl_no']) else "").upper()
            f_expiry = c4.date_input("License Expiry", value=safe_date(cust['dl_expiry'] if cust else None, default=date.today()))
            
            countries = ["Fiji", "Australia", "NZ", "USA", "Other"]
            def_idx = countries.index(cust['country_of_issue']) if cust and cust.get('country_of_issue') in countries else 0
            f_country = st.selectbox("Issue Country", countries, index=def_idx)
            
            # IMAGE SECTION (OPTIONAL)
            st.write("### ID Document Management")
            if cust and cust.get('license_scan_path'):
                try:
                    img_url = supabase.storage.from_("license-docs").create_signed_url(cust['license_scan_path'], 60)
                    st.info("✅ ID Scan exists.")
                    st.link_button("👁️ View Existing ID Scan", img_url['signedURL'])
                except:
                    st.caption("No accessible ID scan found.")

            license_file = st.file_uploader("Upload ID Scan (Optional)", type=['png', 'jpg', 'jpeg', 'pdf'])

            sub_col, can_col = st.columns(2)
            if sub_col.form_submit_button("💾 Save Record", use_container_width=True):
                # Validations
                age = (date.today() - f_dob).days // 365
                if not f_name or not f_dl:
                    st.error("Full Name and License Number are required.")
                elif age < 21:
                    st.error(f"Compliance Violation: Age is {age} (21+ required).")
                elif f_expiry < date.today():
                    st.error("Compliance Violation: License has expired.")
                else:
                    try:
                        # Path retention logic
                        f_path = cust.get('license_scan_path') if cust else None
                        if license_file:
                            file_ext = license_file.name.split('.')[-1]
                            f_path = f"licenses/{f_dl}_{datetime.now().strftime('%Y%m%d')}.{file_ext}"
                            supabase.storage.from_("license-docs").upload(f_path, license_file.getvalue(), {"upsert": "true"})

                        # Payload sanitization (Fixes the 'nan' error)
                        payload = {
                            "name": f_name or "Unknown",
                            "dob": str(f_dob),
                            "email": f_email or "", # Optional
                            "phone": f_phone or "",
                            "physical_address": f_address or "",
                            "dl_no": f_dl,
                            "dl_expiry": str(f_expiry), 
                            "country_of_issue": f_country,
                            "license_scan_path": f_path # Optional
                        }

                        if cust:
                            supabase.table("customers").update(payload).eq("id", cust['id']).execute()
                        else:
                            supabase.table("customers").insert(payload).execute()
                        
                        st.session_state.view_mode = "list"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Database Error: {e}")

            if can_col.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.view_mode = "list"
                st.rerun()

# --- 7. LIST VIEW (SINGLE LINE REGISTRY) ---
if st.session_state.view_mode == "list":
    st.button("➕ Add New Customer", on_click=lambda: st.session_state.update({"view_mode": "add"}), use_container_width=True)
    
    search = st.text_input("🔍 Search Registry", placeholder="Name or License...")
    
    if not df_all.empty:
        st.write("---")
        h1, h2, h3, h4 = st.columns([3, 2, 2, 1])
        h1.caption("**NAME / STATUS**")
        h2.caption("**LICENSE / EXPIRY**")
        h3.caption("**PHONE**")
        h4.caption("**ACTION**")

        for _, row in df_all.iterrows():
            # Robust string conversion for search
            s_name = str(row['name']) if not pd.isna(row['name']) else ""
            s_dl = str(row['dl_no']) if not pd.isna(row['dl_no']) else ""
            
            if search and search.lower() not in s_name.lower() and search.lower() not in s_dl.lower():
                continue
                
            with st.container():
                r1, r2, r3, r4 = st.columns([3, 2, 2, 1])
                
                # Expiry Logic for status icon
                exp_date = safe_date(row['dl_expiry'])
                icon = "🔴" if exp_date < date.today() else "🟢"
                
                r1.write(f"{icon} {s_name}")
                r2.write(f"`{s_dl}` | {row['dl_expiry']}")
                r3.write(f"{row['phone'] if not pd.isna(row['phone']) else ''}")
                
                if r4.button("Edit", key=f"ed_{row['id']}", use_container_width=True):
                    # Convert pandas series row to dictionary for session state
                    st.session_state.selected_customer = row.to_dict()
                    st.session_state.view_mode = "edit"
                    st.rerun()
                st.write("---")
    else:
        st.info("No records found.")