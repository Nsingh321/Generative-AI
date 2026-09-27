import csv
import json
import chromadb
import csv
from functools import lru_cache
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# NOTE: This module contains ONLY the reusable retrieval / schema-context helpers.
# The one-time vector-store INGESTION (CSV -> schema docs -> ChromaDB) lives in
# build_index.py (and generate_schema_docs.ipynb). Nothing here runs at import time.

import os
MODE = os.getenv("SCHEMA_MODE", "real")
if MODE == "obf":
    SCHEMA_SUMMARY_PATH = "obf/schema_summary.json"
    DDL_CATALOG_PATH    = "obf/ddl_catalog.json"
    VECTOR_DB_PATH      = "obf/vector_db"
    COLLECTION_NAME     = "obf_schema"
    RELATIONSHIPS_CSV   = "obf/relationships.csv"   # <-- also switch the one hardcoded in build_fk_graph
else:
    SCHEMA_SUMMARY_PATH = "schema_new/schema_summary_new.json"
    DDL_CATALOG_PATH    = "schema_new/adventureworks_database_ddl.json"
    VECTOR_DB_PATH      = "adventure_works_vector_db"
    COLLECTION_NAME     = "adventure_works_schema"
    RELATIONSHIPS_CSV   = "adventure_works_relationships.csv"

EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
# VECTOR_DB_PATH = "adventure_works_vector_db"
# COLLECTION_NAME = "adventure_works_schema"
# SCHEMA_SUMMARY_PATH = "schema_new/schema_summary_new.json"
# DDL_CATALOG_PATH = "schema_new/adventureworks_database_ddl.json"


def get_join_paths(tables):
    '''Return FK joins hints among the given tables, eg. "obf.T12.col_0026 = obf.T23.col_0116". '''

    tset = set(tables)
    lines = []
    with open(RELATIONSHIPS_CSV, encoding='utf-8-sig') as f:
        for child, ccol, parent , pcol in csv.reader(f):
            if child in tset and parent in tset:
                lines.append(f"{child}.{ccol} = {parent}.{pcol}")

    return "=== JOIN KEYS (how these tables relate) ===\n" + "\n".join(lines) + "\n" if lines else ""


def retrieve_relevant_tables(user_question, top_n=4):
    '''Retrieve the top-n relevant tables according to user's request from the vector database.'''

    # IMPORTANT: query with the SAME embedding model used at ingestion, otherwise
    # the query vector and document vectors live in different spaces.
    embedding_function = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_function)

    results = collection.query(query_texts=[user_question], n_results=top_n)

    # Extract the matched text content blocks and table names
    matched_schemas = results['documents'][0]
    matched_tables = [meta['table_name'] for meta in results['metadatas'][0]]

    # combine the matched schemas into a tightly pruned string context block
    pruned_schema_context = "\n\n".join(matched_schemas)

    return pruned_schema_context, matched_tables


def validate_retrieved_tables(retrieved_tables):
    '''Check if the retrieved tables are present in the database.
    Returns a dict: table_name -> True (present) / False (not present).'''
    is_valid = {}
    try:
        with open(SCHEMA_SUMMARY_PATH, 'r') as f:
            compact_schema_dict = json.load(f)
    except Exception as e: 
        print(f'No schema summary available.Error: {e} ')
        return {}

    for table in retrieved_tables:
        is_valid[table] = table in compact_schema_dict

    return is_valid


def get_compact_schema(list_of_tables):
    '''Take a list of tables and return the associated compact summary (description, column names) of each table.'''
    result = ''

    try:
        with open(SCHEMA_SUMMARY_PATH, 'r') as f:
            full_compact_schema_dict = json.load(f)
    except Exception as e:
        return f'No schema summary available. Error: {e}'

    for table in list_of_tables:
        if table not in full_compact_schema_dict:
            result += f"Table: {table} (Not found in schema catalog)\n\n"
            continue

        # 1. Collect columns specifically for THIS table
        col_list = []
        table_columns = full_compact_schema_dict[table]['columns']
        for col in table_columns:
            # Splits at ' - ' to remove the description suffix, then strip spaces
            clean_col = col.split('-')[0].strip()
            col_list.append(clean_col)

        # 2. Join the column list with commas
        final_col_list = ', '.join(col_list)

        # 3. Fetch the table description
        table_description = full_compact_schema_dict[table]['description']

        # 4. Construct a structured layout for this table
        result += f"Table: {table}\n"
        result += f"Description: {table_description}\n"
        result += f"Columns: {final_col_list}\n"
        result += "-" * 40 + "\n"  # divider between tables

    return result


def get_table_ddl(list_of_tables):
    '''Takes a list of tables and returns their raw SQL DDL CREATE TABLE statements.'''
    ddl_context = ""

    try:
        with open(DDL_CATALOG_PATH, 'r') as f:
            ddl_catalog = json.load(f)
    except FileNotFoundError:
        return "DDL Catalog asset not found."

    for table in list_of_tables:
        if table in ddl_catalog:
            print(f' -- Getting DDL for table: {table} -- ')
            ddl_context += f"-- DDL for {table}\n"
            ddl_context += ddl_catalog[table] + "\n\n"

    return ddl_context

def load_ddl_catalog():
    '''Load the entire DDL catalog -> adventure works'''
    try:
        with open(DDL_CATALOG_PATH,'r') as f:
            ddl_dict = json.load(f)
    except Exception as e:
        print(f'No DDL available.Error: {e} ')
        return {}
    
    return ddl_dict
    


# Tool (function) schema kept for optional function-calling flows.
table_function = {
    "name": "get_table_ddl",
    "description": "Get the schema for a specific table name. Use this before writing SQL.",
    "parameters": {
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "The name of the table",
            },
        },
        "required": ["table_name"],
        "additionalProperties": False,
    },
}


def get_tools():
    return [{"type": "function", "function": table_function}]

def find_tables_for_columns(column_names, candidate_tables):
    '''For each column, return which of candidate_tables actually contain it.
    Case-insensitive. Uses the column lists already in schema_summary_new.json.'''

    try:
        with open(SCHEMA_SUMMARY_PATH) as f:
            summary = json.load(f)

    except Exception:
        return {c: [] for c in column_names}
    
    owners = {} # (key = col, value = list of tables that has 'col'). A column can be present in multiple candidate tables
    for col in column_names:
        col_lc = col.lower()
        hits = []

        for t in candidate_tables:
            if t not in summary:
                continue

            # get all the actual columns from candidate table -> t
            actual_table_cols = [c.split('(')[0].strip().lower() for c in summary[t]["columns"]]
            
            # check if the col_lc is in actual_table_cols 
            if col_lc in actual_table_cols:
                hits.append(t)

        owners[col] = hits 
    return owners

            


@lru_cache(maxsize=1)
def build_fk_graph():
    '''Undirected FK adjacency map:
      table -> set of directly-joinable tables.
      Read once from the relationships CSV and cached for the process lifetime.'''
    
    graph = {}
    # RELATIONSHIPS_CSV = "adventure_works_relationships.csv"
    with open(RELATIONSHIPS_CSV, 'r', encoding='utf-8-sig') as f:
        for row in csv.reader(f):
            # print(row)
            if len(row) < 3: # because the csv has child Table, child col, parent table, parent col
                continue
            child, parent = row[0].strip(), row[2].strip()
            if not child or not parent or child == parent:
                # skip blanks + self loops
                continue
            graph.setdefault(child, set()).add(parent) # undirected both ways
            graph.setdefault(parent,set()).add(child)
            # print(graph)
            # print('-'*30)
    
    return graph
# build_fk_graph()





def rank_tables_by_similarity(question, top_seeds=6):
    '''Query the vector store ONCE for all the tables, ranked by similarity
    to the question.
    Returns (seeds, sim_scores):
    seeds -> top 'top_seeds' table names (the semantic anchors)
    sim_scores -> {table_name:similarity} for EVERY table (similarity = 1 - cosine_distance)'''

    embedding_function = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = client.get_collection(name = COLLECTION_NAME, embedding_function=embedding_function)

    total = collection.count() # no. of tables in the store
    results = collection.query(query_texts=[question], n_results=total)

    tables = [m['table_name'] for m in results['metadatas'][0]]
    distances = results['distances'][0]

    # chroma cosine distance in [0-2]; similarity = 1 - distance. Results already best-first.
    sim_scores = {t: 1.0 - d for t, d in zip(tables, distances)}
    seeds = tables[:top_seeds]
    return seeds, sim_scores

def expand_with_fk_neighbors(seeds, graph, sim_scores,hops = 1, max_tables = 10):
    '''Grow semantic seed tables with their FK-graph neighbors
    Candidates are ranked by "bridge score" = how many already-selected tables
    a neighbor directly connects to. A table joining two selected tables is 
    almost certainly a needed junction table, so we keep it even if it is semantically dissimilar
    to the question. Seeds are never evicted; total is capped at max_tables.'''

    if graph is None:
        graph = build_fk_graph()
    
    seeds = list(dict.fromkeys(seeds)) # dedupe, keep order
    # print('Seeds inside expand_with_fk_neighbors: ',seeds)

    selected = list(seeds) # seeds always survive
    # print('SELECTED: ', selected)

    selected_set = set(selected)
    # print('SELECTED SET: ', selected_set)

    frontier = set(seeds) 
    # print('frontier: ', frontier)

    hops_left = hops
    for _ in range(hops):
        # score each candidate by how many tables in the current frontier touch it
        # (scanning the WHOLE frontier first, then ranking once per hop)
        scores = {}
        for table in frontier:
            # print('TABLE: ', table)
            for nbr in graph.get(table, ()):
                # print('nbr: ', nbr)
                if nbr not in selected_set:
                    scores[nbr] = scores.get(nbr, 0) + 1
            # print(f'SCORE FOR TABLE: {table} -> {scores}')
            # print('-'*20)

        # print(f'SCORES this hop: ', scores)
        if not scores:
            break

        # bridge score desc, then vector similarity-to-question for a deterministic tiebreak
        ranked = sorted(scores.items(), key = lambda kv: (-kv[1], -sim_scores.get(kv[0],0.0)))
        # print('RANKED: ', ranked)

        # Reserve room for the remaining hops instead of letting one
        # well-connected seed (e.g. a hub table with 9+ FKs) spend the
        # WHOLE budget in hop 1 and starve later hops (which is what was
        # silently happening before: hop 1 alone filled max_tables, so
        # hop 2 never ran and Person.Person was never reached).
        remaining_budget = max_tables - len(selected)
        this_hop_budget = max(1, remaining_budget // hops_left)
        # print(f'remaining_budget={remaining_budget}, this_hop_budget={this_hop_budget}')

        added = []
        for nbr, _score in ranked:
            if len(selected) >= max_tables or len(added) >= this_hop_budget:
                break

            selected.append(nbr)
            # print('SELECTED LIST: ', selected)
            selected_set.add(nbr)
            # print('SELECTED SET: ', selected_set)
            added.append(nbr) # <- only what was NEW this hop
            # print('ADDED: ', added)

        # print('SELECTED LENGTH: ', len(selected))
        hops_left -= 1
        if len(selected) >= max_tables or not added:
            break

        # print('FRONTIER BEFORE: ', frontier)
        frontier = set(added) # next hop expands only from newly added
        # print('FRONTIER AFTER: ', frontier)
        # print('='*50)

    return selected


# TESTING
# if __name__ == "__main__":
#     import json
#     g = build_fk_graph()
#     eval_set = json.load(open('eval/adventureworks_eval.json', encoding='utf-8'))
#     total_recall, n = 0.0, 0
#     for cat in ('Basic', 'Medium', 'Hard'):
#         for iid, item in eval_set[cat].items():
#                 # print(f'iid:{iid}, cat:{cat}')
#                 seeds, sim = rank_tables_by_similarity(item['prompt'], top_seeds=6)
#                 # print('SEEDS: ',seeds)
#                 # print('SIMILARITY: ',sim)
#                 # print('-'*20)
#                 tables = set(expand_with_fk_neighbors(seeds, g, sim_scores=sim, hops=2, max_tables=12))
#                 gold = set(item['gold_tables'])
#                 recall = len(gold & tables) / len(gold)
#                 total_recall += recall; n += 1
#                 flag = '' if recall == 1.0 else '   <-- MISS'
#                 print(f'{iid}: recall={recall:.2f}  missing={sorted(gold - tables)}{flag}')
#         print(f'\nMEAN RECALL: {total_recall/n:.3f}')