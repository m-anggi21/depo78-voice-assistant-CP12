import streamlit as st
from modules.auth_web import login_page

st.set_page_config(page_title="Depo 78 Ordering System", page_icon="🛒")

if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# Halaman Login sebagai landing page
login_page()
