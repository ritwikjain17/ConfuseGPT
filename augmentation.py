import json
from openai import OpenAI
import os
import anthropic

from utils import is_correct, read_jsonl
from evaluation import chgpt3_5

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

examples = [
    {
        "role": "user",
        "content": "Q: John buys 1.5 ounces of silver and twice as much gold.  The silver costs $20 per ounce.  The gold is 50 times more expensive per ounce.  How much does he spend on everything?",
    },
    {
        "role": "assistant",
        "content": "John buys 1.5 ounces of silver and twice as much gold.  The silver costs $20 per ounce.  The gold is 50 times more expensive per ounce. +|Bronze costs 3 times more than gold.|+ How much does he spend on everything?",
    },
    {
        "role": "user",
        "content": "Q: Jason joined the military when he turned 18.  It took him 8 years to raise to the rank of chief.  Then 25% longer than that to go from chief to master chief.  He then spent 10 years more in the military before retiring.  How old was he when he retired?",
    },
    {
        "role": "assistant",
        "content": "Jason joined the military when he turned 18.  It took him 8 years to raise to the rank of chief.  Then 25% longer than that to go from chief to master chief. +|Half the time as master chief he also loved fishing.|+  He then spent 10 years more in the military before retiring.  How old was he when he retired?",
    },
    # {
    #     "role": "user",
    #     "content": "Q: Noel bakes 4 dozen donuts for his class. There are 30 students in class, but only 80% like donuts. How many donuts does each student who likes donuts get to eat?",
    # },
    # {
    #     "role": "assistant",
    #     "content": "Noel bakes 4 dozen donuts for his class. There are 30 students in class, but only 80% like donuts. +|There are as many teachers as half of the students.|+ How many donuts does each student who likes donuts get to eat?",
    # },
    {
        "role": "user",
        "content": "Q: Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether in April and May?\nBAD EXAMPLE: +|She also gave away 10 clips as free samples in June.|+ Giving away can be considered selling",
    },
    {
        "role": "assistant",
        "content": "Q: Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. +|Additionally she sold 5 pens.|+ How many clips did Natalia sell altogether in April and May?",
    },
    {
        "role": "user",
        "content": "Q: John buys 2 shirts. The first shirt costs $6 more than the second shirt. If the first shirt costs $15, how much, in dollars, did the shirts cost in total?",
    },
    {
        "role": "assistant",
        "content": "John buys 2 shirts. The first shirt costs $6 more than the second shirt. If the first shirt costs $15, how much, in dollars, did the shirts cost in total +|, knowing that a pair of jeans costs half the total of shirts|+ ?",
    },
    {
        "role": "user",
        "content": "Q: Amy biked 12 miles yesterday. If she biked 3 miles less than twice as far as yesterday, how many miles did she bike in total in the two days?",
    },
    {
        "role": "assistant",
        "content": "Amy biked 12 miles yesterday. If she biked 3 miles less than twice as far as yesterday, how many miles did she bike in total in the two days +|considering she walks 5 miles both days for her warm-up|+?",
    },
    {
        "role": "user",
        "content": "Q: Jack has been driving for the past 9 years. He drives 37,000 miles every four months. How many miles has Jack driven since he started driving?\nBAD EXAMPLE: +|and rides his motorcycle for 5000 miles every six months|+ riding can be interpreted as driving.",
    },
    {
        "role": "assistant",
        "content": "Jack has been driving for the past 9 years. He drives 37,000 miles every four months. +|He also flies twice a year across the country, each flight covering about 3000 miles.|+ How many miles has Jack driven since he started driving?",
    },
]

system_content = (
    "You are a helpful assistant for designing tricky math question problems. "
    "Propose changes to the given question by adding other numbers that might seem relevant but do not affect the answer. "
    "Only add content in enclosed in +|...|+ and do not change the rest of the problem. "
)


claude = anthropic.Anthropic(
    api_key=os.environ.get("ANTHR_API_KEY"),
)


def claude_augmentation(question):
    message = claude.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=2048,
        system=system_content,
        messages=[
            *examples,
            {
                "role": "user",
                "content": f"Q: {question}",
            },
        ],
    )
    return message.content[0].text


def create_augmentation(question):
    return (
        client.chat.completions.create(
            seed=42,
            messages=[
                {
                    "role": "system",
                    "content": system_content,
                },
                *examples,
                {
                    "role": "user",
                    "content": f"Q: {question}",
                },
            ],
            model="gpt-4",
        )
        .choices[0]
        .message.content
    )


def random_augmentation(q: str):
    idx = q.find(".")
    q = (
        q[: idx + 1] + " The cat sat on the mat. " + q[idx + 1 :]
        if idx > 0
        else " The cat sat on the mat. " + q
    )
    return q


def strip_augm_delimiter(s):
    return s.replace("+|", "").replace("|+", "")


def main():
    pred_instances = read_jsonl("gsm8k-data/correct-gpt35.jsonl")

    with open("gsm8k-data/augmented-by-claude-opus-gpt35.jsonl", "a") as f:
        for pred in pred_instances[428:]:
            augmented = claude_augmentation(pred["question"])
            result = chgpt3_5(strip_augm_delimiter(augmented))
            correct = is_correct(result, pred)
            pred["augmented"] = augmented
            pred["augmented_answer"] = result
            pred["augmented_is_correct"] = correct
            f.write(f"{json.dumps(pred)}\n")


main()
