import hashlib
import json

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

    enc_requests = searcher.encode_strings(requests)
    enc_ads = searcher.encode_strings(ads)

    pred_markup = {}
    for req_id, enc_req in enumerate(enc_requests, start=1):
        print(f"Request {req_id} out of {len(requests)}")
        pred_ad_idx_list = searcher.search(enc_req, enc_ads)
        # full_pipeline.search() returns 0-based list indices (the list contains all lines from input file),
        # but advertisement id is 1-based line number
        pred_markup[str(req_id)] = [str(idx + 1) for idx in pred_ad_idx_list]

    confusion_matrix = metrics.calc_confusion_matrix(true_markup, pred_markup, n_ads=len(ads), n_requests=len(requests))
    all_stats = metrics.calc_all_stats(confusion_matrix)
    all_stats["conf_matr"] = confusion_matrix

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
