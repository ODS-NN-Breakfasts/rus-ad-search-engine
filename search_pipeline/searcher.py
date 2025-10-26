from typing import List, Any

import sentence_transformers
import scipy
#import numpy as np


# Loading of this model constantly produce a false warning about non-initialized weights. A similar one is
# described here: https://huggingface.co/FacebookAI/roberta-large-mnli/discussions/7. It looks like the only
# way to disable this warning is to turn off all warnings from Huggingface.
NLP_MODEL = sentence_transformers.SentenceTransformer(
    "ai-forever/ru-en-RoSBERTa",
    local_files_only=True,  # set to False to download model for the first time
)

DEFAULT_PROB_THR = 0.5


def _preprocess(text: str) -> str:
    text = text.replace("\\n", "\n")
    text = text.strip()
    text = text.lower()  # many words have vectors only in lowercase
    return text


def encode_strings(string_list: List[str]) -> List[Any]:
    encoded_list = NLP_MODEL.encode([_preprocess(string) for string in string_list], normalize_embeddings=True)
    return encoded_list


def get_probs(encoded_request: Any, encoded_ad_list: List[Any]) -> List[int]:

    def cosine_sim(x, y):
        dst = scipy.spatial.distance.cosine(x, y)  # range is from 0 to 2
        return 1 - (dst/2)

    def euc_sim(x, y):
        dst = np.sqrt(np.sum((x-y)**2))/(np.sqrt(np.sum(x**2)) + np.sqrt(np.sum(y**2)))
        return 1 - dst

    probs = [cosine_sim(encoded_request, enc_ad) for enc_ad in encoded_ad_list]
    #probs = [euc_sim(encoded_request, enc_ad) for enc_ad in encoded_ad_list]
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
