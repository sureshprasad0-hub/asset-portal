import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# --- 1. SECURITY GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. DATABASE & STORAGE CONNECTION ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

st.title("🏁 Vehicle Check-In & Inspection")
st.write("Complete this form when a vehicle is returned to the yard.")

# Fetch Company Name for the Header
c_res_settings = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res_settings.data[0]['config_value'] if c_res_settings.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 3. FETCH DATA ---
# Updated to include odo_out from the rentals table
r_res = supabase.table("rentals").select(
    "id, vehicle_id, fuel_out, odo_out, fleet(plate, brand, model), customers(name)"
).eq("status", "Active").execute()

# Completed Rentals for the Registry below
history_res = supabase.table("rentals").select(
    "id, total, date_out, return_date_actual, fuel_out, fuel_in, notes, photo_proof_url, fleet(plate, model), customers(name)"
).eq("status", "Completed").order("return_date_actual", desc=True).limit(10).execute()

# --- 4. CHECK-IN FORM ---
if r_res.data:
    rental_options = {f"{r['fleet']['plate']} - {r['customers']['name']}": r for r in r_res.data}
    selected_label = st.selectbox("Select Returning Vehicle", options=list(rental_options.keys()))
    selected_rental = rental_options[selected_label]
    
    r_id = selected_rental['id']
    v_id = selected_rental['vehicle_id']

    with st.form("checkin_form", clear_on_submit=True):
        st.subheader(f"Return Inspection: {selected_rental['fleet']['plate']}")
        
        col1, col2 = st.columns(2)
        with col1:
            # Display the odometer reading from when the car left
            odo_departure = selected_rental.get('odo_out', 0)
            st.info(f"📟 **Departure Odometer:** {odo_departure:,} km")
            
            # Input for the new reading
            odo_in = st.number_input(
                "Closing Odometer Reading (km)", 
                min_value=int(odo_departure), 
                step=1,
                help="Enter current dashboard reading. Must be higher than departure."
            )
            
        with col2:
            fuel_in = st.select_slider(
                "Return Fuel Level", 
                options=["Empty", "1/8", "1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "Full"], 
                value="Full"
            )

        notes = st.text_area("Return Notes / Damage Inspection", placeholder="Describe any issues or mark as 'Clean'...")
        
        img_file = st.file_uploader("Upload Return Condition Photo (Optional)", type=['png', 'jpg', 'jpeg'])

        if st.form_submit_button("Finalize Return & Update Fleet", type="primary"):
            photo_url = None
            if img_file:
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_path = f"returns/{r_id}_{timestamp}_{img_file.name}"
                    supabase.storage.from_("vehicle-photos").upload(
                        path=file_path,
                        file=img_file.getvalue(),
                        file_options={"content-type": img_file.type}
                    )
                    photo_url = supabase.storage.from_("vehicle-photos").get_public_url(file_path)
                except Exception as e:
                    st.error(f"Image Upload Failed: {e}")

            # --- 6. DATABASE UPDATES ---
            try:
                # Update Rental Record with Closing Mileage
                supabase.table("rentals").update({
                    "status": "Completed",
                    "fuel_in": fuel_in,
                    "odo_in": odo_in,
                    "notes": notes,
                    "photo_proof_url": photo_url,
                    "return_date_actual": str(datetime.now().date())
                }).eq("id", r_id).execute()
                
                # Update Master Fleet Inventory with current mileage
                supabase.table("fleet").update({
                    "status": "Available",
                    "odometer": odo_in
                }).eq("id", v_id).execute()
                
                st.success(f"Success! {selected_rental['fleet']['plate']} is now back in inventory at {odo_in:,} km.")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"Database Update Failed: {e}")
else:
    st.info("No vehicles are currently marked as 'Active' rentals.")

# --- 5. RECENT RETURN HISTORY ---
st.write("---")
st.subheader("📋 Recently Returned Vehicles")
if history_res.data:
    for rent in history_res.data:
        with st.container(border=True):
            r1, r2, r3, r4 = st.columns([3, 3, 2, 1])
            r1.write(f"🚗 **{rent['fleet']['plate']}**")
            r1.caption(f"{rent['fleet']['model']}")
            
            r2.write(f"👤 **{rent['customers']['name']}**")
            r2.caption(f"Notes: {rent['notes'] if rent['notes'] else 'No issues'}")
            
            r3.write(f"📅 {rent['return_date_actual']}")
            r3.caption(f"Fuel In: {rent['fuel_in']}")
            
            if r4.button("View", key=f"hist_{rent['id']}", use_container_width=True):
                st.session_state[f"hist_detail_{rent['id']}\"] = not st.session_state.get(f"hist_detail_{rent['id']}", False)
            
            if st.session_state.get(f"hist_detail_{rent['id']}", False):
                with st.container(border=True):
                    sd1, sd2 = st.columns([2, 1])
                    with sd1:
                        st.markdown(f"**Final Total:** ${float(rent['total']):,.2f}")
                        st.write(f"**Departure Fuel:** {rent['fuel_out']}")
                    with sd2:
                        if rent.get('photo_proof_url'):
                            st.image(rent['photo_proof_url'], caption="Condition at Return")