import streamlit as st
from modules.admin_actions import admin_page

if st.session_state.get("role") != "admin":
    st.error("Halaman ini hanya untuk admin.")
else:
    admin_page()
