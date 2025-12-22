# corresponding analysis is in research/topic_classifier_rosberta.ipynb
import os
import sys

from sklearn.decomposition import PCA
from sklearn.svm import SVC
import sentence_transformers
import numpy as np
import pickle

_LAUNCH_DIR = os.path.abspath(os.getcwd())
if os.path.join(_LAUNCH_DIR, "search_pipeline") == os.path.dirname(os.path.abspath(__file__)):
    sys.path.append(os.path.join(_LAUNCH_DIR))
from utils import dataset_utils


# Loading of this model constantly produce a false warning about non-initialized weights. A similar one is
# described here: https://huggingface.co/FacebookAI/roberta-large-mnli/discussions/7. It looks like the only
# way to disable this warning is to turn off all warnings from Huggingface.
NLP_MODEL = sentence_transformers.SentenceTransformer(
    "ai-forever/ru-en-RoSBERTa",
    local_files_only=True,  # set to False to download model for the first time
)
N_PCA_COMPONENTS = 19
MODEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_topic_classifier.pkl")
_TARGET_CLASS_ID = 0


def _get_req_categories(filename):
    req_categories = {}
    with open(filename, encoding="utf-8") as f:
        for line_idx, cat_info_line in enumerate(f, start=1):
            cat_info_line = cat_info_line.strip()
            if len(cat_info_line) == 0 or cat_info_line.startswith("#"):
                continue
            pos = cat_info_line.find(":")
            if pos < 0:
                raise ValueError(f"Could not find \":\" on line {line_idx}")
            cat_name = cat_info_line[:pos].strip()
            cat_info = cat_info_line[pos + 1:].strip()

            cat_lines = []
            for line_info in cat_info.split(","):
                line_info = line_info.strip()
                if "-" in line_info:
                    beg_str, end_str = line_info.split("-")
                    cat_lines += list(range(int(beg_str.strip()), int(end_str.strip()) + 1))
                else:
                    cat_lines.append(int(line_info))

            if cat_name in req_categories:
                req_categories[cat_name] = list(sorted(set(req_categories[cat_name] + cat_lines)))
            else:
                req_categories[cat_name] = list(sorted(cat_lines))
    all_lines_set = set(line for lines in req_categories.values() for line in lines)
    assert list(sorted(all_lines_set)) == list(range(1, max(all_lines_set) + 1))
    return req_categories


def _preprocess(text):
    text = text.replace("\\n", "\n").replace("\n", " ")
    text = text.strip()
    return text


def _load_data():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
    # REQUESTS_FILE = os.path.join(data_dir, "request_db.txt")
    ADS_FILE = os.path.join(data_dir, "ads_db.txt")
    MATCHING_FILE = os.path.join(data_dir, "matching_db.txt")
    REQ_CATEGORIES_FILE = os.path.join(data_dir, "request_categories.txt")

    with open(ADS_FILE, encoding="utf-8") as f:
        ads_raw = f.readlines()
    req_categories = _get_req_categories(REQ_CATEGORIES_FILE)
    true_markup = dataset_utils.load_matching_data(MATCHING_FILE)

    return ads_raw, req_categories, true_markup


def _train():
    REQ_CAT_NAME = "одежда"

    ads_raw, req_categories, true_markup = _load_data()
    ads = [_preprocess(text) for text in ads_raw]

    ad_embeddings = NLP_MODEL.encode(ads)

    pca = PCA(n_components=N_PCA_COMPONENTS)
    pca_ad_embeddings = pca.fit_transform(ad_embeddings)

    classes = []
    for ad_idx in range(len(ad_embeddings)):
        ad_cat_list = list(set(
            REQ_CAT_NAME for cat_line in req_categories[REQ_CAT_NAME]
            if str(ad_idx + 1) in true_markup.get(str(cat_line), [])
        ))
        if len(ad_cat_list) == 0:
            classes.append(-1)
        else:
            classes.append(_TARGET_CLASS_ID)
    classes = np.asarray(classes)

    clf = SVC()
    clf.fit(pca_ad_embeddings, classes)

    with open(MODEL_FILE, "wb") as f:
        clf_pipeline_list = [pca, clf]
        pickle.dump(clf_pipeline_list, f, protocol=5)


def load_model():
    with open(MODEL_FILE, "rb") as f:
        clf_pipeline_list = pickle.load(f)
    return clf_pipeline_list


def are_ads_about_clothes(clf_pipeline_list, ad_list):
    pca = clf_pipeline_list[0]
    clf = clf_pipeline_list[1]

    ads = [_preprocess(text) for text in ad_list]
    ad_embeddings = NLP_MODEL.encode(ads)
    pca_ad_embeddings = pca.transform(ad_embeddings)

    pred_classes = clf.predict(pca_ad_embeddings)
    return [pred_class == _TARGET_CLASS_ID for pred_class in pred_classes]


if __name__ == "__main__":
    print("Training...")
    _train()
    print("Done")
