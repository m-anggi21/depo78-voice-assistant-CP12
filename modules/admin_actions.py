import streamlit as st
import mysql.connector

DB = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "depo78"
}

def db():
    return mysql.connector.connect(**DB)


def get_orders():
    c = db().cursor(dictionary=True)
    c.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = c.fetchall()
    return rows


def admin_page():
    st.title("📦 Admin Dashboard Depo 78")

    orders = get_orders()

    for o in orders:
        with st.expander(f"Order {o['nomor_antrian']} — {o['nama_lengkap']}"):
            st.write(o)

            new_status = st.selectbox(
                "Ubah status:",
                ["menunggu", "diproses", "dikirim", "selesai"],
                index=["menunggu", "diproses", "dikirim", "selesai"].index(o["status"]),
                key=f"stat-{o['id']}"
            )

            if st.button(f"Simpan status {o['id']}", key=f"smp-{o['id']}"):
                conn = db()
                c = conn.cursor()
                c.execute("UPDATE orders SET status=%s WHERE id=%s",
                          (new_status, o["id"]))
                conn.commit()
                conn.close()
                st.success("Status diperbarui. Refresh halaman.")
