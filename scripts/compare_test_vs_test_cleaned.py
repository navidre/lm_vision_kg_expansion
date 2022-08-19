import sys
import pandas as pd
from tqdm import tqdm
sys.path.append('./')
from scripts.gpt3_cskc_using_conceptnet import load_conceptnet_100k

test_df = load_conceptnet_100k('./data/test.txt')
# test_cleaned.txt comes from this work: https://github.com/allenai/commonsense-kg-completion
col_names = ['pred', 'subj', 'obj']
test_cleaned_df = pd.read_csv('./data/test_cleaned.txt', sep='\t', header=None, names=col_names, index_col=None)

for index, row in tqdm(test_df.iterrows(), desc='Comparing test vs test_cleaned: '):
    subj, pred, obj = row.subj, row.pred, row.obj
    subj_cleaned, pred_cleaned, obj_cleaned = test_cleaned_df.iloc[index].subj, test_cleaned_df.iloc[index].pred, test_cleaned_df.iloc[index].obj
    if not ((subj == subj_cleaned) and (pred == pred_cleaned) and (obj == obj_cleaned)):
        print(f'{subj}, {pred}, {obj} ---> {subj_cleaned}, {pred_cleaned}, {obj_cleaned}')