import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# --- 1. GATEKEEPER: ADMIN/MANAGER ONLY ---
# Ensuring financial and operational data is restricted
if 'logged_in' not in st.session_state or st.session_state.get('user_role') not in ['Admin', 'Manager']:
    st.error("Access Restricted: Financial Reports require Manager or Admin privileges.")
    st.stop()

# --- 2. CONNECTION ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Business Intelligence & Revenue")

# Fetch Company Name for the Header
c_res_settings = supabase.table("settings").select("config_value").eq("config_key", "company_name").execute()
company_display = c_res_settings.data[0]['config_value'] if c_res_settings.data else "YOUR RENTAL & TOURS"
st.caption(f"📍 {company_display}")

# --- 3. ACTION: CHECK-IN / COMPLETE RENTAL ---
# Added this section to allow closing active contracts and returning vehicles to fleet
with st.expander("🚗 Return Vehicle (Check-In)", expanded=False):
    # Fetch only Active rentals
    active_res = supabase.table("rentals").select("id, vehicle_id, fleet(plate), customers(name)").eq("status", "Active").execute()
    
    if active_res.data:
        active_list = [f"{r['fleet']['plate']} - {r['customers']['name']}" for r in active_res.data]
        selected_return = st.selectbox("Select Active Rental to Close", options=active_list)
        
        col1, col2 = st.columns(2)
        actual_in = col1.datetime_input("Actual Return Date & Time", value=datetime.now())
        fuel_in = col2.select_slider(
            "Return Fuel Level",
            options=["Empty", "1/8", "1/4", "3/8", "1/2", "5/8", "3/4", "7/8", "Full"],
            value="Full"
        )
        
        notes = st.text_area("Return Notes (Condition, cleaning, etc.)")
        
        if st.button("Complete Check-In", use_container_width=True, type="primary"):
            # Get IDs from selection
            rental_idx = active_list.index(selected_return)
            rental_id = active_res.data[rental_idx]['id']
            v_id = active_res.data[rental_idx]['vehicle_id']
            
            try:
                # 1. Update Rental Status
                supabase.table("rentals").update({
                    "status": "Completed",
                    "fuel_in": fuel_in,
                    "actual_return": actual_in.isoformat(),
                    "notes": notes
                }).eq("id", rental_id).execute()
                
                # 2. Return Vehicle to Inventory
                supabase.table("fleet").update({"status": "Available"}).eq("id", v_id).execute()
                
                st.success(f"Check-in successful! Vehicle is now 'Available'.")
                st.rerun()
            except Exception as e:
                st.error(f"Check-in failed: {e}")
    else:
        st.info("No active rentals currently out in the field.")

st.divider()

# --- 4. FETCH & DISPLAY REVENUE DATA ---
res = supabase.table("rentals").select("*, fleet(plate, brand), customers(name)").execute()

if res.data:
    df = pd.json_normalize(res.data)
    
    # Ensure numeric types for calculations to prevent f-string TypeErrors
    df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
    df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce').fillna(0)
    df['subtotal'] = pd.to_numeric(df['subtotal'], errors='coerce').fillna(0)
    
    # --- TOP LEVEL METRICS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Gross Revenue", f"${df['total'].sum():,.2f}")
    m2.metric("VAT Collected", f"${df['tax_amount'].sum():,.2f}")
    m3.metric("Total Bookings", len(df))

    st.divider()

    # --- VISUALS ---
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Revenue by Vehicle")
        rev_by_plate = df.groupby('fleet.plate')['total'].sum().sort_values(ascending=False)
        st.bar_chart(rev_by_plate)

    with col_right:
        st.subheader("Booking Status")
        st.write(df['status'].value_counts())

    # --- DETAILED LOG (FOR AUDIT) ---
    st.divider()
    st.subheader("Transaction History")
    cols = ['date_out', 'fleet.plate', 'customers.name', 'total', 'status']
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

else:
    st.info("No rental history found. Start processing check-outs to see data here.")