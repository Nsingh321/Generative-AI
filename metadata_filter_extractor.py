import sqlparse
from sqlparse.sql import Where, Comparison, Identifier
from sqlparse.tokens import String
import re

def extract_text_filter_columns(sql_query):
    """Parses SQL statement to find text column identifiers used in comparisons against string literals."""
    parsed = sqlparse.parse(sql_query)[0]
    filter_columns = []
    
    where_token = None
    for token in parsed.tokens:
        if isinstance(token, Where):
            where_token = token
            break
            
    if not where_token:
        return filter_columns

    for token in where_token.tokens:
        if isinstance(token, Comparison):
            has_string_literal = any(t.ttype == String.Single for t in token.tokens)
            if has_string_literal:
                for t in token.tokens:
                    if isinstance(t, Identifier):
                        col_name = t.get_real_name()
                        parent_name = t.get_parent_name() or ""
                        filter_columns.append({
                            "full_token": t.value,
                            "column_name": col_name,
                            "alias": parent_name
                        })
    return filter_columns

def resolve_alias_to_table(sql_query, alias_name):
    """Maps a table alias back to its raw schema.table name."""
    if not alias_name:
        return None
    pattern = r"([\w.]+)\s+(?:as\s+)??" + re.escape(alias_name) + r"\b"
    match = re.search(pattern, sql_query, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

