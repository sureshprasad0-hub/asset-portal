import streamlit as st
import pandas as pd

def show(supabase):
    st.subheader("🚗 Fleet Inventory Report")

    try:
        # Fetch fleet data
        res = supabase.table("fleet").select("*").order("plate").execute()
        
        if not res.data:
            st.info("No vehicles found in inventory.")
            return

        df = pd.DataFrame(res.data)

        # --- FILTERS ---
        all_statuses = ["All"] + sorted(df['status'].unique().tolist())
        selected_status = st.selectbox("Filter by Fleet Status", all_statuses)

        if selected_status != "All":
            df = df[df['status'] == selected_status]

        # --- GROUPING & SUMMARY ---
        st.write(f"### Inventory Summary ({selected_status})")
        
        # Display grouping by status
        summary = df.groupby('status').size().reset_index(name='Count')
        st.table(summary)

        # --- DATA TABLE ---
        st.dataframe(df[['plate', 'brand', 'model', 'year', 'status', 'current_odo']], 
                     use_container_width=True, hide_index=True)

        # --- ACTIONS: EXPORT & PRINT ---
        st.divider()
        c1, c2 = st.columns(2)

        with c1:
            # Export to CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export to CSV",
                data=csv,
                file_name=f"fleet_inventory_{selected_status.lower()}.csv",
                mime='text/csv',
                use_container_width=True
            )

        with c2:
            # Print Option (Browser Print Dialog)
            if st.button("🖨️ Print Report", use_container_width=True):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
                st.info("Browser print dialog triggered.")

    except Exception as e:
        st.error(f"Error generating fleet report: {e}")