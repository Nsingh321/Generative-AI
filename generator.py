from dotenv import load_dotenv
import os
import ollama
from openai import OpenAI

from pydantic import BaseModel, Field, ValidationError
from typing import Optional
from sql_metadata import Parser
from schema import validate_retrieved_tables, get_compact_schema, get_table_ddl, get_join_paths
from config import GENERATOR_MODEL, GENERATOR_PROVIDER


load_dotenv(override = True)


base_url = "http://localhost:11434/v1"
generator_model = GENERATOR_MODEL

TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
FIREWORKS_API_KEY = os.getenv('FIREWORKS_API_KEY')

together_client = OpenAI(
    api_key=TOGETHER_API_KEY,
    base_url="https://api.together.ai/v1",
    timeout=300.0
)

deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=300.0
)

fireworks_client = OpenAI(
    api_key=FIREWORKS_API_KEY,
    base_url="https://api.fireworks.ai/inference/v1",
    timeout=300.0
)

# SYSTEM_PROMPT =f'''
# You are a expert in SQL. You have access to following schema: {schema_summary}
# RULES:
# 1. Call the schema tool whenever schema information is insufficient to answer correctly.
# 2. Before generating sql, ALWAYS check that the tool call has been made for all tables included in the final sql query. 
# 3. You are allowed to use alias for tables or columns.
# 4. You should never guess column names. If you are unsure, then call the tool to get the table schema. 
# 5. Do NOT call the tool with the same table name twice.
# 6. Do NOT include markdowns (eg. ```sql```) or explainations in the final output. 

# Translate this natural language request into a JSON object containing two fields. The first field 'select' will be a SELECT query answering the question. When no sql can be generated then this field will be empty. The second field 'reason' will be your reason for generating or not generating that SQL query. 
# '''

# GENERATOR_SYSTEM_PROMPT = '''
# You are a Senior SQL Expert. You have access following summary: {schema_summary}

# OPERATIONAL RULES:
# 1. TOOL FIRST: If you don't have the full DDL for a table, use 'get_table_info'. If you have sufficient schema information, then proceed to generate SQL.
# 2. NO GUESSING: Never invent column names. If unsure, call the tool.
# 3. ALIASES: Use clear table aliases (e.g., 't' for tracks).
# 4. CUSTOMER DATA: Always include 'first_name' and 'last_name' when customers are requested.

# OUTPUT FORMAT:
# Return a JSON object. 
# - Use 'reasoning' to explain your join path and column choices.
# - Use 'sql_query' for the code. 
# - If the question is vague (e.g., "do something"), set 'is_vague' to true and 'sql_query' to "".
# '''

GENERATOR_SYSTEM_PROMPT = """
You are an expert T-SQL Data Analyst assistant for MS SQL Server.\n
Your job is to write a highly optimized SQL query based on the provided schemas.\n
"CRITICAL RULES:
- You must only use the tables provided in the schema context below. NEVER assume other tables exist.\n
- If you don't have enough context to generate the SQL then say so.
- Always write tables with their full schema prefix exactly as shown in the DDL (e.g. Person.Person, never Person).
- Always prefix column names with table aliases to prevent ambiguity.\n\n
=== TABLE DESCRIPTIONS ===\n{pruned_schema_context}\n
=== ACTUAL TABLE DDL (CREATE STATEMENTS) === \n{raw_ddl_context}  
=== FK RELATIONSHIPS === \n{fk_relationships}

# OUTPUT FORMAT:
# Respond strictly in the designated JSON schema format defined below - 
# reasoning - Use 'reasoning' to explain your join path and column choices.
# sql_query - Use 'sql_query' for the code. 
# is_vague - If the question is vague (e.g., "do something"), set 'is_vague' to true and 'sql_query' to "".
"""
    


def generate_user_prompt(question: str) -> str:
    return f""" 
    CRITICAL RULES:
    - If the user is not clear about his intention, then ask the user to be specific. In this case, do NOT produce SQL.
    - NEVER generate SQL for related to DROP, DELETE, TRUNCATE, UPDATE unless the user explicitly asks.
    - For ranking, use RANK() unless the question says otherwise. 
    - Please refer the below examples to identify vague requests:
    #### VAGUE:
    - Show me something interesting
    - Give me insights
    - Analyze the data   

    User question: {question}."""

class GeneratorLLMResponse(BaseModel):
    reasoning: str = Field(description = 'Step-by-step logic explanation which tables/columns are used and why.')
    sql_query: Optional[str] = Field(description ='The final SQL query for a given natural language question. Leave as an empty string if the user request is too vague or invalid.')
    is_vague: bool = Field(description ="Set to True if the user's question cannot be converted to SQL due to lack of clarity.")
    

def get_response(message, retrieved_tables):

    # 1. Create a local list/set to track tools/tables used in THIS specific request
    tables_discovered = set()
    
    validity = validate_retrieved_tables(retrieved_tables)
    if not isinstance(validity, dict):
        validity = {}
    valid_tables = [t for t in retrieved_tables if validity.get(t, False)]
    print(f'Retrieved tables: {retrieved_tables}')
    print(f'Valid tables: {valid_tables}')

    # 5. Get the compact schema for each of the retrived tables
    pruned_schema_context = get_compact_schema(valid_tables)

    # 6. Fetch DDL Statements
    pruned_raw_ddl_context = get_table_ddl(valid_tables)

    # 7. Get FK relationships among the retrieved tables
    fk_relationships = get_join_paths(retrieved_tables)

    # 8. Construct the messages list by dynamically inserting the compact schema, valid tables ddl, fk relationships in the system prompt
    messages = [
        {"role": "system", "content": GENERATOR_SYSTEM_PROMPT.format(pruned_schema_context=pruned_schema_context,raw_ddl_context=pruned_raw_ddl_context,fk_relationships=fk_relationships)},
        {"role": "user", "content": generate_user_prompt(message)}
    ]

    response = chat_with_json_retry(messages,temp=0)

    if not response['status']:
        print("Failed to generate a valid JSON response after maximum - 3 retries.")
        # return 'generator_invalid_json', list(valid_tables)
        return {
            'status': 'generator_invalid_json',
            'result': None,
            'tables': None
        }

    structured_response = response['response']
    if structured_response.is_vague:
        return {
            'status': 'vague_request',
            'result': None,
            'tables': None
        }

    tables_discovered = get_sql_tables(structured_response.sql_query)
        
    # return structured_response, list(tables_discovered)
    return {
        'status': 'success',
        'result': structured_response,
        'tables': list(tables_discovered)
    }


def chat_with_json_retry(messages,temp = 0, max_retries=3):
    """
    Handles generation and guarantees matching the Pydantic JSON schema 
    via an iterative retry loop over any conversational message history.
    Returns:
    False - If the generator cannot give back a structured response
    Pydantic object - If the generator can give back a structured response
    """
    current_retry = 0
    structured_response = False

    while current_retry <= max_retries:
        if GENERATOR_PROVIDER == "together":
            completion = together_client.chat.completions.create(
                model=generator_model,
                messages=messages,
                temperature=temp,
                response_format={"type": "json_object"}
            )
            content_str = completion.choices[0].message.content
            assistant_message = {"role": "assistant", "content": content_str}
        elif GENERATOR_PROVIDER == "deepseek":
            completion = deepseek_client.chat.completions.create(
                model=generator_model,
                messages=messages,
                temperature=temp,
                response_format={"type": "json_object"}
            )
            content_str = completion.choices[0].message.content
            assistant_message = {"role": "assistant", "content": content_str}
        elif GENERATOR_PROVIDER == "fireworks":
            completion = fireworks_client.chat.completions.create(
                model=generator_model,
                messages=messages,
                temperature=temp,
                response_format={"type": "json_object"}
            )
            content_str = completion.choices[0].message.content
            assistant_message = {"role": "assistant", "content": content_str}
        else:
            final_response = ollama.chat(
                model=generator_model,
                messages=messages,
                options={'temperature': temp},
                format=GeneratorLLMResponse.model_json_schema()
            )
            content_str = final_response['message']['content']
            assistant_message = final_response['message']

        if test_output_json_structure(GeneratorLLMResponse, content_str):
            structured_response = GeneratorLLMResponse.model_validate_json(content_str)

            return {
                "status" : True,
                "response": structured_response
            }

        current_retry += 1
        if current_retry <= max_retries:
            print(f'-- RETRYING JSON STRUCTURE: Attempt {current_retry} of {max_retries} --')
            messages.append(assistant_message)
            messages.append({
                "role": "user",
                "content": "Your previous response did not match the required JSON schema. Please output valid JSON only matching the schema."
            })

    # return structured_response
    return {
                "status" : False,
                "response": None
            }


def test_output_json_structure(structured_class:type[BaseModel], content:str):
    '''Test the output JSON model format.'''
    try:
        structured_class.model_validate_json(content)
        print(f'Correct JSON schema output returned for {structured_class.__name__}.')
        print(f'Structured response: {structured_class.model_validate_json(content)}')
        return True
    except ValidationError as e:
        print(f'Invalid schema for {structured_class.__name__}: {e}')
        return False
    except Exception as e:
        print(f'General Error parsing JSON: {e}')
        return False

def get_sql_tables(sql_query):

    '''Extract unique tables used by the generator in the SQL.'''
    # This automatically handles subqueries, aliases, and CTEs
    parsed_tables = []
    try:
        clean_query_string = sql_query.replace('[', '').replace(']', '')
        parsed_tables = list(set(Parser(clean_query_string).tables))
        # print(f'SQL PARSED TABLES : {parsed_tables}')
        return parsed_tables
    except Exception:
        parsed_tables = []
        print(f'Exception occured in get_sql_tables(). Returning parsed tables: {parsed_tables}')
        return parsed_tables