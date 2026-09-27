
from generator import test_output_json_structure

from pydantic import BaseModel, Field
import os

from dotenv import load_dotenv
from openai import OpenAI
from metadata_filter_extractor import *
from config import EVALUATION_MODEL

load_dotenv()

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

client = OpenAI(
    api_key= DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=300.0
)


# schema_summary = get_summary_schema()

JUDGE_EVALUATION_SYSTEM_PROMPT = '''
You are an expert evaluator for SQL. 
You have access to following :

#### SCHEMAS EXPLORED DURING GENERATION: 
{tables_discovered}

#### SCHEMAS USED IN FINAL SQL:
{query_tables}

#### FK RELATIONSHIPS IN THE SCHEMA:
{fk_relationships}

You will be provided with a user's natural language request for a sql query and a SQL query fulfilling that request.
 
RELEVANCY_SCORE_CRITERIA = 
Relevance (1-5) - A measure of how accurately the SQL query fulfills the user's intent.
- PRIMARY METRIC: Semantic Accuracy. Does the SQL return the exact data requested?
- SECONDARY METRIC: Optimization. Once accuracy is confirmed, penalize queries with redundant joins or unnecessary complexity.

SCORING RUBRIC:
5: Perfect. Accurate logic, correct tables, and optimized code.
4: Accurate, but uses slightly inefficient logic (e.g., unnecessary joins).
3: Partially accurate, but misses a secondary filter or uses a slightly wrong aggregation.
2: Inaccurate. The SQL runs, but returns data that doesn't answer the user's core question.
1: Completely irrelevant or logically broken.

OUTPUT FORMAT: 
Return a JSON object. 
is_acceptable : Set to True if the SQL query is fulfilling the user's objective otherwise set to False.
feedback: Keep your feedback on point and provide your explanation in 1-2 bullet points at max. of how the SQL query failed to satify user's intent."
score: Score between (1-5) depending upon how much the sql query is relevant to the user's question by using the above scoring method.
'''

class Evaluation(BaseModel):
    is_acceptable: bool = Field(description="Set to True if the SQL query is fulfilling the user's objective otherwise set to False.")
    feedback: str = Field(description="Keep your feedback on point and provide your explanation in 1-2 bullet points at max. of how the SQL query failed to satify user's intent.")
    score: int = Field(ge=1, le=5, 
        description="Score based on 'Semantic Precision'— how accurately the SQL logic mirrors the user's request."
    )


def get_judge_response(judge_system_prompt, user_question, llm_generated_sql):

    '''Return judge response for a generated llm response'''

    user_message_prompt = f'''
    You have been provided with the user's request and a generated sql for that request.
    User question: {user_question}
    Generated SQL: {llm_generated_sql}
    Please provide your feedback. 
'''
    messages = [{'role': 'system', 'content': judge_system_prompt},
                {'role':'user', 'content': user_message_prompt}]
    
    MAX_RETRY_JSON_OUTPUT = 3
    current_json_retry = 0
    structured_judge_response = False

    while(current_json_retry <= MAX_RETRY_JSON_OUTPUT):

        judge_response = client.chat.completions.create(model = EVALUATION_MODEL,
                                                    messages=messages,
                                                    response_format={"type": "json_object"},
                                                    temperature=0,
                                                    top_p=0.1,
                                                    max_tokens=2000)
    
    
        if test_output_json_structure(Evaluation, judge_response.choices[0].message.content):
        
            structured_judge_response = Evaluation.model_validate_json(judge_response.choices[0].message.content)
            break
    
        current_json_retry += 1

        if current_json_retry <= MAX_RETRY_JSON_OUTPUT:
                print(f'-- RETRYING: Attempt {current_json_retry} of {MAX_RETRY_JSON_OUTPUT} for correct JSON output for judge--')
                
                # Append the broken response and a user correction message to the ongoing conversation
                messages.append({
                                "role": "assistant", 
                                "content": judge_response.choices[0].message.content
                            })
                messages.append({
                    "role": "user",
                    "content": (
                        "Your previous response did not match the required JSON schema. "
                        "Please correct the fields, ensure all properties exist, and output valid JSON only."
                    )
                })

    if not structured_judge_response:
        print(f"Failed to generate a valid JSON response after maximum retries. {judge_response}")
        return {"status" : 'judge_invalid_json',
                "judge_tokens" : judge_response.usage}


    return {"status":structured_judge_response,
            "judge_tokens":judge_response.usage}
 

