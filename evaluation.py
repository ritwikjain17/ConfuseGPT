import os
import anthropic
from openai import OpenAI

from utils import extract_answer, is_correct, read_jsonl
import json

system = {
    "role": "system",
    "content": "You are a helpful assistant for reasoning about math problems."
    "You are allowed to freely generate any text that is relevant to the solution of the problem."
    "At the end of the response return the final result X as `#### X` without units."
    'For example if the question is "How much is $2 + $2?" the reply should be "$2 + $2 = $4. #### 4"',
}

oai = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

claude = anthropic.Anthropic(api_key=os.environ.get("ANTHR_API_KEY"))


def haiku(question):
    message = claude.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=2048,
        system=system["content"],
        messages=[
            {
                "role": "user",
                "content": f"{question}",
            },
        ],
    )
    return message.content[0].text

def chgpt3_5(question):
    chat_completion = oai.chat.completions.create(
        seed=42,
        messages=[system, {"role": "user", "content": question}],
        model="gpt-3.5-turbo",
    )
    return chat_completion.choices[0].message.content


def accuracy():
    tr_instances = read_jsonl("gsm8k-data/augmented-by-claude-opus-gpt35.jsonl")
    pred_instances = read_jsonl("gsm8k-data/baseline-results-gpt35.jsonl")

    n_correct = 0
    with open('gsm8k-data/correct-gpt35-correct-haiku.jsonl', 'a') as f:
        for pred, gt_example in zip(pred_instances, tr_instances):
            # if bool(int(gt_example['augmentation_changes_answer'])):
            #     gt = extract_answer(gt_example['augmented_answer'])
            # else:
            #     gt = extract_answer(gt_example['answer'])
            if extract_answer(gt_example['answer']) == extract_answer(pred['answer']):
                # f.write(f"{json.dumps(pred)}\n")
                n_correct += 1

    print(n_correct / min(len(pred_instances), len(tr_instances)))

def strip_augm_delimiter(s):
    return s.replace("+|", "").replace("|+", "")


def main():
    instances = read_jsonl("gsm8k-data/augmented-by-claude-opus-gpt35-heval.jsonl")
    with open("gsm8k-data/baseline-results-gpt35.jsonl", "w") as f:
        for x in instances:
            q = x['question']
            idx = q.find('.')
            q = q[:idx + 1] + " The cat sat on the mat. " + q[idx + 1:] if idx > 0 else " The cat sat on the mat. " + q

            answer = chgpt3_5(strip_augm_delimiter(q))

            line = json.dumps({"question": q, "answer": answer})
            f.write(f"{line}\n")


if __name__ == '__main__':
    # main()
    accuracy()
