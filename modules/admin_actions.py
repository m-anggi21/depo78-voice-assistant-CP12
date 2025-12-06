import psycopg2
import psycopg2.extras
from modules.db import get_db


# ========================================================
# GET ALL ORDERS
# ========================================================
def get_all_orders():
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT id, user_id, nama_lengkap, cluster, blok, no_rumah,
               nomor_antrian, total_harga, status, created_at
        FROM orders
        ORDER BY created_at DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


# ========================================================
# GET ORDER ITEMS
# ========================================================
def get_order_items(order_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT nama_item, qty, harga_satuan, total_harga
        FROM order_items
        WHERE order_id = %s
    """, (order_id,))

    rows = cur.fetchall()
    conn.close()
    return rows


# ========================================================
# UPDATE STATUS ORDER
# ========================================================
def update_order_status(order_id, new_status):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE orders
        SET status = %s
        WHERE id = %s
    """, (new_status, order_id))

    conn.commit()
    conn.close()
    return True


# ========================================================
# DELETE ORDER
# ========================================================
def delete_order(order_id):
    conn = get_db()
    cur = conn.cursor()

    # DELETE ITEMS FIRST
    cur.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))

    # DELETE PARENT ORDER
    cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))

    conn.commit()
    conn.close()
    return True
