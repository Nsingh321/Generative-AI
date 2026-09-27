import pyodbc
import json
import os

def generate_database_ddl_catalog():
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=localhost\\SQLEXPRESS;"
        "Database=AdventureWorks2025;"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
    )
    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    # Query to fetch all tables
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE';
    """)
    tables = cursor.fetchall()
    
    ddl_catalog = {}
    
    for row in tables:
        schema = row.TABLE_SCHEMA
        table_name = row.TABLE_NAME
        full_name = f"{schema}.{table_name}"
        
        # Query column definitions for this specific table
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION;
        """)
        columns = cursor.fetchall()
        
        # Build the mock/clean CREATE TABLE DDL statement
        ddl_lines = []
        for col in columns:
            col_name = col.COLUMN_NAME
            data_type = col.DATA_TYPE
            max_len = col.CHARACTER_MAXIMUM_LENGTH
            nullable = "NULL" if col.IS_NULLABLE == "YES" else "NOT NULL"
            
            # Format types with lengths like nvarchar(50)
            if max_len == -1:
                type_str = f"{data_type}(MAX)"
            elif max_len is not None:
                type_str = f"{data_type}({max_len})"
            else:
                type_str = data_type
                
            ddl_lines.append(f"    [{col_name}] {type_str} {nullable}")
            
        # Combine into an actual SQL DDL statement string
        ddl_statement = f"CREATE TABLE [{schema}].[{table_name}] (\n"
        ddl_statement += ",\n".join(ddl_lines)
        ddl_statement += "\n);"
        
        ddl_catalog[full_name] = ddl_statement

    conn.close()
    
    # Save to a local json file for your pipeline
    os.makedirs('schema_new', exist_ok=True)
    with open('schema_new/adventureworks_database_ddl.json', 'w') as f:
        json.dump(ddl_catalog, f, indent=4)
        
    print("Successfully generated DDL catalog for all tables!")

# Run it once to build the asset
# generate_database_ddl_catalog()