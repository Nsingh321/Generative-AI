from generator import get_response, get_sql_tables, GeneratorLLMResponse
from validator import execute_ms_sql_query, validate_sql
from schema import retrieve_relevant_tables, get_table_ddl, get_compact_schema, build_fk_graph, expand_with_fk_neighbors, rank_tables_by_similarity,get_join_paths
from judge import JUDGE_EVALUATION_SYSTEM_PROMPT, Evaluation, get_judge_response
from pipeline.state import Status
from pipeline.repair import find_out_of_context_tables


def retrieve(state, seed_top_n=6, hops=2, max_tables=12):
    # '''Get the relevant tables from the vector store according to the user's request.'''
    '''Semantic anchors from the vector store, then structural completion via FK graph'''
    # 1. semantic anchors (embeddings find WHERE in the schema to look)
    # _, seeds = retrieve_relevant_tables(state.question, top_n = seed_top_n)
    seeds, sim_scores = rank_tables_by_similarity(state.question, top_seeds = seed_top_n)
    # 2. structural explansion (FK graph completes the JOIN paths)
    tables = expand_with_fk_neighbors(seeds, graph = build_fk_graph(),sim_scores=sim_scores, hops = hops, max_tables=max_tables)
    # 3. build context on the explanded set
    state.retrieved_tables = tables
    state.schema_context = get_compact_schema(tables)
    # state.schsema_context, state.retrieved_tables = retrieve_relevant_tables(state.question, top_n=6 ) # top_n = 4 (before , now = 6 -> raises recall)
    state.ddl_context = get_table_ddl(tables)
    return state

# def is_retrieval_efficient(state):
#     "Check and update the status if the model is not able to generate SQL by using the retrieved table names. "
#     "In other terms, the generator understands the user's request but unable to generate SQL because no relevant table(s) retrieved."
#     if (state.status.value != "vague_request" and (state.candidate_sql or '') == ''):
#         state.status = Status.RETRIEVAL_INEFFICIENCY

#     return state


def generate(state):
    '''Get a response from the generator and update the status
    (vague_request / generator_invalid_json / generated).'''
    response = get_response(state.question, state.retrieved_tables)

    if response['status'] == "vague_request":
        state.status = Status.VAGUE_REQUEST
        state.structured_response = None
        state.candidate_sql = None

    elif response['status'] == "generator_invalid_json":
        state.status = Status.GENERATOR_INVALID_JSON
        state.structured_response = None
        state.candidate_sql = None

    else:
        state.status = Status.GENERATED
        state.structured_response = response['result']
        state.candidate_sql = (
            response['result'].sql_query
            if isinstance(response['result'], GeneratorLLMResponse) else None
        )

    return state


def validate(state):
    '''Validate the SQL for out-of-context tables, syntax errors / zero-row value mismatches. Update the state.'''

    # before execution, find the out of context tables 
    ooc = find_out_of_context_tables(state.candidate_sql, state.retrieved_tables)

    # if there contains any out-of-context tables -> set the status, update the state. Skip execution and directly go to repair 
    if ooc:
        print('OOC tables found -> ', ooc)
        state.unretrieved_tables = ooc # new state field
        state.status = Status.OUT_OF_CONTEXT_TABLE
        return state


    status, records, error_msg = execute_ms_sql_query(state.candidate_sql)

    # Syntax / execution error
    if not status:
        state.status = Status.SYNTAX_ERROR
        state.records = records
        state.last_error = error_msg
        state.repair_context = None
        return state

    # Executable -> classify by rows returned
    result = validate_sql(state.candidate_sql, records)
    state.records = records
    state.last_error = error_msg

    if result['status'] == 'pass':                 # rows > 0
        state.status = Status.PASS_EXEC
        state.repair_context = None
    elif result['status'] == 'needs_value_repair':  # 0 rows + text filters to fix
        state.status = Status.ZERO_ROWS_VALUE_MISMATCH
        state.repair_context = result['repair_context']
    else:                                           # legit 0 rows, nothing to repair
        state.status = Status.ZERO_ROWS_LEGIT
        state.repair_context = None

    return state


def judge(state):
    '''Judge the candidate SQL for logical correctness (final gate).'''
    tables_discovered_schema = get_compact_schema(state.retrieved_tables)
    query_tables_schema = get_compact_schema(get_sql_tables(state.candidate_sql))
    fk_relationships = get_join_paths(state.retrieved_tables)

    judge_prompt = JUDGE_EVALUATION_SYSTEM_PROMPT.format(
        tables_discovered=tables_discovered_schema,
        query_tables=query_tables_schema,
        fk_relationships = fk_relationships
    )

    result = get_judge_response(judge_prompt, state.question, state.candidate_sql)
    state.judge_tokens = result['judge_tokens']

    if result['status'] == 'judge_invalid_json':
        state.status = Status.JUDGE_INVALID_JSON
        return state

    evaluation = result['status']  # Evaluation object on success
    if isinstance(evaluation, Evaluation):
        state.judge = evaluation
        # Accumulate feedback across attempts so the generator stops repeating mistakes
        state.judge_feedback += f"\nAttempt {state.attempts + 1}: {evaluation.feedback}"
        state.status = Status.ACCEPTED if evaluation.is_acceptable else Status.JUDGE_REJECT

    return state


