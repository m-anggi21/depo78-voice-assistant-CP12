import mysql.connector
import time

DB = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "depo78"
}

def db():
    return mysql.connector.connect(**DB)

def generate_queue():
    today = time.strftime("%y%m%d")
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO queue_numbers(tanggal) VALUES (%s)", (today,))
    conn.commit()
    c.execute("SELECT LAST_INSERT_ID()")
    urut = c.fetchone()[0]
    conn.close()
    return f"Dep78-{today}-{urut:03d}"

def save_order_web(user, cart_items, total):
    conn = db()
    c = conn.cursor()

    nomor = generate_queue()
    c.execute("""
        INSERT INTO orders (user_id, nama_lengkap, cluster, blok, no_rumah, 
            nomor_antrian, total_harga, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'menunggu')
    """, (user["id"], user["nama"], user["cluster"], user["blok"],
          user["no_rumah"], nomor, total))
    conn.commit()

    c.execute("SELECT LAST_INSERT_ID()")
    order_id = c.fetchone()[0]

    for item in cart_items:
        key, qty, nama_item, harga_satuan = item
        total_item = qty * harga_satuan
        c.execute("""
            INSERT INTO order_items(order_id,nama_item,qty,harga_satuan,total_harga)
            VALUES (%s,%s,%s,%s,%s)
        """, (order_id, nama_item, qty, harga_satuan, total_item))

    conn.commit()
    conn.close()
    return nomor, order_id
