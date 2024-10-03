import os
from openai import OpenAI
import json
import re
import csv

def read_jsonl(path: str):
    with open(path) as fh:
        return [json.loads(line) for line in fh.readlines() if line]

ANS_RE = re.compile(r"#### (\-?[0-9\.\,]+)")
INVALID_ANS = "[invalid]"

"""Index: 338
Extracted Final Part:  <<20/10=2>>2 miles per gallon.
#### 2
Found Units: mile, gallon
Number of Units Found: 2

Index: 4504
Extracted Final Part: 1>>1 remaining hour when the car can drive.
That means during 13 hours the car will be able to drive 80 + 8 = 88 miles.
#### 88
Found Units: mile, hour
Number of Units Found: 2

Index: 2512
Extracted Final Part: 40.00>>40.00
This recipe makes 4 quarts and the total price of the vegetables was $40.00 so each quart costs 40/4 = $10.00
#### 10
Found Units: $, quart
Number of Units Found: 2

Index: 601
Extracted Final Part: 30>>30 feet per second.
To close on a distance of 200 feet, it would take the cheetah 210/30=7 seconds to catch the gazelle.
#### 7
Found Units: feet, second
Number of Units Found: 2

Index: 7077
Extracted Final Part: 24>>24 inches
12 inches is 1 foot and they have 24 inches of snow so they have 24/12 = 2 feet of snow
#### 2
Found Units: inch, feet, foot
Number of Units Found: 3

Index: 3042
Extracted Final Part:  <<693/11=63>>63 miles per hour.
#### 63
Found Units: mile, hour, miles per hour
Number of Units Found: 3

Index: 7330
Extracted Final Part: 6>>6 feet of sand.
Digging at a rate of 2 feet per hour, Pirate Rick could uncover his treasure in 6/2=3 hours.
#### 3
Found Units: feet, hour
Number of Units Found: 2

Index: 1571
Extracted Final Part:  <<180*120=21600>>21600 square inches. Since each tile is 1 square inch, this is also the number of tiles she needs.
#### 21600
Found Units: inch, square inch
Number of Units Found: 2

Index: 1885
Extracted Final Part:  2800 feet deep.
To dig a hole that is 400 feet less than twice as deep as his father's hole working at a rate of 4 feet per hour, Michael will have to work for 2800/4 = 700 hours.
#### 700
Found Units: feet, hour
Number of Units Found: 2

Index: 1983
Extracted Final Part: 27>>27
Then divide the cost of the meat by the total grocery bill and multiply by 100% to express the answer as a percentage: $9 / $27 * 100% = 33.333%, which rounds down to 33%
#### 33
Found Units: $, cent
Number of Units Found: 2

Index: 4062
Extracted Final Part: 2160>>2160/month
Then divide the cost of the concert by Jenna's monthly earnings and multiply by 100% to express the answer as a percentage: $216 / $2160 * 100% = 10%
#### 10
Found Units: month, $, cent
Number of Units Found: 3

"""

def extract_answer(completion):
    """
    match = ANS_RE.search(completion)
    if match:
        match_str = match.group(1).strip()
        match_str = match_str.replace(",", "")
        return match_str
    else:
        return INVALID_ANS"""
    matches = re.findall(r'[+-]?[\d,]*\.?\d+', completion)
    if matches:
        last_number_str = matches[-1].replace(',', '')
        return last_number_str
    else:
        return INVALID_ANS

#haircuts, eggsm balls, colors, males, females, pages, pizza, votes, socks, marbels, flowers, books, players, fish, caps, stairs, candies, age (n times as old), stickers, doughbuts, apples, boxes of biscuits, seeds, notebooks, pen, books, bars (like of chocolate), workers, marks.score in exams, apples

#unit_list = [meter, meters, centimeters, centimeter, kilometers, kilometer, inches, inch, feet, foot, yard, yards, mile, miles, gram, grams, kilograms, kilogram, pounds, ounces, pound, ounce, liter, liters, milliliter, milliliters, gallons, gallon, second, seconds, minute, minutes, hour, hours, day, days, week, weeks, month, months, year, years, dollar, dollars, $, cent, cents, kWh, kilowatt-hours, watt, watts, kilobyte, kilobytes, bytes, byte, megabytes, megabyte, gigabytes, gigabyte, quart, quarts, square meters, square meter, square centimeter, square centimeters, square inch, square inches, square feet, square foot, acres, acre, hectares, hectare, GB, cm, km, hr, ml, mL, oz, ft, euro, euros, KB, MB]
#carefull about confusing day of the week like wednesday, thursday etc. with day during regex)
def is_correct(model_completion, gt_example):
    gt_answer = extract_answer(gt_example["answer"])
    assert gt_answer != INVALID_ANS
    return extract_answer(model_completion) == gt_answer

def count_dollar_signs(text):
    count = 0
    for char in text:
        if char == '$':
            count += 1
    return count

def count_unit_occurrences(instances, unit_regex):
    questions_with_unit = 0
    total_occurrences = 0
    total_3_occurences = 0
    for instance in instances:
        question = instance['question']
        matches = unit_regex.findall(question)
        match_count = len(matches)
        if match_count > 0:
            questions_with_unit += 1
            total_occurrences += match_count
            if match_count >= 3:
                total_3_occurences += 1
    return questions_with_unit, total_occurrences, total_3_occurences

def find_questions_with_multiple_occurrences(instances, unit_regex, min_occurrences=3, max_results=100):
    indices = []
    for index, instance in enumerate(instances):
        question = instance['question']
        matches = unit_regex.findall(question)
        if len(matches) >= min_occurrences:
            indices.append(index)
        if len(indices) >= max_results:
            break
    return indices

def load_excluded_indices(file_path):
    with open(file_path, 'r') as file:
        return {int(line.strip()) for line in file}

"""def count_matching_questions(instances, patterns, excluded_indices):
    count = 0
    for index, instance in enumerate(instances):
        if index in excluded_indices:
            continue
        question = instance['question']
        matches = sum(1 for pattern in patterns.values() if pattern.search(question))
        if matches >= 2:
            count += 1
    return count"""

def count_matching_questions(instances, patterns, excluded_indices, output_file_path):
    count = 0
    qualifying_indices = []
    for index, instance in enumerate(instances):
        if index in excluded_indices:
            continue
        question = instance['question']
        matches = {key: len(pattern.findall(question)) for key, pattern in patterns.items()}
        qualified_patterns = sum(1 for occ in matches.values() if occ >= 2)
        qualified_patterns_another = sum(1 for occ in matches.values() if occ >= 1)
        if qualified_patterns_another >= 3:
            count += 1
            qualifying_indices.append(index)

    with open(output_file_path, 'w') as file:
        for index in qualifying_indices:
            file.write(f"{index}\n")

    return count

def count_mixed_unit_questions(instances, patterns, excluded_indices, output_file_path):
    count = 0
    qualifying_indices = []
    for index, instance in enumerate(instances):
        if index in excluded_indices:
            continue
        question = instance['question']
        matches = {key: len(pattern.findall(question)) for key, pattern in patterns.items()}
        qualified_patterns = sum(1 for occ in matches.values() if occ >= 2)
        qualified_patterns_another = sum(1 for occ in matches.values() if occ >= 1)
        if qualified_patterns >= 1 and qualified_patterns_another == 2:
            count += 1
            qualifying_indices.append(index)

    with open(output_file_path, 'w') as file:
        for index in qualifying_indices:
            file.write(f"{index}\n")

    return count


def analyze_questions(instances, patterns, indices):
    analysis_results = {}
    for index in indices:
        if index < len(instances):
            question = instances[index]['question']
            occurrences = {key: len(pattern.findall(question)) for key, pattern in patterns.items()}
            filtered_occurrences = {key: count for key, count in occurrences.items() if count > 0}
            if len(filtered_occurrences) == 2 and any(count >= 2 for count in filtered_occurrences.values()):
                analysis_results[index] = filtered_occurrences

    return analysis_results

def perturb_question(question, pattern, new_unit, ratio, occurrences):
    def replacement(match):
        number = match.group(1).replace(',', '').strip()
        return f"{float(number) * ratio} {new_unit}"

    all_matches = list(re.finditer(pattern, question))
    skip_indices = set()
    if len(all_matches) >= 4:
        skip_indices = {1, 2}
    elif len(all_matches) == 3:
        skip_indices = {1}
    elif len(all_matches) == 2:
        skip_indices = {1}

    modified_question = question
    for i, match in enumerate(all_matches):
        if i not in skip_indices:
            modified_question = modified_question.replace(match.group(0), replacement(match), 1)
    return modified_question

def extract_final_unit(answer, unit_list_1, index):
    positions = [pos for pos, char in enumerate(answer) if char == '=']
    if len(positions) < 2:
        return "No valid part found", [], 0 

    second_last_equal_pos = positions[-2]
    final_part = answer[second_last_equal_pos + 1:]

    found_units = [unit for unit in unit_list_1 if unit in final_part]
    count_units = len(found_units)
    """found_units = []
    for unit in unit_list_1:
        pattern = fr"\b{re.escape(unit)}\b"  # Escaping unit in case it contains regex special characters
        if re.search(pattern, final_part, re.IGNORECASE):
            found_units.append(unit)

    count_units = len(found_units)"""
    """found_units = []
    for unit in unit_list_1:
        # Check if the unit is present in the final part
        if unit in final_part:
            # Check if the plural form of the unit is also present
            plural_unit = unit + 's'
            if plural_unit in final_part:
                continue  # Skip adding the unit if its plural form is present
            found_units.append(unit)
    count_units = len(found_units)"""
    with open('output.txt', 'a') as f:
        f.write("Index: " + str(index) +  "\n")
        f.write("Extracted Final Part: " + final_part + "\n")
        f.write("Found Units: " + ", ".join(found_units) + "\n")
        f.write("Number of Units Found: " + str(count_units) + "\n")
        f.write("----------------------------------------\n")

    return final_part, found_units, count_units

instances = read_jsonl("gsm8k-data/checking_train.jsonl")
instance = instances[10]
question = instance['question']
answer = instance['answer']
#litre, dollar, gram, second, hour, cents, watts, euros, hectares
units_patterns = {
    "meter": r"(\d+(\.\d+)?)\s*(meters?)",
    "centimeter": r"(\d+(\.\d+)?)\s*(centimeters?|cm)",
    "kilometer": r"(\d+(\.\d+)?)\s*(kilometers?|km)",
    "inch": r"(\d+(\.\d+)?)\s*(inches|inch)",
    "feet": r"(\d+(\.\d+)?)\s*(feet|foot|ft)",
    "yard": r"(\d+(\.\d+)?)\s*(yards?|yd)",
    "mile": r"(\d+(\.\d+)?)\s*(miles?)",
    "kilogram": r"(\d+(\.\d+)?)\s*(kilograms?|kg)",
    "pound": r"(\d+(\.\d+)?)\s*(pounds?|lbs?|lb)",
    "ounce": r"(\d+(\.\d+)?)\s*(ounces?|oz)",
    "milliliter": r"(\d+(\.\d+)?)\s*(milliliters?|ml)",
    "gallon": r"(\d+(\.\d+)?)\s*(gallons?|gal)",
    "minute": r"(\d+(\.\d+)?)\s*(minutes?|min)",
    "kilobyte": r"(\d+(\.\d+)?)\s*(kilobytes?|kb)",
    "megabyte": r"(\d+(\.\d+)?)\s*(megabytes?|mb)",
    "gigabyte": r"(\d+(\.\d+)?)\s*(gigabytes?|gb)",
    "quart": r"(\d+(\.\d+)?)\s*(quarts?|qt)",
    "square meter": r"(\d+(\.\d+)?)\s*(square meters?|sq m)",
    "square centimeter": r"(\d+(\.\d+)?)\s*(square centimeters?|sq cm)",
    "square inch": r"(\d+(\.\d+)?)\s*(square inches|sq in)",
    "square feet": r"(\d+(\.\d+)?)\s*(square feet|sq ft)",
    "square foot": r"(\d+(\.\d+)?)\s*(square foot|sq ft)",
    "acre": r"(\d+(\.\d+)?)\s*(acres?|acre)",
    "liter": r"(\d+(\.\d+)?)\s*(liters?)",
    "dollar": r"(\d+(\.\d+)?)\s*(dollars?)",
    "gram": r"(\d+(\.\d+)?)\s*(grams?)",
    "second": r"(\d+(\.\d+)?)\s*(seconds?)",
    "hour": r"(\d+(\.\d+)?)\s*(hours?)",
    "cent": r"(\d+(\.\d+)?)\s*(cents?)",
    "watt": r"(\d+(\.\d+)?)\s*(watts?)",
    "euro": r"(\d+(\.\d+)?)\s*(euros?)",
    "hectare": r"(\d+(\.\d+)?)\s*(hectares?)",
    "miles_per_hour_pattern": r"(\d+(\.\d+)?)\s*(miles per hour|mile per hour|mph)",
    "kilometers_per_hour_pattern": r"(\d+(\.\d+)?)\s*(kilometers per hour|kilometer per hour|km\/?h|kmph|km\/hr)",
    "meters_per_second_pattern": r"(\d+(\.\d+)?)\s*(meters per second|meter per second|m\/s)",
    "dollar_symbol_pattern": r"\$([\s]*[\d,]+(\.\d{2})?)"
}

final_units_patterns = ["$", "pound", "mile", "minute", "hour"]

unit_list_1 = ["meter", "centimeter", "kilometer", "inch", "feet", "foot",
             "yard", "mile", "gram", "kilogram", "pound", 
             "ounce", "liter", "milliliter", "gallon", "second", 
             "minute", "hour", "day", "week", "month", "year", 
             "dollar", "$", "cent", "kWh", "kilowatt-hours", "watt", "kilobyte", 
             "byte", "megabyte", "gigabyte", "quart", 
             "square meter", "square centimeter", "square inch", "square feet", 
             "square foot", "acre", "hectare", "cm", "km", "ml", "mL", 
             "euro", "oz", "km/hr", "m/s", "kilometers per hour", "miles per hour", "meters per second", "mph"]

"""unit_list = ["meter", "centimeter", "kilometer", "inch", "feet",
             "yard", "mile", "gram", "kilogram", "pound", 
             "ounce", "liter", "milliliter", "gallons", "gallon", "second", "seconds", 
             "minute", "minutes", "hour", "hours"
             "dollar", "dollars", "$", "cent", "cents", "watt", "watts", "kilobyte", "kilobytes", 
             "megabytes", "megabyte", "gigabytes", "gigabyte", "quart", "quarts", "square meters", 
             "square meter", "square centimeter", "square centimeters", "square inch", "square inches", "square feet", 
             "square foot", "acres", "acre", "hectares", "hectare", "cm", "km", "ml", "mL", "euros"]"""


unit_conversion_mapping = {
    "dollar_symbol_pattern": {"new_unit": "euros", "ratio": 2},
    "inch": {"new_unit": "centimeter", "ratio": 0.5},
    "gallon": {"new_unit": "liter", "ratio": 0.5},
    "ounce": {"new_unit": "gram", "ratio": 3},
    "feet": {"new_unit": "yard", "ratio": 0.5},
    "hour": {"new_unit": "yolo", "ratio": 3},
    "mile": {"new_unit": "kilometer", "ratio": 0.5},
    "minute": {"new_unit": "jiffy", "ratio": 3}
}

#3363, 3617 for euro are false positives so only use euros in the unit_list

#heirarchy 

#construction logic: if the end of the answer contains one of the above units then append the sentence "in ____ units" else dont append anything.


#kwh only 2 lines contain kwh, 510 and 2683
# for ml  check if there are any other alphabets from a - z to its left or right, lines 1672, 1808, 1877, 1914, 2060, 2473, 4366, 4832, 5125

# for oz: lines 1239, 2381, 2397, 2853, 3389, 3518, 3565, 3745, 4015, 4054, 4114, 4152, 4600, 4763, 5340, 5578, 5988, 6307, 6701, 6714,  6876, 7280
# false positives for oz because of words like dozen, frozen, mozzarella etc.

#false positive for km: line 729, 5657 (for example bookmark)

#KB can be removed as no instances of KB in the sense of KiloBytes. Similarly, ft hasnt really been used as feet.
unit_list = ["$"]

#mph false positive at 1928, 2716

#no false positives for km/hr and m/s so include that.

#no false positives for kilometers per hour and for miles per hour.

#only 1 appearance of meters per second in 3752

#2125 questions contain $
#15 lines contain km



"""lines_for_km/hr = [1]
lines_for_m/s = []
lines_for_mph = []
lines_for_kilometers_per_hour = []
lines_for_miles_per_hour = []
lines_for_meters_per_second = [3752]"""


# Count how many questions have at least one of the units
count_with_units = 0

#question_text ="George had $100. He bought a shirt for $24 and he also bought a pair of socks. Then he had $65 left. How much is a pair of socks?"

#if any(unit in question_text for unit in unit_list):
        #count_with_units += 1
"""num = 0
for instance in instances:
    question_text = instance['question'].lower()  # Assuming each instance has a 'question' key and text is stored there
    if any(unit in question_text for unit in unit_list):
        count_with_units += 1
        if(count_dollar_signs(question_text) > 2):
            num += 1
            if(num <= 10):
                print(question_text)

print(f"Number of questions with at least one unit: {count_with_units}")
print(f"Num: {num}")
print(count_with_units - num)"""

results = {}

for unit, pattern in units_patterns.items():
    unit_regex = re.compile(pattern, re.IGNORECASE)
    questions_with_unit, total_occurrences, total_3_occurences = count_unit_occurrences(instances, unit_regex)
    results[unit] = {
        "Questions with at least one occurrence": questions_with_unit,
        "Total occurrences in all questions": total_occurrences,
        "Three or more": total_3_occurences
    }

for unit, counts in results.items():
    print(f"{unit.title()} - Questions with at least one occurrence: {counts['Questions with at least one occurrence']}, Total occurrences: {counts['Total occurrences in all questions']}, Questions with 3 or more occurences: {counts['Three or more']}")

dollar_symbol_pattern = r"\$([\s]*[\d,]+(\.\d{2})?)"
compiled_pattern = re.compile(dollar_symbol_pattern)

indices_with_multiple_dollars = find_questions_with_multiple_occurrences(instances, compiled_pattern)

with open("indices_with_multiple_dollars.txt", "w") as file:
    for index in indices_with_multiple_dollars:
        file.write(f"{index}\n")

excluded_indices = load_excluded_indices("indices_with_multiple_dollars.txt")

regex_patterns_others = {
    "pound": re.compile(r"(\d+(\.\d+)?)\s*(pounds?|lbs?|lb)"),
    "minute": re.compile(r"(\d+(\.\d+)?)\s*(minutes?|min)"),
    "mile": re.compile(r"(\d+(\.\d+)?)\s*(miles?)"),
    "hour": re.compile(r"(\d+(\.\d+)?)\s*(hours?)"),
    "feet": re.compile(r"(\d+(\.\d+)?)\s*(feet|foot|ft)"),
    "ounce": re.compile(r"(\d+(\.\d+)?)\s*(ounces?|oz)"),
    "gallon": re.compile(r"(\d+(\.\d+)?)\s*(gallons?|gal)"),
    "inch": re.compile(r"(\d+(\.\d+)?)\s*(inches|inch)"),
    "dollar_symbol_pattern": re.compile(r"\$([\s]*[\d,]+(\.\d{2})?)")
}

output_file_path = "indices_with_more_than_four_regex.txt"

matching_question_count = count_matching_questions(instances, regex_patterns_others, excluded_indices, output_file_path)

print(f"Number of questions (excluding those in the file) with at least 3 of the specified units: {matching_question_count}")

final_excluded_indices = excluded_indices.union(load_excluded_indices("indices_with_more_than_four_regex.txt"))
#print(final_excluded_indices)

final_question_index_list_without_dollar_path = "mixed_unit_indices.txt"

mixed_unit_question_count = count_mixed_unit_questions(instances, regex_patterns_others, final_excluded_indices, final_question_index_list_without_dollar_path)

print(f"Number of questions with mixed units and atleast 1 unit appearing atleast twice: {mixed_unit_question_count}")

indices_mixed = load_excluded_indices("mixed_unit_indices.txt")

analysis_results = analyze_questions(instances, regex_patterns_others, indices_mixed)

with open('analysis_results.json', 'w') as f:
    json.dump(analysis_results, f, indent=4)

print(f"Results have been stored in 'analysis_results.json'")


modified_questions = []
initial_original_questions = []
for index, patterns in analysis_results.items():
    index = int(index)
    appending_string = f"Assume "
    if index < len(instances):
        question = instances[index]['question']
        answer_text = extract_answer(instances[index]['answer'])
        initial_original_questions.append({"question": question, "answer": answer_text})
        count_keeper = 0
        for unit, count in patterns.items():
            if unit in unit_conversion_mapping:
                question = perturb_question(question, regex_patterns_others[unit],
                                            unit_conversion_mapping[unit]["new_unit"],
                                            unit_conversion_mapping[unit]["ratio"],
                                            count)
                if unit == "dollar_symbol_pattern":
                    appending_string += f"1 $ equals {unit_conversion_mapping[unit]['ratio']} {unit_conversion_mapping[unit]['new_unit']}"
                else:
                    appending_string += "1 "
                    appending_string += unit
                    appending_string += f" equals {unit_conversion_mapping[unit]['ratio']} {unit_conversion_mapping[unit]['new_unit']}"

                if count_keeper == 0:
                    appending_string += " and "
                else :
                    appending_string += ". "
                
                count_keeper += 1
        final_part, found_units, count_units = extract_final_unit(instances[index]['answer'], unit_list_1, index)
        #print("Extracted Final Part:", final_part)
        #print("Found Units:", found_units)
        #print("Number of Units Found:", count_units)

        question = appending_string + question
        end_str = ""

        if count_units != 0:
            if index == 338:
                end_str = "Give the answer in miles per gallon."
            elif index == 4504:
                end_str = "Give the answer in miles."
            elif index == 2512:
                end_str = "Give the answer in dollars."
            elif index == 601:
                end_str = "Give the answer in seconds."
            elif index == 7077:
                end_str = "Give the answer in feet."
            elif index == 3042:
                end_str = "Give the answer in miles per hour."
            elif index == 7330:
                end_str = "Give the answer in hours."
            elif index == 1572:
                end_str = "Give the answer in square inches."
            elif index == 1885:
                end_str = "Give the answer in hours."
            elif index == 1983:
                end_str = ""
            elif index == 4062:
                end_str = ""
            else:
                first_pos = float('inf')
                first_unit = None
                for unit in found_units:
                    pos = final_part.find(unit)
                    if pos != -1 and pos < first_pos:
                        first_pos = pos
                        first_unit = unit
                if first_unit == "$":
                    end_str = "Give the answer in dollars."
                elif first_unit == "feet":
                    end_str = "Give the answer in feet."
                else:
                    end_str = "Give the answer in " + first_unit + "s."

        question = question + " " + end_str   
        modified_questions.append({"question": question, "answer": answer_text})



with open('modified_questions.json', 'w') as file:
    json.dump(modified_questions, file, indent=4)

with open('initial_original_questions.json', 'w') as file:
    json.dump(initial_original_questions, file, indent=4)


final_answers_gpt = []

with open('modified_questions.json', 'r') as file:
        data_gpt_final = json.load(file)

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

"""
question_input = "Assume 1 mile equals 0.5 kilometer and 1 $ equals 2 euros. The cost of filling a car fuel tank is 90.0 euros and this can take you 250.0 kilometer before refilling. Mallory was going to her grammy's house, 2000 miles away. If she used 3/5 times as much money on food as she spent on filling the car fuel tank for the whole journey, calculate the total amount of money she used. Give the answer in dollars."

chat_completion = client.chat.completions.create(
    seed=42,
    messages=[
        {
            "role": "system",
            "content":
            "You are a helpful assistant for reasoning about math problems."
            "You are allowed to freely generate any text that is relevant to the solution of the problem."
            "At the end of the response return the final result X as `#### X` without units."
            "For example if the question is \"How much is $2 + $2?\" the reply should be \"$2 + $2 = $4. #### 4\""
        },
        {
            "role": "user",
            "content": question_input
        }
    ],
    model="gpt-3.5-turbo",
)
response = chat_completion.choices[0].message.content
final_answer = extract_answer(response)
final_answers_gpt.append({"answer": final_answer})

print(response)
print(final_answer)"""


final_answers_chain_of_thought = []
#for idx, patterns in analysis_results.items():
for item in data_gpt_final:
    #idx = int(idx)
    #question_input = instances[idx]['question']
    question_input = item["question"]
    chat_completion = client.chat.completions.create(
        seed=42,
        messages=[
            {
                "role": "system",
                "content":
                "You are a helpful assistant for reasoning about math problems."
                "You are allowed to freely generate any text that is relevant to the solution of the problem."
                "At the end of the response return the final result X as `#### X` without units."
                "For example if the question is \"How much is $2 + $2?\" the reply should be \"$2 + $2 = $4. #### 4\""
            },
            {
                "role": "user",
                "content": question_input
            }
        ],
        model="gpt-3.5-turbo",
    )
    response = chat_completion.choices[0].message.content
    final_answers_chain_of_thought.append({"answer": response})
    final_answer = extract_answer(response)
    final_answers_gpt.append({"answer": final_answer})

        

with open('Final_answers.json', 'w') as outfile:
        json.dump(final_answers_gpt, outfile, indent=4)

with open('Final_chain_of_thoughts.json', 'w') as outfile:
        json.dump(final_answers_chain_of_thought, outfile, indent=4)


"""
with open('Final_answers_train_set.json', 'w') as outfile:
        json.dump(final_answers_gpt, outfile, indent=4)
"""


with open('Final_answers_train_set.json', 'r') as file:
        train_ans_file = json.load(file)

with open('Final_answers.json', 'r') as file:
        perturb_ans_file = json.load(file)

total_correct_train = 0
total_correct_perturb = 0
total_question_count = 0
index = 0
for item_val in data_gpt_final:
    total_question_count += 1
    answer = item_val["answer"]
    answer = answer.replace(',', '')
    correct_answer = float(answer)
    train_answer = float(train_ans_file[index]["answer"])
    perturb_answer = float(perturb_ans_file[index]["answer"])
    if train_answer == correct_answer:
        total_correct_train += 1
    if perturb_answer == correct_answer:
        total_correct_perturb += 1
    index += 1

print("Total correct answers for perturbed dataset: ", total_correct_perturb)
print("Total correct answers on original dataset: ", total_correct_train)
print("Total no of questions ", total_question_count)

perturb_accuracy = float(total_correct_perturb/total_question_count)
original_accuracy = float(total_correct_train/total_question_count)
print("accuracy on pertured dataset: ", perturb_accuracy)
print("accuracy on original dataset: ", original_accuracy)
    


"""
correct_answers = []
for item in data_gpt_final:
    answer = item["answer"]
    answer = answer.replace(',', '')
    correct_answer = float(answer)

    try:
        converted_float = float(input_string)
        print(f"The string has been successfully converted to float: {converted_float}")
    except ValueError:
        print("The provided string is not a valid float.")"""


"""
print(question)
print("-"*100)
print("## Correct answer")
expected_answer = extract_answer(answer)
print(expected_answer)
print(f"## Response 1/{len(chat_completion.choices)}")
print(response)
response_value = extract_answer(response)
print(f"## Correct = {expected_answer == response_value}")
pass"""
