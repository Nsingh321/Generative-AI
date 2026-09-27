
import sqlparse
import pyodbc
import json

from metadata_filter_extractor import extract_text_filter_columns, resolve_alias_to_table
from config import conn_str

def parse_llm_sql(llm_generated_sql):
    is_parsed = False
    restricted_sql = False

    try:
        parsed = sqlparse.parse(llm_generated_sql)
        for i in range(len(parsed)):
            stmt = parsed[i]
            is_parsed = True
            if stmt.get_type().lower() in ['drop','alter','truncate','delete','update']:
                restricted_sql = True
                print(f'stmt: {stmt} cannot be used')
                return restricted_sql, is_parsed
        return restricted_sql, is_parsed
    except Exception as e:
        print('Exception occured while parsing LLM SQL: ',e)
        is_parsed = False
        return restricted_sql, is_parsed
    

def execute_ms_sql_query(llm_generated_sql):
    '''Execute generated SQL against MS SQL Server AdventureWorks database'''

    error_msg = ''
    # conn_str = (
    #     "Driver={ODBC Driver 18 for SQL Server};"
    #     "Server=localhost\\SQLEXPRESS;"  # server name/instance
    #     "Database=AdventureWorks2025;" # DB name
    #     "Trusted_Connection=yes;"
    #     "Encrypt=no;" # Crucial for local dev environments to avoid SSL cert errors
    # )
    
    try:
        records = 0
        conn = pyodbc.connect(conn_str)
        with conn.cursor() as cursor:

            restricted_sql, is_parsed = parse_llm_sql(llm_generated_sql)
    
            if is_parsed and restricted_sql:
                print('The SQL query cannot be executed as it starts with restricted keywords either drop,alter,truncate,delete,update.')
                error_msg = 'Error while parsing LLM SQL.'
                return False,[],error_msg
            elif not is_parsed and not restricted_sql :
                print('SQL query cannot be parsed. Cannot proceed ahead.')
                error_msg = 'SQL query cannot be parsed. Cannot proceed ahead.'
                return False,[],error_msg
                

            else:
                # restricted_sql = False and is_parsed = True
                print('LLM generated SQL starts with SELECT statement.')
                cursor.execute(llm_generated_sql)
                records = cursor.fetchall()  
                # print(f'Records are: {records[:5]}')
                
                print(f'Count of records: {len(records)}')
                error_msg = 'SQL query has no errors.'
                
                return True, records,error_msg

            
    except Exception as e:
        # error_msg = f'Error, while executing the SELECT query: {e}'
        print(f'Error, while executing the SELECT query: {e}')
        error_msg = f'Error, while executing the SELECT query: {e}'
        return False, [],error_msg
    
    finally:
        if conn:
            conn.close()
    

def generate_repair_reference_context(sql_query):
    """Queries the database for actual values of columns used in broken text filters."""
    
    text_filters = extract_text_filter_columns(sql_query)
    print(f'Inside generate_repair_reference_context. text_filters:{text_filters}')
    repair_context = ""
    
    for filter_info in text_filters:
        alias = filter_info["alias"]
        col_raw = filter_info["column_name"]
        real_table = resolve_alias_to_table(sql_query, alias)
        
        if real_table:
            try:
                # Dynamic top 10 unique value extraction
                lookup_sql = f"SELECT DISTINCT TOP 10 [{col_raw}] FROM {real_table} WHERE [{col_raw}] IS NOT NULL;"
                success, records, _ = execute_ms_sql_query(lookup_sql)

                # records is a list of single-column pyodbc rows
                if success and len(records) > 0:
                    possible_values = [str(r[0]) for r in records]
                    print(f'Inside generate_repair_reference_context - possible_values: {possible_values}')
                    values_block = "\n".join([f"- {v}" for v in possible_values])
                    
                    repair_context += f"Column: {real_table}.{col_raw} (Used as '{filter_info['full_token']}')\n"
                    repair_context += f"Actual Values in Database:\n{values_block}\n\n"
            except Exception as ex:
                print(f"Could not read distinct lookup values for {real_table}: {ex}")
                repair_context += f"Column: {real_table}.{col_raw}\n"
                repair_context += "⚠️ [System Warning]: This column name does not exist in this table schema. Please inspect your DDL definitions to select a valid column.\n\n"

                
    return repair_context

def validate_sql(sql,records):
    '''Part of Validation Layer'''
    '''Given a SQL candidate, is it semantically reasonable?'''
    
    # 2. Check the count rows returned
    if len(records) > 0:
        return {
            'status' : 'pass',
            'sql' : sql,
            'records' : records,
            'value_repair' : 'False'
        }
    
    # 3. If Zero rows returned -> we need value repair
    if len(records) == 0:
        repair_context = generate_repair_reference_context(sql)

        if repair_context:
            return {
                'status': 'needs_value_repair',
                'sql': sql,
                'repair_context': repair_context,
                'value_repair' : 'True'
            }
        
    return {
        'status': 'zero_rows',
        'sql' : sql,
        'records' : records,
        'value_repair' : 'False'

    }


if __name__ == "__main__":

    # Test gold sql from adventure_works_expansion.json on database
    exp = json.load(open('eval/adventureworks_eval_expansion.json', encoding='utf-8'))
    for cat in ('Medium','Hard','Expert'):
        for iid, item in exp[cat].items():
            ok, rows, err = execute_ms_sql_query(item['gold_sql'])
            print(f"{iid}: {'OK '+str(len(rows))+' rows' if ok else 'FAIL -> '+err}")


