import re
from generator import chat_with_json_retry,validate_retrieved_tables,get_sql_tables
from pipeline.state import Status
from schema import find_tables_for_columns,rank_tables_by_similarity,get_compact_schema,get_table_ddl,load_ddl_catalog


def _regenerate(state, instruction, extra_context=""):
    '''Shared repair helper: rebuild a fully-contextualized prompt and regenerate SQL.
    Always includes the user question, the SQL being repaired, and the schema/DDL context
    so the model is never repairing blind.'''

    system_content = (
        "You are an expert T-SQL assistant for MS SQL Server, fixing a previously "
        "generated query.\n"
        "=== TABLE DESCRIPTIONS ===\n" + (state.schema_context or "") + "\n"
        "=== ACTUAL TABLE DDL (CREATE STATEMENTS) ===\n" + (state.ddl_context or "") + "\n"
        "Respond strictly in the required JSON schema (reasoning, sql_query, is_vague)."
    )

    user_content = (
        f"User question: {state.question}\n\n"
        f"Previous SQL:\n{state.candidate_sql}\n\n"
        f"{instruction}\n"
        f"{extra_context}"
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

    temp = 0.4 # so that the model explores a different query and can escape the fixed point when temp = 0. At temp=0, it keeps producing the same errors.
    response = chat_with_json_retry(messages, temp = temp)

    if not response['status']:
        print("Failed to generate a valid JSON response after maximum - 3 retries.")
        state.status = Status.GENERATOR_INVALID_JSON
        return state

    state.structured_response = response['response']
    state.candidate_sql = state.structured_response.sql_query
    return state


def repair_syntax(state):

    # before regenerating syntax instruction, find the columns in error_msg(for which the generator cannot figure out the tables) 
    # and setup the locator instruction hint to guide generator about the tables that contains those columns
    locator = build_column_locator_hint(state.last_error, state.retrieved_tables)
    print('LOCATOR:-> ', locator)
    
    # for column error, pass the locator as extra context
    # for other types of errors, locator is empty
    return _regenerate(
        state,
        f"The previous query failed to execute with error: {state.last_error}. "
        "Return a corrected, syntactically valid version.",
        extra_context=locator, # precise, computed hint (empty when not a column error)
    )


def repair_value(state):
    return _regenerate(
        state,
        "The previous query executed but returned 0 rows because the literal filter "
        "values do not match the exact values stored in the database. Use the actual "
        "values below to correct the WHERE filters.",
        extra_context="\n=== ACTUAL DATABASE VALUES ===\n" + (state.repair_context or ""),
    )


def repair_feedback(state):
    return _regenerate(
        state,
        "The query is logically incorrect. Correct it based on the reviewer feedback below.",
        extra_context="\n=== REVIEWER FEEDBACK ===\n" + (state.judge_feedback or ""),
    )

def repair_unretrieved_table(state):
    '''Check if the generator has used any unretrieved tables that were not retrieved. 
    Yes: Use the generator's knowledge to retrieve that table that it thinks is useful to generate sql.
         If no such table exists, then instruct it to generate sql only using the retrieved tables.
    No:  No action in this case since generator has used the retrieved tables to generate sql.
      '''
    
    ddl_catalog = load_ddl_catalog()

    catalog_bare = {k.split('.')[-1].lower(): k for k in ddl_catalog} #dictionary with key = bare:value = full key

    add_tables,bad_names = [], []
    for t in state.unretrieved_tables:
        key = _resolve_in_catalog(t, ddl_catalog, catalog_bare) # exact or bare name mismatch

        if key:
            # CASE 1: if this table exists in ddl catalog -> real table, but it was not retrieved -> add it in add_tables
            print('KEY: ',key)
            add_tables.append(key)
        else:
            # CASE 2: else this table does not exist in ddl catalog -> add it in bad_names
            bad_names.append(t)

    # CASE 2 fallback: vector-search for the wrong name(s)
    print('BAD NAMES: ', bad_names)
    for name in bad_names:
        suggestions, _ = rank_tables_by_similarity(name, top_seeds = 2)
        add_tables.extend(suggestions)

    new_tables = list(dict.fromkeys(state.retrieved_tables + add_tables))
    print('NEW TABLES: ', new_tables)

    # update the state for the new tables
    state.retrieved_tables = new_tables
    state.schema_context = get_compact_schema(new_tables)
    state.ddl_context = get_table_ddl(new_tables)

    instruction = "Your previous query referenced tables that were not in the provided schema. "

    if bad_names:
        instruction += (f"These names do not exist in the database: {bad_names}. "
                        "Use ONLY the tables now provided below. ")
    
    return _regenerate(state, instruction)


def _resolve_in_catalog(table, ddl_catalog, catalog_bare):
    '''Check if a table exists in ddl catalog. '''
    nt = table.replace('[','').replace(']','').replace('"','').strip()
    if nt in ddl_catalog:
        # extract Schema.table
        return nt
    return catalog_bare.get(nt.split('.')[-1].lower(), "") # bare name -> full key, else ''


def _norm(t):
    return t.replace('[','').replace(']','').replace('"','').strip().lower()

def find_out_of_context_tables(sql, retrieved_tables):
    sql_used = get_sql_tables(sql) # get the tables used in sql
    retrieved_norm = {_norm(r) for r in retrieved_tables}
    retrieved_bare = {r.split('.')[-1] for r in retrieved_norm} # bare table names

    out  = []
    for t in sql_used:
        nt = _norm(t) # normalize the sql table
        if nt in retrieved_norm:
            # sql table exists in retrived tables -> valid table. Now check for next table
            continue

        # if (due to any normalization or naming convention mismatch) it is unable to match same tables above then check here. 
        # check only on the basis of just bare table names
        if nt.split('.')[-1] in retrieved_bare:  # if matches -> move to next
            continue

        out.append(t) # this will contain the unretrieved table names
    return out

def parse_invalid_columns(error_msg):
    '''Helper: Pull column names out of a SQL Server 42S22 error.
    The final list with the column name is scanned against the retrieved tables schema.
    The table containing these column names will be fetched and explicitely told to the generator.
    ...INVALID COLUMN NAME  'FirstName'. ...Invalid column name 'LastName' 
    -> ['FirstName, 'LastName']'''

    cols = re.findall(r"Invalid column name '([^']+)'", error_msg or "")
    return list(dict.fromkeys(cols))

def build_column_locator_hint(error_msg, retrieved_tables):
    '''Build an instruction hint for generator to locate right candidate tables (for columns inside error_msg) by looking in retrieved tables.'''
    bad_cols = parse_invalid_columns(error_msg=error_msg)

    if not bad_cols:
        return ""
    
    owners = find_tables_for_columns(bad_cols, retrieved_tables)
    lines = []
    for col, tables in owners.items():

        # if tables exist for this bad column (in error_msg) -> construct the instruction hint for generator to use the table(s)
        if tables:
            lines.append(f"- Column '{col}' is NOT on the table you used."
                         f"It exists in: {' ,'.join(tables)}. Join that table and select '{col}' from there. ")
            
        else:
            # No tables exist (for this column)-> construct the instruction to not use this column
            lines.append(f"- Column '{col}' does not exist in ANY provided table. Do not use it. ")

    return "=== COLUMN LOCATION HINTS ===\n" + "\n".join(lines)+"\n"
        

REPAIR_ROUTER = {
    Status.SYNTAX_ERROR: repair_syntax,
    Status.ZERO_ROWS_VALUE_MISMATCH: repair_value,
    Status.JUDGE_REJECT: repair_feedback,
    Status.OUT_OF_CONTEXT_TABLE : repair_unretrieved_table
}

# TESTING:
if __name__ == "__main__":

    # test - 1
    # print(build_column_locator_hint(error_msg="Error, while executing the SELECT query: ('42S22', \"[42S22] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Invalid column name 'FirstName'. (207) (SQLExecDirectW); [42S22] [Microsoft][ODBC Driver 18 for SQL Server][SQL Server]Invalid column name 'LastName'. (207)\")" ,
    #                                 retrieved_tables= [
    #         "HumanResources.Department",
    #         "HumanResources.Employee",
    #         "HumanResources.EmployeeDepartmentHistory",
    #         "HumanResources.JobCandidate",
    #         "HumanResources.EmployeePayHistory",
    #         "HumanResources.Shift",
    #         "Person.Person",
    #         "Sales.SalesPerson",
    #         "Person.BusinessEntityContact",
    #         "Sales.Store"
    #     ]))

    # test - 2
    R = ['Sales.Customer', 'Sales.SalesTerritory']
    assert find_out_of_context_tables('SELECT * FROM Sales.Customer', R) == []
    assert find_out_of_context_tables('SELECT * FROM Customer', R) == []              # bare -> no flag
    assert find_out_of_context_tables('SELECT * FROM [Sales].[Customer]', R) == []    # bracketed
    assert find_out_of_context_tables('SELECT * FROM Sales.SalesOrderHeader', R) == ['Sales.SalesOrderHeader']

    cat = load_ddl_catalog(); bare = {k.split('.')[-1].lower(): k for k in cat}
    assert _resolve_in_catalog('SalesOrderHeader', cat, bare) == 'Sales.SalesOrderHeader'
    assert _resolve_in_catalog('Orders', cat, bare) == ''
    print('ALL REPAIR UNIT TESTS PASSED')