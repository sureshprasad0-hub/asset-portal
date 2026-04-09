import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# --- 1. SECURITY GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- 2. DATABASE CONNECTION ---
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
# We fetch Active rentals and join the fleet table to see the departure odometer
r_res = supabase.table("rentals").select(
    "id, vehicle_id, fuel_out, odo_out, fleet(plate, brand, model, odometer), customers(name)"
).eq("status", "Active").execute()

# --- 4. CHECK-IN FORM ---
if r_res.data:
    rental_options = {f"{r['fleet']['plate']} - {r['customers']['name']}": r for r in r_res.data}
    selected_label = st.selectbox("Select Active Rental to Close", options=list(rental_options.keys()), index=None)

    if selected_label:
        selected_rental = rental_options[selected_label]
        
        with st.form("checkin_form", clear_on_submit=True):
            st.subheader(f"Inspection: {selected_rental['fleet']['plate']}")
            
            col1, col2 = st.columns(2)
            with col1:
                # ODOMETER TRACKING
                # Show where the vehicle started
                start_odo = selected_rental.get('odo_out', 0)
                st.info(f"📟 **Departure Odometer:** {start_odo:,} km")
                
                # Input for current mileage - min_value ensures mileage can't go backwards
                new_odo = st.number_input(
                    "Return Odometer Reading (km)", 
                    min_value=int(start_odo), 
                    value=int(start_odo),
                    help="Enter the current reading from the vehicle dashboard."
                )
                
            with col2:
                fuel_in = st.select_slider("Return Fuel Level", options=["Empty", "1/4", "1/2", "3/4", "Full"], value="Full")
                condition = st.selectbox("Vehicle Condition", ["Clean / No Damage", "Needs Cleaning", "Minor Damage", "Major Damage / Accident"])

            notes = st.text_area("Inspection Notes", placeholder="Note any new scratches, mechanical issues, or items left behind...")

            submitted = st.form_submit_button("Finalize Check-In", use_container_width=True, type="primary")

            if submitted:
                try:
                    # 1. Update the Rental Record with return stats
                    supabase.table("rentals").update({
                        "status": "Completed",
                        "odo_in": new_odo,
                        "fuel_in": fuel_in,
                        "condition_on_return": condition,
                        "notes": notes,
                        "return_date_actual": datetime.now().isoformat()
                    }).eq("id", selected_rental['id']).execute()

                    # 2. Update the Fleet Master Record (Make it Available & update current Odometer)
                    supabase.table("fleet").update({
                        "status": "Available",
                        "odometer": new_odo
                    }).eq("id", selected_rental['vehicle_id']).execute()

                    st.success(f"Vehicle {selected_rental['fleet']['plate']} is back in the yard and ready for the next rental!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to process return: {e}")
else:
    st.info("No vehicles are currently out on rental.")

# --- 5. RECENT RETURNS REGISTRY ---
st.write("---")
st.subheader("📋 Recently Returned Assets")

history_res = supabase.table("rentals").select(
    "id, return_date_actual, odo_in, fuel_in, fleet(plate, model), customers(name)"
).eq("status", "Completed").order("return_date_actual", desc=True).limit(5).execute()

if history_res.data:
    for rent in history_res.data:
        with st.container(border=True):
            h1, h2, h3 = st.columns([3, 3, 2])
            
            h1.write(f"🚗 **{rent['fleet']['plate']}**")
            h1.caption(f"Returned by {rent['customers']['name']}")
            
            # Format the date for readability
            ret_date = datetime.fromisoformat(rent['return_date_actual']).strftime("%d %b, %H:%M")
            h2.write(f"📅 {ret_date}")
            h2.caption(f"Fuel In: {rent['fuel_in']}")
            
            h3.write(f"📟 {rent.get('odo_in', 0):,} km")
            h3.caption("Final Mileage")
else:
    st.info("No recently completed rentals to display.")