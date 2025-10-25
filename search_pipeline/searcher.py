from typing import List, Any

import spacy


# to download it for the first time: python -m spacy download ru_core_news_lg
NLP_MODEL = spacy.load("ru_core_news_lg")

DEFAULT_PROB_THR = 0.5


def _preprocess(text: str) -> str:
    text = text.replace("\\n", "\n").replace("\n", " ")
    text = text.strip()
    text = text.lower()  # many words have vectors only in lowercase
    return text


def encode_strings(string_list: List[str]) -> List[Any]:
    encoded_list = []
    for string in string_list:
        string = _preprocess(string)
        encoded_list.append(NLP_MODEL(string))
    return encoded_list


def get_probs(encoded_request: Any, encoded_ad_list: List[Any]) -> List[int]:
    if encoded_request.has_vector:
        # spaCy similarity ranges between -1 and 1, like cosine similarity
        probs = [(encoded_request.similarity(enc_ad) + 1)/2 if enc_ad.has_vector else 0 for enc_ad in encoded_ad_list]
    else:
        probs = [0]*len(encoded_ad_list)
    return probs


def search(encoded_request: Any, encoded_ad_list: List[Any], prob_thr=DEFAULT_PROB_THR) -> List[int]:
    probs = get_probs(encoded_request, encoded_ad_list)
    found_idx_list = []
    for idx, prob in enumerate(probs):
        # NOTE: it is extremely important to use ">=" here, as sklearn.metrics.roc_curve() may return
        # a threshold that is equal to some edge level in probs, so the difference between ">" and ">="
        # will become crusual, not just a small deviation
        if prob >= prob_thr:
            found_idx_list.append((idx, prob))

    # return indexes sorted by largest probability
    return [item[0] for item in sorted(found_idx_list, reverse=True, key=lambda item: item[1])]
