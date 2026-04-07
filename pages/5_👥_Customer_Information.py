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

# --- 3. SESSION STATE MANAGEMENT ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "list"  # Options: list, add, edit
if 'selected_customer' not in st.session_state:
    st.session_state.selected_customer = None

def enter_add_mode():
    st.session_state.view_mode = "add"
    st.session_state.selected_customer = None

def enter_list_mode():
    st.session_state.view_mode = "list"
    st.session_state.selected_customer = None

# --- 4. FORM LOGIC (REUSABLE FOR ADD & EDIT) ---
if st.session_state.view_mode in ["add", "edit"]:
    cust = st.session_state.selected_customer
    mode_label = "Edit Customer" if cust else "New Customer Registration"
    
    with st.container(border=True):
        st.subheader(mode_label)
        with st.form("customer_form"):
            # Pre-fill values if in edit mode
            f_name = st.text_input("Full Legal Name", value=cust['name'] if cust else "").strip()
            f_dob = st.date_input("Date of Birth", value=datetime.strptime(cust['dob'], '%Y-%m-%d').date() if cust else date(1995, 1, 1))
            
            col1, col2 = st.columns(2)
            f_email = col1.text_input("Email", value=cust['email'] if cust else "")
            f_phone = col2.text_input("Mobile", value=cust['phone'] if cust else "")
            f_address = st.text_area("Physical Address", value=cust['physical_address'] if cust else "")

            st.divider()
            col3, col4 = st.columns(2)
            f_dl = col3.text_input("License Number", value=cust['dl_no'] if cust else "").upper()
            f_expiry = col4.date_input("License Expiry", value=datetime.strptime(cust['dl_expiry'], '%Y-%m-%d').date() if cust else date.today())
            
            f_country = st.selectbox("Issue Country", ["Fiji", "Australia", "NZ", "USA", "Other"], 
                                     index=["Fiji", "Australia", "NZ", "USA", "Other"].index(cust['country_of_issue']) if cust else 0)

            btn_label = "Update Information" if cust else "Verify & Save"
            
            c1, c2 = st.columns(2)
            if c1.form_submit_button(btn_label, use_container_width=True):
                # Validations
                age = (date.today() - f_dob).days // 365
                if not f_name or not f_dl or not f_email:
                    st.error("Name, License, and Email are required.")
                elif age < 21:
                    st.error(f"Compliance Error: Age is {age}. Minimum 21 required.")
                elif f_expiry < date.today():
                    st.error("Compliance Error: License is expired.")
                else:
                    data_payload = {
                        "name": f_name, "dob": str(f_dob), "email": f_email,
                        "phone": f_phone, "physical_address": f_address,
                        "dl_no": f_dl, "dl_expiry": str(f_expiry), "country_of_issue": f_country
                    }
                    
                    try:
                        if cust: # UPDATE
                            supabase.table("customers").update(data_payload).eq("id", cust['id']).execute()
                            st.success("Customer record updated.")
                        else: # INSERT
                            supabase.table("customers").insert(data_payload).execute()
                            st.success("Customer record created.")
                        
                        enter_list_mode()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if c2.form_submit_button("Cancel", use_container_width=True):
                enter_list_mode()
                st.rerun()

# --- 5. LIST VIEW ---
if st.session_state.view_mode == "list":
    st.button("➕ Add New Customer", on_click=enter_add_mode, use_container_width=True)
    st.divider()
    
    search = st.text_input("🔍 Search Registry", placeholder="Name or License...")
    
    # Fetch Customers
    res = supabase.table("customers").select("*").order("name").execute()
    
    if res.data:
        for person in res.data:
            # Filter logic
            if search and search.lower() not in person['name'].lower() and search.lower() not in person['dl_no'].lower():
                continue
                
            with st.container(border=True):
                col_info, col_btn = st.columns([4, 1])
                
                with col_info:
                    st.write(f"**{person['name']}**")
                    st.caption(f"License: {person['dl_no']} | Expires: {person['dl_expiry']}")
                
                with col_btn:
                    if st.button("View/Edit", key=f"edit_{person['id']}", use_container_width=True):
                        st.session_state.selected_customer = person
                        st.session_state.view_mode = "edit"
                        st.rerun()
    else:
        st.info("No customers found.")