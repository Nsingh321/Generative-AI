"""
Step 1 of the obfuscation harness: build a COMPLETE, clean rename map.

- Preserves your hand-assigned table -> obf.TNN mappings from obf/rename_map.json
  (extracted tolerantly by regex, so the current malformed JSON / junk rows / trailing
  comma don't matter).
- Auto-assigns obf.TNN to any base table you didn't map.
- Introspects every column via INFORMATION_SCHEMA and assigns a globally-unique token
  col_0001, col_0002, ... (global uniqueness makes de-obfuscation unambiguous).
- Writes a clean, valid obf/rename_map.json:  {"tables": {...}, "columns": {...}}
- Validates the map is bijective and complete before writing.

Read-only against the DB (metadata only). Run:  python build_obf_map.py
"""
import re
import json
import pyodbc
from config import conn_str

MAP_PATH = "obf/rename_map.json"


def load_existing_table_map(path):
    """Regex-extract 'Schema.Table' -> 'obf.TNN' pairs, ignoring empty values / dupes / bad JSON."""
    existing = {}
    try:
        text = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        return existing
    for real, obf in re.findall(r'"([^"]+)"\s*:\s*"(obf\.T\d+)"', text):
        existing.setdefault(real, obf)          # keep first non-empty assignment
    return existing


def list_base_tables(cursor):
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA <> 'obf'
        ORDER BY TABLE_SCHEMA, TABLE_NAME;
    """)
    return [f"{r.TABLE_SCHEMA}.{r.TABLE_NAME}" for r in cursor.fetchall()]


def list_columns(cursor, schema, table):
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION;
    """, schema, table)
    return [r.COLUMN_NAME for r in cursor.fetchall()]


def build():
    existing = load_existing_table_map(MAP_PATH)
    print(f"Preserved {len(existing)} hand-assigned table mappings from {MAP_PATH}")

    conn = pyodbc.connect(conn_str)
    cur = conn.cursor()
    all_tables = list_base_tables(cur)

    # --- tables: keep existing obf names, assign fresh TNN to any that are missing ---
    used = set(existing.values())
    next_n = max([int(v.split("T")[1]) for v in used], default=0) + 1
    tables = {}
    for real in all_tables:
        if real in existing:
            tables[real] = existing[real]
        else:
            obf = f"obf.T{next_n:02d}"
            while obf in used:
                next_n += 1
                obf = f"obf.T{next_n:02d}"
            tables[real] = obf
            used.add(obf)
            next_n += 1
            print(f"  auto-assigned {real} -> {obf}")

    # --- columns: globally-unique token per (table.column) ---
    columns = {}
    ctr = 1
    for real in all_tables:
        schema, table = real.split(".", 1)
        for col in list_columns(cur, schema, table):
            columns[f"{real}.{col}"] = f"col_{ctr:04d}"
            ctr += 1
    conn.close()

    # --- validate bijective + complete ---
    assert len(set(tables.values())) == len(tables), "duplicate obf table name!"
    assert len(set(columns.values())) == len(columns), "duplicate obf column token!"
    assert set(tables) == set(all_tables), "table map does not cover all base tables!"

    out = {"tables": tables, "columns": columns}
    with open(MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {MAP_PATH}: {len(tables)} tables, {len(columns)} columns (bijective, complete).")


if __name__ == "__main__":
    build()
