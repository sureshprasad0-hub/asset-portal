import streamlit as st
import pandas as pd

def show(supabase):
    st.subheader("💰 Revenue & Financial Performance")
    res = supabase.table("rentals").select("*, fleet!fk_rentals_fleet(plate, brand), customers!fk_rentals_customers(name)").execute()
    if res.data:
        df = pd.json_normalize(res.data)
        df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
        df['tax_amount'] = pd.to_numeric(df['tax_amount'], errors='coerce').fillna(0)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Revenue", f"${df['total'].sum():,.2f}")
        m2.metric("VAT Collected", f"${df['tax_amount'].sum():,.2f}")
        m3.metric("Total Bookings", len(df))
        st.dataframe(df[['date_out', 'fleet!fk_rentals_fleet.plate', 'customers!fk_rentals_customers.name', 'total', 'status']], use_container_width=True, hide_index=True)