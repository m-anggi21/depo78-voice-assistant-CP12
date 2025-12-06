# ============================================================
# NLP ENGINE — DEPO 78
# Modular & Rapi (Opsi 1) — 100% logic sama seperti versi CLI
# ============================================================

import re


# ============================================================
# A. NORMALISASI & KONSTANTA
# ============================================================

def normalize(s):
    """Menormalkan string menjadi lowercase tanpa simbol aneh."""
    if s is None:
        return ""
    s = str(s).lower()
    s = re.sub(r"[^a-z0-9\s\.]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# STOPWORDS yang tidak berpengaruh pada parsing
STOPWORDS = {
    "saya", "aku", "mau", "ingin", "dong", "ya", "deh", "nih",
    "pesan", "beli", "order", "punya", "tolong"
}

# Kata angka dasar
NUM_WORDS = {
    "satu": 1, "sebuah": 1, "sebiji": 1,
    "dua": 2, "tiga": 3, "empat": 4, "lima": 5,
    "enam": 6, "tujuh": 7, "delapan": 8,
    "sembilan": 9, "sepuluh": 10, "sebelas": 11,
    "duabelas": 12, "dua belas": 12
}


# ============================================================
# SIZE GROUP CONFIG (SAMA PERSIS SEPERTI CLI)
# ============================================================

SIZE_GROUP = {
    "big": {
        "words": ["besar", "gede", "jumbo"],
        "patterns": ["1500", "1.5"],
    },
    "medium": {
        "words": ["sedang", "tanggung"],
        "patterns": ["600", "500"],
    },
    "small": {
        "words": ["mini", "kecil", "baby", "bebi"],
        "patterns": ["330", "350"],
    },
    "cup-only": {
        "words": ["cup", "gelas"],
        "patterns": ["cup", "240"],
    },
    "galon": {
        "words": ["galon"],
        "patterns": ["19", "galon"],
    }
}

# kumpulan kata varian yang dianggap "mengandung varian"
ALIAS_VARIANT_WORDS = set()
for cfg in SIZE_GROUP.values():
    for w in cfg["words"]:
        ALIAS_VARIANT_WORDS.add(w)

# Tambahan kata varian dari CLI
ALIAS_VARIANT_WORDS |= {
    "gas",
    "kg", "kilo", "kilogram",
    "ml", "mililiter",
    "l", "liter", "ltr",
}

# Kata kemasan
PACKAGING_WORDS = {"dus", "kardus", "karton", "kerdus", "box"}
ALIAS_VARIANT_WORDS |= PACKAGING_WORDS


# ============================================================
# CATEGORY GUESS
# ============================================================

def guess_category(tokens):
    """Deteksi kategori umum berdasarkan kata-kata."""
    s = " ".join(tokens)
    if re.search(r"\b(gas|elpiji|lpg|bright|tabung|kg)\b", s):
        return "gas"

    if re.search(r"\b(air|galon|aqua|minerale|le|mineral|leminerale|botol|dus|cup|gelas)\b", s):
        return "air"

    return None


# ============================================================
# NUMERIK VARIANT / QTY DETECTION SUPPORT
# ============================================================

def word_to_num(t):
    """Konversi kata atau angka string menjadi integer qty."""
    t = t.strip().lower()
    if t.isdigit():
        return int(t)

    # angka bentuk float
    try:
        if re.fullmatch(r"\d+(\.\d+)?", t):
            val = float(t)
            return max(1, int(val))
    except:
        pass

    return NUM_WORDS.get(t, None)


def expand_quantity(tokens):
    """
    Logika qty dari CLI — digunakan untuk parsing jumlah eksplisit,
    termasuk format '3 botol', '2 dus', dan deteksi angka selain varian.
    """
    UNIT_VARIAN = {"kg", "kilo", "kilogram", "l", "liter", "ltr", "ml", "mililiter"}
    QTY_UNITS = {
        "tabung", "galon", "botol", "dus", "karton", "pack", "buah",
        "pcs", "pcs.", "cup", "gelas"
    }

    s = " ".join(tokens)

    # Format "3 botol"
    m = re.search(r"\b(\d+)\s*(" + "|".join(QTY_UNITS) + r")\b", s)
    if m:
        try:
            return max(1, int(m.group(1)))
        except:
            pass

    # Hilangkan pola angka + satuan varian (misal 3 kg, 600 ml)
    s2 = re.sub(r"\b\d+(?:\.\d+)?\s*(kg|kilo|kilogram|l|liter|ltr|ml|mililiter)\b", " ", s)
    s2 = re.sub(r"\s+", " ", s2).strip()

    toks = s2.split()
    for i, t in enumerate(toks):
        n = word_to_num(t)
        if n:
            # Pastikan bukan varian
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if nxt in UNIT_VARIAN:
                continue
            return n

    # fallback ambil angka pertama
    m3 = re.search(r"\b(\d+)\b", s2)
    if m3:
        try:
            return max(1, int(m3.group(1)))
        except:
            pass

    return 1
# ============================================================
# B. ALIAS ENGINE
# ============================================================

# alias_index akan diisi oleh build_alias_index()
ALIAS_INDEX = {}


def build_alias_index(catalog):
    """
    Sama seperti CLI:
    - Membuat dictionary: alias_norm -> list produk key.
    - alias_norm adalah hasil normalize(alias).
    """
    global ALIAS_INDEX
    idx = {}

    for key, meta in catalog.items():
        aliases = meta.get("aliases", [])
        if not aliases:
            continue

        for alias in aliases:
            alias_norm = normalize(alias)
            if not alias_norm:
                continue

            idx.setdefault(alias_norm, []).append(key)

    ALIAS_INDEX = idx
    return idx


def alias_has_variant_info(alias_str):
    """
    Menentukan apakah alias mengandung informasi varian.
    Sama 100% seperti CLI:
    - Apabila alias mengandung angka ukuran atau kata varian:
      contoh: aqua 600, gas 3kg, galon, dus, besar, kecil.
    """
    s = normalize(alias_str)
    if not s:
        return False

    # Jika ada angka → kemungkinan ukuran / varian
    if any(ch.isdigit() for ch in s):
        return True

    tokens = s.split()
    # Jika mengandung kata varian
    if any(tok in ALIAS_VARIANT_WORDS for tok in tokens):
        return True

    return False


def find_alias_candidates_from_text(text_norm):
    """
    Mengembalikan:
    - strong_keys → alias yang mengandung info varian
    - weak_keys   → alias generik (brand saja)
    """
    strong = set()
    weak = set()

    if not ALIAS_INDEX:
        return [], []

    for alias_norm, keys in ALIAS_INDEX.items():
        if alias_norm in text_norm:
            if alias_has_variant_info(alias_norm):
                strong.update(keys)
            else:
                weak.update(keys)

    return list(strong), list(weak)


def find_direct_alias_hits(text_norm):
    """
    PRIORITAS UTAMA CLI:
    1. Exact match alias
    2. Partial match (alias_norm in text_norm atau sebaliknya)
    Jika menghasilkan satu produk → langsung dipilih.
    """
    text_norm = normalize(text_norm)
    if not text_norm or not ALIAS_INDEX:
        return []

    exact_keys = set()
    partial_keys = set()

    # Exact match
    for alias_norm, keys in ALIAS_INDEX.items():
        if text_norm == alias_norm:
            exact_keys.update(keys)

    if exact_keys:
        return list(exact_keys)

    # Partial match
    for alias_norm, keys in ALIAS_INDEX.items():
        if alias_norm in text_norm or text_norm in alias_norm:
            partial_keys.update(keys)

    return list(partial_keys)
# ============================================================
# BRAND ENGINE
# ============================================================

def extract_brand_tokens(tokens):
    """
    Sama dengan CLI:
    - Menghapus angka dan satuan (ml, liter, kg)
    - Menghapus kata generik 'gas' dan 'air'
    - Menghapus token panjang tidak wajar
    """
    GENERIC_BRAND_WORDS = {"gas", "air"}
    out = []

    for t in tokens:
        if not t:
            continue

        # kata generik bukan brand
        if t in GENERIC_BRAND_WORDS:
            continue

        # angka / ukuran / unit → diabaikan
        if re.fullmatch(
            r"\d+|"           # 3, 600
            r"\d+\.\d+|"      # 1.5
            r"\d+ml|"         # 600ml
            r"\d+\.\d+ml|"    # 1.5ml
            r"\d+l|"          # 1l
            r"\d+\.\d+l|"     # 1.5l
            r"kg|kilo|kilogram|liter|l|ltr|ml|mililiter|"
            r"galon|botol|dus|pack|karton|kardus|kerdus|pcs|buah|cup|gelas",
            t
        ):
            continue

        if len(t) > 30:
            continue

        out.append(t)

    return out


def find_brand_candidates(tokens, catalog):
    """
    Sama seperti CLI:
    Brand candidate ditemukan dari:
    1. Token yang cocok dengan meta['brand']
    2. Jika 1 tidak ada, cocokkan kata di nama + aliases
    """
    toks_norm = [normalize(t) for t in tokens if t]
    brand_tokens = extract_brand_tokens(toks_norm)

    if not brand_tokens:
        return []

    candidates = []
    seen = set()

    # 1) Cocok dengan kolom brand persis
    for bt in brand_tokens:
        for key, meta in catalog.items():
            brand = (meta.get("brand") or "").strip().lower()
            if brand and bt == brand and key not in seen:
                candidates.append(key)
                seen.add(key)

    if candidates:
        return candidates

    # 2) Cocok nama / alias (lebih longgar)
    for bt in brand_tokens:
        patt = re.compile(r"\b" + re.escape(bt) + r"\b")
        for key, meta in catalog.items():
            hay = " ".join([
                normalize(meta.get("nama", "")),
                *[normalize(a) for a in meta.get("aliases", [])]
            ])
            if patt.search(hay) and key not in seen:
                candidates.append(key)
                seen.add(key)

    return candidates
# ============================================================
# C. VARIANT DETECTION
# ============================================================

def detect_variant(tokens):
    """Deteksi varian eksplisit dari CLI."""
    joined = " ".join(tokens).replace(",", " ")

    # numerik kg
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|kilo|kilogram)\b", joined)
    if m:
        raw = m.group(1)
        if raw.endswith(".0"):
            raw = raw[:-2]
        return f"{raw}kg"

    # liter
    m = re.search(r"(\d+(?:\.\d+)?)\s*(l|liter|ltr)\b", joined)
    if m:
        raw = m.group(1)
        if raw.endswith(".0"):
            raw = raw[:-2]
        return f"{raw}l"

    # ml
    m = re.search(r"(\d+)\s*(ml|mililiter)\b", joined)
    if m:
        raw = m.group(1)
        return f"{raw}ml"

    # galon
    if re.search(r"\b(galon|19l|19|isi ulang)\b", joined):
        return "19l"

    # 1.5L
    if re.search(r"\b(1,5ml|1.5ml|1/5ml|1,5|1.5|1/5)\b", joined):
        return "1.5ml"

    # 600ml
    if re.search(r"\b(600ml|600)\b", joined):
        return "600ml"

    # 500ml
    if re.search(r"\b(500ml|500)\b", joined):
        return "500ml"

    # 400ml
    if re.search(r"\b(400ml|400)\b", joined):
        return "400ml"

    # 330ml
    if re.search(r"\b(330ml|330)\b", joined):
        return "330ml"

    # 240ml
    if re.search(r"\b(240ml|240)\b", joined):
        return "240ml"

    return None


def guess_variant_from_fragment(tokens):
    """Deteksi varian dari fragment (tidak eksplisit) — CLI logic."""
    s = " ".join(tokens)

    # galon
    if re.search(r"\b(gal|galon|19)\b", s):
        return "19l"

    # botol 1.5
    if re.search(r"\b(bot|botol|1\.5|1,5|1/5)\b", s):
        return "1.5ml"

    # botol 600
    if re.search(r"\b(bot|botol|600)\b", s):
        return "600ml"

    # botol 500
    if re.search(r"\b(bot|botol|500)\b", s):
        return "500ml"

    # botol 400
    if re.search(r"\b(bot|botol|400)\b", s):
        return "400ml"

    # botol 330
    if re.search(r"\b(bot|botol|330)\b", s):
        return "330ml"

    # cup 240
    if re.search(r"\b(gelas|cup|240)\b", s):
        return "240ml"

    return None


# ============================================================
# SIZE GROUP DETECTION
# ============================================================

def detect_size_group(tokens):
    """Mendeteksi group ukuran (besar/small/galon) berdasarkan kata."""
    for group, cfg in SIZE_GROUP.items():
        if any(w in tokens for w in cfg["words"]):
            return group
    return None


def find_products_by_size_group(size_group, catalog):
    """Mengambil list produk yang cocok dengan size-group tertentu."""
    patterns = SIZE_GROUP[size_group]["patterns"]
    results = []

    for key, meta in catalog.items():
        varian = meta.get("varian", "").lower()
        if any(p in varian for p in patterns):
            results.append(key)

    return results


def find_all_keys_for_varian(category, varian, catalog):
    """
    Sama seperti CLI:
    Mengambil semua produk dengan varian tertentu,
    fallback ke kategori apa pun jika kategori tidak cocok.
    """
    results = []

    for key, meta in catalog.items():
        if meta.get("varian") == varian and (
            not category or meta.get("kategori") == category
        ):
            results.append(key)

    if not results and category:
        # fallback abaikan kategori
        for key, meta in catalog.items():
            if meta.get("varian") == varian:
                results.append(key)

    return results
# ============================================================
# D. CORE NLP PARSER
# ============================================================

def split_into_chunks(text):
    """
    Memecah kalimat menjadi beberapa segmen berdasarkan 'dan', koma,
    atau penghubung lain, sama seperti CLI.
    """
    text = normalize(text)
    text = text.replace(",", " dan ")
    text = text.replace(" & ", " dan ")
    raw_parts = text.split(" dan ")

    chunks = []
    for part in raw_parts:
        p = part.strip()
        if p:
            chunks.append(p)

    return chunks


def tokenize(chunk):
    """Tokenizer sederhana seperti CLI."""
    chunk = normalize(chunk)
    tokens = chunk.split()
    return [t for t in tokens if t not in STOPWORDS]


def resolve_final_product(chunk_info, catalog):
    """
    Sama seperti CLI:
    Menggabungkan semua kandidat yang ditemukan:
    - direct alias
    - strong alias
    - weak alias
    - brand candidates
    - explicit varian
    - size-group
    Lalu menentukan 1 produk final atau ambiguity.
    """

    # 1. Direct alias override
    if chunk_info["direct_keys"]:
        if len(chunk_info["direct_keys"]) == 1:
            k = chunk_info["direct_keys"][0]
            return k, None
        else:
            return None, list(chunk_info["direct_keys"])

    # Kumpulkan kandidat
    candidates = set()

    # 2. strong alias
    for k in chunk_info["strong_keys"]:
        candidates.add(k)

    # 3. brand
    for k in chunk_info["brand_keys"]:
        candidates.add(k)

    # 4. weak alias
    for k in chunk_info["weak_keys"]:
        candidates.add(k)

    # 5. varian explicit
    if chunk_info["explicit_varian"]:
        var_keys = find_all_keys_for_varian(
            chunk_info["category"],
            chunk_info["explicit_varian"],
            catalog
        )
        for k in var_keys:
            candidates.add(k)

    # 6. fragment varian (tidak explicit)
    if chunk_info["fragment_varian"]:
        var_keys2 = find_all_keys_for_varian(
            chunk_info["category"],
            chunk_info["fragment_varian"],
            catalog
        )
        for k in var_keys2:
            candidates.add(k)

    # 7. size group contains
    if chunk_info["size_group"]:
        sg_keys = find_products_by_size_group(chunk_info["size_group"], catalog)
        for k in sg_keys:
            candidates.add(k)

    # Jika tidak ada kandidat sama sekali
    if not candidates:
        return None, None

    # Jika hanya satu kandidat → fix
    if len(candidates) == 1:
        return list(candidates)[0], None

    # Jika lebih dari satu & explicit varian cocok → reduksi
    if chunk_info["explicit_varian"]:
        filtered = []
        for k in candidates:
            varian = catalog[k].get("varian")
            if varian == chunk_info["explicit_varian"]:
                filtered.append(k)

        if len(filtered) == 1:
            return filtered[0], None
        elif len(filtered) > 1:
            return None, filtered

    # Jika masih lebih dari satu
    return None, list(candidates)


def parse_single_chunk(chunk, catalog):
    """
    Menganalisis 1 chunk (misal: 'aqua 600 dua'):
    Menghasilkan:
      {
        "raw": "...",
        "tokens": [...],
        "qty": n,
        "category": "...",
        "explicit_varian": "...",
        "fragment_varian": "...",
        "size_group": "...",
        "strong_keys": [...],
        "weak_keys": [...],
        "brand_keys": [...],
        "direct_keys": [...],
        "final_key": "...",
        "ambiguity": [...]
      }
    """

    info = {
        "raw": chunk,
        "tokens": [],
        "qty": 1,
        "category": None,
        "explicit_varian": None,
        "fragment_varian": None,
        "size_group": None,
        "strong_keys": [],
        "weak_keys": [],
        "brand_keys": [],
        "direct_keys": [],
        "final_key": None,
        "ambiguity": None
    }

    # Tokenization
    tokens = tokenize(chunk)
    info["tokens"] = tokens

    # Category guess
    info["category"] = guess_category(tokens)

    # QTY detection
    info["qty"] = expand_quantity(tokens)

    # Explicit varian (angka + unit)
    info["explicit_varian"] = detect_variant(tokens)

    # Fragment varian (misal 'botol 600', 'gelas 240')
    info["fragment_varian"] = guess_variant_from_fragment(tokens)

    # Size-group detection
    info["size_group"] = detect_size_group(tokens)

    # Direct alias match
    info["direct_keys"] = find_direct_alias_hits(chunk)

    # Alias strong / weak
    s, w = find_alias_candidates_from_text(chunk)
    info["strong_keys"] = s
    info["weak_keys"] = w

    # Brand keys
    info["brand_keys"] = find_brand_candidates(tokens, catalog)

    # Final resolution
    fk, amb = resolve_final_product(info, catalog)
    info["final_key"] = fk
    info["ambiguity"] = amb

    return info


def parse_orders_verbose(text, catalog):
    """
    Fungsi PARSER utama.
    Dulu versi CLI menghasilkan print dan prompt;
    di versi Streamlit (OPSI B), ia hanya:
      → mengembalikan list hasil setiap chunk
    """

    text = normalize(text)
    if not text:
        return []

    chunks = split_into_chunks(text)

    results = []
    for ch in chunks:
        parsed = parse_single_chunk(ch, catalog)
        results.append(parsed)

    return results
# ============================================================
# E. UTILITY UNTUK UI STREAMLIT (OPSI B)
# ============================================================

def is_ambiguous(parsed_chunk):
    """
    Mengembalikan True jika chunk memiliki ambiguity lebih dari 1 produk.
    """
    if parsed_chunk is None:
        return False
    amb = parsed_chunk.get("ambiguity")
    return amb is not None and len(amb) > 1


def needs_clarification(parsed_chunk):
    """
    Mengecek apakah UI perlu meminta user memilih:
    - brand
    - varian
    - produk final
    """
    if parsed_chunk is None:
        return False

    # Kasus ambiguity produk
    if is_ambiguous(parsed_chunk):
        return True

    # Kasus tidak ada final key, tetapi ada beberapa kandidat alias
    if parsed_chunk.get("final_key") is None:
        # Jika memang benar-benar tidak ditemukan kandidat — kategori tidak jelas
        # UI bisa memunculkan “produk tidak ditemukan”
        if not parsed_chunk.get("strong_keys") and \
           not parsed_chunk.get("weak_keys") and \
           not parsed_chunk.get("brand_keys") and \
           not parsed_chunk.get("explicit_varian") and \
           not parsed_chunk.get("fragment_varian"):
            return False
        return True

    return False


def get_ambiguity_options(parsed_chunk, catalog):
    """
    Mengambil list produk (nama variant lengkap) yang menjadi ambiguity.
    Berguna untuk UI: user klik salah satu.
    """
    amb = parsed_chunk.get("ambiguity")
    if not amb:
        return []

    out = []
    for key in amb:
        meta = catalog[key]
        label = f"{meta.get('nama')} ({meta.get('varian')})"
        out.append({"key": key, "label": label})

    return out


def format_final_item(parsed_chunk, catalog):
    """
    Mengubah parsed result menjadi format item yang siap masuk keranjang:
    {
      "product_key": "...",
      "nama_item": "...",
      "harga": ...,
      "qty": ...
    }
    """
    key = parsed_chunk.get("final_key")
    if not key:
        return None

    meta = catalog[key]
    return {
        "product_key": key,
        "nama_item": meta.get("nama"),
        "harga": meta.get("harga"),
        "qty": parsed_chunk.get("qty", 1)
    }


def explain_chunk(parsed_chunk, catalog):
    """
    Menghasilkan penjelasan dalam bentuk dictionary, sehingga UI dapat
    menampilkan:
    - produk ditemukan
    - jumlah
    - ambiguity
    - tidak ditemukan
    Tanpa print().
    """
    if parsed_chunk["final_key"]:
        key = parsed_chunk["final_key"]
        meta = catalog[key]
        return {
            "status": "ok",
            "message": f"Produk terdeteksi: {meta['nama']} ({meta['varian']}), jumlah {parsed_chunk['qty']}.",
            "product_key": key
        }

    if parsed_chunk["ambiguity"]:
        opts = get_ambiguity_options(parsed_chunk, catalog)
        return {
            "status": "ambiguity",
            "message": "Beberapa produk cocok. Pilih salah satu:",
            "options": opts
        }

    # Jika sama sekali tidak menemukan product
    return {
        "status": "not_found",
        "message": f"Tidak dapat mengenali produk dari input: '{parsed_chunk['raw']}'."
    }


def summarize_parsed_results(all_chunks, catalog):
    """
    Mengambil list hasil parsed_orders_verbose() dan menghasilkan:
    - apakah aman dimasukkan ke keranjang?
    - daftar hasil final / daftar error.

    return format:
    {
        "ok": bool,
        "items": [...],      # item valid
        "errors": [...],     # chunk yang gagal
        "needs_choice": [...] # chunk yang ambigu
    }
    """
    items = []
    errors = []
    needs_choice = []

    for ch in all_chunks:
        if ch["final_key"]:
            items.append(format_final_item(ch, catalog))
        elif ch["ambiguity"]:
            needs_choice.append(explain_chunk(ch, catalog))
        else:
            errors.append(explain_chunk(ch, catalog))

    ok = len(errors) == 0 and len(needs_choice) == 0

    return {
        "ok": ok,
        "items": items,
        "errors": errors,
        "needs_choice": needs_choice
    }


def apply_user_choice(parsed_chunk, chosen_key):
    """
    Dipanggil oleh UI ketika user memilih salah satu ambiguity:
    parsed_chunk['final_key'] = chosen_key
    parsed_chunk['ambiguity'] = None
    """
    parsed_chunk["final_key"] = chosen_key
    parsed_chunk["ambiguity"] = None
    return parsed_chunk
