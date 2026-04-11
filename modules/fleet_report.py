import streamlit as st
import pandas as pd

def show(supabase):
    st.subheader("🚗 Detailed Fleet Inventory Report")

    try:
        # Fetch complete fleet data
        res = supabase.table("fleet").select("*").order("plate").execute()
        
        if not res.data:
            st.info("No vehicles found in inventory.")
            return

        df = pd.DataFrame(res.data)

        # --- 1. FILTERS & SUMMARY ---
        if 'status' in df.columns:
            all_statuses = ["All"] + sorted(df['status'].unique().tolist())
            selected_status = st.selectbox("Filter by Fleet Status", all_statuses)

            if selected_status != "All":
                df = df[df['status'] == selected_status]
            
            st.write(f"### Inventory Summary ({selected_status})")
            summary = df.groupby('status').size().reset_index(name='Count')
            st.table(summary)
        else:
            selected_status = "All"

        # --- 2. GLOBAL FLEET TABLE ---
        # Displaying key columns only in the overview table
        standard_columns = ['plate', 'brand', 'model', 'year', 'status', 'current_odo']
        available_overview = [col for col in standard_columns if col in df.columns]
        
        st.write("### Quick Overview")
        st.dataframe(df[available_overview], use_container_width=True, hide_index=True)

        # --- 3. DETAILED INDIVIDUAL VEHICLE REPORT ---
        st.divider()
        st.write("### 🔎 Individual Vehicle Detail Report")
        
        # Create a search/select box for a specific vehicle
        vehicle_options = {f"{v['plate']} - {v.get('brand','')} {v.get('model','')}": v['id'] for _, v in df.iterrows()}
        selected_label = st.selectbox("Select a vehicle for full details", options=vehicle_options.keys(), index=None, placeholder="Search Plate Number...")

        if selected_label:
            v_id = vehicle_options[selected_label]
            v = df[df['id'] == v_id].iloc[0]
            
            with st.container(border=True):
                st.markdown(f"## Vehicle Report: {v['plate']}")
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("**🆔 BASIC INFO**")
                    st.write(f"**Brand:** {v.get('brand', 'N/A')}")
                    st.write(f"**Model:** {v.get('model', 'N/A')}")
                    st.write(f"**Year:** {v.get('year', 'N/A')}")
                with c2:
                    st.markdown("**🔧 TECHNICAL**")
                    st.write(f"**Odometer:** {v.get('current_odo', 0):,} km")
                    st.write(f"**Engine No:** {v.get('engine_no', 'N/A')}")
                    st.write(f"**Chassis No:** {v.get('chassis_no', 'N/A')}")
                with c3:
                    st.markdown("**📅 COMPLIANCE**")
                    st.write(f"**Status:** {v.get('status', 'N/A')}")
                    st.write(f"**Rego Expiry:** {v.get('rego_expiry', 'N/A')}")
                    st.write(f"**Next Service:** {v.get('next_service_odo', 0):,} km")

                if v.get('notes'):
                    st.divider()
                    st.write("**Maintenance & Fleet Notes:**")
                    st.info(v['notes'])

        # --- 4. ACTIONS: EXPORT & PRINT ---
        st.divider()
        act1, act2 = st.columns(2)

        with act1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Current View to CSV",
                data=csv,
                file_name=f"fleet_report_{selected_status.lower()}.csv",
                mime='text/csv',
                use_container_width=True
            )

        with act2:
            if st.button("🖨️ Print This Page", use_container_width=True):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error generating fleet report: {e}")