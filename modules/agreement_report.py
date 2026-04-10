import streamlit as st
import urllib.parse

def show(supabase, branding):
    st.subheader("📄 Rental Agreement Template")
    
    # 1. Fetch recent rentals
    rentals_query = supabase.table("rentals").select(
        "id, date_out, fleet!fk_rentals_fleet(plate), customers!fk_rentals_customers(name)"
    ).order("date_out", desc=True).limit(20).execute()
    
    if not rentals_query.data:
        st.info("No rental records found.")
        return

    options = {f"{r['date_out']} | {r['fleet']['plate']} | {r['customers']['name']}": r['id'] for r in rentals_query.data}
    selected_label = st.selectbox("Search Rental Record", options.keys())
    
    # 2. Use a button to trigger the display
    if st.button("Generate Full Report", use_container_width=True):
        st.session_state.view_agreement_id = options[selected_label]

    # 3. Render the report if an ID is stored in session state
    if st.session_state.get('view_agreement_id'):
        rental_id = st.session_state.view_agreement_id
        
        # Fetch full details including the signature and terms
        r_data = supabase.table("rentals").select(
            "*, fleet!fk_rentals_fleet(*), customers!fk_rentals_customers(*)"
        ).eq("id", rental_id).single().execute()
        
        if r_data.data:
            r = r_data.data
            with st.container(border=True):
                # Header
                h1, h2 = st.columns([1, 2])
                with h1:
                    if branding.get("company_logo"):
                        st.image(branding.get("company_logo"), width=150)
                with h2:
                    st.markdown(f"## {branding.get('company_name', 'RCA Fiji')}")
                    st.caption(f"📍 {branding.get('company_address', '')}")

                st.markdown("<h2 style='text-align: center;'>RENTAL AGREEMENT</h2>", unsafe_allow_html=True)
                st.divider()

                # Details
                c1, c2 = st.columns(2)
                c1.write(f"**Customer:** {r['customers']['name']}")
                c2.write(f"**Vehicle:** {r['fleet']['plate']} ({r['fleet']['brand']})")

                # Terms & Conditions from Settings
                st.markdown("### 📜 Terms & Conditions")
                st.caption(branding.get("rental_terms", "Standard terms apply."))

                # Signature
                st.markdown("### ✍️ Signature")
                sig = r.get('signature_data') or r.get('signature_url')
                if sig:
                    st.image(sig, width=300)
                else:
                    st.warning("No signature captured for this rental.")

                # Action Buttons
                st.divider()
                if st.button("🖨️ Print / Save PDF"):
                    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
                
                if st.button("❌ Close Report"):
                    st.session_state.view_agreement_id = None
                    st.rerun()