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

def enter_list_mode():
    st.session_state.view_mode = "list"
    st.session_state.selected_customer = None
    st.rerun()

def safe_date(date_val, default=date(1995, 1, 1)):
    if not date_val: return default
    try:
        return datetime.strptime(date_val, '%Y-%m-%d').date()
    except:
        return default

# --- 4. FORM VIEW (ADD / EDIT) ---
if st.session_state.view_mode in ["add", "edit"]:
    cust = st.session_state.selected_customer
    mode_label = "📝 Edit Customer Profile" if cust else "➕ New Customer Registration"
    
    with st.container(border=True):
        st.subheader(mode_label)
        with st.form("customer_form", clear_on_submit=False):
            st.write("### Personal Details")
            f_name = st.text_input("Full Legal Name", value=cust['name'] if cust else "").strip()
            f_dob = st.date_input("Date of Birth", value=safe_date(cust['dob'] if cust else None))
            
            col1, col2 = st.columns(2)
            f_email = col1.text_input("Email", value=cust['email'] if cust else "")
            f_phone = col2.text_input("Mobile", value=cust['phone'] if cust else "")
            f_address = st.text_area("Physical Address", value=cust['physical_address'] if cust else "")

            st.divider()
            st.write("### Driver's License Compliance")
            col3, col4 = st.columns(2)
            f_dl = col3.text_input("License Number", value=cust['dl_no'] if cust else "").upper()
            f_expiry = col4.date_input("License Expiry", value=safe_date(cust['dl_expiry'] if cust else None, default=date.today()))
            
            f_country = st.selectbox("Issue Country", ["Fiji", "Australia", "NZ", "USA", "Other"], 
                                     index=0 if not cust else ["Fiji", "Australia", "NZ", "USA", "Other"].index(cust.get('country_of_issue', 'Fiji')))
            
            # --- IMAGE UPLOAD SECTION ---
            st.write("### ID Verification Document")
            if cust and cust.get('license_scan_path'):
                try:
                    # Generate a signed URL so the user can see the existing file
                    res = supabase.storage.from_("license-docs").create_signed_url(cust['license_scan_path'], 60)
                    st.info("✅ Current ID Scan is on file.")
                    st.link_button("👁️ View Current ID Scan", res['signedURL'])
                except:
                    st.warning("⚠️ Could not retrieve existing ID scan.")

            license_file = st.file_uploader("Upload New/Replacement ID Scan", type=['png', 'jpg', 'jpeg', 'pdf'])

            sub_col, can_col = st.columns(2)
            submitted = sub_col.form_submit_button("💾 Save Record", use_container_width=True)
            cancelled = can_col.form_submit_button("❌ Cancel", use_container_width=True)

            if submitted:
                age = (date.today() - f_dob).days // 365
                if not f_name or not f_dl or not f_email:
                    st.error("Name, License, and Email are required.")
                elif age < 21:
                    st.error(f"Compliance Error: Customer age is below 21.")
                elif f_expiry < date.today():
                    st.error("Compliance Error: Driver's License has expired.")
                else:
                    try:
                        file_path = cust.get('license_scan_path') if cust else None
                        
                        # Upload new file if provided
                        if license_file:
                            file_ext = license_file.name.split('.')[-1]
                            file_path = f"licenses/{f_dl}_{datetime.now().strftime('%Y%m%d')}.{file_ext}"
                            supabase.storage.from_("license-docs").upload(file_path, license_file.getvalue(), {"upsert": "true"})

                        payload = {
                            "name": f_name, "dob": str(f_dob), "email": f_email,
                            "phone": f_phone, "physical_address": f_address,
                            "dl_no": f_dl, "dl_expiry": str(f_expiry), 
                            "country_of_issue": f_country,
                            "license_scan_path": file_path
                        }

                        if cust:
                            supabase.table("customers").update(payload).eq("id", cust['id']).execute()
                        else:
                            supabase.table("customers").insert(payload).execute()
                        
                        st.success("Record saved!")
                        st.session_state.view_mode = "list"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if cancelled:
                enter_list_mode()

# --- 5. LIST VIEW ---
if st.session_state.view_mode == "list":
    st.button("➕ Add New Customer", on_click=lambda: st.session_state.update({"view_mode": "add"}), use_container_width=True)
    st.divider()
    
    search = st.text_input("🔍 Search Registry", placeholder="Name or License...")
    res = supabase.table("customers").select("*").order("name").execute()
    
    if res.data:
        for person in res.data:
            if search and search.lower() not in person['name'].lower() and search.lower() not in person['dl_no'].lower():
                continue
                
            with st.container(border=True):
                info, action = st.columns([4, 1])
                info.write(f"**{person['name']}**")
                info.caption(f"DL: {person['dl_no']} | Expiry: {person['dl_expiry']}")
                
                if action.button("Edit", key=f"btn_{person['id']}", use_container_width=True):
                    st.session_state.selected_customer = person
                    st.session_state.view_mode = "edit"
                    st.rerun()
    else:
        st.info("No customers registered.")