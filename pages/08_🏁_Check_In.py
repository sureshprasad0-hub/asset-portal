import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# --- 1. GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🏁 Vehicle Check-In")

# Fetch Company Name for Header
c_res_settings = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res_settings.data[0]['config_value'] if c_res_settings.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 3. DATA FETCHING (Updated to include odo_out) ---
# Fetching odo_out so we can validate that the new reading is higher
r_res = supabase.table("rentals").select(
    "id, vehicle_id, fuel_out, odo_out, fleet(plate, brand, model), customers(name)"
).eq("status", "Active").execute()

if r_res.data:
    rental_options = {f"{r['fleet']['plate']} - {r['customers']['name']}": r for r in r_res.data}
    selected_label = st.selectbox("Select Returning Vehicle", options=list(rental_options.keys()))
    selected_rental = rental_options[selected_label]

    with st.form("checkin_form", clear_on_submit=True):
        st.subheader(f"Inspection: {selected_rental['fleet']['plate']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Display Departure Odometer for reference
            odo_departure = selected_rental.get('odo_out', 0)
            st.write(f"**Departure Odometer:** {odo_departure:,} km")
            
            # New Odometer Input
            new_odo = st.number_input(
                "Closing Odometer Reading (km)", 
                min_value=int(odo_departure), 
                step=1,
                help="Enter the current dashboard reading. Must be equal to or greater than departure."
            )
            
        with col2:
            fuel_in = st.select_slider(
                "Return Fuel Level", 
                options=["Empty", "1/8", "1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "Full"], 
                value="Full"
            )

        notes = st.text_area("Return Notes / Damage Inspection", placeholder="Describe any new issues or 'Clean'...")

        if st.form_submit_button("Finalize Return & Update Fleet", type="primary"):
            try:
                # 1. Update Rental History with Closing Mileage
                supabase.table("rentals").update({
                    "status": "Completed",
                    "fuel_in": fuel_in,
                    "odo_in": new_odo, # Recorded for this specific trip
                    "notes": notes,
                    "return_date_actual": datetime.now().isoformat()
                }).eq("id", selected_rental['id']).execute()
                
                # 2. Sync Back to Master Fleet Registry
                # This ensures the vehicle is 'Available' with the NEW mileage
                supabase.table("fleet").update({
                    "status": "Available",
                    "odometer": new_odo # Updates the master inventory
                }).eq("id", selected_rental['vehicle_id']).execute()
                
                st.success(f"Return Processed! {selected_rental['fleet']['plate']} is now Available at {new_odo:,} km.")
                st.rerun()
                
            except Exception as e:
                st.error(f"Failed to process return: {e}")
else:
    st.info("No vehicles are currently marked as 'Active' rentals.")
    if st.button("Refresh Registry"):
        st.rerun()