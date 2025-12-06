import streamlit as st
import psycopg2
import psycopg2.extras

def get_db():
    conn = psycopg2.connect(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        sslmode=st.secrets["DB_SSLMODE"]
    )
    return conn
