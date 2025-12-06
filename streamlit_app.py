import streamlit as st
from modules.auth_web import login_page

# ==========================================
# CONFIG
# ==========================================
st.set_page_config(
    page_title="Depo 78 Ordering System",
    page_icon="🛒",
    layout="wide"
)

# ==========================================
# INIT SESSION
# ==========================================
if "user" not in st.session_state:
    st.session_state["user"] = None

if "role" not in st.session_state:
    st.session_state["role"] = None

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False


# ==========================================
# REDIRECT LOGIC
# ==========================================
# Jika sudah login → redirect otomatis
if st.session_state["logged_in"]:

    # ADMIN → langsung ke Admin Dashboard
    if st.session_state["role"] == "admin":
        st.switch_page("pages/3_Admin_Dashboard.py")

    # USER → langsung ke halaman User Order
    elif st.session_state["role"] == "user":
        st.switch_page("pages/2_User_Order.py")

    else:
        st.error("Role tidak dikenali!")


# ==========================================
# LANDING PAGE = LOGIN PAGE
# ==========================================
login_page()
