import streamlit as st
from modules.nlp_engine import (
    parse_orders_verbose,
    summarize_parsed_results,
    get_ambiguity_options,
    apply_user_choice,
)
from modules.catalog_loader import load_catalog
from modules.order_utils_web import save_order_web
from modules.voice_input_auto import voice_auto_component

# ============================================================
# INITIALIZE SESSION STATE
# ============================================================

def init_session():
    if "cart" not in st.session_state:
        st.session_state.cart = []  # list of {product_key, nama_item, harga, qty}

    if "pending_ambiguity" not in st.session_state:
        st.session_state.pending_ambiguity = None  # {chunk_info, options}

    if "order_active" not in st.session_state:
        st.session_state.order_active = True  # session ordering aktif

    if "last_message" not in st.session_state:
        st.session_state.last_message = ""


# ============================================================
# UTILITY
# ============================================================

def add_items_to_cart(items):
    """Menambahkan item-item yang sudah final ke keranjang."""
    for it in items:
        st.session_state.cart.append(it)


def render_cart_summary():
    """Menampilkan ringkasan keranjang secara visual."""
    cart = st.session_state.cart
    if not cart:
        st.info("Keranjang masih kosong.")
        return 0

    total = 0
    for it in cart:
        subtotal = it["harga"] * it["qty"]
        total += subtotal
        st.write(f"- **{it['nama_item']}** x{it['qty']} (Rp{subtotal:,})")

    st.write("---")
    st.success(f"Total harga: **Rp{total:,}**")
    return total


def finalize_order(user):
    """Menyimpan order ke database dan reset keranjang."""
    cart = st.session_state.cart
    if not cart:
        st.warning("Keranjang kosong.")
        return None, None

    total_harga = sum(it["harga"] * it["qty"] for it in cart)
    nomor, order_id = save_order_web(user, cart, total_harga)

    # reset state
    st.session_state.cart = []
    st.session_state.order_active = False

    return nomor, order_id


# ============================================================
# NLP PROCESSOR
# ============================================================

def handle_user_input(text, catalog):
    """
    Menerima input user (text), menjalankan NLP, dan update state.
    Return value akan diperiksa oleh UI.
    """

    text_norm = text.lower().strip()

    # ====== SPECIAL COMMANDS ======
    if text_norm == "cukup":
        return {"type": "summary"}

    if text_norm == "bayar":
        return {"type": "pay"}

    # ====== NORMAL NLP ======
    parsed_chunks = parse_orders_verbose(text_norm, catalog)
    summary = summarize_parsed_results(parsed_chunks, catalog)

    result = {"type": "parsed", "summary": summary, "chunks": parsed_chunks}

    # Jika ada ambiguity, kita simpan 1 per 1
    if summary["needs_choice"]:
        need = summary["needs_choice"][0]
        st.session_state.pending_ambiguity = need
        result["type"] = "need_choice"

    return result


def user_choose_ambiguity(chosen_key):
    """Ketika user memilih satu produk dari daftar ambiguity."""
    need = st.session_state.pending_ambiguity
    if not need:
        return

    catalog = load_catalog()

    chunk_info = need.get("chunk_info")
    if not chunk_info:
        return

    # Terapkan pilihan
    apply_user_choice(chunk_info, chosen_key)

    # Masukkan 1 item final ke keranjang
    item = {
        "product_key": chosen_key,
        "nama_item": catalog[chosen_key]["nama"],
        "harga": catalog[chosen_key]["harga"],
        "qty": chunk_info["qty"]
    }
    st.session_state.cart.append(item)

    # Hapus ambiguity
    st.session_state.pending_ambiguity = None


# ============================================================
# MAIN UI PAGE: USER ORDER PAGE
# ============================================================

def user_order_page():
    st.title("🛒 Voice/Text Ordering — Depo 78")
    init_session()

    user = st.session_state.get("user")
    if not user:
        st.error("Anda belum login.")
        return

    catalog = load_catalog()

    # ============================================================
    # TEXT INPUT AREA
    # ============================================================
    st.subheader("⌨️ Input Teks")
    text_inp = st.text_input("Contoh: 'aqua galon dua', 'gas bright 5kg satu', 'cukup', 'bayar'")

    if st.button("Kirim Teks"):
        if not text_inp.strip():
            st.warning("Masukkan perintah.")
        else:
            result = handle_user_input(text_inp, catalog)
            st.session_state.last_message = text_inp
            _process_result(result, user, catalog)



    # ============================================================
    # VOICE INPUT AREA (AUTO MODE)
    # ============================================================
    st.subheader("🎤 Voice Input (Auto Mode)")
    st.markdown("Klik **Start** → Bicara → Sistem otomatis mengenali perintah Anda.")

    def process_voice(text):
        st.success(f"🎧 Anda berkata: **{text}**")

        result = handle_user_input(text, catalog)
        st.session_state.last_message = text

        _process_result(result, user, catalog)

    voice_auto_component(process_voice)



    # ============================================================
    # SIDEBAR: CART SUMMARY
    # ============================================================
    st.sidebar.header("🧺 Keranjang Saat Ini")
    render_cart_summary()

# ============================================================
# INTERNAL RESULT PROCESSOR
# ============================================================

def _process_result(result, user, catalog):
    """Memproses hasil NLP berdasarkan tipe event."""

    # ---------- RINGKASAN ----------
    if result["type"] == "summary":
        st.subheader("📦 Ringkasan Pesanan")
        render_cart_summary()
        return

    # ---------- BAYAR ----------
    if result["type"] == "pay":
        nomor, oid = finalize_order(user)
        if nomor:
            st.success(f"Pesanan berhasil disimpan! Nomor antrian: **{nomor}**")
        else:
            st.error("Gagal menyimpan order.")
        return

    # ---------- AMBIGUITY ----------
    if result["type"] == "need_choice":
        need = st.session_state.pending_ambiguity
        st.warning(need["message"])

        for opt in need["options"]:
            label = opt["label"]
            key = opt["key"]

            # Temukan chunk_info yang ambiguous
            for ch in result["chunks"]:
                if ch["ambiguity"]:
                    need["chunk_info"] = ch
                    break

            if st.button(label):
                user_choose_ambiguity(key)
                st.success(f"Produk **{label}** dipilih dan ditambahkan ke keranjang.")
        return

    # ---------- PARSED NORMAL ----------
    if result["type"] == "parsed":
        summary = result["summary"]

        if summary["errors"]:
            st.error("❌ Beberapa input tidak dikenali:")
            for err in summary["errors"]:
                st.write(f"- {err['message']}")

        if summary["items"]:
            add_items_to_cart(summary["items"])
            st.success(f"✔ {len(summary['items'])} item ditambahkan ke keranjang.")

        if not summary["errors"]:
            st.info("Input berhasil diproses.")
