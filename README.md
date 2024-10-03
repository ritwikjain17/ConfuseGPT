## Authors
Anxhelo Xhebraj
Ritwik Jain

## Install dependencies
```
pip install -r requirements.txt
```

## Scripts
- `units_perturbation.py` contains scripts used for creating the perturbation
  experiment
- `augmentation.py` contains the randomization perturbation and the prompt for the Opus based augmentation
- The remaining scripts are used for evaluation and other utilities

### Example

Running augmentation on the subset of gsm8k of the paper
```
OPENAI_API_KEY=... ANTHR_API_KEY=... python augmentation.py
```

## Data

- `gsm8k-data/`
    - `train.jsonl`: initial data
    - `train-gpt35.jsonl`: gpt3.5 results for first K instances of `train.jsonl`
    - `correct-gpt35.jsonl`: subset of `train-gpt35.jsonl` comprising of questions gpt3.5 got right
    - `augmented-by-claude-opus-gpt35.jsonl`: subset of `correct-gpt35.jsonl` augmented by claude and answered by gpt 3.5
    - `augmented-by-claude-opus-gpt35-heval.jsonl`: result of human evaluation of `augmented-by-claude-opus-gpt35.jsonl`
    - `correct-gpt35-haiku.jsonl`: result of `haiku` model on the `correct-gpt35.jsonl` dataset
    - `baseline-results-gpt35.jsonl`: result of `gpt3.5` model on subset of ``augmented-by-claude-opus-gpt35.jsonl` original question perturbed by a random sentence
    - `baseline-results-haiku.jsonl`: result of `haiku` model on subset of ``augmented-by-claude-opus-gpt35.jsonl` original question perturbed by a random sentence
    - `units_augmentation`
        - `final_answers.json`: the extracted answer
        - `final_chain_of_thoughts.json`: the chain-of-thought

