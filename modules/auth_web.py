import streamlit as st
import hashlib
import psycopg2
import psycopg2.extras
from modules.db import get_db


# =====================================================
# HASH PASSWORD
# =====================================================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()


# =====================================================
# LOGIN
# =====================================================
def login_page():
    st.title("🔐 Login Sistem Depo 78")

    username = st.text_input("Username")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            conn = get_db()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            cur.execute("""
                SELECT * FROM users
                WHERE username = %s AND password_hash = %s
            """, (username, hash_password(pw)))

            customer = cur.fetchone()
            conn.close()

        except Exception as e:
            st.error(f"Gagal menghubungkan database: {e}")
            return

        if not customer:
            st.error("Username atau password salah.")
            return

        st.session_state["user"] = dict(user)
        st.session_state["role"] = customer["role"].lower()
        st.session_state["logged_in"] = True

        if customer["role"] == "admin":
            st.switch_page("pages/3_Admin_Dashboard.py")
        else:
            st.switch_page("pages/2_User_Order.py")


# =====================================================
# REGISTER
# =====================================================
def register_page():
    st.title("📝 Registrasi Akun Pengguna")

    nama = st.text_input("Nama lengkap")
    username = st.text_input("Username")
    cluster = st.text_input("Cluster")
    blok = st.text_input("Blok")
    no_rumah = st.text_input("No Rumah")
    gender = st.selectbox("Gender", ["L", "P"])
    notelp = st.text_input("Nomor Telepon")
    pw = st.text_input("Password", type="password")
    cpw = st.text_input("Konfirmasi Password", type="password")

    if st.button("Daftar"):

        if pw != cpw:
            st.error("Password tidak sama.")
            return

        try:
            conn = get_db()
            cur = conn.cursor()

            # cek username
            cur.execute("SELECT id FROM users WHERE username=%s", (username,))
            exists = cur.fetchone()

            if exists:
                st.error("Username sudah digunakan!")
                conn.close()
                return

            # insert user baru
            cur.execute("""
                INSERT INTO users
                    (nama, username, cluster, blok, no_rumah, gender, notelp, password_hash, role)
                VALUES
                    (%s,%s,%s,%s,%s,%s,%s,%s,'customer')
            """, (
                nama, username, cluster, blok, no_rumah,
                gender, notelp, hash_password(pw)
            ))

            conn.commit()
            conn.close()

            st.success("Akun berhasil dibuat! Silakan login.")

        except Exception as e:
            st.error(f"Gagal mendaftar: {e}")

