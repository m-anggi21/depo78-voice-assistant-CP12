import pandas as pd
import os

DATA_PATH = "data/catalog_depo78_clean.csv"

def load_catalog():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("Catalog CSV tidak ditemukan.")

    df = pd.read_csv(DATA_PATH)

    # Convert ke dictionary seperti CLI
    catalog = {}
    for _, row in df.iterrows():
        key = f"{row['kategori']}:{row['varian']}"
        if key in catalog:
            key += "_dup"

        alias_list = []
        if isinstance(row["aliases"], str):
            alias_list = [a.strip().lower() for a in row["aliases"].split("|")]

        catalog[key] = {
            "nama": row["nama"],
            "harga": row["harga"],
            "kategori": row["kategori"],
            "varian": row["varian"],
            "brand": str(row["brand"]).lower() if "brand" in row else "",
            "aliases": alias_list,
            "isi": str(row["isi"]).lower() if "isi" in row else ""
        }
    return catalog
