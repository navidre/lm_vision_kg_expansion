import os
from pathlib import Path
from dotenv import load_dotenv
import openai

number_to_string = {1: 'one', 
                    2: 'two',
                    5: 'five',
                    10: 'ten',
                    20: 'twenty',
                    30: 'thirty'}

HOME = str(Path.home())

TEMPERATURE = 0 # t
FREQUENCY_PENALTY = 0 # fp 
PRESENCE_PENALTY = 0 # pp
MAX_TOKENS = 100 # mt
TOP_P = 1 # tp
ENGINE = 'text-davinci-002' # e

load_dotenv(f'{Path().resolve()}/.env')
openai.api_key = os.environ['OPENAI_API_KEY']

def q_and_a_gpt3(prompt, question, num_of_concepts_returned, temperature=TEMPERATURE, max_tokens=MAX_TOKENS, top_p=TOP_P, frequency_penalty=FREQUENCY_PENALTY, presence_penalty=PRESENCE_PENALTY, engine=ENGINE):
    start_sequence = "\nA:"
    restart_sequence = "\n\nQ: "
    prompt_as_input = f"{prompt}\n\nQ: {question} Name {number_to_string[num_of_concepts_returned]}.{start_sequence}"
    response = openai.Completion.create(
                engine=engine,
                prompt=prompt_as_input,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=presence_penalty,
                presence_penalty=frequency_penalty,
                logprobs=20,
                stop=["\n"]
                )
    text_answer = response['choices'][0]['text']
    return text_answer, response


def extract_array_from_text(answer, is_fuzzy=False):
    try:
        if is_fuzzy:
            answer_array = [x.lstrip() for x in answer.split('Therefore,')[1].replace('.', '').split(',')]
            return answer_array, answer.split('Therefore,')[0]
        else: 
            answer_array = [x.lstrip() for x in answer.replace('.', '').split(',')]
            return answer_array, ''
    except:
        print(f'**** Could not make array from: {answer}')
        return [], ''

def generate_find_object_question_from_triple(subj, pred, obj):
    start_sequence = "\nA:"
    restart_sequence = "\n\nQ: "

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Generate grammatically sound questions for the following triples to find the object, which is annotated by [OBJ].\n\nQ: match --> CapableOf --> light candle\nA: What is match capable of?\n\nQ: {subj} --> {pred} --> [OBJ]{start_sequence}",
        temperature=0,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n"]
    )

    text_answer = response['choices'][0]['text'].strip()
    return text_answer

def generate_find_subject_question_from_triple(subj, pred, obj):
    start_sequence = "\nA:"
    restart_sequence = "\n\nQ: "

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=f"Generate grammatically sound questions for the following triples to find the subject, which is annotated by [SUBJ].\n\nQ: music --> CreatedBy --> composer\nA: What does composer create?\n\nQ: [SUBJ] --> {pred} --> {obj}{start_sequence}",
        temperature=0,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n"]
    )

    text_answer = response['choices'][0]['text'].strip()
    return text_answer

def generate_sentence_from_triple_using_gpt3(subj, pred, obj, temperature):
    start_sequence = "\nA:"
    restart_sequence = "\n\nQ: "

    response = openai.Completion.create(
        engine="text-curie-001",
        prompt=f"Generate grammatically sound sentences for the following triples.\n\nQ: music --> CreatedBy --> composer\nA: Music is created by a composer.\n\nQ: bench --> AtLocation --> park\nA: Bench can be seen in a park.\n\nQ: {subj} --> {pred} --> {obj}{start_sequence}",
        temperature=temperature,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n"]
    )

    text_answer = response['choices'][0]['text'].strip()
    return text_answer

def evaluate_sentence_by_gpt3(prompt, sentence, temperature=TEMPERATURE, max_tokens=MAX_TOKENS, top_p=TOP_P, frequency_penalty=FREQUENCY_PENALTY, presence_penalty=PRESENCE_PENALTY, engine=ENGINE):
    start_sequence = "\nA:"
    restart_sequence = "\n\nQ: "
    prompt_as_input = f"{prompt}{restart_sequence}{sentence} Is it true?{start_sequence}"
    response = openai.Completion.create(
                engine=engine,
                prompt=prompt_as_input,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=presence_penalty,
                presence_penalty=frequency_penalty,
                logprobs=20,
                stop=["\n"]
                )
    text_answer = response['choices'][0]['text'].strip().lower()
    return text_answer, response