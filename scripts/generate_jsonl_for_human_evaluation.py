import random, csv, os, sys, json
import pandas as pd
from tqdm import tqdm
import numpy as np
from pathlib import Path
from ast import literal_eval
import language_tool_python
sys.path.append('./')
from utils.gpt_3_utils import generate_sentence_from_triple_using_gpt3

def select_triples_to_evaluate(save_csv_file_path, gpt3_answers_file_path, top_n, n, all_rows=False, all_results=False, is_fuzzy=False, is_predicate_expansion=False, only_weights=[]):
    gpt3_answers_df = pd.read_csv(gpt3_answers_file_path, dtype=object)
    if all_rows:
        selected_triple_answers = gpt3_answers_df
    else:
        selected_triple_answers = gpt3_answers_df.sample(n=n)
    # Defining CSV
    csv_file =  open(save_csv_file_path, 'w')
    csv_writer = csv.writer(csv_file, delimiter=",")
    csv_writer.writerow(['weight', 'subject', 'predicate', 'object'])
    weight = '-'
    triples_so_far = []
    for index, row in tqdm(selected_triple_answers.iterrows(), desc='Extracting top-n answers: '):
        subj, pred, obj, find_subj_answers, find_obj_answers = row.subject, row.predicate, row.object, literal_eval(row.find_subj_answers), literal_eval(row.find_obj_answers)
        if is_fuzzy or is_predicate_expansion:
            weight = row.weight
            if weight not in only_weights:
                continue
        # Write find_subjects
        selected_find_subj_answers = find_subj_answers if all_results else find_subj_answers[:top_n]
        found_subj_triples = [[weight, found_subj, pred, obj] for found_subj in selected_find_subj_answers if 'therefore' not in found_subj.lower()]
        for row in found_subj_triples:
            triple_string = f'{weight}:{row[1]}:{row[2]}:{row[3]}'
            if triple_string in triples_so_far:
                continue
            else:
                triples_so_far.append(triple_string)
                csv_writer.writerow(row)
        # Write find_objects
        selected_find_obj_answers = find_obj_answers if all_results else find_obj_answers[:top_n]
        found_obj_triples = [[weight, subj, pred, found_obj] for found_obj in selected_find_obj_answers if 'therefore' not in found_obj.lower()]
        for row in found_obj_triples:
            triple_string = f'{weight}:{row[1]}:{row[2]}:{row[3]}'
            if triple_string in triples_so_far:
                continue
            else:
                triples_so_far.append(triple_string)
                csv_writer.writerow(row)
    # Closing CSV File
    csv_file.close()
    return save_csv_file_path

def generate_sentence_from_triple_using_pattern(subj, pred, obj, fix_grammar=True, grammar_tool=None):
    # pattern of sentence
    if pred in ['has']:
        sentence = f'{subj} {pred} {obj}.'
    else:
        sentence = f'{subj} can be seen {pred} {obj}.'
    # Fixing grammar
    if fix_grammar:
        sentence = grammar_tool.correct(sentence)
    return sentence

def generate_fuzzy_sentence_from_triple_using_pattern(weight, subj, pred, obj, fix_grammar=True, grammar_tool=None):
    # Fuzzy Weight
    fuzzy_text = ''
    if weight == 'high':
        fuzzy_text = 'likely'
    elif weight == 'mid':
        fuzzy_text = 'NOT likely'
    # pattern of sentence
    if pred in ['has']:
        sentence = 'It is ' + fuzzy_text + f' for {subj} to have {obj}.'
    elif pred in ['used for']:
        if weight == 'high':
            sentence = f'{subj} is {pred} {obj}.'
        else:
            sentence = f'{subj} is NOT usually {pred} {obj}.'
    elif pred in ['made of']:
        if weight == 'high':
            sentence = f'{subj} can be {pred} {obj}.'
        else:
            sentence = f'{subj} is NOT usually {pred} {obj}.'
    elif pred in ['has property']:
        if weight == 'high':
            sentence = f'{obj} is a property of {subj}.'
        else:
            sentence = f'{subj} is NOT likely to be {obj}.'
    else:
        sentence = 'It is ' + fuzzy_text + f' to see {subj} {pred} {obj}.'
    # Fixing grammar
    if fix_grammar:
        sentence = grammar_tool.correct(sentence)
    return sentence

def generate_sentences(out_path, triples_csv_data, out_file_name, already_evaluated_sentences_to_exclude_path, use_gpt3=False, is_fuzzy=False, is_predicate_expansion=False):
    # Loading output manifest
    if already_evaluated_sentences_to_exclude_path != '':
        with open(already_evaluated_sentences_to_exclude_path) as f:
            already_evaluated_sentences_to_exclude = [json.loads(line)['source'] for line in f]
    else:
        already_evaluated_sentences_to_exclude = []
    # Out file path - JSONL format for evaluation
    out_file_path = f'{out_path}/{out_file_name}'
    # Loading the selected triples dataframe
    csv_df = pd.read_csv(triples_csv_data)
    jsonl_file = open(out_file_path, 'w')
    # Limited triples CSV for reference
    # Defining CSV
    csv_file =  open(f'{out_path}/triples_to_evaluate_limited.csv', 'w')
    csv_writer = csv.writer(csv_file, delimiter=",")
    csv_writer.writerow(['weight', 'subject', 'predicate', 'object'])
    # Grammar check tool
    tool = language_tool_python.LanguageTool('en-US')  # use a local server (automatically set up), language English
    for index, row in tqdm(csv_df.iterrows(), desc='Generating sentences per triples: '):
        weight = '-'
        if is_fuzzy or is_predicate_expansion:
            weight = row.weight
        subj, pred, obj = row.subject, row.predicate, row.object
        if use_gpt3:
            for temperature in [0, 0.7, 1]:
                sentence = generate_sentence_from_triple_using_gpt3(subj, pred, obj)
                if sentence != '':
                    break
        else:
            if is_fuzzy or is_predicate_expansion:
                sentence = generate_fuzzy_sentence_from_triple_using_pattern(weight, subj, pred, obj, fix_grammar=True, grammar_tool=tool)
            else:
                sentence = generate_sentence_from_triple_using_pattern(subj, pred, obj, fix_grammar=True, grammar_tool=tool)
        # Checking if it the sentence is already evaluated
        if sentence not in already_evaluated_sentences_to_exclude:
            line_to_write = '{"source": "' + sentence + '"}\n' 
            jsonl_file.writelines([line_to_write])
            # Writinf to CSV for reference
            row = [weight, subj, pred, obj]
            csv_writer.writerow(row)
    jsonl_file.close()
    csv_file.close()
    print(f'*** Questions saved at: {out_file_path}')
    return out_file_path

def check_triple_existence_in_wpkg(triples_csv_file_path, wpkg_path):
    save_csv_file_path = f'{Path(triples_csv_file_path).parent}/{Path(triples_csv_file_path).stem}_only_new.csv'
    # WpKG Loading
    with open(wpkg_path, 'r') as fp:
        wpkg = json.load(fp)
    # Loading predicted triples
    triples_df = pd.read_csv(triples_csv_file_path, dtype=object)
    # Defining CSV
    csv_file = open(save_csv_file_path, 'w')
    csv_writer = csv.writer(csv_file, delimiter=",")
    csv_writer.writerow(['subject', 'predicate', 'object'])
    # Assessing new triples
    new_triples = []
    for index, row in tqdm(triples_df.iterrows(), desc='Checking duplicates: '):
        predicted_triple = f'{row.subject}:{row.predicate}:{row.object}'
        if predicted_triple not in wpkg.keys():
            row = [row.subject, row.predicate, row.object]
            csv_writer.writerow(row)
    # Closing CSV File
    csv_file.close()
    return save_csv_file_path    

if __name__ == "__main__":
    context_free_wpkg_path = './data/wpkg/causal-motifs-sgdet-exmp-tde-sum-score-vg.json'
    # Point workpath to the directory of the GPT-3 responses from expand_wpkg_using_gpt_3.py script
    work_path = './results/gpt_3_wpkg_large_experiment_curie_first'
    evaluation_work_path = f'{work_path}/human_evaluation/to_evaluate/'
    # Update file name of gpt3_answers_file_path if needed
    gpt3_answers_file_path = f'{work_path}/questions_5_returned_concepts_fuzzy_updated_with_answers_using_text_curie_001_model_fuzzy.csv'
    save_csv_file_path = f'{evaluation_work_path}/triples_to_evaluate.csv'
    out_jsonl_file_name = f'sentences_to_evaluate.jsonl'
    # already_evaluated_sentences_to_exclude_path = f'{work_path}/human_evaluation/to_evaluate/fuzzy/second_evaluation_round/sentences_to_evaluate.jsonl'
    already_evaluated_sentences_to_exclude_path = ''
    is_fuzzy = True # Expanding randomly-selected triples with fuzzy weights
    is_predicate_expansion = False # Expanding specific concepts with user-provided predicates
    all_rows, all_results = True, True # all rows and all concept resuls to be processed
    only_weights = ['high', 'mid'] # The only weights to be processed
    check_current_kg = False # Check for duplicates
    
    # Check parameters
    if is_fuzzy and is_predicate_expansion:
        raise Exception('At least one of is_fuzzy or is_predicate_expansion should be false.')

    # Creating possible missing evaluation directory
    if not os.path.exists(evaluation_work_path):
        os.makedirs(evaluation_work_path)

    # Only needed in case all_rows is False or all_results is False
    random.seed(66)
    np.random.seed(66)
    top_n = 5 # If all_results is False, top_n concept results are sampled; otherwise, all results are processed.
    n = 25 # If all_rows is False, n rows are sampled; otherwise, all rows are processed.
    ########

    # Selecting the triples
    save_csv_file_path = select_triples_to_evaluate(save_csv_file_path, gpt3_answers_file_path, top_n, n, all_rows=all_rows, all_results=all_results, is_fuzzy=is_fuzzy, is_predicate_expansion=is_predicate_expansion, only_weights=only_weights)
    print(f'*** save_csv_file_path: {save_csv_file_path}')
    # [Optional] checking if they exist in the current KG
    if check_current_kg:
        if not (is_fuzzy or is_predicate_expansion):
            save_csv_file_path_only_new = check_triple_existence_in_wpkg(save_csv_file_path, context_free_wpkg_path)
        else:
            save_csv_file_path_only_new = save_csv_file_path
    else:
        save_csv_file_path_only_new = save_csv_file_path
    # Generating sentences from triples
    jsonl_file_path = generate_sentences(evaluation_work_path, save_csv_file_path_only_new, out_jsonl_file_name, already_evaluated_sentences_to_exclude_path, use_gpt3=False, is_fuzzy=is_fuzzy, is_predicate_expansion=is_predicate_expansion)