import streamlit as st

def show(supabase, branding):
    st.subheader("📄 Rental Agreement Template")
    
    # Initialize sub-state for the specific record
    if 'view_agreement_id' not in st.session_state:
        st.session_state.view_agreement_id = None

    # Fetch recent rentals
    res = supabase.table("rentals").select(
        "id, date_out, fleet!fk_rentals_fleet(plate), customers!fk_rentals_customers(name)"
    ).order("date_out", desc=True).limit(20).execute()
    
    if res.data:
        options = {f"{r['date_out']} | {r['fleet']['plate']} | {r['customers']['name']}": r['id'] for r in res.data}
        selected = st.selectbox("Select Record", options.keys())
        
        # When clicked, save the ID to session state
        if st.button("Generate Full Report"):
            st.session_state.view_agreement_id = options[selected]
            st.rerun()

    # If an ID is saved, show the report
    if st.session_state.view_agreement_id:
        rental_id = st.session_state.view_agreement_id
        r = supabase.table("rentals").select(
            "*, fleet!fk_rentals_fleet(*), customers!fk_rentals_customers(*)"
        ).eq("id", rental_id).single().execute().data
        
        if r:
            with st.container(border=True):
                st.markdown(f"<h2 style='text-align: center;'>{branding.get('company_name')}</h2>", unsafe_allow_html=True)
                st.divider()
                st.write(f"**Customer:** {r['customers']['name']}")
                st.write(f"**Vehicle:** {r['fleet']['plate']}")
                
                # Dynamic Terms & Signature
                st.markdown("### 📜 Terms & Conditions")
                st.caption(branding.get("rental_terms", "Default terms..."))
                
                sig = r.get('signature_data')
                if sig:
                    st.image(sig, width=250)
                
                if st.button("❌ Close This Agreement"):
                    st.session_state.view_agreement_id = None
                    st.rerun()