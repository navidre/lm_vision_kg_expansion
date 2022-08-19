import sys
import pandas as pd
from pathlib import Path
from tqdm import tqdm
sys.path.append('./')
from utils.gpt_3_utils import evaluate_sentence_by_gpt3

def evaluate_triples_by_gpt3(csv_manifest_path, engine='text-curie-001'):
    # Loading input CSV
    manifest_df = pd.read_csv(csv_manifest_path)
    manifest_df['makes_sense_gpt3'] = None
    manifest_df['reason'] = None
    # Save path
    save_path = f'{Path(csv_manifest_path).parent}/{Path(csv_manifest_path).stem}_gpt3_evaluated_with_{engine}.csv'
    # Evaluating by GPT-3
    prompt = 'Each sentence is a visual common sense statement. Answer with yes if makes sense or no if it does not.\n\nQ: It is less likely to see elephant under table. Is it true?\nA: Elephant is very large and does not fit under a table. Therefore, yes.\n\nQ: It is likely to see cup on pole. Is it true?\nA: Pole has limited area and is used to hold things like flags. Therefore, no.'
    for index, row in tqdm(manifest_df.iterrows(), desc='Evaluating by GPT-3: '):
        sentence = row.evaluated_sentence
        text_answer, response = evaluate_sentence_by_gpt3(prompt, sentence, engine=engine)
        if 'therefore,' not in text_answer:
            manifest_df.loc[index, 'reason'] = text_answer
        else:
            # Extracting the answer
            reason, yes_no_answer = text_answer.split('therefore,')
            yes_no_answer = yes_no_answer.replace('.', '').strip()
            if yes_no_answer == 'yes':
                manifest_df.loc[index, 'makes_sense_gpt3'] = 1
                manifest_df.loc[index, 'reason'] = reason
            elif yes_no_answer == 'no':
                manifest_df.loc[index, 'makes_sense_gpt3'] = 0
                manifest_df.loc[index, 'reason'] = reason
            else:
                manifest_df.loc[index, 'reason'] = text_answer   
        # Saving the result in each step
        manifest_df.to_csv(save_path, index=False)
    # Returning the save path
    print(f'GPT-3-evaluated result saved at: {save_path}')
    return save_path

if __name__ == "__main__":
    work_path = './results/gpt_3_wpkg_large_experiment/human_evaluation/to_evaluate'
    csv_manifest_path = f'{work_path}/output_manifest.csv'
    engine = 'text-curie-001'

    evaluated_path = evaluate_triples_by_gpt3(csv_manifest_path, engine)