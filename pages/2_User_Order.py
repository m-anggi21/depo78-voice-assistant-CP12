import streamlit as st
from modules.order_session import user_order_page

# Pastikan user login
if "logged_in" not in st.session_state or st.session_state["logged_in"] != True:
    st.error("Anda belum login.")
    st.stop()

# Pastikan role adalah customer (atau user)
if st.session_state["role"] not in ["customer", "user"]:
    st.error("Anda tidak memiliki akses ke halaman ini.")
    st.stop()

user_order_page()
