import streamlit as st
import mysql.connector
import hashlib

DB = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "depo78"
}

def db():
    return mysql.connector.connect(**DB)

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()


# =====================================================
# LOGIN PAGE
# =====================================================
def login_page():
    st.title("🔐 Login Sistem Depo 78")

    username = st.text_input("Username")
    pw = st.text_input("Password", type="password")

    if st.button("Login"):

        conn = db()
        c = conn.cursor(dictionary=True)
        c.execute("""
            SELECT * FROM users 
            WHERE username=%s AND password_hash=%s
        """, (username, hash_password(pw)))

        user = c.fetchone()
        conn.close()

        if not user:
            st.error("Username atau password salah.")
            return

        # SIMPAN SESSION STATE DENGAN CARA YANG BENAR
        st.session_state["user"] = user
        st.session_state["role"] = user["role"].lower()   # FIX UTAMA
        st.session_state["logged_in"] = True

        if st.session_state["role"] == "admin":
            st.success("Login berhasil. Anda login sebagai Admin.")
            st.switch_page("pages/3_Admin_Dashboard.py")
        else:
            st.success("Login berhasil. Anda login sebagai User.")
            st.switch_page("pages/2_User_Order.py")

# =====================================================
# REGISTER PAGE (USER ONLY)
# =====================================================
def register_page():
    st.title("📝 Registrasi Akun Pengguna")

    nama = st.text_input("Nama lengkap")
    username = st.text_input("Username")
    cluster = st.text_input("Cluster")
    blok = st.text_input("Blok")
    no_rumah = st.text_input("No Rumah")
    gender = st.selectbox("Gender", ["L", "P"])
    telepon = st.text_input("Nomor Telepon")
    pw = st.text_input("Password", type="password")
    cpw = st.text_input("Konfirmasi Password", type="password")

    if st.button("Daftar"):

        if pw != cpw:
            st.error("Password tidak sama.")
            return

        conn = db()
        c = conn.cursor()

        c.execute("SELECT id FROM users WHERE username=%s", (username,))
        if c.fetchone():
            st.error("Username sudah digunakan.")
            return

        c.execute("""
            INSERT INTO users(nama, username, cluster, blok, no_rumah,
                gender, notelp, password_hash, role)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'user')
        """, (nama, username, cluster, blok, no_rumah,
              gender, telepon, hash_password(pw)))

        conn.commit()
        conn.close()

        st.success("Akun berhasil dibuat! Silakan login.")
