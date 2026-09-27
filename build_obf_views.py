"""
Step 2 of the obfuscation harness: generate the obfuscated VIEW layer.

For every real table it emits:
    CREATE OR ALTER VIEW obf.T07 AS
      SELECT [BusinessEntityID] AS col_0101, [FirstName] AS col_0102, ...
      FROM [Person].[Person];

so that obfuscated SQL (e.g. SELECT col_0102 FROM obf.T07) runs directly against the real
data with NO SQL-text translation. Reads obf/rename_map.json (built by build_obf_map.py).

Writes obf/obf_views.sql. Pass --execute to also run it against the DB.
Usage:
    python build_obf_views.py            # just write the .sql
    python build_obf_views.py --execute  # write AND create the views in the DB
"""
import sys
import json
import pyodbc
from config import conn_str

MAP_PATH = "obf/rename_map.json"
SQL_OUT = "obf/obf_views.sql"


def columns_for(table, columns_map):
    """Return [(real_col, obf_col), ...] for one real 'Schema.Table', in map order."""
    prefix = table + "."
    out = []
    for full, obf in columns_map.items():
        if full.startswith(prefix):
            real_col = full[len(prefix):]
            out.append((real_col, obf))
    return out


def build_view_sql(mp):
    tables, columns_map = mp["tables"], mp["columns"]
    stmts = [
        "IF SCHEMA_ID('obf') IS NULL EXEC('CREATE SCHEMA obf');",
        "GO",
    ]
    for real, obf in tables.items():
        schema, table = real.split(".", 1)
        obf_table = obf.split(".", 1)[1]           # 'obf.T07' -> 'T07'
        cols = columns_for(real, columns_map)
        if not cols:
            print(f"  WARNING: no columns mapped for {real}; skipping")
            continue
        select_list = ",\n    ".join(f"[{rc}] AS {oc}" for rc, oc in cols)
        stmts.append(
            f"CREATE OR ALTER VIEW obf.[{obf_table}] AS\n"
            f"  SELECT\n    {select_list}\n"
            f"  FROM [{schema}].[{table}];"
        )
        stmts.append("GO")
    return "\n".join(stmts) + "\n"


def execute_sql(sql):
    """Run the script batch-by-batch (split on GO, which is a client directive not T-SQL)."""
    conn = pyodbc.connect(conn_str, autocommit=True)
    cur = conn.cursor()
    batches = [b.strip() for b in sql.split("\nGO") if b.strip()]
    for b in batches:
        cur.execute(b)
    conn.close()
    print(f"Executed {len(batches)} batches against the DB.")


if __name__ == "__main__":
    mp = json.load(open(MAP_PATH, encoding="utf-8"))
    sql = build_view_sql(mp)
    with open(SQL_OUT, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"Wrote {SQL_OUT}: {len(mp['tables'])} views.")
    if "--execute" in sys.argv:
        execute_sql(sql)
