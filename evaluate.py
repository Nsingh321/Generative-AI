import json
import os
import re
import glob
from datetime import datetime
from datetime import date
from decimal import Decimal
from collections import Counter
from pipeline.controller import run_pipeline
from validator import execute_ms_sql_query
from config import EVALUATION_MODEL, GENERATOR_MODEL
from judge import JUDGE_EVALUATION_SYSTEM_PROMPT
from decimal import Decimal

EVAL_SET_PATH = "eval/adventureworks_eval_expansion.json"


def retrieval_recall(gold_tables, retrieved_tables):
    '''Fraction of gold tables that were retrieved. 1.0 means every table the
    gold query needs was present in the retrieved context.'''
    if not gold_tables:
        return None
    gold = set(gold_tables)
    retrieved = set(retrieved_tables or [])
    return round(len(gold & retrieved) / len(gold), 3)


def build_single_output(sql_category, item_id, item, output_list,
                        evaluation_model, generator_model, sys_prompt_version, current_sys_prompt, rmap,is_obf=False):
    user_question = item['prompt']
    print(f'\nUSER QUESTION [{sql_category}/{item_id}]: {user_question}')

    pipeline_result = run_pipeline(user_question)
    _,gold_rows,_ = execute_ms_sql_query(item['gold_sql'])
    ok, pred_rows, _ = execute_ms_sql_query(pipeline_result['generated_sql'])
    pipeline_result['execution_match'] = bool(ok) and execution_match(gold_rows, pred_rows, ordered = item.get('ordered',False)) # strict
    pipeline_result['entity_match'] = bool(ok) and entity_match(gold_rows, pred_rows) # column-tolerant

    
    retrieved_obf_to_real = [rmap.get(t,t) for t in pipeline_result.get("retrieved_tables") or []]

    retrieved_original = pipeline_result.get('retrieved_tables')
    # attach eval metadata
    pipeline_result['item_id'] = item_id
    pipeline_result['user_question'] = user_question
    pipeline_result['sql_category'] = sql_category
    pipeline_result['tests'] = item.get('tests')
    pipeline_result['gold_sql'] = item.get('gold_sql')
    pipeline_result['gold_tables'] = item.get('gold_tables')

    if not is_obf:
        pipeline_result['retrieval_recall'] = retrieval_recall(
            item.get('gold_tables'), retrieved_original)
    else:
        pipeline_result['retrieval_recall'] = retrieval_recall(
                    item.get('gold_tables'), retrieved_obf_to_real)
    pipeline_result['evaluation_model'] = evaluation_model
    pipeline_result['generator_model'] = generator_model
    pipeline_result['sys_prompt_version'] = sys_prompt_version
    pipeline_result['current_sys_prompt'] = current_sys_prompt

    # judge-score-derived quality bucket
    if pipeline_result['judge_score'] is not None:
        if pipeline_result['judge_score'] == 5:
            pipeline_result['status'] = 'perfect_sql'
        elif pipeline_result['judge_score'] >= 3:
            pipeline_result['status'] = 'acceptable_sql'
        else:
            pipeline_result['status'] = 'poor_sql'

    output_list.append(pipeline_result)
    print('-'*30)


def run_output(categories, evaluation_model, generator_model, judge_sys_prompt_version, judge_current_sys_prompt,is_obf=False):
    output_list = []

    with open(EVAL_SET_PATH, 'r', encoding='utf-8') as js:
        eval_set = json.load(js)

    if is_obf:
        # obf mode only: map retrieved obf tables back to real tables before comparing to gold_tables
        rmap = {obf:real for real,obf in json.load(open("obf/rename_map.json"))["tables"].items()}

    for category in categories:
        if category not in eval_set:
            continue

        for item_id, item in eval_set[category].items():
            build_single_output(category, item_id, item, output_list,
                                 evaluation_model, generator_model, judge_sys_prompt_version, judge_current_sys_prompt,rmap,is_obf=is_obf)

    print('\nALL DONE!')
    print_summary(output_list)
    return output_list


def _canon(v):
    if isinstance(v, (float,Decimal)): return round(float(v), 4) # numbers -> rounded float
    return str(v).strip() # everything else -> clean string

def _norm_rows(rows):
    return [tuple(_canon(c) for c in row) for row in rows]

# METRIC: EXECUTION ACCURACY
def execution_match(gold_rows, pred_rows, ordered=False):
    print('INSIDE execution_match() ')
    print(f'GOLD ROWS: ', gold_rows)
    print(f'PRED_ROWS: ', pred_rows)
    # g,p = _norm_rows(gold_rows), _norm_rows(pred_rows)
    # print('g: ', g)
    # print('p: ', p)

    # if ordered: #TOP-N + ORDER BY questions: order matters
    #     return g==p
    
    # return sorted(g) == sorted(p) # otherwise compare as an order-insensitive multiset

    g = [tuple(_canon(c) for c in r) for r in gold_rows]
    p = [tuple(_canon(c) for c in r) for r in pred_rows]

    # print('g: ', g)
    # print('p: ', p)

    if len(g) != len(p): # different row count -> never a match
        # print('GOLD LENGTH: ', len(g))
        # print('PRED LENGTH: ', len(p))
        # print('returning=> False')
        return False

    # print('ORDERED: ', ordered)
    if ordered: # order + columns matter
        if g == p: # STRICT
            # print('returning=> True')
            return True
        # return all(set(gr)<= set(pr) for gr, pr in zip(g,p)) # LOOSE positional containment

        # Not strict but Same rows, same order and predicted row contains extra columns 
        ls = []
        for gr, pr in zip(g,p):
            # print('set(gr): ', set(gr))
            # print('set(pr): ', set(pr))
            ls.append(set(gr)<= set(pr))
        # print(f'ls: ', ls)
        return all(ls)

    # Unordered case
    if sorted(g) == sorted(p): # sort both then compare. Handles Same rows, different order, unordered" → True
        # print('SORTED g: ', sorted(g))
        # print('SORTED p: ', sorted(p))
        return True
    remaining = [set(r) for r in p] # LOOSE containment, greedy match
    # print('remaining: ', remaining)

    for gs in (set(r) for r in g):
        # print('gs: ', gs)
        hit = next((ps for ps in remaining if gs<= ps), None) # For each predicted row, check if it is container in any gold row. 
        # print('hit: ',hit)
        if hit is None: # If all the predicted row is not part of 1 gold row, then hit is None and it is a mismatch
            # print('returning=> False')
            return False
        remaining.remove(hit) # Without removal, two gold rows could both match the same predicted row and wrongly pass
        # print(f'remaining: {remaining}, after removing hit: {hit} ')

    # print('returning => True')
    return True

def entity_match(gold_rows, pred_rows):
    '''Column-tolerant (entity-level) match.
    Same row count, and each gold row pairs 1-to-1 with a predicted row where ONE row's
    value-set is a subset of the other's (in EITHER direction). 
    This forgives extra OR missing decorative columns (e.g. pred omits a count, or adds an ID)
    but does NOT bridge identifier substitutions like ProductID<->Name (values don't overlap), 
    so it never over-accepts a genuinely different answer.'''

    g = _norm_rows(gold_rows)
    p = _norm_rows(pred_rows)

    if (len(g) != len(p)): # different entity count -> not a match
        return False

    remaining = [set(r) for r in p]
    for gs in (set(r) for r in g):
        # match - if the gold values contains the pred row OR the pred row contains gold values
        hit = next((ps for ps in remaining if gs <= ps or ps <= gs), None)

        if hit is None:
            return False
        remaining.remove(hit) # 1-to-1 pairing (same as strict)

    return True




def print_summary(output_list):
    '''Quick console summary: status distribution + mean retrieval recall.'''
    n = len(output_list)
    if n == 0:
        return
    
    status_counts = Counter(r['status'] for r in output_list)
    recalls = [r['retrieval_recall'] for r in output_list if r['retrieval_recall'] is not None]
    mean_recall = round(sum(recalls) / len(recalls), 3) if recalls else None

    # Execution accuracy = fraction of questions whose result matched gold
    # ex_flags = [bool(r.get('execution_match')) for r in output_list]
    # exec_acc = round(sum(ex_flags) / n, 3)
    # print(f'Execution Accuracy : {exec_acc} ({sum(ex_flags)}/{n})')

    strict = sum(bool(r.get('execution_match')) for r in output_list)
    entity = sum(bool(r.get('entity_match')) for r in output_list)
    print(f'Strict Execution Accuracy : {strict}/{n} ({strict/n:.3f})')
    print(f'Entity Execution Accuracy : {entity}/{n} ({entity/n:.3f})')

    # strict - fail but entity-pass = pure column-presentation differences (model was right)
    col_only = [r['item_id'] for r in output_list if not r.get('execution_match') and r.get('entity_match')]

    # entity-fail = genuine differences (wrong rows / different entities / value errors)
    genuine = [r['item_id'] for r in output_list if not r.get('entity_match')]
    print('Column-presentation only (strict-fail, entity-pass):', col_only)
    print('Genuine failures (entity-fail):', genuine)

    # The valuable bit: where judge and EX DISAGREE (judge fooled)
    print('\n--- judge vs execution accuracy ---')
    for r in output_list:
        judge_ok = r.get('judge_score') is not None and r['judge_score'] >= 3
        if judge_ok != bool(r.get('execution_match')):
            print(f'MISMATCH {r['item_id']}: judge_score = {r.get('judge_score')} , execution_match={bool(r.get('execution_match'))}')



    print('\n=== SUMMARY ===')
    print(f'Total questions: {n}')
    for status, count in status_counts.most_common():
        print(f'  {status}: {count} ({100*count/n:.0f}%)')
    print(f'Mean retrieval recall: {mean_recall}')


def save_to_json(data, filename):
    '''Serialize Python data to JSON and save it to a file.'''
    if not isinstance(filename, str) or not filename.endswith(".json"):
        raise ValueError("Filename must be a string ending with .json")
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        print(f"JSON saved successfully to {filename}")
    except (IOError, TypeError) as e:
        print(f"Error saving JSON: {e}")


if __name__ == "__main__":

    categories = ['Basic', 'Medium', 'Hard', 'Expert']
    JUDGE_SYS_PROMPT_VERSION = 1  # bump after modifying the judge system prompt


    is_obf = os.getenv("SCHEMA_MODE", "real") == "obf"
    output_list = run_output(categories, EVALUATION_MODEL, GENERATOR_MODEL,
                             JUDGE_SYS_PROMPT_VERSION, JUDGE_EVALUATION_SYSTEM_PROMPT,is_obf=is_obf)



    # out_name = f"runs/run_{next_run}_aw_{today_str}.json"
    out_name = f"runs/run_aw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_to_json(output_list, out_name)

    
    # Test 2
    # tests: (name, gold_rows, pred_rows, ordered, expected)
    # tests = [
        # ('exact match',                     [('A',1),('B',2)],       [('A',1),('B',2)],           False, True),   # STRICT unordered
        # ('same rows diff order, unordered', [('A',1),('B',2)],       [('B',2),('A',1)],           False, True),   # order ignored
        # ('same rows diff order, ordered',   [('A',1),('B',2)],       [('B',2),('A',1)],           True,  False),  # order enforced
        # ('extra column (h2), ordered',      [('AWC Logo Cap',8311)], [(712,'AWC Logo Cap',8311)], True,  True),   # LOOSE containment
        # ('wrong value',                     [('A',1)],               [('A',2)],                   False, False),  # genuinely wrong
        # ('different row count',             [('A',1)],               [('A',1),('B',2)],           False, False),  # length guard
        # ('float/decimal noise',             [('A',1.00001)],         [('A',Decimal("1.0"))],      False, True),   # _canon rounding
    # ]
    # for name, g, p, o, exp in tests:
    #     got = execution_match(g, p, o)
    #     print(f"[{'PASS' if got == exp else 'FAIL'}] {name:34s} got={got}  expected={exp}")
    #     print('-'*50)


    # Test 3 - Test execution accuracy
    # with open ('runs/run_aw_2026_07_25.json') as f:
    #     run_list = list(json.load(f))

    # # print(run_list[0])

    # print_summary(run_list)

    # Test - 4 (Test Entity Execution metric)
    # assert entity_match([('A',1)], [('A',)]) is True          # pred omits count
    # assert entity_match([('A',)], [(99,'A')]) is True          # pred adds an ID
    # assert entity_match([('A',1)], [('A',2)]) is False         # value differs
    # assert entity_match([('A',1)], [('A',1),('B',2)]) is False # row count  