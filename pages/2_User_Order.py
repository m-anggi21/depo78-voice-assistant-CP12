import streamlit as st
from modules.order_session import user_order_page
from modules.voice_input_auto import voice_auto_component

if st.session_state.get("role") != "customer":
    st.write("DEBUG SESSION:", dict(st.session_state))
    st.error("Anda tidak memiliki akses ke halaman ini.")
    st.stop()
else:
    user_order_page()
