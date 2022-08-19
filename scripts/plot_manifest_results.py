import numpy as np 
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import seaborn as sns
sns.set_style("dark")

def plot_manifest_results(csv_manifest_path, filter_column_name=None):
    # Loading input CSV
    manifest_df = pd.read_csv(csv_manifest_path)
    # Extracting data
    predicates = list(set(list(manifest_df.predicate)))
    weights = list(set(list(manifest_df.weight)))
    # Calculating accuracies per predicate
    accuracies = {weight: {} for weight in weights}
    for predicate in predicates:
        for weight in weights:
            if filter_column_name == None:
                filtered_df = manifest_df[(manifest_df.weight == weight) & (manifest_df.predicate == predicate)]
            else:
                filtered_df = manifest_df[(manifest_df.weight == weight) & (manifest_df.predicate == predicate) & (manifest_df[filter_column_name] == 1)]
            if len(filtered_df) == 0:
                print(f'filtered_df is empty for weight {weight} and predicate {predicate}!')
                import IPython; IPython. embed(); exit(1)
            accuracy = sum(list(filtered_df.makes_sense)) * 1.0 / len(filtered_df)
            accuracies[weight][predicate] = accuracy
    # Plotting the results
    print(accuracies)
    # if len(weights) != 2:
    #     raise Exception('Please update method to plot cases with more or less weight types.')
    # labels = {'high': 'More Likely', 'mid': 'Less Likely'}  
    # plotdata = pd.DataFrame({
    #     labels['high']:accuracies['high'],
    #     labels['mid']:accuracies['mid'],
    #     }, 
    #     index=predicates
    # )  
    # plotdata.plot(kind="bar")
    # plt.xticks(rotation=45)
    # plt.xlabel("Predicates")
    # plt.ylabel("Accuracies")
    # if filter_column_name == None:
    #     plt.title("Predicted triple accuracies")
    # else:
    #     plt.title("Predicted triple accuracies after extra processing")
    # plt.legend()
    # plt.tight_layout() # Avoiding cropping
    # plt.grid(True)
    # # Saving
    # is_filtered_str = '' if filter_column_name == None else f'_{filter_column_name}'
    # save_path = f'{Path(csv_manifest_path).parent}/{Path(csv_manifest_path).stem}{is_filtered_str}_plot.pdf'
    # plt.savefig(save_path)
    # return save_path

def select_n_triples_randomly(csv_path, n=100):
    np.random.seed(44)
    df = pd.read_csv(csv_manifest_path)
    sampled_df = df.sample(n=n)
    accuracy = sum(list(sampled_df.makes_sense)) * 1.0 / len(sampled_df)
    print(f'accuracy: {accuracy}')



if __name__ == "__main__":
    # TODO: Fix the script to plot sorted!
    work_path = './results/gpt_3_wpkg_large_experiment/human_evaluation/to_evaluate'
    # GPT-3 Raw Response
    csv_manifest_path = f'{work_path}/output_manifest.csv'
    # select_n_triples_randomly(csv_manifest_path, n=100)
    plot_path = plot_manifest_results(csv_manifest_path)
    # GPT-3 Post-Evaluated
    csv_manifest_path = f'{work_path}/output_manifest_gpt3_evaluated_manually_processed.csv'
    # select_n_triples_randomly(csv_manifest_path, n=100)
    plot_path = plot_manifest_results(csv_manifest_path, filter_column_name='makes_sense_gpt3')