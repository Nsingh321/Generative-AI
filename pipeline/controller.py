from pipeline.state import PipelineState, Status, TERMINAL, GO_TO_JUDGE, snapshot
from pipeline.steps import retrieve, generate, validate, judge
from pipeline.repair import REPAIR_ROUTER


def run_pipeline(question, max_attempts=3):
    state = PipelineState(question=question, max_attempts=max_attempts)
    state = retrieve(state)   # get relevant tables
    state = generate(state)   # generate sql
    # state = is_retrieval_efficient(state) # check if the retrieved tables are sufficient for generator



    # Generator produced invalid_json or , vague request -> STOP here
    if state.status in TERMINAL:
        return finalize(state)

    while True:
        state = validate(state)

        # Executed OK (rows>0 or legit-zero) -> judge is the final gate
        if state.status in GO_TO_JUDGE:
            state = judge(state)

            # Judge accepted or produced invalid_json -> STOP here
            if state.status in TERMINAL:
                return finalize(state)
            
        # else JUDGE_REJECT or OUT_OF_CONTEXT_TABLE-> fall through to repair routing below
        # --- repair routing (loop level): syntax / value / judge_reject /out-of-context-table ---
        strategy = REPAIR_ROUTER.get(state.status)
        print('Strategy: -> ', strategy)

        # No repair for this status, or budget exhausted -> human intervention
        if strategy is None or state.attempts >= state.max_attempts:
            state.status = Status.NEEDS_HUMAN
            return finalize(state)

        state.history.append(snapshot(state))  # audit BEFORE mutating
        state.attempts += 1
        state = strategy(state)  # produces new candidate_sql; loop re-validates it

        # Generator failed to produce valid JSON while repairing -> STOP here
        if state.status == Status.GENERATOR_INVALID_JSON:
            return finalize(state)


def finalize(state):
    return {
        "status": state.status.value,
        "generated_sql": state.candidate_sql,
        "judge_score": state.judge.score if state.judge else None,
        "judge_feedback": state.judge_feedback if state.judge else None,
        "judge_tokens_usage": _format_tokens(state.judge_tokens),
        "attempts": state.attempts,
        "retrieved_tables": list(state.retrieved_tables),
        "tables_discovered": len(state.retrieved_tables),
        "history": state.history,  # full audit trail per question
    }


def _format_tokens(usage):
    '''Normalize the judge usage object into a JSON-serializable dict.'''
    if usage is None:
        return None
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }
