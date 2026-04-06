import streamlit as st
import pandas as pd
from supabase import create_client

# --- GATEKEEPER: ADMIN/MANAGER ONLY ---
if 'logged_in' not in st.session_state or st.session_state.get('user_role') not in ['Admin', 'Manager']:
    st.error("Access Restricted: Financial Reports require Manager or Admin privileges.")
    st.stop()

# --- CONNECTION ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Business Intelligence & Revenue")

# --- FETCH COMPLETED RENTALS ---
# We pull data including the tax and subtotal columns we added earlier
res = supabase.table("rentals").select("*, fleet(plate, brand), customers(name)").execute()

if res.data:
    df = pd.json_normalize(res.data)
    
    # Ensure numeric types for calculations
    df['total'] = pd.to_numeric(df['total'], errors='coerce')
    df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce')
    df['subtotal'] = pd.to_numeric(df['subtotal'], errors='coerce')
    
    # --- TOP LEVEL METRICS ---
    total_rev = df['total'].sum()
    total_vat = df['tax_amount'].sum()
    total_rentals = len(df)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Gross Revenue", f"${total_rev:,.2f}")
    m2.metric("VAT Collected", f"${total_vat:,.2f}")
    m3.metric("Total Bookings", total_rentals)

    st.divider()

    # --- VISUALS ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Revenue by Vehicle")
        rev_by_plate = df.groupby('fleet.plate')['total'].sum().sort_values(ascending=False)
        st.bar_chart(rev_by_plate)

    with col_right:
        st.subheader("Booking Status")
        status_counts = df['status'].value_counts()
        st.write(status_counts) # Simple breakdown of Active vs Completed

    # --- DETAILED LOG (FOR AUDIT) ---
    st.divider()
    st.subheader("Transaction History")
    # Clean up the dataframe for display
    display_df = df[['date_out', 'fleet.plate', 'customers.name', 'subtotal', 'tax_amount', 'total', 'status']]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.info("No rental history found. Start processing check-outs to see data here.")