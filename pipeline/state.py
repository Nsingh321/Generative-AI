from enum import Enum
from dataclasses import dataclass, field
from judge import Evaluation
from generator import GeneratorLLMResponse

class Status(str, Enum):
    '''Every possible way a query can end.'''
    INIT = "init"
    GENERATED = "generated"

    # terminal-before-validation
    VAGUE_REQUEST = "vague_request"
    GENERATOR_INVALID_JSON = "generator_invalid_json"

    # validation outcomes
    PASS_EXEC = "pass_exec"
    SYNTAX_ERROR = "syntax_error"
    ZERO_ROWS_VALUE_MISMATCH = "zero_rows_value_mismatch"
    ZERO_ROWS_LEGIT = "zero_rows_legit"
    OUT_OF_CONTEXT_TABLE = 'out_of_context_table'

    # judge outcomes
    ACCEPTED = 'accepted'
    JUDGE_REJECT = 'judge_reject'
    JUDGE_INVALID_JSON = 'judge_invalid_json'

    # terminal control
    NEEDS_HUMAN = 'needs_human_intervention'

# queries that can be sent to the terminal
TERMINAL = {Status.VAGUE_REQUEST, Status.GENERATOR_INVALID_JSON,
            Status.ACCEPTED, Status.JUDGE_INVALID_JSON, Status.NEEDS_HUMAN}

# passed queries that will be sent to the judge
GO_TO_JUDGE = {Status.PASS_EXEC, Status.ZERO_ROWS_LEGIT}

@dataclass
class PipelineState:
    question : str
    max_attempts : int = 3

    # retrieval
    retrieved_tables : list[str] = field(default_factory=list)
    unretrieved_tables : list[str] = field(default_factory=list)
    schema_context : str = ""
    ddl_context : str = ""


    # generation (object kept for audit. string is the source of truth)
    structured_response: GeneratorLLMResponse | None = None
    candidate_sql : str | None = None

    # validation
    records: list | None = None
    last_error : str | None = None #DB error text for repair_syntax
    repair_context: str | None = None #real values for repair_value

    # judge
    judge: Evaluation | None = None
    judge_feedback: str = ""
    judge_tokens: dict | None = None

    # control + audit
    status: Status = Status.INIT
    attempts: int = 0
    history: list[dict] = field(default_factory=list)


def snapshot(state):
    '''Immutable, JSON-serializable record of one attempt, for the audit trail in finalize().'''
    return {
        "attempt": state.attempts,
        "status": state.status.value,
        "candidate_sql": state.candidate_sql,
        "last_error": state.last_error,
        "had_repair_context": bool(state.repair_context),
        "judge_score": state.judge.score if state.judge else None,
        "judge_feedback": state.judge_feedback,
    }
