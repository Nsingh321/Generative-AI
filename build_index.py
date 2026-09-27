"""
One-time index builder for the AdventureWorks schema vector store.

Pipeline:
  1. Load exported CSVs (schema + relationships)
  2. Build a compact schema summary JSON (LLM fallback description if missing)
  3. Write one text document per table into schema_documents/
  4. Embed the documents with BAAI/bge-large-en-v1.5 and store them in ChromaDB

Run this ONLY when the schema changes:  python build_index.py
It is intentionally guarded by __main__ so importing project modules never
triggers re-ingestion.
"""

import os
import json
import pandas as pd
import ollama
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from schema import (
    EMBEDDING_MODEL,
    VECTOR_DB_PATH,
    COLLECTION_NAME,
    SCHEMA_SUMMARY_PATH,
)

DOCS_DIR = "schema_documents"


def build_schema_summary():
    """Build schema_summary_new.json from the exported CSVs."""
    df_schema = pd.read_csv(
        'adventure_works_full.csv',
        names=['schema_name', 'table_name', 'table_description',
               'column_name', 'data_type', 'max_length', 'column_description'],
    )
    df_rel = pd.read_csv(
        'adventure_works_relationships.csv',
        names=['table_name', 'column_name', 'referenced_table_name', 'referenced_column_name'],
    )

    # Pre-process relationships into a lookup dictionary (both directions)
    rel_dict = {}
    for _, row in df_rel.iterrows():
        tbl, ref_tbl = row['table_name'], row['referenced_table_name']
        col, ref_col = row['column_name'], row['referenced_column_name']
        rel_dict.setdefault(tbl, [])
        rel_dict.setdefault(ref_tbl, [])
        rel_dict[tbl].append(f"{col} -> {ref_tbl}.{ref_col}")
        rel_dict[ref_tbl].append(f"Referenced by {tbl}.{col} via {ref_col}")

    schema_summary = {}
    for (schema, table_name), group in df_schema.groupby(['schema_name', 'table_name']):
        full_table_name = f"{schema}.{table_name}"

        raw_desc = group['table_description'].dropna().unique()
        table_desc = str(raw_desc[0]) if len(raw_desc) > 0 else "None"

        columns_list = [
            f"{row['column_name']} ({row['data_type']}) - ({row['column_description']})"
            for _, row in group.iterrows()
        ]
        columns_str = ", ".join(columns_list)

        if table_desc in ["None", "nan", ""]:
            prompt = (f"Based on the table name '{full_table_name}' and columns "
                      f"[{columns_str}], write a one-sentence summary of what this table tracks.")
            response = ollama.chat(model='granite4.1:8b', messages=[{"role": "user", "content": prompt}])
            table_desc = response['message']['content'].strip()

        schema_summary[full_table_name] = {
            "description": table_desc,
            "columns": columns_list,
            "relationships": rel_dict.get(full_table_name, ["No explicit foreign key relationships"]),
        }

    os.makedirs(os.path.dirname(SCHEMA_SUMMARY_PATH), exist_ok=True)
    with open(SCHEMA_SUMMARY_PATH, 'w') as f:
        json.dump(schema_summary, f, indent=4)
    print(f"Wrote schema summary for {len(schema_summary)} tables -> {SCHEMA_SUMMARY_PATH}")
    return schema_summary


def write_schema_documents(full_schema_summary):
    """Write one .txt document per table for embedding."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    for key, val in full_schema_summary.items():
        columns_str = ", ".join(val['columns'])
        relationships_str = "\n".join(val['relationships'])
        schema_catalog = (
            f'Table: {key}\n'
            f'Description: {val["description"]}\n'
            f'Columns: {columns_str}\n'
            f'Relationships:\n{relationships_str}\n'
        )
        safe_filename = f"{key.replace('.', '_')}.txt"
        with open(os.path.join(DOCS_DIR, safe_filename), 'w', encoding='utf-8') as f:
            f.write(schema_catalog)
    print(f"Wrote {len(full_schema_summary)} schema documents -> {DOCS_DIR}/")


def ingest_into_chroma():
    """Embed the schema documents and store them in ChromaDB."""
    embedding_function = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )

    documents, metadatas, ids = [], [], []
    print('Reading schema files...')
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".txt"):
            table_name = filename.replace(".txt", "").replace("_", ".")
            with open(os.path.join(DOCS_DIR, filename), 'r', encoding="utf-8") as f:
                documents.append(f.read())
            metadatas.append({"table_name": table_name, "source": filename})
            ids.append(table_name)

    if documents:
        print(f'Embedding and adding {len(documents)} tables to ChromaDB...')
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print("Ingestion complete! Vector DB is ready.")
    else:
        print("No documents found to process.")


if __name__ == "__main__":
    summary = build_schema_summary()
    write_schema_documents(summary)
    ingest_into_chroma()
