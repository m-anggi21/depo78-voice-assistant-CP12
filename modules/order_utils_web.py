import time
import psycopg2
import psycopg2.extras
from modules.db import get_db   # gunakan koneksi Supabase


# ============================================================
# GENERATE NOMOR ANTRIAN
# Format: Dep78-YYMMDD-XXX
# ============================================================
def generate_queue():
    today = time.strftime("%y%m%d")

    conn = get_db()
    cur = conn.cursor()

    # Insert row dummy → supaya dapat auto-increment id
    cur.execute("""
        INSERT INTO queue_numbers (tanggal)
        VALUES (%s)
        RETURNING id
    """, (today,))

    queue_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    return f"Dep78-{today}-{queue_id:03d}"


# ============================================================
# SAVE ORDER → untuk USER WEB STREAMLIT
# cart_items format dari order_session.py:
# {
#   "product_key": ...
#   "nama_item": ...
#   "harga": ...
#   "qty": ...
# }
# ============================================================
def save_order_web(user, cart_items, total):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    nomor = generate_queue()

    # INSERT ke tabel orders
    cur.execute("""
        INSERT INTO orders (
            user_id, nama_lengkap, cluster, blok, no_rumah,
            nomor_antrian, total_harga, status
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,'menunggu')
        RETURNING id
    """, (
        user["id"], user["nama"], user["cluster"], user["blok"],
        user["no_rumah"], nomor, total
    ))

    order_id = cur.fetchone()["id"]
    conn.commit()

    # INSERT ORDER ITEMS
    for item in cart_items:
        cur.execute("""
            INSERT INTO order_items (
                order_id, nama_item, qty, harga_satuan, total_harga
            )
            VALUES (%s,%s,%s,%s,%s)
        """, (
            order_id,
            item["nama_item"],
            item["qty"],
            item["harga"],
            item["qty"] * item["harga"],
        ))

    conn.commit()
    conn.close()

    return nomor, order_id
