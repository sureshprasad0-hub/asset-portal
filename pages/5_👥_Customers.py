import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. GATEKEEPER: SECURITY CHECK ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. DATABASE CONNECTION ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Connection Error: Check Streamlit Secrets.")
    st.stop()

st.title("👥 Customer Directory")

# --- 3. ACTION: REGISTER NEW CUSTOMER ---
# Using an expander to save space on mobile screens
with st.expander("➕ Register New Customer", expanded=False):
    with st.form("add_customer", clear_on_submit=True):
        full_name = st.text_input("Full Name (as per ID)").strip()
        dl_no = st.text_input("Driver's License Number").strip().upper()
        phone = st.text_input("Phone Number (Fiji/International)")
        
        if st.form_submit_button("Register Customer", use_container_width=True):
            if full_name and dl_no:
                try:
                    supabase.table("customers").insert({
                        "name": full_name, 
                        "dl_no": dl_no, 
                        "phone": phone
                    }).execute()
                    st.success(f"Customer {full_name} successfully registered!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please provide both Name and License Number.")

# --- 4. DISPLAY: CUSTOMER LIST ---
st.subheader("Existing Clients")

# Search bar for quick lookup on the go
search_query = st.text_input("🔍 Search by Name or DL No", placeholder="Enter name or license...")

# Fetch data from Supabase
c_res = supabase.table("customers").select("*").order("name").execute()

if c_res.data:
    df = pd.DataFrame(c_res.data)
    
    # Filter logic for the search bar
    if search_query:
        df = df[df['name'].str.contains(search_query, case=False) | 
                df['dl_no'].str.contains(search_query, case=False)]

    if not df.empty:
        # Display as a clean, interactive table
        st.dataframe(
            df[['name', 'dl_no', 'phone']], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Count for quick oversight
        st.caption(f"Showing {len(df)} registered customers.")
    else:
        st.info("No customers match your search.")
else:
    st.info("No customers registered yet. Use the form above to add your first client.")

# --- 5. ADMIN TOOLS ---
if st.session_state['user_role'] == 'Admin':
    st.divider()
    with st.expander("🗑️ Admin: Delete Customer"):
        target_name = st.selectbox("Select Customer to Remove", options=[c['name'] for c in c_res.data] if c_res.data else [])
        if st.button("Permanently Delete", type="primary"):
            supabase.table("customers").delete().eq("name", target_name).execute()
            st.success(f"Record for {target_name} deleted.")
            st.rerun()