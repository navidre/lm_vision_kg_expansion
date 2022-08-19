import json
import pandas as pd
from tqdm import tqdm

def generate_csv_from_manifest(work_path, input_csv_filename, output_manifest_filename, experiment_name, is_fuzzy=False, is_predicate_expansion=False):
    # Loading output manifest
    with open(f'{work_path}/{output_manifest_filename}') as f:
        output_evaluations = [json.loads(line) for line in f]
    # Loading input CSV
    input_csv_df = pd.read_csv(f'{work_path}/{input_csv_filename}', dtype=object)
    # Empty output dataframe
    csv_df = pd.DataFrame()
    # Iterating and generating CSV
    experiment_metadata_tag = experiment_name + '-metadata'
    makes_sense_count = 0
    total_count = len(output_evaluations)
    for index, row in tqdm(input_csv_df.iterrows(), desc='Generating responses CSV: '):
        # Skipping error cases
        if 'class-name' not in output_evaluations[index][experiment_metadata_tag]:
            total_count -= 1
            continue
        # Counting make sense occurrences
        if is_fuzzy or is_predicate_expansion:
            makes_sense = 1 if (output_evaluations[index][experiment_metadata_tag]['class-name'] == 'Correct') else 0
        else:
            makes_sense = 1 if (output_evaluations[index][experiment_metadata_tag]['class-name'] == 'Makes sense') else 0
        makes_sense_count += makes_sense
        row_dict = {'weight': row.weight,
                    'subject': row.subject,
                    'predicate': row.predicate,
                    'object': row.object,
                    'evaluated_sentence': output_evaluations[index]['source'],
                    'makes_sense': makes_sense,
                    'confidence': output_evaluations[index][experiment_metadata_tag]['confidence']
                    }
        csv_df = csv_df.append(row_dict, ignore_index=True)
    out_file_path = f'{work_path}/output_manifest.csv'
    csv_df.to_csv(out_file_path, index=False)
    makes_sense_percentage = makes_sense_count * 1.0 / total_count 
    print(f'makes_sense_percentage: {makes_sense_percentage}')
    return out_file_path, makes_sense_percentage


if __name__ == "__main__":
    work_path = './results/gpt_3_wpkg_large_experiment_curie_first/human_evaluation/to_evaluate'
    input_csv_filename = 'triples_to_evaluate.csv'
    output_manifest_filename = 'output.manifest'
    experiment_name = 'curie-first-only-high'
    is_fuzzy = True # Expanding randomly-selected triples with fuzzy weights
    is_predicate_expansion = False # Expanding specific concepts with user-provided predicates
    
    # Check parameters
    if is_fuzzy and is_predicate_expansion:
        raise Exception('At least one of is_fuzzy or is_predicate_expansion should be false.')
    
    out_file_path, makes_sense_percentage = generate_csv_from_manifest(work_path, input_csv_filename, output_manifest_filename, experiment_name, is_fuzzy=is_fuzzy, is_predicate_expansion=is_predicate_expansion)
