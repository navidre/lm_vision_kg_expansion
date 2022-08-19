import pandas as pd
from tqdm import tqdm
from ast import literal_eval

def update_hit_at_ten_count(pred, hit_at_ten_count, predicate_count, left_hit=False, right_hit=False):
    # TODO: Debug why turns 1.
    if left_hit or right_hit:
        if pred in hit_at_ten_count.keys():
            hit_at_ten_count[pred] += 1
        else:
            hit_at_ten_count[pred] = 1
    # Counting occurrence regardless of hits
    if pred in predicate_count.keys():
        predicate_count[pred] += 1
    else:
        predicate_count[pred] = 1
    return hit_at_ten_count, predicate_count
        

def calculate_hits_at_n(work_path, results_file_path):
    # Once looking at left and once looking at right top n. 
    # Then we calculate the average times that we hit top n
    # Hit@{1, 3, 10}
    results_df = pd.read_csv(results_file_path, dtype=object)
    analysis_df = pd.DataFrame(dtype=object)
    left_hits_at_1_count, left_hits_at_3_count, left_hits_at_10_count = 0, 0, 0
    right_hits_at_1_count, right_hits_at_3_count, right_hits_at_10_count = 0, 0, 0
    hit_at_ten_count, predicate_count, hit_at_ten_percentage = {}, {}, {}
    for index, row in tqdm(results_df.iterrows(), desc='Calculating hits: '):
        left_hit_at_1, left_hit_at_3, left_hit_at_10, right_hit_at_1, right_hit_at_3, right_hit_at_10 = False, False, False, False, False, False
        subj, pred, obj, subj_answers, obj_answers = row.subject, row.predicate, row.object, literal_eval(row.find_subj_answers), literal_eval(row.find_obj_answers)
        subj_answers, obj_answers = [x.lower() for x in subj_answers], [x.lower() for x in obj_answers]
        # Calculating Left Hits
        if any(subj in concept for concept in subj_answers[:1]):
            left_hit_at_1 = True
            left_hits_at_1_count += 1
        if any(subj in concept for concept in subj_answers[:3]):
            left_hit_at_3 = True
            left_hits_at_3_count += 1
        if any(subj in concept for concept in subj_answers[:10]):
            left_hit_at_10 = True
            left_hits_at_10_count += 1
            hit_at_ten_count, predicate_count = update_hit_at_ten_count(pred, hit_at_ten_count, predicate_count, left_hit=True, right_hit=False)
        # Calculating Right Hits
        if any(obj in concept for concept in obj_answers[:1]):
            right_hit_at_1 = True
            right_hits_at_1_count += 1
        if any(obj in concept for concept in obj_answers[:3]):
            right_hit_at_3 = True
            right_hits_at_3_count += 1
        if any(obj in concept for concept in obj_answers[:10]):
            right_hit_at_10 = True
            right_hits_at_10_count += 1
            hit_at_ten_count, predicate_count = update_hit_at_ten_count(pred, hit_at_ten_count, predicate_count, left_hit=True, right_hit=True)
        # Updating hits
        hit_at_ten_count, predicate_count = update_hit_at_ten_count(pred, hit_at_ten_count, predicate_count, left_hit=False, right_hit=False)
        # Adding data for diagnosis
        row_dict = {'subject': subj,
                    'predicate': pred,
                    'object': obj,
                    'find_subj_question': row.find_subj_question,
                    'find_subj_answers': row.find_subj_answers,
                    'subj_hit_at_1': left_hit_at_1, 'subj_hit_at_3': left_hit_at_3, 'subj_hit_at_10': left_hit_at_10,
                    'find_obj_question': row.find_obj_question,
                    'find_obj_answers': row.find_obj_answers,
                    'obj_hit_at_1': right_hit_at_1, 'obj_hit_at_3': right_hit_at_3, 'obj_hit_at_10': right_hit_at_10}
        analysis_df = analysis_df.append(row_dict, ignore_index = True)
    # Average Hits
    hits_at_1, hits_at_3, hits_at_10 = (left_hits_at_1_count + right_hits_at_1_count)/(2*len(results_df)), (left_hits_at_3_count + right_hits_at_3_count)/(2*len(results_df)), (left_hits_at_10_count + right_hits_at_10_count)/(2*len(results_df))
    analysis_path = f'{work_path}/evaluation_analysis.csv'
    analysis_df.to_csv(analysis_path, index=False)
    metrics_values_path = f'{work_path}/metric_values.txt'
    # Calculating hit_at_ten_percentage
    hit_at_ten_percentage = {pred_key: (hit_at_ten_count[pred_key]/pred_count) if pred_key in hit_at_ten_count.keys() else 0 for pred_key, pred_count in predicate_count.items()}
    hit_at_ten_percentage = dict(sorted(hit_at_ten_percentage.items(), key=lambda item: item[1]))
    # Ordering predicate_count based on the most common predicates
    predicate_count = dict(sorted(predicate_count.items(), key=lambda item: item[1], reverse=True))
    # Miss count 
    hit_miss_count = {pred_key: (pred_count - hit_at_ten_count[pred_key]) if pred_key in hit_at_ten_count.keys() else pred_count for pred_key, pred_count in predicate_count.items()}
    hit_miss_count = dict(sorted(hit_miss_count.items(), key=lambda item: item[1], reverse=True))
    with open (metrics_values_path, 'w') as f:
        f.write(f'hits_at_1: {hits_at_1}; hits_at_3: {hits_at_3}; hits_at_10: {hits_at_10}\n')
        f.write('\n\n *** Hit Miss Counts *** \n\n')
        f.write(f'{hit_miss_count}')
        f.write('\n\n *** Predicate Counts *** \n\n')
        f.write(f'{predicate_count}')
        f.write('\n\n *** Hit@10 Percentage per Predicate *** \n\n')
        f.write(f'{hit_at_ten_percentage}')

if __name__ == "__main__":
    work_path = './results/gpt_3_cskc'
    results_file_name = 'questions_10_returned_concepts_with_answers_using_text_davinci_002_model.csv'
    results_file_path = f'{work_path}/{results_file_name}'
    calculate_hits_at_n(work_path, results_file_path)
