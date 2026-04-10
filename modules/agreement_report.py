import streamlit as st
import urllib.parse

def show(supabase, branding):
    st.subheader("📄 Rental Agreement Template")
    rentals_query = supabase.table("rentals").select("id, date_out, fleet!fk_rentals_fleet(plate), customers!fk_rentals_customers(name)").order("date_out", desc=True).limit(20).execute()
    
    if rentals_query.data:
        options = {f"{r['date_out']} | {r['fleet']['plate']} | {r['customers']['name']}": r['id'] for r in rentals_query.data}
        selected_label = st.selectbox("Search Rental Record", options.keys())
        
        if st.button("Generate Report"):
            r = supabase.table("rentals").select("*, fleet!fk_rentals_fleet(*), customers!fk_rentals_customers(*)").eq("id", options[selected_label]).single().execute().data
            with st.container(border=True):
                st.markdown(f"## {branding.get('company_name')}")
                st.write(f"**Customer:** {r['customers']['name']} | **Vehicle:** {r['fleet']['plate']}")
                st.markdown("### 📜 TERMS & CONDITIONS")
                st.caption(branding.get("rental_terms", "Standard terms apply."))
                if r.get('signature_data'):
                    st.image(r['signature_data'], width=250)