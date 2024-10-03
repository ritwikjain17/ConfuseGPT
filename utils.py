import json
import re

def read_jsonl(path: str):
    with open(path) as fh:
        return [json.loads(line) for line in fh.readlines() if line]

ANS_RE = re.compile(r"#### (\-?[0-9\.\,]+)")
INVALID_ANS = "[invalid]"


def extract_answer(completion):
    matches = re.findall(r'[+-]?[\d,]*\.?\d+', completion)
    if matches:
        last_number_str = matches[-1].replace(',', '')
        return last_number_str
    else:
        return INVALID_ANS

def is_correct(model_completion, gt_example):
    gt_answer = extract_answer(gt_example["answer"])
    assert gt_answer != INVALID_ANS
    return extract_answer(model_completion) == gt_answer
