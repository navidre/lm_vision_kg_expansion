import sys, json, os
import pandas as pd
from tqdm import tqdm
from pathlib import Path
sys.path.append('./')
from utils.wpkg_utils import find_most_common_predicates, find_top_triple_for_predicates, find_possible_subjects_and_objects, generate_all_prompts, select_triples_from_wpkg_based_on_predicates, QUESTION_TEMPLATES, FUZZY_QUESTION_TEMPLATES
from gpt3_cskc_using_conceptnet import get_triples_from_gpt_3

def generate_questions(out_path, selected_wpkg_triples, selected_entities_to_expand, top_preds, n, is_fuzzy=False, is_predicate_expansion=False, weights=['high', 'mid']):
    if is_fuzzy:
        suffix = '_fuzzy'
    elif is_predicate_expansion:
        suffix = '_predicate_expansion'
    else:
        suffix = ''
    out_file_name = f'questions_{n}_returned_concepts' + suffix + '.csv'
    out_file_path = f'{out_path}/{out_file_name}'
    csv_df = pd.DataFrame()
    # Predicate Expansion
    if is_predicate_expansion:
        for subj in selected_entities_to_expand:
            for pred in top_preds:
                for weight in weights:
                    row_dict = {'weight': weight,
                                'subject': subj,
                                'predicate': pred,
                                'object': 'x',
                                'find_subj_question': '', 'find_subj_text_answer': '', 'find_subj_answers': [], 'find_subj_reason': '', 'find_subj_engine': '', 'find_subj_temperature': '',
                                'find_obj_question': eval('f' + repr(FUZZY_QUESTION_TEMPLATES[pred][weight][1])), 'find_obj_text_answer': '', 'find_obj_answers': [], 'find_obj_reason': '', 'find_obj_engine': '', 'find_obj_temperature': '',
                                }
                    csv_df = csv_df.append(row_dict, ignore_index=True)
        csv_df.to_csv(out_file_path, index=False)
        print(f'*** Questions saved at: {out_file_path}')
        return out_file_path

    # Normal and Fuzzy Cases
    for predicate, triple_strings in tqdm(selected_wpkg_triples.items(), desc='Generating questions ...'):
        for triple_string in triple_strings:
            subj, pred, obj = triple_string.split(':')
            if not is_fuzzy:
                row_dict = {'subject': subj,
                            'predicate': pred,
                            'object': obj,
                            'find_subj_question': eval('f' + repr(QUESTION_TEMPLATES[pred][0])),
                            'find_subj_text_answer': '', 'find_subj_answers': [], 'find_subj_engine': '', 'find_subj_temperature': '',
                            'find_obj_question': eval('f' + repr(QUESTION_TEMPLATES[pred][1])), 
                            'find_obj_text_answer': '', 'find_obj_answers': [], 'find_subj_engine': '', 'find_subj_temperature': ''
                            }
                csv_df = csv_df.append(row_dict, ignore_index=True)
            else:
                for weight in weights:
                    row_dict = {'weight': weight,
                                'subject': subj,
                                'predicate': pred,
                                'object': obj,
                                'find_subj_question': eval('f' + repr(FUZZY_QUESTION_TEMPLATES[pred][weight][0])),
                                'find_subj_text_answer': '', 'find_subj_answers': [], 'find_subj_reason': '', 'find_subj_engine': '', 'find_subj_temperature': '',
                                'find_obj_question': eval('f' + repr(FUZZY_QUESTION_TEMPLATES[pred][weight][1])), 
                                'find_obj_text_answer': '', 'find_obj_answers': [], 'find_obj_reason': '', 'find_obj_engine': '', 'find_obj_temperature': ''
                                }
                    csv_df = csv_df.append(row_dict, ignore_index=True)
            csv_df.to_csv(out_file_path, index=False)
    print(f'*** Questions saved at: {out_file_path}')
    return out_file_path

def get_wpkg_prompt(predicate):
    with open(f'./results/gpt_3_wpkg/all_prompts.json') as json_file:
        all_prompts = json.load(json_file)
    return all_prompts[predicate]

def get_fuzzy_wpkg_prompt(work_path, predicate, weight, is_fuzzy, is_predicate_expansion, const_prompt_text):
    if is_fuzzy:
        suffix = '_fuzzy'
    elif is_predicate_expansion:
        suffix = '_predicate_expansion'
    else:
        suffix = ''
    const_prompt_text = '_const_prompt' if const_fuzzy_prompt else ''
    with open(f'{work_path}/all{suffix}{const_prompt_text}_prompts.json') as json_file:
        all_prompts = json.load(json_file)
    return all_prompts[predicate][weight]

def remove_duplicate_questions(questions_file_path, previous_question_file_paths):
    # Read previous files and append them to one
    previous_questions_df = pd.concat((pd.read_csv(f) for f in previous_question_file_paths)).reset_index(drop=True, inplace=False)
    questions_df = pd.read_csv(questions_file_path)

    updated_questions_df = pd.DataFrame()
    for idx, row in questions_df.iterrows():
        query_df = previous_questions_df[(previous_questions_df.weight == row.weight) & (previous_questions_df.subject == row.subject) & (previous_questions_df.predicate == row.predicate) & (previous_questions_df.object == row.object)]
        if len(query_df) == 0:
            updated_questions_df = updated_questions_df.append(row)
    # Saving
    questions_file_path_updated = f'{Path(questions_file_path).parent}/{Path(questions_file_path).stem}_updated.csv'
    updated_questions_df.to_csv(questions_file_path_updated, index=False)
    return questions_file_path_updated

if __name__ == "__main__":
    work_path = './results/gpt_3_wpkg_large_experiment_curie_first'
    context_free_wpkg_path = './data/wpkg/causal-motifs-sgdet-exmp-tde-sum-score-vg.json'
    top_n_predicates = 5 # Number of top predicates from context_free_wpkg_path to be used as prompts
    no_of_results = 5 # Number of concept results per query (subjects or objects, given relationship and object or subject.)
    no_of_triples_to_expand = 5 # Number of triples from WpKG to expand on
    # The first engine is tried first. If no responses, then the next one is tried
    # engines = ['text-davinci-002', 'text-curie-001']
    engines = ['text-curie-001', 'text-davinci-002']
    is_fuzzy = True # Expanding randomly-selected triples with fuzzy weights
    const_fuzzy_prompt = True # Using constant prompts instead of adaptive ones for the is_fuzzy case. No effect on other cases.
    is_predicate_expansion = False # Expanding specific concepts with user-provided predicates
    # Previous evaluated question files that we want to remove from this run to save resources
    previous_question_file_paths = ['./results/gpt_3_wpkg/human_evaluation/to_evaluate/fuzzy/second_evaluation_round/questions_5_returned_concepts_fuzzy_with_answers_using_text_davinci_002_model_fuzzy_second_round_processed.csv',
                                    './results/gpt_3_wpkg/human_evaluation/to_evaluate/fuzzy/third_evaluation_round/questions_5_returned_concepts_fuzzy_with_answers_using_text_davinci_002_model_fuzzy_second_round_processed.csv',
                                    './results/gpt_3_wpkg/human_evaluation/to_evaluate/predicate_expansion/questions_5_returned_concepts_predicate_expansion_with_answers_using_text_davinci_002_model_predicate_expansion_first_round.csv'
                                    ]

    # If both is_fuzzy and is_predicate_expansion are false, normal expansion of triples is done
    # Test
    if is_fuzzy and is_predicate_expansion:
        raise Exception('At least one of is_fuzzy or is_predicate_expansion should be false.')
    if const_fuzzy_prompt and not is_fuzzy:
        raise Exception('const_fuzzy_prompt should only be used when is_fuzzy is True. Controls if we use dynamic or constant prompts for the is_fuzzy case.')
    # WpKG Loading
    with open(context_free_wpkg_path, 'r') as fp:
        wpkg = json.load(fp)
    # Sorting the WpKG based on weight
    sorted_wpkg = {k: v for k, v in sorted(wpkg.items(), key=lambda item: item[1], reverse=True)}
    
    """ Preparing Prompts """
    # Finding most common predicates
    # Excluding some predicates, such as 'in front of' and 'above'
    # top_preds = find_most_common_predicates(wpkg, top_n_predicates-1, exclude=['in front of', 'near', 'above', 'under', 'with', 'holding', 'over', 'sitting on'])
    top_preds = find_most_common_predicates(wpkg, top_n_predicates, exclude=[])

    # (Optional) overwriting and adjustment of predicates #
    # if is_fuzzy:
    #     # Overwriting
    #     top_preds = ['in', 'has', 'on']
    # if is_predicate_expansion:
    #     # Overwriting
    #     top_preds = ['used for', 'made of', 'has property']
    # # Appending predicates
    # top_preds.extend(['used for', 'made of', 'has property'])
    #######################################################

    # Finding the top triple for each top predicate selected to construct a sample for the prompt
    if is_predicate_expansion:
        top_triples = ['vegetable:in:bowl', 'table:in:room', 'flower:in:vase', 'plane:has:wing', 'people:watching:kite']
        # Empty array with format expected
        possible_concepts = dict(zip(top_triples, [([], [])]*len(top_triples) ))
    else:
        top_triples = find_top_triple_for_predicates(sorted_wpkg, top_preds)
        print(f'*** Top triples used for prompt generation: {top_triples}')
        # Finding possible subjects and possible objects for each of the top triples
        possible_concepts = find_possible_subjects_and_objects(sorted_wpkg, top_triples, no_of_results)
        print(f'*** Possible subjects and objects to be used per triple: {possible_concepts}')
    # Generating all the prompts needed
    all_prompts = generate_all_prompts(possible_concepts, no_of_results, top_preds=top_preds, is_fuzzy=is_fuzzy, is_predicate_expansion=is_predicate_expansion, const_fuzzy_prompt=const_fuzzy_prompt)
    if is_fuzzy:
        suffix = '_fuzzy'
    elif is_predicate_expansion:
        suffix = '_predicate_expansion'
    else:
        suffix = ''
    const_prompt_text = '_const_prompt' if const_fuzzy_prompt else ''
    all_prompts_name = 'all' + suffix + const_prompt_text + '_prompts.json'
    with open(f'{work_path}/{all_prompts_name}', 'w') as f:
        json.dump(all_prompts, f)
    # print(f'*** all prompts: \n\n {all_prompts}')
    
    """ Choosing Predicates to Expand """
    # Selecting the triples to expand
    if is_predicate_expansion:
        selected_entities_to_expand = ['shoe', 'sidewalk', 'tire', 'arm', 'windshield']
        selected_triples_to_expand = []
    else:
        # selected_triples_to_expand = select_triples_from_wpkg_based_on_predicates(sorted_wpkg, top_preds, possible_concepts, no_of_triples_to_expand, exclude_concepts=['track', 'light'], exclude_triples=['flower:in:leaf', 'shirt:on:woman', 'pant:on:man', 'pant:on:person', 'leaf:on:table', 'shirt:on:man'])
        selected_triples_to_expand = select_triples_from_wpkg_based_on_predicates(sorted_wpkg, top_preds, possible_concepts, no_of_triples_to_expand, exclude_concepts=['track'], exclude_triples=[])
        selected_entities_to_expand = []
    # Generating questions for the selected triples
    questions_file_path = generate_questions(work_path, selected_triples_to_expand, selected_entities_to_expand, top_preds, no_of_results, is_fuzzy=is_fuzzy, is_predicate_expansion=is_predicate_expansion)
    
    """ In case we have a previous run, we like to remove the questions already aske before to save resources. """
    questions_file_path = remove_duplicate_questions(questions_file_path, previous_question_file_paths)
    
    """ Getting and Recording GPT-3 Answers """
    # Getting GPT-3 Answers
    gpt3_answers_file_path = f'{work_path}/{Path(questions_file_path).stem}_with_answers_using_{engines[0]}_model'.replace('-', '_')
    gpt3_answers_file_path += suffix + '.csv'
    if not os.path.isfile(gpt3_answers_file_path):
        # Blank copy if does not exist already
        os.system(f'cp {questions_file_path} {gpt3_answers_file_path}')
    get_prompt_method = get_fuzzy_wpkg_prompt if (is_fuzzy or is_predicate_expansion) else get_wpkg_prompt
    get_triples_from_gpt_3(work_path=work_path,
                           gpt3_answers_file_path=gpt3_answers_file_path, 
                           questions_path=questions_file_path, 
                           num_of_concepts_returned=no_of_results,
                           prompt_function=get_prompt_method, 
                           engines=engines,
                           temperatures=[0, 0.7, 1], 
                           specific_predicates=False, 
                           predicates=[],
                           is_fuzzy=is_fuzzy,
                           is_predicate_expansion=is_predicate_expansion,
                           const_fuzzy_prompt=const_fuzzy_prompt)