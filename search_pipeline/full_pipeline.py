from typing import List, Any

import spacy


# to download it for the first time: python -m spacy download ru_core_news_lg
NLP_MODEL = spacy.load("ru_core_news_lg")

DISTANCE_THR = 0.5


def _preprocess(text: str) -> str:
    text = text.replace("\\n", "\n").replace("\n", " ")
    text = text.strip()
    text = text.lower()  # many words has vectors only in lowercase
    return text


def encode_strings(string_list: List[str]) -> List[Any]:
    encoded_list = []
    for string in string_list:
        string = _preprocess(string)
        encoded_list.append(NLP_MODEL(string))
    return encoded_list


def search(encoded_request: Any, encoded_ad_list: List[Any]) -> List[int]:
    found_idx_list = []
    for idx, enc_ad in enumerate(encoded_ad_list):
        distance = 1 - encoded_request.similarity(enc_ad)
        if distance <= DISTANCE_THR:
            found_idx_list.append(idx)

    return found_idx_list
