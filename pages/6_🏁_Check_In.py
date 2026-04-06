import streamlit as st
from datetime import datetime
from supabase import create_client, Client

# --- GATEKEEPER ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

# --- CONNECTION ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🏁 Vehicle Return (Check-In)")

# --- FETCH ACTIVE RENTALS ---
# We join with fleet to show the License Plate instead of just an ID
r_res = supabase.table("rentals").select("id, vehicle_id, fuel_out, fleet(plate, brand), customers(name)").eq("status", "Active").execute()

if not r_res.data:
    st.success("All vehicles are currently in the yard. No active rentals to check in.")
    st.stop()

# Create a selection list
rental_options = {f"{r['fleet']['plate']} - {r['customers']['name']}": r for r in r_res.data}
selected_label = st.selectbox("Select Returning Vehicle", options=list(rental_options.keys()))
selected_rental = rental_options[selected_label]

st.divider()

# --- CHECK-IN FORM ---
with st.form("checkin_form"):
    st.subheader(f"Inspection for {selected_rental['fleet']['plate']}")
    
    col1, col2 = st.columns(2)
    col1.info(f"Fuel Level at Departure: **{selected_rental['fuel_out']}**")
    
    # Fuel Tracking Logic
    fuel_in = col2.select_slider(
        "Current Fuel Level (Return)",
        options=["Empty", "1/4", "1/2", "3/4", "Full"],
        value="Full"
    )
    
    odometer_in = st.number_input("Current Mileage (Optional)", min_value=0)
    condition_notes = st.text_area("Condition Notes (e.g., New scratches, clean)")

    if st.form_submit_button("Confirm Return & Release Vehicle", use_container_width=True):
        # 1. Update the Rental Record to 'Completed'
        supabase.table("rentals").update({
            "status": "Completed",
            "fuel_in": fuel_in,
            "return_date_actual": str(datetime.now().date())
        }).eq("id", selected_rental['id']).execute()
        
        # 2. Set the Vehicle back to 'Available'
        supabase.table("fleet").update({
            "status": "Available",
            "return_date": "-"
        }).eq("id", selected_rental['vehicle_id']).execute()
        
        st.success(f"Vehicle {selected_rental['fleet']['plate']} is now back in inventory!")
        st.balloons()