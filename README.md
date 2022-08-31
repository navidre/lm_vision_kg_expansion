# symmetry_2022_code
This work is published in MDPI's Symmetry journal: [Utilizing Language Models to Expand Vision-Based Commonsense Knowledge Graphs](https://www.mdpi.com/2073-8994/14/8/1715).

## Tutorial

### Expansion of a commonsense KG
1. Open the [expansion script](scripts/expand_wpkg_using_gpt_3.py).
2. Adjust the varibales under <em> __name__ == "__main__" </em> if needed.
3. The variable <em> context_free_wpkg_path </em> stores the path of the initial commonsense KG with the following format: "subj:pred:obj": weight.

NOTE: OpenAI's API key should be added as an environment variable.

4. After running, we should have a CSV file with this format in the output: "\*\_with\_answers\_\*.csv". Each row contains a predicate with its query weight, find_subject and find_object questions, and also the results from GPT-3. Also a first try to extract concepts from the response, which will be refined in the next step.
5. Open [the human evaluation preparation script](scripts/generate_jsonl_for_human_evaluation.py). Set the workspace path to the workspace of the previous step. The outputs are two files. One a CSV file called <em> triples_to_evaluate.csv </em> that shows the triples going to be evaluated in CSV format. The other file is a JSONL format with generated sentences, called <em> sentences_to_evaluate.jsonl </em>, ready to be fed to Amazon mTurk as an input. 

NOTE: As there are two error-prone processes of answer extraction from natural language and sentence generation base on them; it is necessary to vet the results to make sure there are no structurally-incorrect triples to evaluate. There is a grammar check done automatically to remove some of these issues.

6. For evaluation, we used Amazon mTurk through the [AWS SageMaker's Ground Truth module](https://aws.amazon.com/sagemaker/data-labeling/). We created a labeling job with the following specifications and procedures:

    6a. Creating a specific bucket under S3 and a specific folder underneath for each experiment. Placed the JSONL file under this folder. An empty subdirectory created for the evaluation results as well.
    6b. Starting a new labeling job with the following specifications:
        
        - Manual data setup
        - "Input dataset location" pointing to the JSONL file and "Output dataset location" to the results subfolder, both from the 6a step.
        - Task: Text Classification (Single Label)
        - Worker types: Amazon Mechanical Turk
        - Appropriate timeout and task expiration time
        - Uncheck automated data labeling
        - Under additional configuration, select 3 workers.
        - Brief description:
            Using your own commonsense, decide if a sentence is correct or incorrect. Assume sentences with visual context, e.g. in the case of “It is likely to see cloud behind cow.”, imagine that you are in a field and you see cows. Then it makes sense to see clouds behind cows. Please ignore grammatical errors. Grammatical errors do not make a sentence incorrect.
        - Instructions:
            Using your own commonsense, decide if a sentence is correct or incorrect. 

            Assume sentences with visual context, e.g. in the case of “It is likely to see cloud behind cow.”, imagine that you are in a field and you see cows. Then it makes sense to see clouds behind cows.

            Please ignore grammatical errors. Grammatical errors do not make a sentence incorrect.

            More examples:

            It is NOT likely to see elephant on table. —> Correct

            It is likely to see food in plate. —> Correct
        - Options:
            - Correct
            - Incorrect
7. Once the labeling is done on Amazon mTurk, a manifest file is generated and placed under AWS S3's results folder specified in step 6a. Output manifest file is under <em> manifests/output </em> subfolder. Download the manifest file and place it under the same folder as the JSONL file generated in step 5. Then, open the [manifest processing script](scripts/process_output_manifest.py). This method calculates the acuracy of the results and writes the manifest under <em> </em>.
8. To plot the output manifest results, you can use [the plotting script](scripts/plot_manifest_results.py). The output is a PDF file saved under the specified work path including the manifest output file.

## Citation
If you find this project helpful, please consider citing our work.

```
@Article{rezaei2022expansion,
AUTHOR = {Rezaei, Navid and Reformat, Marek Z.},
TITLE = {Utilizing Language Models to Expand Vision-Based Commonsense Knowledge Graphs},
JOURNAL = {Symmetry},
VOLUME = {14},
YEAR = {2022},
NUMBER = {8},
ARTICLE-NUMBER = {1715},
URL = {https://www.mdpi.com/2073-8994/14/8/1715},
ISSN = {2073-8994},
DOI = {10.3390/sym14081715}
}

@InProceedings{rezaei2022contextual,
author="Rezaei, Navid
and Reformat, Marek Z.
and Yager, Ronald R.",
title="Generating Contextual Weighted Commonsense Knowledge Graphs",
booktitle="Information Processing and Management of Uncertainty in Knowledge-Based Systems",
year="2022",
publisher="Springer International Publishing",
address="Cham",
pages="593--606",
isbn="978-3-031-08971-8"
}

@InProceedings{rezaei2020wpkg,
author="Rezaei, Navid
and Reformat, Marek Z.
and Yager, Ronald R.",
title="Image-Based World-perceiving Knowledge Graph (WpKG) with Imprecision",
booktitle="Information Processing and Management of Uncertainty in Knowledge-Based Systems",
year="2020",
publisher="Springer International Publishing",
address="Cham",
pages="415--428",
isbn="978-3-030-50146-4"
}
```
