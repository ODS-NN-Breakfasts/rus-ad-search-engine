import hashlib
import json

import numpy as np

from utils import dataset_utils
from utils import metrics
from search_pipeline import searcher


REQUEST_DB_PATH = "data/request_db.txt"
AD_DB_PATH = "data/ads_db.txt"
MARKUP_PATH = "data/matching_db.txt"

METRICS_PATH = "metrics.json"


def calc_dataset_metrics():
    with open(REQUEST_DB_PATH, "r", encoding="utf-8") as f:
        requests = f.readlines()
    with open(AD_DB_PATH, "r", encoding="utf-8") as f:
        ads = f.readlines()
    true_markup = dataset_utils.load_matching_data(MARKUP_PATH)

    print("Encoding requests...")
    enc_requests = searcher.encode_strings(requests)
    assert len(enc_requests) == len(requests)
    print("Encoding advertisements...")
    enc_ads = searcher.encode_strings(ads)
    assert len(enc_ads) == len(ads)

    print("Calculating match probabilities...")
    matching_probs = []
    for req_id, enc_req in enumerate(enc_requests, start=1):
        matching_probs.append(searcher.get_probs(enc_req, enc_ads))
    matching_probs = np.asarray(matching_probs)
    assert np.max(matching_probs) <= 1
    assert np.min(matching_probs) >= 0

    print("Calculating optimal threshold...")
    opt_threshold = metrics.calc_optimal_threshold(matching_probs, true_markup, len(requests), len(ads))
    direct_markup = metrics.convert_probs_to_markup(matching_probs, opt_threshold, len(requests), len(ads))

    print("Searching with optimal threshold...")
    pred_markup = {}
    for req_id, enc_req in enumerate(enc_requests, start=1):
        pred_ad_idx_list = searcher.search(enc_req, enc_ads, opt_threshold)
        if len(pred_ad_idx_list) > 0:
            # searcher.search() returns 0-based list indices (the list contains all lines from input file),
            # but advertisement id is 1-based line number
            pred_markup[str(req_id)] = [str(idx + 1) for idx in pred_ad_idx_list]
    # searcher returns matches, sorted by matching probability, so we re-sort the arrays for this comparison
    assert {k: list(sorted(v)) for k, v in pred_markup.items()} == {k: list(sorted(v)) for k, v in direct_markup.items()}

    print("Calculating stats...")
    confusion_matrix = metrics.calc_confusion_matrix(true_markup, pred_markup, n_ads=len(ads), n_requests=len(requests))
    all_stats = metrics.calc_all_stats(confusion_matrix)
    all_stats["conf_matr"] = confusion_matrix
    all_stats["threshold"] = opt_threshold

    metrics.compare_with_saved_stats(all_stats, confusion_matrix)

    print(f"Saving new stats to {METRICS_PATH}...")
    with open(REQUEST_DB_PATH, "rb") as f:
        req_db_hash_str = hashlib.md5(f.read()).hexdigest()
    with open(AD_DB_PATH, "rb") as f:
        ad_db_hash_str = hashlib.md5(f.read()).hexdigest()
    with open(MARKUP_PATH, "rb") as f:
        markup_hash_str = hashlib.md5(f.read()).hexdigest()
    all_stats["data_hashes"] = {
        "request_db": req_db_hash_str,
        "ad_db": ad_db_hash_str,
        "markup": markup_hash_str,
    }

    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        f.write(json.dumps(all_stats, indent=4))
    print("Done")


if __name__ == "__main__":
    calc_dataset_metrics()
