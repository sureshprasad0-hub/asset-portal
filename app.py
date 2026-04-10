import streamlit as st
from supabase import create_client, Client
from PIL import Image

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Login Page",
    page_icon="🚗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

supabase = init_connection()

# --- 3. CUSTOM CSS FOR RCA DESIGN ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    /* Vertical alignment for header columns */
    [data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 5. LOGIN INTERFACE ---
if not st.session_state['logged_in']:
    head_col1, head_col2 = st.columns([1, 3])
    
    with head_col1:
        try:
            logo = Image.open("image_718d46.png")
            st.image(logo, use_container_width=True)
        except:
            st.write("🚗")
            
    with head_col2:
        st.markdown("<h1 style='margin:0;'>RENTAL CAR APPLICATION (RCA)</h1>", unsafe_allow_html=True)

    st.caption("<center>Secure Rental Car Management Portal</center>", unsafe_allow_html=True)
    st.write("---")

    with st.container():
        with st.form("login_gate"):
            u = st.text_input("Username", placeholder="e.g. admin").strip().lower()
            p = st.text_input("Password", type="password").strip()
            
            if st.form_submit_button("Sign In to RCA Dashboard"):
                res = supabase.table("portal_users").select("*").eq("username", u).eq("password_hash", p).execute()
                if res.data:
                    st.session_state.update({
                        "logged_in": True, 
                        "user_role": res.data[0]['role'], 
                        "user_name": res.data[0]['full_name']
                    })
                    st.success("Login Successful!")
                    # Redirection directly to 01 Dashboard
                    st.switch_page("pages/01_📊_Dashboard.py")
                else:
                    st.error("Invalid credentials. Please contact your system administrator.")

# --- 6. LOGOUT INTERFACE ---
else:
    st.subheader(f"Welcome back, {st.session_state.get('user_name', 'User')}")
    if st.button("Secure Logout"):
        st.session_state['logged_in'] = False
        st.session_state.pop('user_role', None)
        st.session_state.pop('user_name', None)
        st.rerun()
        
    st.divider()
    if st.button("Return to Dashboard"):
        st.switch_page("pages/01_📊_Dashboard.py")