import streamlit as st
from supabase import create_client, Client
from datetime import datetime

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
                # New: Display Previously Billed Amount
                prev_billed = float(r.get('total', 0))
                st.metric("Previously Billed", f"${prev_billed:,.2f}")
                
            with col2:
                # Combined Date and Time Field
                return_ts_input = st.datetime_input("Return Date & Time", value=datetime.now())
                odo_in = st.number_input("Odometer In", value=int(odo_out), min_value=int(odo_out))
                
                # Fuel intervals set to 1/8
                fuel_options = ["Empty", "1/8", "1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "Full"]
                fuel_in = st.select_slider("Fuel Level In", options=fuel_options, value="Full")

            st.divider()
            notes = st.text_area("Return Condition / Damage Notes", placeholder="Note any new scratches or issues...")

            # Calculation Logic
            try:
                # Handle ISO timestamp from DB
                out_ts_str = r['date_out'].replace('T', ' ')
                out_ts = datetime.fromisoformat(out_ts_str)
                
                # Calculate Duration (Days)
                duration = return_ts_input - out_ts
                days_rented = duration.days + (1 if duration.seconds > 3600 else 0) 
                days_rented = max(days_rented, 1) 
                
                final_total = days_rented * float(r['rate'])
                # New: Calculate Extra Charges
                extra_charges = max(0.0, final_total - prev_billed)
                
                c_metrics = st.columns(3)
                c_metrics[0].write(f"📊 **Duration:** {days_rented} Day(s)")
                c_metrics[1].write(f"💰 **Final Total:** ${final_total:,.2f}")
                c_metrics[2].write(f"⚠️ **Extra Due:** ${extra_charges:,.2f}")

                if st.button("Complete Check-In", type="primary", use_container_width=True):
                    # 1. Update Rental Record
                    supabase.table("rentals").update({
                        "status": "Completed",
                        "date_returned": return_ts_input.isoformat(),
                        "odo_in": odo_in,
                        "fuel_in": fuel_in,
                        "notes": notes,
                        "total": final_total # Update with final total including extra charges
                    }).eq("id", r['id']).execute()

                    # 2. Update Fleet Odometer and Status
                    supabase.table("fleet").update({
                        "status": "Available",
                        "current_odo": odo_in
                    }).eq("id", r['vehicle_id']).execute()

                    st.success(f"Check-in complete. Final amount: ${final_total:,.2f} (${extra_charges:,.2f} extra).")
                    st.balloons()
                    st.rerun()
            except Exception as parse_err:
                st.error(f"Calculation Error: {parse_err}")
    else:
        st.write("Please select an active rental to begin.")

except Exception as e:
    st.error(f"Error loading check-in data: {e}")