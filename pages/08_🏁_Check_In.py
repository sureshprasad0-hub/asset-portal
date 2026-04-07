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

# --- 3. FETCH ACTIVE RENTALS ---
# We join with fleet and customers to give the staff clear context
r_res = supabase.table("rentals").select(
    "id, vehicle_id, fuel_out, fleet(plate, brand, model), customers(name)"
).eq("status", "Active").execute()

if not r_res.data:
    st.success("✅ All vehicles are currently in the yard. No active rentals to check in.")
    if st.button("Go to Dashboard"):
        st.switch_page("pages/1_📊_Dashboard.py")
    st.stop()

# Create a searchable dictionary for the dropdown
rental_options = {
    f"{r['fleet']['plate']} - {r['customers']['name']} ({r['fleet']['brand']})": r 
    for r in r_res.data
}
selected_label = st.selectbox("Select Returning Vehicle", options=list(rental_options.keys()))
selected_rental = rental_options[selected_label]

st.divider()

# --- 4. CHECK-IN FORM ---
with st.form("checkin_form", clear_on_submit=True):
    st.subheader(f"Inspection: {selected_rental['fleet']['plate']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Fuel at Departure: **{selected_rental['fuel_out']}**")
        fuel_in = st.select_slider(
            "Current Fuel Level (Return)",
            options=["Empty", "1/4", "1/2", "3/4", "Full"],
            value="Full"
        )
    
    with col2:
        st.write("### 📸 Condition Proof")
        # Captures photo via mobile camera or file upload
        img_file = st.file_uploader("Take Photo of Vehicle Condition", type=['png', 'jpg', 'jpeg'])
    
    st.write("### 📝 Inspection Notes")
    notes = st.text_area("Record any new scratches, dents, or interior issues", placeholder="e.g., Small scratch on rear bumper, car cleaned.")

    if st.form_submit_button("Finalize Return & Release Vehicle", use_container_width=True):
        r_id = selected_rental['id']
        v_id = selected_rental['vehicle_id']
        photo_url = None

        # --- 5. IMAGE UPLOAD LOGIC ---
        if img_file:
            try:
                # Generate a unique filename using timestamp and rental ID
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = f"returns/{r_id}_{timestamp}_{img_file.name}"
                
                # Upload to Supabase Storage Bucket 'vehicle-photos'
                supabase.storage.from_("vehicle-photos").upload(
                    path=file_path,
                    file=img_file.getvalue(),
                    file_options={"content-type": img_file.type}
                )
                
                # Get the public URL to save in the database
                photo_url = supabase.storage.from_("vehicle-photos").get_public_url(file_path)
            except Exception as e:
                st.error(f"Image Upload Failed: {e}")

        # --- 6. DATABASE UPDATES ---
        try:
            # Update Rental Record to 'Completed'
            supabase.table("rentals").update({
                "status": "Completed",
                "fuel_in": fuel_in,
                "notes": notes,
                "photo_proof_url": photo_url,
                "return_date_actual": str(datetime.now().date())
            }).eq("id", r_id).execute()
            
            # Release Vehicle back to 'Available' status
            supabase.table("fleet").update({
                "status": "Available",
                "return_date": "-"
            }).eq("id", v_id).execute()
            
            st.success(f"Success! {selected_rental['fleet']['plate']} is now back in inventory.")
            st.balloons()
            st.info("Redirecting to Dashboard...")