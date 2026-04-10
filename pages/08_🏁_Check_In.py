import streamlit as st
from supabase import create_client, Client
from datetime import datetime, time

# --- 1. GATEKEEPER & CONNECTION ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in on the Home page first.")
    st.stop()

url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🏁 Vehicle Check-In")
st.caption("Process returns and finalize rental billing.")

# Fetch Company Name for Header
c_res = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res.data[0]['config_value'] if c_res.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 2. FETCH ACTIVE RENTALS ---
try:
    # Use explicit foreign key relationships
    active_res = supabase.table("rentals").select(
        "*, fleet!fk_rentals_fleet(plate, brand, model), customers!fk_rentals_customers(name)"
    ).eq("status", "Active").execute()

    if not active_res.data:
        st.info("No active rentals currently out.")
        st.stop()

    # Empty default selection
    rental_options = {
        f"{r['fleet']['plate']} - {r['customers']['name']}": r for r in active_res.data
    }
    
    option_list = [""] + list(rental_options.keys())
    selected_label = st.selectbox("Select Vehicle to Check-In", options=option_list, index=0)

    if selected_label != "":
        r = rental_options[selected_label]

        # --- 3. CHECK-IN FORM ---
        with st.container(border=True):
            st.subheader(f"Return Details: {r['fleet']['plate']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Customer:** {r['customers']['name']}")
                st.write(f"**Date Out:** {r['date_out']}")
                odo_out = r.get('odo_out', 0)
                st.write(f"**Odometer Out:** {odo_out:,} km")
                
            with col2:
                # Updated: Return date and specific time input
                return_date = st.date_input("Return Date", value=datetime.now().date())
                return_time = st.time_input("Return Time", value=datetime.now().time())
                odo_in = st.number_input("Odometer In", value=int(odo_out), min_value=int(odo_out))
                
                # Updated: Fuel intervals set to 1/8
                fuel_options = ["Empty", "1/8", "1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "Full"]
                fuel_in = st.select_slider("Fuel Level In", options=fuel_options, value="Full")

            st.divider()
            notes = st.text_area("Return Condition / Damage Notes", placeholder="Note any new scratches or issues...")

            # Calculation Logic
            try:
                # Combine date and time for full timestamp
                return_ts = datetime.combine(return_date, return_time)
                
                # Handle ISO timestamp from DB
                out_ts_str = r['date_out'].replace('T', ' ')
                out_ts = datetime.fromisoformat(out_ts_str)
                
                # Calculate Duration (Days)
                duration = return_ts - out_ts
                days_rented = duration.days + (1 if duration.seconds > 3600 else 0) # Grace period of 1 hour
                days_rented = max(days_rented, 1) 
                
                total_due = days_rented * float(r['rate'])
                
                st.write(f"📊 **Rental Duration:** {days_rented} Day(s)")
                st.write(f"💰 **Final Total:** ${total_due:,.2f}")

                if st.button("Complete Check-In", type="primary", use_container_width=True):
                    # 1. Update Rental Record
                    supabase.table("rentals").update({
                        "status": "Completed",
                        "date_returned": return_ts.isoformat(),
                        "odo_in": odo_in,
                        "fuel_in": fuel_in,
                        "notes": notes,
                        "total": total_due
                    }).eq("id", r['id']).execute()

                    # 2. Update Fleet Odometer and Status
                    supabase.table("fleet").update({
                        "status": "Available",
                        "current_odo": odo_in
                    }).eq("id", r['vehicle_id']).execute()

                    st.success(f"Check-in complete. {r['fleet']['plate']} Odometer updated to {odo_in:,} km.")
                    st.balloons()
                    st.rerun()
            except Exception as parse_err:
                st.error(f"Calculation Error: {parse_err}")
    else:
        st.write("Please select an active rental to begin.")

except Exception as e:
    st.error(f"Error loading check-in data: {e}")