# {'AtLocation','CapableOf','Causes','CausesDesire','CreatedBy','DefinedAs','Desires','HasA','HasFirstSubevent','HasPrerequisite','HasProperty','HasSubevent','IsA','MadeOf','MotivatedByGoal','NotCapableOf','NotHasProperty','NotIsA','PartOf','ReceivesAction','RelatedTo','UsedFor'}

import os, sys, json, csv
from tqdm import tqdm
import pandas as pd
from pathlib import Path
import numpy as np
import networkx  as nx
import math
from ast import literal_eval
sys.path.append('./')
from utils.question_templates import question_templates
from utils.gpt_3_utils import q_and_a_gpt3, number_to_string, extract_array_from_text, generate_find_object_question_from_triple, generate_find_subject_question_from_triple
from calculate_metrics import calculate_hits_at_n
# from utils.vg_utils import get_concepts_and_predicates
# from utils.gephi_utils import gpt3_answers_to_gexf
    
def generate_questions(out_path, conceptnet_data, n):
    out_file_name = f'questions_{n}_returned_concepts.csv'
    out_file_path = f'{out_path}/{out_file_name}'
    if os.path.isfile(out_file_path):
        csv_df = pd.read_csv(out_file_path)
    else:
        csv_df = pd.DataFrame()
    for index, row in tqdm(conceptnet_data.iterrows(), desc='Generating questions for GPT-3: '):
        subj, pred, obj = row.subj, row.pred, row.obj
        if not ((csv_df['subject'] == subj) & (csv_df['predicate'] == pred) & (csv_df['object'] == obj)).any():
            find_subject_question = generate_find_subject_question_from_triple(subj, pred, obj)
            find_object_question = generate_find_object_question_from_triple(subj, pred, obj)
            row_dict = {'subject': subj,
                        'predicate': pred,
                        'object': obj,
                        'find_subj_question': find_subject_question,
                        'find_obj_question': find_object_question, 
                        'find_subj_text_answer': '', 'find_subj_answers': [], 'find_subj_probabilities': [], 'find_obj_text_answer': '', 'find_obj_answers': [], 'find_obj_probabilities': []}
            csv_df = csv_df.append(row_dict, ignore_index = True)
            csv_df.to_csv(out_file_path, index=False)
    print(f'*** Questions saved at: {out_file_path}')
    return out_file_path

def fix_bad_question_generations(out_path, n, predicates=[], specific_predicates=False):
    out_file_name = f'questions_{n}_returned_concepts.csv'
    out_file_path = f'{out_path}/{out_file_name}'
    csv_df = pd.read_csv(out_file_path)
    for index, row in tqdm(csv_df.iterrows(), desc='Generating questions for GPT-3: '):
        subj, pred, obj = row.subject, row.predicate, row.object
        find_subject_question = row.find_subj_question
        find_object_question = row.find_obj_question
        # Checking if specific predicates are changed
        if specific_predicates:
            if pred not in predicates:
                continue
        # Pattern fixes
        if pred == 'AtLocation':
            find_subject_question = f'What is at {obj}?'
        elif pred == 'HasSubevent':
            find_subject_question = f'In which event does {obj} happen?'
        elif pred == 'MadeOf':
            find_subject_question = f'What can you make with {obj}?'
        elif pred == 'UsedFor':
            find_subject_question = f'What do you need to {obj}?'
        elif pred == 'HasProperty':
            find_subject_question = f'What has property {obj}?'
            find_object_question = f'What property does {subj} have?'
        elif pred == 'HasPrerequisite':
            find_subject_question = f'What happens after {obj}?'
        elif pred == 'ReceivesAction':
            find_subject_question = f'What receives {obj} action?' 
            find_object_question = f'What action does {subj} receive?'
        elif pred == 'NotCapableOf':
            find_subject_question = f'What cannot {obj}?'
        elif pred == 'MotivatedByGoal':
            find_subject_question = f'What action motivation of {obj} results in?'
            find_object_question = f'What is {subj} motivated by?'
        elif pred == 'HasA':
            find_subject_question = f'What has {obj}?'
        elif pred == 'IsA':
            find_subject_question = f'What can be {obj}?'
        elif pred == 'CausesDesire':
            find_subject_question = f'What causes the desire to {obj}?'
        elif pred == 'HasFirstSubevent':
            find_subject_question = f'What is {obj} the first subevent of?'
        elif pred == 'NotHasProperty':
            find_object_question = f'What property {subj} does not have?'
        elif pred == 'NotIsA':
            find_object_question = f'What {subj} is not?'
        elif pred == 'PartOf':
            find_subject_question = f'What is part of {obj}?'

        if (find_subject_question != row.find_subj_question) or (find_object_question != row.find_obj_question):
            csv_df.loc[index, 'find_subj_question'] = find_subject_question
            csv_df.loc[index, 'find_obj_question'] = find_object_question
            csv_df.to_csv(out_file_path, index=False)
    print(f'*** Questions saved at: {out_file_path}')
    return out_file_path


def generate_prompt(num_of_concepts_returned):
    sample_response_words = ['knife', 'fork', 'spoon', 'glass', 'napkin', 'plate', 'salt', 'pepper', 'ketchup', 'mustard', 'sugar', 'bread', 'butter', 'mayonnaise']
    if num_of_concepts_returned > len(sample_response_words):
        raise Exception(f'Number of requested concepts are larger than the available samples in prompt: {num_of_concepts_returned} > {len(sample_response_words)}')
    sliced_string_response_words = ', '.join(sample_response_words[:num_of_concepts_returned])
    prompt = f'Q: What can you see besides a plate? Name {number_to_string[num_of_concepts_returned]}.\nA: {sliced_string_response_words}.'
    return prompt

def generate_better_prompt(predicate):
    find_subj_prompt, find_obj_prompt = None, None
    # Generic prompt
    # As in this example: https://beta.openai.com/playground/p/w09hHjYD0575R0UwSSudZ4MW
    prompt = 'Q: What can you see besides a plate? Name ten.\nA: knife, fork, spoon, glass, napkin, plate, glass, salt, pepper, ketchup.\n\nQ: What is a cat? Name ten.\nA: mammal, animal, domesticated, carnivore, feline, friend, chordata, furry, active, funny.\n\nQ: What is at earth? Name ten.\nA: continents, countries, mountains, oceans, seas, rivers, people, animals, streets, buildings.'
    # Specific prompts
    if predicate == 'IsA':
        # https://beta.openai.com/playground/p/E32kUf0DohQw0tUzLCXrexrT
        find_obj_prompt = 'Q: What is a cat? Name ten.\nA: mammal, animal, domesticated, carnivore, feline, friend, chordata, furry, active, funny.'
    elif predicate == 'AtLocation':
        # https://beta.openai.com/playground/p/1dQNNm7r7ikWTthkmEggwFZY
        find_subj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What is at park? Name ten.\nA: bench, trees, squirrel, flowers, people, children, grass, soil, playground, walking paths.'
        find_obj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: Where is a table? Name ten.\nA: restaurant, bar, classroom, park, coffeeshop, office, home, kitchen, lobby, hotel room.'
    elif predicate == 'HasProperty':
        find_obj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What properties does water have? Name ten.\nA: liquid, clear, polar, has neutral pH, excellent solvent, has high heat capacity, has high heat of vaporization, has cohesive and adhesive properties, less dense as solid, has melting point of zero degrees celsius.'
    elif predicate == 'CapableOf':
        find_subj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What is capable of running? Name ten.\nA: man, woman, child, boy, girl, cat, dog, cheetah, lion, kangaroo.'
        find_obj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What is cat capable of? Name ten.\nA: walking, running, jumping, eating, purring, pooping, peeing, seeing, meowing, scratching.'
    elif predicate == 'HasSubevent':
        find_obj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What is the subevent of exercise? Name ten.\nA: maintaining good health, maintaining muscle strength, getting fit, staying fit, getting in shape, losing weight, maintaining muscle strength, staying fit, staying healthy, dancing.\n\nQ: What is a cat? Name ten.\nA: mammal, animal, domesticated, carnivore, feline, friend, chordata, furry, active, funny.'
    elif predicate == 'UsedFor':
        find_subj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What do u need to cook? Name ten.\nA: pan, stove, oven, knife, cutting board, mixing bowl, skillet, barbecue, saucepan, seasonings.'
        find_obj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What is knife used for? Name ten.\nA: cutting, chopping, dicing, slicing, mincing, peeling, separating, killing, fighting, incision.'
    elif predicate == 'HasPrerequisite':
        find_subj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What happens after studying hard? Name ten.\nA: getting high grades, becoming top student, graduating, passing exam, entering university, having headache, getting a good job, becoming a physician, becoming an engineer, reaching your goals.'
        find_obj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What is the prerequisite for entering university? Name ten.\nA: studying, growing older, sitting exams, exam preparation, working hard, sacrificing, studying mathematics, studying physics, learning reading and writing, having high grades.'
    elif predicate == 'Causes':
        find_subj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What causes an injury? Name ten.\nA: falling, accident, poisoning, fall, slipping, improper use of tools, drowning, suffocation, electrical discharge, burn.'
    elif predicate == 'CausesDesire':
        find_subj_prompt = 'Answer with ten concepts separated with comma.\n\nQ: What causes an injury? Name ten.\nA: falling, accident, poisoning, fall, slipping, improper use of tools, drowning, suffocation, electrical discharge, burn.'
    
    find_subj_prompt = prompt if find_subj_prompt == None else find_subj_prompt
    find_obj_prompt = prompt if find_obj_prompt == None else find_obj_prompt
    return find_subj_prompt, find_obj_prompt

def get_triples_from_gpt_3(work_path, gpt3_answers_file_path, questions_path, num_of_concepts_returned, prompt_function, engines=['curie'], temperatures=[0, 0.6, 1], specific_predicates=False, predicates=[], is_fuzzy=False, is_predicate_expansion=False, const_fuzzy_prompt=False):
    print(f'*** engine: {engines}')
    questions_df = pd.read_csv(questions_path, dtype=object)
    gpt3_answers_df = pd.read_csv(gpt3_answers_file_path, dtype=object)
    answered_count = 0
    for index, row in tqdm(gpt3_answers_df.iterrows(), desc='Extracting commonsense from GPT-3: '):
        # Processing specific triples only
        if specific_predicates:
            if row.predicate not in predicates:
                continue
        new_update = False
        # Generating relevant prompt
        if is_fuzzy or is_predicate_expansion:
            find_subj_prompt, find_obj_prompt = prompt_function(work_path, row.predicate, row.weight, is_fuzzy, is_predicate_expansion, const_fuzzy_prompt)
        else:
            find_subj_prompt, find_obj_prompt = prompt_function(row.predicate)
        # Adjusting temperature for Fuzzy
        # TODO: Update to get from input without overwriting
        if is_fuzzy or is_predicate_expansion:
            if row.weight == 'high':
                temperatures = [0, 0.7, 1]
            else:
                temperatures = [0.7, 1]
        # Find subject question
        find_subj_question = questions_df.iloc[index].find_subj_question
        gpt3_answers_df.iloc[index].find_subj_question = find_subj_question
        # Making sure the verbalized question exists
        if type(find_subj_question) == str and find_subj_question != '':
            # Only processing response if we have no answers
            if len(literal_eval(row.find_subj_answers)) == 0 or literal_eval(row.find_subj_answers)[0] == '':
                print(f'\n Processing: [SUBJ] --> {row.predicate} --> {row.object} \n')
                for engine in engines:
                    for temperature in temperatures:
                        subj_text_answer, subj_response = q_and_a_gpt3(find_subj_prompt, find_subj_question, num_of_concepts_returned, engine=engine, temperature=temperature)
                        if is_fuzzy or is_predicate_expansion:
                            subj_answers, reason = extract_array_from_text(subj_text_answer, is_fuzzy=is_fuzzy) if row.weight == 'low' else extract_array_from_text(subj_text_answer)
                        else:
                            subj_answers, reason = extract_array_from_text(subj_text_answer)
                        if subj_text_answer != '':
                            break
                    if subj_text_answer != '':
                        break

                gpt3_answers_df.loc[index, 'find_subj_text_answer'] = subj_text_answer
                gpt3_answers_df.loc[index, 'find_subj_answers'] = subj_answers
                gpt3_answers_df.loc[index, 'find_subj_engine'] = engine
                gpt3_answers_df.loc[index, 'find_subj_temperature'] = temperature
                if is_fuzzy or is_predicate_expansion:
                    gpt3_answers_df.loc[index, 'find_subj_reason'] = reason.strip()
                answered_count += 1
                new_update = True

        # Find object question
        find_obj_question = questions_df.iloc[index].find_obj_question
        gpt3_answers_df.iloc[index].find_obj_question = find_obj_question
        # Making sure the verbalized question exists
        if type(find_obj_question) == str and find_obj_question != '':
            # Only processing response if we have no answers
            if len(literal_eval(row.find_obj_answers)) == 0 or literal_eval(row.find_obj_answers)[0] == '':
                print(f'\n Processing: {row.subject} --> {row.predicate} --> [OBJ] \n')
                for engine in engines:
                    for temperature in temperatures:
                        obj_text_answer, obj_response = q_and_a_gpt3(find_obj_prompt, find_obj_question, num_of_concepts_returned, engine=engine, temperature=temperature)
                        if is_fuzzy or is_predicate_expansion:
                            obj_answers, reason = extract_array_from_text(obj_text_answer, is_fuzzy=(is_fuzzy or is_predicate_expansion)) if row.weight == 'low' else extract_array_from_text(obj_text_answer)
                        else:
                            obj_answers, reason = extract_array_from_text(obj_text_answer)
                        if obj_text_answer != '':
                            break
                    if obj_text_answer != '':
                        break
                gpt3_answers_df.loc[index, 'find_obj_text_answer'] = obj_text_answer
                gpt3_answers_df.loc[index, 'find_obj_answers'] = obj_answers
                gpt3_answers_df.loc[index, 'find_obj_engine'] = engine
                gpt3_answers_df.loc[index, 'find_obj_temperature'] = temperature
                if is_fuzzy or is_predicate_expansion:
                    gpt3_answers_df.loc[index, 'find_obj_reason'] = reason.strip()
                answered_count += 1
                new_update = True
        
        # Saving step results
        if new_update:
            gpt3_answers_df.to_csv(gpt3_answers_file_path, index=False)

    # Saving results
    print(f'*** Answers saved at: {gpt3_answers_file_path}')
    return gpt3_answers_file_path


def load_conceptnet_100k(data_path, only_true=True):
    col_names = ['pred', 'subj', 'obj', 'true']
    data = pd.read_csv(data_path, sep='\t', header=None, names=col_names, index_col=None)
    if only_true:
        data = data[data['true']==1]
    return data

if __name__ == "__main__":
    work_path = './results/gpt_3_cskc'
    conceptnet_100k_path = './data/test.txt'
    num_of_concepts_returned = 10
    engine = 'text-davinci-002'
    generate_questions = False

    # Generating verbalized questions to ask from GPT-3
    questions_out_file_name = f'questions_{num_of_concepts_returned}_returned_concepts.csv'
    questions_path = f'{work_path}/{questions_out_file_name}'
    if generate_questions:
        conceptnet_data = load_conceptnet_100k(conceptnet_100k_path)
        questions_path = generate_questions(work_path, conceptnet_data, num_of_concepts_returned)
        questions_path = fix_bad_question_generations(work_path, num_of_concepts_returned)
    # Updating specific predicate questions if needed
    # questions_path = fix_bad_question_generations(work_path, num_of_concepts_returned, predicates=['IsA', 'AtLocation'], specific_predicates=True)
    
    # Getting GPT-3 Answers
    gpt3_answers_file_path = f'{work_path}/{Path(questions_path).stem}_with_answers_using_{engine}_model.csv'.replace('-', '_')
    if not os.path.isfile(gpt3_answers_file_path):
        # Blank copy if does not exist already
        os.system(f'cp {questions_path} {gpt3_answers_file_path}')
    get_triples_from_gpt_3(gpt3_answers_file_path, questions_path, num_of_concepts_returned, generate_better_prompt, engine=engine, temperatures=[0, 0.6, 1])
    
    # Calculating metrics
    results_file_name = f'questions_{num_of_concepts_returned}_returned_concepts_with_answers_using_{engine}_model.csv'.replace('-', '_')
    results_file_path = f'{work_path}/{results_file_name}'
    calculate_hits_at_n(work_path, results_file_path)