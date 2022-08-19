import json, random
from tqdm import tqdm

random.seed(66)
NUM_TO_STRING = {1: 'one', 
                    2: 'two',
                    5: 'five',
                    10: 'ten',
                    20: 'twenty',
                    30: 'thirty'}
PROMPT_TEMPLATE = 'Answer with five items separated with comma.\n\nQ: {sample_question} Name {no_of_results}.\nA: {sample_results}.'
# 'predicate': (find_subj_question, find_obj_question)

FUZZY_PROMPT_TEMPLATES = {
    'high': 'Answer with five items separated with comma.\n\nQ: What most likely has window? Name five.\nA: Window is usually used to see through. Therefore, train, building, house, car, bus.\n\nQ: What number can most likely be on? Name five.\nA: Number is made of digits and can be written on different things for information. Therefore, train, sidewalk, track, street, building.',
    'mid': 'Answer with five items separated with comma.\n\nQ: What less likely has window? Name five.\nA: Window is usually used to see through. Therefore, hat, drawer, vase, basket, box.\n\nQ: What number can less likely be on? Name five.\nA: Number is made of digits and can be written on different things for information. Therefore, window, people, rock, tree, jacket.',
    'low': 'Answer with five items separated with comma.\n\nQ: What does not have window? Name five.\nA: Window is usually used to see through. Therefore, desk, laptop, chair, pen, mug.\n\nQ: What book cannot be in? Name five.\nA: Book is physically sensitive and usually in places for reading or borrowing. Therefore, fire, dirt, mud, water, wood.'
}

QUESTION_TEMPLATES = {
    'near': ('What is near {obj}?', 'What is near {subj}?'),
    'under': ('What is under {obj}?', 'What is above {subj}?'),
    'behind': ('What is behind {obj}?', 'What is in front of {subj}?'),
    'in': ('What is in {obj}?','What is {subj} in?'),
    'has': ('What has {obj}?','What does {subj} have?'),
    #  cup --> on --> table
    'on': ('What is on {obj}?','What {subj} can be on?'),
    #  eggs --> with --> ham
    'with': ('What is with {obj}?','What is with {subj}?'),
    # human --> sitting on --> bench
    'sitting on': ('Who can sit on {obj}?','Where can {subj} sit?'),
    # woman --> wearing --> skirt
    'wearing': ('Who can wear {obj}?','What can {subj} wear?'),
    # sky --> above --> us
    'above': ('What is above {obj}?', 'What is under {subj}?'),
    # tree --> along --> street
    'along': ('What is along {obj}?', 'What is along {subj}?'),
    # fork --> for --> eating
    'for': ('What can be used for {obj}?', 'What is {subj} used for?'),
    # person --> watching --> TV
    'watching': ('Who watches {obj}?','What can {subj} watch?')
}

FUZZY_QUESTION_TEMPLATES = {
    # toy --> in --> toy box
    'in': {
        'high': ('What is most likely to be in {obj}?','Where is {subj} most likely in?', [0, 0.7, 1]),
        'mid': ('What is less likely to be in {obj}?','Where is {subj} less likely in?', [0.7, 1]),
        'low': ('What cannot be in {obj}?','Where cannot {subj} be in?', [0.7, 1])
    },
    # Man --> has --> arm
    'has': {
        'high': ('What most likely has {obj}?','What does {subj} most likely have?', [0, 0.7, 1]),
        'mid': ('What less likely has {obj}?','What does {subj} less likely have?', [0.7, 1]),
        'low': ('What cannot have {obj}?','What {subj} cannot have?', [0.7, 1])
    },
    #  cup --> on --> table
    'on': {
        'high': ('What is most likely on {obj}?','What {subj} can most likely be on?', [0, 0.7, 1]),
        'mid': ('What is less likely on {obj}?','What {subj} can less likely be on?', [0.7, 1]),
        'low': ('What cannot be on {obj}?','What {subj} cannot be on?', [0.7, 1])
    },
    # hammer --> used for --> hitting nail
    'used for': {
        'high': ('What is most likely used for {obj}?','What is {subj} most likely used for?', [0, 0.7, 1]),
        'mid': ('What is less likely used for {obj}?','What is {subj} less likely used for?', [0.7, 1]),
        'low': ('What cannot be used for {obj}?','For what {subj} cannot be used?', [0.7, 1])
    },
    # stove --> made of --> metal
    'made of': {
        'high': ('What is most likely made of {obj}?','What is {subj} most likely made of?', [0, 0.7, 1]),
        'mid': ('What is less likely made of {obj}?','What is {subj} less likely made of?', [0.7, 1]),
        'low': ('What cannot be made of {obj}?','What cannot {subj} be made of?', [0.7, 1])
    },
    # brewed tea --> has property --> hot 
    'has property': {
        'high': ('What most likely has property {obj}?','What property does {subj} most likely have?', [0, 0.7, 1]),
        'mid': ('What less likely has property {obj}?','What property does {subj} less likely have?', [0.7, 1]),
        'low': ('What cannot have property {obj}?','What property {subj} cannot have?', [0.7, 1])
    },
    # chair --> near --> table
    'near': {
        'high': ('What is most likely near {obj}?','What {subj} can most likely be near?', [0, 0.7, 1]),
        'mid': ('What is less likely near {obj}?','What {subj} can less likely be near?', [0.7, 1]),
        'low': ('What cannot be near {obj}?','What {subj} cannot be near?', [0.7, 1])
    },
    #  foot --> under --> table
    'under': {
        'high': ('What is most likely under {obj}?','What is most likely above {subj}?', [0, 0.7, 1]),
        'mid': ('What is less likely under {obj}?','What is less likely above {subj}?', [0.7, 1]),
        'low': ('What cannot be under {obj}?','What cannot be above {subj}?', [0.7, 1])
    },
    #  person --> behind --> wall
    'behind': {
        'high': ('What is most likely behind {obj}?','What {subj} can most likely be behind?', [0, 0.7, 1]),
        'mid': ('What is less likely behind {obj}?','What {subj} can less likely be behind?', [0.7, 1]),
        'low': ('What cannot be behind {obj}?','What {subj} cannot be behind?', [0.7, 1])
    },
    #  person --> in front of --> wall
    'in front of': {
        'high': ('What is most likely in front of {obj}?','What {subj} can most likely be in front of?', [0, 0.7, 1]),
        'mid': ('What is less likely in front of {obj}?','What {subj} can less likely be in front of?', [0.7, 1]),
        'low': ('What cannot be in front of {obj}?','What {subj} cannot be in front of?', [0.7, 1])
    },
    #  plane --> above --> clouds
    'above': {
        'high': ('What is most likely above {obj}?','What {subj} can most likely be above?', [0, 0.7, 1]),
        'mid': ('What is less likely above {obj}?','What {subj} can less likely be above?', [0.7, 1]),
        'low': ('What cannot be above {obj}?','What {subj} cannot be above?', [0.7, 1])
    },
    #  man --> with --> woman
    'with': {
        'high': ('What is most likely with {obj}?','What {subj} can most likely be with?', [0, 0.7, 1]),
        'mid': ('What is less likely with {obj}?','What {subj} can less likely be with?', [0.7, 1]),
        'low': ('What cannot be with {obj}?','What {subj} cannot be with?', [0.7, 1])
    },
    #  man --> holding --> cup
    'holding': {
        'high': ('What or who is most likely holding {obj}?','What {subj} can most likely hold?', [0, 0.7, 1]),
        'mid': ('What or who is less likely holding {obj}?','What {subj} can less likely hold?', [0.7, 1]),
        'low': ('What or who cannot hold {obj}?','What {subj} cannot hold?', [0.7, 1])
    },
}

def find_most_common_predicates(wpkg, top_n_predicates, exclude=[]):
    # Counting predicates
    pred_count = {}
    for triple, v in wpkg.items():
        subj, pred, obj = triple.split(':')
        if pred in pred_count.keys():
            pred_count[pred] += 1
        else:
            pred_count[pred] = 1
    # Sorting
    sorted_preds = {k: v for k, v in sorted(pred_count.items(), key=lambda item: item[1], reverse=True)}
    sorted_preds_arr = [k for k, v in sorted_preds.items() if k not in exclude]
    return sorted_preds_arr[:top_n_predicates]

def generate_all_prompts(possible_concepts, no_of_results, top_preds=[], is_fuzzy=False, is_predicate_expansion=False, weights=['high', 'mid'], const_fuzzy_prompt=False):
    # Format is {'triple_string': (find_subj_prompt, find_obj_prompt)}
    all_prompts = {}
    if is_predicate_expansion or const_fuzzy_prompt:
        for weight in weights:
            for pred in top_preds:
                if pred not in all_prompts.keys():
                    all_prompts[pred] = {}
                all_prompts[pred][weight] = (FUZZY_PROMPT_TEMPLATES[weight], FUZZY_PROMPT_TEMPLATES[weight])
    elif is_fuzzy:
        for weight in weights:
            for triple_string, (possible_subjects, possible_objects) in possible_concepts.items():
                subj, pred, obj = triple_string.split(':')
                find_subj_prompt, find_obj_prompt = generate_fuzzy_prompt(subj, pred, obj, weight, possible_subjects, possible_objects, n=no_of_results)
                if pred not in all_prompts.keys():
                    all_prompts[pred] = {}
                all_prompts[pred][weight] = (find_subj_prompt, find_obj_prompt)
    else:
        for triple_string, (possible_subjects, possible_objects) in possible_concepts.items():
            subj, pred, obj = triple_string.split(':')
            find_subj_prompt, find_obj_prompt = generate_prompt(subj, pred, obj, possible_subjects, possible_objects, n=no_of_results)
            all_prompts[pred] = (find_subj_prompt, find_obj_prompt)
    return all_prompts

def generate_fuzzy_prompt(subj, pred, obj, weight, possible_subjects, possible_objects, n=5):
    no_of_results = NUM_TO_STRING[n]
    # Find subject prompt
    sample_question = FUZZY_QUESTION_TEMPLATES[pred][weight][0]
    sample_question = eval('f' + repr(sample_question))
    sample_results = ', '.join(possible_subjects)
    find_subj_prompt = eval('f' + repr(FUZZY_PROMPT_TEMPLATES[weight]))
    # Find object prompt
    sample_question = FUZZY_QUESTION_TEMPLATES[pred][weight][1]
    sample_question = eval('f' + repr(sample_question))
    sample_results = ', '.join(possible_objects)
    find_obj_prompt = eval('f' + repr(FUZZY_PROMPT_TEMPLATES[weight]))
    return find_subj_prompt, find_obj_prompt

def generate_prompt(subj, pred, obj, possible_subjects, possible_objects, n=5):
    """_summary_

    Args:
        subj (_type_): Subject of the sample triple
        pred (_type_): Predicate of the sample triple
        obj (_type_): Object of the sample triple
        possible_subjects (_type_): Possible subjects that are already known in WpKG
        possible_objects (_type_): Possible objects that are already known in WpKG
        n (int, optional): The number of concepts to be returned. Defaults to 5.
    """
    no_of_results = NUM_TO_STRING[n]
    # Find subject prompt
    sample_question = QUESTION_TEMPLATES[pred][0]
    sample_question = eval('f' + repr(sample_question))
    sample_results = ', '.join(possible_subjects)
    find_subj_prompt = eval('f' + repr(PROMPT_TEMPLATE))
    # Find object prompt
    sample_question = QUESTION_TEMPLATES[pred][1]
    sample_question = eval('f' + repr(sample_question))
    sample_results = ', '.join(possible_objects)
    find_obj_prompt = eval('f' + repr(PROMPT_TEMPLATE))
    return find_subj_prompt, find_obj_prompt

def find_top_triple_for_predicates(sorted_wpkg, predicates):
    top_triples = {}
    for predicate in predicates:
        for triple, weight in sorted_wpkg.items():
            subj, pred, obj = triple.split(':')
            # Ignoring triples with equal subject and object
            if subj == obj:
                continue
            if pred == predicate:
                top_triples[predicate] = triple
                break
    return top_triples

def find_possible_subjects_and_objects(sorted_wpkg, triples, no_of_results):
    """Finding the no_of_results possible concepts after for cases of subj-pred-[MASK] and [MASK]-pred-obj.
    Using sorted_wpkg to find the most probable triples.

    Args:
        sorted_wpkg (_type_): Sorted WpKG.
        triples (_type_): Triples to analyze in the form of predicate: triple_string. Sample triple string in form of 'subj:pred:obj'.
        no_of_results (_type_): Number of concepts to be found
    """
    # In the form of triple_string: (possible_subjects, possible_objects)
    possible_concepts = {}
    for pred, triple_string in triples.items():
        subj, _, obj = triple_string.split(':')
        possible_subjects = []
        possible_objects = []
        for triple, weight in sorted_wpkg.items():
            candidate_subj, candidate_pred, candidate_obj = triple.split(':')
            # Finding possible subjects
            if (candidate_obj == obj) and (candidate_pred == pred):
                if (candidate_subj not in possible_subjects) and (len(possible_subjects) < no_of_results) and (candidate_subj != subj):
                    possible_subjects.append(candidate_subj)
            # Finding possible objects
            if (candidate_subj == subj) and (candidate_pred == pred):
                if (candidate_obj not in possible_objects) and (len(possible_objects) < no_of_results) and (candidate_obj != obj):
                    possible_objects.append(candidate_obj)
            # Breaking the search loop if we already have enough possible concepts
            if (len(possible_objects) >= no_of_results) and (len(possible_subjects) >= no_of_results):
                break
        # Storing the possible subjects and concepts
        # Format: { 'sample_triple_string': (possible_subjects, possible_objects) }
        possible_concepts[triple_string] = (possible_subjects, possible_objects)
    return possible_concepts

def filter_wpkg_based_on_predicate(wpkg, predicate):
    # Processing WpKG
    # TODO: Update to graph query to improve time compexity. The graph is not too large to cause a problem now.
    filtered_wpkg = {}
    for triple, v in tqdm(wpkg.items(), desc=f'Filtering WpKG based on {predicate}: '):
        subj, pred, obj = triple.split(':')
        if pred == predicate:
            filtered_wpkg[triple] = v
    return filtered_wpkg

def pick_random_key_from_wpkg(wpkg: dict):
    """Picking a random key from WpKG

    Args:
        wpkg (dict): WpKG

    Returns:
        _type_: the random key
    """
    keys = list(wpkg.keys())
    random_key = random.choice(keys)
    return random_key

def select_top_n_from_wpkg(sorted_wpkg, data_size):
    # Keeping the top_n triples with highest weights
    top_wpkg_keys = sorted(sorted_wpkg, key=sorted_wpkg.get, reverse=True)[:data_size]
    top_wpkg = {k: sorted_wpkg[k] for k in top_wpkg_keys}
    return top_wpkg

def select_top_n_from_wpkg_without_repetition(sorted_wpkg, data_size):
    # Keeping the top_n triples with highest weights
    top_wpkg_keys = sorted(sorted_wpkg, key=sorted_wpkg.get, reverse=True)[:data_size]
    top_wpkg = {k: sorted_wpkg[k] for k in top_wpkg_keys if k.split(':')[0] != k.split(':')[2]}
    return top_wpkg

def select_triples_from_wpkg_based_on_predicates(sorted_wpkg, top_preds, possible_concepts, no_of_triples_to_expand, top_wpkg_size_to_select_from=1000, exclude_concepts=[], exclude_triples=[]):
    """_summary_

    Args:
        wpkg (_type_): WpKG graph in JSON format of { 'subj:pred:obj': weight }
        top_preds (_type_): top predicates to be used for generating prompts and expansion. Same predicates
                            are used in prompt and expansion as prompts are examples for guidance of expansion.
        possible_concepts (_type_): possible concepts (subjects and objects) that were used to generate prompts.
                                    We do not select the triples used in prompts for expansion.
        no_of_triples_to_expand (_type_): The number of triples to be selected to expand on.
    """
    selected_triples = {}
    already_in_prompt = {} # structure: { 'predicate': [triple_strings] }.
    # Finding the triples already in prompt
    for triple_string, (possible_subjects, possible_objects) in possible_concepts.items():
        subj, pred, obj = triple_string.split(':')
        already_in_prompt[pred] = []
        for possible_subject in possible_subjects:
            already_in_prompt[pred].append(f'{possible_subject}:{pred}:{obj}')
        for possible_object in possible_objects:
            already_in_prompt[pred].append(f'{subj}:{pred}:{possible_object}')
    # Selecting the top triples from WpKG to select from
    top_wpkg = select_top_n_from_wpkg_without_repetition(sorted_wpkg, top_wpkg_size_to_select_from)
    # Selecting n random triples to extend not already in prompt
    for predicate in top_preds:
        print(predicate)
        selected_triples[predicate] = []
        # Filtering based on predicate
        filtered_wpkg = filter_wpkg_based_on_predicate(top_wpkg, predicate)
        # Gathering random triples to expand that are not in prompt
        if len(filtered_wpkg) < no_of_triples_to_expand:
            # Selecting what exists from the inital WpKG
            selected_triples[predicate] = list(filtered_wpkg.keys())
            # Selecting the remaining randomly from the whole top WpKG
            # TODO: This part needs to be revised as sometimes it resutls in nonsense questions, such as "What is made of man?"
            for i in range(no_of_triples_to_expand-len(selected_triples[predicate])):
                random_triple = pick_random_key_from_wpkg(top_wpkg)
                subj, pred, obj = random_triple.split(':')
                # TODO: Add safety check if needed. As triples are most probably new, not needed.
                # Updating wth the predicate that is missing extra relations as ultimately we only need one concept and relation to make questions
                random_triple_updated = f'{subj}:{predicate}:{obj}'
                selected_triples[predicate].append(random_triple_updated)
        else:
            while len(selected_triples[predicate]) < no_of_triples_to_expand:
                random_triple = pick_random_key_from_wpkg(filtered_wpkg)
                subj, pred, obj = random_triple.split(':')
                if random_triple in exclude_triples:
                    continue
                if (subj in exclude_concepts) or (obj in exclude_concepts):
                    continue
                if random_triple in selected_triples[predicate]:
                    continue
                if random_triple not in already_in_prompt[predicate]:
                    selected_triples[predicate].append(random_triple)
    return selected_triples