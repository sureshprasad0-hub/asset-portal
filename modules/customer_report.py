import streamlit as st
import pandas as pd
from datetime import date

def show(supabase):
    st.subheader("👥 All Customers Registry")

    try:
        # Fetch all customers ordered by name
        res = supabase.table("customers").select("*").order("name").execute()
        
        if not res.data:
            st.info("No customer records found in the system.")
            return

        df = pd.DataFrame(res.data)

        # --- 1. SEARCH & FILTER SECTION ---
        search_query = st.text_input("🔍 Search by Name, License, or Phone", placeholder="Type to filter...")
        
        if search_query:
            # Simple case-insensitive filter
            df = df[
                df['name'].str.contains(search_query, case=False, na=False) |
                df['dl_no'].str.contains(search_query, case=False, na=False) |
                df['phone'].str.contains(search_query, case=False, na=False)
            ]

        # --- 2. SUMMARY METRICS ---
        m1, m2 = st.columns(2)
        m1.metric("Total Registered", len(df))
        
        # Count expired licenses if field exists
        if 'dl_expiry' in df.columns:
            expired_count = len(df[pd.to_datetime(df['dl_expiry']).dt.date < date.today()])
            m2.metric("Expired Licenses", expired_count, delta_color="inverse")

        # --- 3. CUSTOMER DATA TABLE ---
        st.write("### Records")
        st.dataframe(
            df[['name', 'phone', 'email', 'dl_no', 'dl_expiry']], 
            use_container_width=True, 
            hide_index=True
        )

        # --- 4. DETAILED CUSTOMER LOOKUP ---
        st.divider()
        st.write("### 🔎 Detailed Customer Profile")
        selected_customer = st.selectbox(
            "Select a customer to view full profile", 
            options=df['name'].tolist(),
            index=None,
            placeholder="Choose a name..."
        )

        if selected_customer:
            cust = df[df['name'] == selected_customer].iloc[0]
            
            with st.container(border=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Full Name:** {cust['name']}")
                    st.markdown(f"**Phone:** {cust.get('phone', 'N/A')}")
                    st.markdown(f"**Email:** {cust.get('email', 'N/A')}")
                    st.markdown(f"**Address:** {cust.get('address', 'N/A')}")
                with c2:
                    st.markdown(f"**License Number:** {cust.get('dl_no', 'N/A')}")
                    st.markdown(f"**License Expiry:** {cust.get('dl_expiry', 'N/A')}")
                    st.markdown(f"**Date of Birth:** {cust.get('dob', 'N/A')}")
                    
                st.divider()
                st.write("**Internal Notes:**")
                st.info(cust.get('notes') or "No specific notes for this customer.")

    except Exception as e:
        st.error(f"Error loading customer data: {e}")