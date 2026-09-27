"""
Step 3 of the obfuscation harness: rebuild the 4 retrieval assets with OBF names but
REAL descriptions, so the pipeline can run in SCHEMA_MODE=obf.

Transforms (via obf/rename_map.json):
  1. relationships CSV      -> obf/relationships.csv        (for build_fk_graph)
  2. schema_summary JSON    -> obf/schema_summary.json      (for get_compact_schema)
  3. DDL catalog JSON       -> obf/ddl_catalog.json         (for get_table_ddl)
  4. schema documents       -> obf/schema_documents/*.txt   (embedded into Chroma)
     + new Chroma collection 'obf_schema' at obf/vector_db  (for retrieval)

Descriptions and data types are KEPT REAL; only structural NAMES are obfuscated.
No LLM, no API. Deterministic and offline-testable.  Run:  python build_obf_assets.py

Known limitation: a few real descriptions mention real column names (e.g. NameStyle's
desc references "FirstName/LastName"). We keep descriptions verbatim; a stricter variant
would scrub those. The main memorization crutch (the names the model queries) is broken.
"""
import os
import csv
import json
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

MAP_PATH = "obf/rename_map.json"
SRC_SUMMARY = "schema_new/schema_summary_new.json"
SRC_DDL = "schema_new/adventureworks_database_ddl.json"
SRC_REL = "adventure_works_relationships.csv"

OBF_DIR = "obf"
OBF_SUMMARY = f"{OBF_DIR}/schema_summary.json"
OBF_DDL = f"{OBF_DIR}/ddl_catalog.json"
OBF_REL = f"{OBF_DIR}/relationships.csv"
OBF_DOCS = f"{OBF_DIR}/schema_documents"
OBF_VDB = f"{OBF_DIR}/vector_db"
OBF_COLLECTION = "obf_schema"
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"


def load_map():
    mp = json.load(open(MAP_PATH, encoding="utf-8"))
    tables, columns = mp["tables"], mp["columns"]

    def T(real_table):
        return tables[real_table]

    def C(real_table, real_col):
        return columns[f"{real_table}.{real_col}"]

    return tables, columns, T, C


def transform_relationships(T, C):
    """obf/relationships.csv + an obf rel_dict (both directions) for the summary/docs."""
    rel_dict = {}
    rows_out = []
    with open(SRC_REL, encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if len(row) < 4:
                continue
            child, ccol, parent, pcol = (x.strip() for x in row[:4])
            try:
                oc, occ, op, opc = T(child), C(child, ccol), T(parent), C(parent, pcol)
            except KeyError as e:
                print(f"  WARNING: relationship references unmapped {e}; skipping row {row}")
                continue
            rows_out.append([oc, occ, op, opc])
            rel_dict.setdefault(oc, []).append(f"{occ} -> {op}.{opc}")
            rel_dict.setdefault(op, []).append(f"Referenced by {oc}.{occ} via {opc}")

    with open(OBF_REL, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows_out)
    print(f"  wrote {OBF_REL} ({len(rows_out)} FK edges)")
    return rel_dict


def transform_summary(T, C, rel_dict):
    src = json.load(open(SRC_SUMMARY, encoding="utf-8"))
    out = {}
    for real_table, info in src.items():
        obf_table = T(real_table)
        obf_cols = []
        for col in info["columns"]:
            name, rest = col.split(" (", 1)              # split on FIRST ' (' (desc may contain parens)
            obf_cols.append(f"{C(real_table, name.strip())} ({rest}")
        out[obf_table] = {
            "description": info["description"],           # KEPT REAL
            "columns": obf_cols,
            "relationships": rel_dict.get(obf_table, ["No explicit foreign key relationships"]),
        }
    json.dump(out, open(OBF_SUMMARY, "w", encoding="utf-8"), indent=4)
    print(f"  wrote {OBF_SUMMARY} ({len(out)} tables)")
    return out


def transform_ddl(tables, columns, T):
    src = json.load(open(SRC_DDL, encoding="utf-8"))
    out = {}
    for real_table, ddl in src.items():
        schema, table = real_table.split(".", 1)
        obf_tbl = T(real_table).split(".", 1)[1]          # 'obf.T23' -> 'T23'
        new = ddl.replace(f"[{schema}].[{table}]", f"[obf].[{obf_tbl}]")
        for full_col, obf_col in columns.items():
            if full_col.startswith(real_table + "."):
                real_col = full_col[len(real_table) + 1:]
                new = new.replace(f"[{real_col}]", f"[{obf_col}]")   # bracketed = exact, safe
        out[T(real_table)] = new
    json.dump(out, open(OBF_DDL, "w", encoding="utf-8"), indent=4)
    print(f"  wrote {OBF_DDL} ({len(out)} tables)")


def build_docs_and_index(obf_summary):
    os.makedirs(OBF_DOCS, exist_ok=True)
    docs, metadatas, ids = [], [], []
    for obf_table, info in obf_summary.items():
        cols = ", ".join(info["columns"])
        rels = "\n".join(info["relationships"])
        text = (f"Table: {obf_table}\nDescription: {info['description']}\n"
                f"Columns: {cols}\nRelationships:\n{rels}\n")
        open(os.path.join(OBF_DOCS, f"{obf_table.replace('.', '_')}.txt"), "w", encoding="utf-8").write(text)
        docs.append(text)
        metadatas.append({"table_name": obf_table})
        ids.append(obf_table)

    ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=OBF_VDB)
    # drop any prior obf collection so re-runs are clean
    try:
        client.delete_collection(OBF_COLLECTION)
    except Exception:
        pass
    coll = client.get_or_create_collection(OBF_COLLECTION, embedding_function=ef,
                                           metadata={"hnsw:space": "cosine"})
    coll.add(documents=docs, metadatas=metadatas, ids=ids)
    print(f"  embedded {len(docs)} docs into Chroma collection '{OBF_COLLECTION}' at {OBF_VDB}")


if __name__ == "__main__":
    os.makedirs(OBF_DIR, exist_ok=True)
    tables, columns, T, C = load_map()
    print("Building obfuscated assets...")
    rel_dict = transform_relationships(T, C)
    obf_summary = transform_summary(T, C, rel_dict)
    transform_ddl(tables, columns, T)
    build_docs_and_index(obf_summary)
    print("Done. Obfuscated assets are ready under obf/.")
