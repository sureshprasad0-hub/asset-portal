import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🚗 Fleet Inventory")

# --- ACTION: ADD NEW VEHICLE ---
with st.expander("➕ Register New Asset", expanded=False):
    with st.form("add_vehicle", clear_on_submit=True):
        col1, col2 = st.columns(2)
        plate = col1.text_input("License Plate").strip().upper()
        brand = col2.text_input("Brand/Make")
        model = st.text_input("Model")
        
        if st.form_submit_button("Add to Fleet", use_container_width=True):
            if plate and brand:
                supabase.table("fleet").insert({
                    "plate": plate, "brand": brand, "model": model, "status": "Available"
                }).execute()
                st.success(f"Vehicle {plate} added!")
                st.rerun()

# --- DISPLAY & EDIT FLEET ---
st.subheader("Current Assets")
f_res = supabase.table("fleet").select("*").order("plate").execute()

if f_res.data:
    df = pd.DataFrame(f_res.data)
    
    # Simple Mobile-Friendly List
    for index, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**{row['plate']}**\n{row['brand']} {row['model']}")
            
            # Status Color Logic
            status_color = "🟢" if row['status'] == "Available" else "🔴" if row['status'] == "Rented" else "🟡"
            c2.write(f"{status_color} {row['status']}")
            
            # Quick Status Update (Restricted to Managers/Admins)
            if st.session_state['user_role'] in ['Admin', 'Manager']:
                if row['status'] != 'Rented': # Prevent manual override of active rentals
                    new_status = c3.selectbox("Update", ["Available", "Maintenance"], key=f"upd_{row['id']}")
                    if new_status != row['status']:
                        supabase.table("fleet").update({"status": new_status}).eq("id", row['id']).execute()
                        st.rerun()
else:
    st.info("No vehicles registered yet.")