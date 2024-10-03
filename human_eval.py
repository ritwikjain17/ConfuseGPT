import json
from utils import read_jsonl, extract_answer


# (augmentation changes answer, is answer correct)
def main():
    pred_instances = read_jsonl("gsm8k-data/augmented-by-claude-opus-gpt35.jsonl")
    with open("gsm8k-data/augmented-by-claude-opus-gpt35-heval.jsonl", "w") as f:
        for pred in pred_instances:
            print(pred['augmented'])
            print('-' * 80)
            print(pred['augmented_answer'])
            print("Correct answer", extract_answer(pred['answer']))
            res = input()
            a, b = res.split()
            pred['augmentation_changes_answer'] = a
            pred['augmented_answer_correct'] = b
            f.write(f"{json.dumps(pred)}\n")

if __name__ == "__main__":
    main()
