import json
import pathlib

import numpy as np
import sklearn


METRICS_PATH = pathlib.Path(__file__).resolve().parent / '..' / 'metrics.json'


def calc_optimal_threshold(probs, true_markup, n_requests, n_ads):
    assert isinstance(probs, np.ndarray) and probs.shape == (n_requests, n_ads)
    assert np.max(probs) <= 1
    assert np.min(probs) >= 0

    true_probs = []
    for request_id in range(1, n_requests + 1):
        if str(request_id) in true_markup:
            true_probs.append([])
            for advert_id in range(1, n_ads + 1):
                if str(advert_id) in true_markup[str(request_id)]:
                    true_probs[request_id - 1].append(1)
                else:
                    true_probs[request_id - 1].append(0)
        else:
            true_probs.append([0]*n_ads)
    true_probs = np.asarray(true_probs)
    assert true_probs.shape == (n_requests, n_ads)

    # https://stats.stackexchange.com/q/287117/
    prevalence = np.count_nonzero(true_probs == 1, keepdims=False)/true_probs.size
    assert prevalence > 0
    fpr_vec, tpr_vec, thr_vec = sklearn.metrics.roc_curve(true_probs.flatten(), probs.flatten())
    recall_vec = tpr_vec
    tnr_vec = 1 - fpr_vec

    zero_div_idxs = np.where((recall_vec*prevalence) + ((1 - tnr_vec)*(1 - prevalence)) == 0)[0]
    if zero_div_idxs.size > 0:
        # to avoid zero-division warning from numpy below
        recall_vec[zero_div_idxs] += 1e-8
    precision_vec = (recall_vec*prevalence)/((recall_vec*prevalence) + ((1 - tnr_vec)*(1 - prevalence)))

    zero_div_idxs = np.where(precision_vec + recall_vec == 0)[0]
    if zero_div_idxs.size > 0:
        # to avoid zero-division warning from numpy below
        precision_vec[zero_div_idxs] += 1e-8
        recall_vec[zero_div_idxs] += 1e-8
    f1_vec = 2*(precision_vec*recall_vec)/(precision_vec + recall_vec)

    opt_thr = thr_vec[np.argmax(f1_vec)]
    if np.isinf(opt_thr):
        opt_thr = 1

    return opt_thr


def convert_probs_to_markup(probs, threshold, n_requests, n_ads):
    assert isinstance(probs, np.ndarray) and probs.shape == (n_requests, n_ads)
    assert np.max(probs) <= 1
    assert np.min(probs) >= 0

    markup = {}
    for request_id in range(1, n_requests + 1):
        matched_ad_ids = []
        for advert_id in range(1, n_ads + 1):
            # NOTE: it is extremely important to use ">=" here, as sklearn.metrics.roc_curve() may return
            # a threshold that is equal to some edge level in probs, so the difference between ">" and ">="
            # will become crusual, not just a small deviation
            if probs[request_id - 1, advert_id - 1] >= threshold:
                matched_ad_ids.append(str(advert_id))
        if len(matched_ad_ids) > 0:
            markup[str(request_id)] = matched_ad_ids.copy()

    return markup


def calc_confusion_matrix(true_markup, pred_markup, n_ads, n_requests):
    """
    Counts True Positive, False Positive, True Negative, False Negative metrics.
    :param true_markup: result of dataset_utils.load_matching_data
    :param pred_markup: in the same format as true_markup
    :param n_ads: amount of ads in ads_db.txt
    :param n_requests: amount of requests in requests_db.txt
    :return: dict of metrics
    """
    assert len(true_markup) <= n_requests
    assert max(len(ads) for ads in true_markup) <= n_ads
    assert all(isinstance(k, str) and all(isinstance(vv, str) for vv in v) for k, v in true_markup.items())
    assert all(
        int(k) > 0 and int(k) <= n_requests and all(int(vv) > 0 and int(vv) <= n_ads for vv in v)
        for k, v in true_markup.items()
    )
    assert all(isinstance(k, str) and all(isinstance(vv, str) for vv in v) for k, v in pred_markup.items())
    assert all(
        int(k) > 0 and int(k) <= n_requests and all(int(vv) > 0 and int(vv) <= n_ads for vv in v)
        for k, v in pred_markup.items()
    )

    metrics = {"TP": 0,
               "FP": 0,
               "TN": 0,
               "FN": 0
               }

    for request_i in range(1, n_requests + 1):
        request_i = str(request_i)

        if (request_i not in true_markup) and (request_i not in pred_markup):
            TN = n_ads
            metrics["TN"] += TN

        elif (request_i in true_markup) and (request_i not in pred_markup):
            FN = len(true_markup[request_i])
            TN = n_ads - FN
            metrics["FN"] += FN
            metrics["TN"] += TN

        elif (request_i not in true_markup) and (request_i in pred_markup):
            FP = len(pred_markup[request_i])
            TN = n_ads - FP
            metrics["FP"] += FP
            metrics["TN"] += TN

        else:
            mapping_indices = true_markup[request_i]
            prediction_indices = pred_markup[request_i]
            TP, FP, TN, FN = 0, 0, 0, 0

            for prediction_i in range(1, n_ads + 1):
                prediction_i = str(prediction_i)

                if (prediction_i not in mapping_indices) and (prediction_i not in prediction_indices):
                    TN += 1

                elif (prediction_i in mapping_indices) and (prediction_i not in prediction_indices):
                    FN += 1

                elif (prediction_i not in mapping_indices) and (prediction_i in prediction_indices):
                    FP += 1

                else:
                    TP += 1

            metrics["TP"] += TP
            metrics["FP"] += FP
            metrics["TN"] += TN
            metrics["FN"] += FN

    return metrics


def calc_all_stats(confusion_matrix):
    """
    Counts confusion matrix-based metrics from accuracy to F-score.
    :param confusion_matrix: dict of metrics from calc_confusion_matrix fn
    :return: dict of metrics
    """
    metrics = {}
    TP = confusion_matrix["TP"]
    FP = confusion_matrix["FP"]
    TN = confusion_matrix["TN"]
    FN = confusion_matrix["FN"]

    metrics["accuracy"] = (TP + TN) / (TP + FP + TN + FN)

    if TP + FP:
        metrics["precision"] = TP / (TP + FP)
    else:
        metrics["precision"] = 0

    if TP + FN:
        metrics["recall"] = TP / (TP + FN)
    else:
        metrics["recall"] = 0

    if metrics["precision"] + metrics["recall"]:
        metrics["f1"] = 2 * (metrics["precision"] * metrics["recall"]) / (metrics["precision"] + metrics["recall"])
    else:
        metrics["f1"] = 0

    return metrics


def compare_with_saved_stats(new_stats, new_confusion_matrix):

    def format_int(val):
        if not isinstance(val, str):
            val = str(val)
        return val

    def format_float(val):
        if not isinstance(val, str):
            val = f"{val:0.3f}"
        return val

    def format_int_diff(old, new):
        if not isinstance(old, str) and not isinstance(new, str):
            diff = new - old
            if diff > 0:
                diff = f"📈 {diff}"
            elif diff < 0:
                diff = f"📉 {diff}"
            else:
                diff = f"↔️  {diff}"
        else:
            diff = "n/a"
        return diff

    def format_float_diff(old, new):
        if not isinstance(old, str) and not isinstance(new, str):
            diff = new - old
            if diff > 0:
                diff = f"📈 {diff:0.3f}"
            elif diff < 0:
                diff = f"📉 {diff:0.3f}"
            else:
                diff = f"↔️  {diff:0.3f}"
        else:
            diff = "n/a"
        return diff

    F1_MIN_DIFF = 0.05

    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        old_stats = json.load(f)

    old_tp = old_stats["conf_matr"].get("TP", "n/a")
    old_fp = old_stats["conf_matr"].get("FP", "n/a")
    old_tn = old_stats["conf_matr"].get("TN", "n/a")
    old_fn = old_stats["conf_matr"].get("FN", "n/a")
    old_precision = old_stats.get("precision", "n/a")
    old_recall = old_stats.get("recall", "n/a")
    old_f1 = old_stats.get("f1", "n/a")

    new_tp = new_confusion_matrix.get("TP", "n/a")
    new_fp = new_confusion_matrix.get("FP", "n/a")
    new_tn = new_confusion_matrix.get("TN", "n/a")
    new_fn = new_confusion_matrix.get("FN", "n/a")
    new_precision = new_stats.get("precision", "n/a")
    new_recall = new_stats.get("recall", "n/a")
    new_f1 = new_stats.get("f1", "n/a")

    print("-----------------------------------------------------------------------------------------")
    print("|\tMetric\t\t|\tOld Value\t|\tNew Value\t|\tDiff\t|")
    print("-----------------------------------------------------------------------------------------")
    print(f"|\tTP\t\t|\t{format_int(old_tp)}\t\t|\t{format_int(new_tp)}\t\t|\t{format_int_diff(old_tp, new_tp)}\t|")
    print(f"|\tFP\t\t|\t{format_int(old_fp)}\t\t|\t{format_int(new_fp)}\t\t|\t{format_int_diff(old_fp, new_fp)}\t|")
    print(f"|\tTN\t\t|\t{format_int(old_tn)}\t\t|\t{format_int(new_tn)}\t\t|\t{format_int_diff(old_tn, new_tn)}\t|")
    print(f"|\tFN\t\t|\t{format_int(old_fn)}\t\t|\t{format_int(new_fn)}\t\t|\t{format_int_diff(old_fn, new_fn)}\t|")
    print(
        f"|\tPrec\t\t|\t{format_float(old_precision)}\t\t|\t{format_float(new_precision)}\t\t|"
        f"\t{format_float_diff(old_precision, new_precision)}\t|"
    )
    print(
        f"|\tRecall\t\t|\t{format_float(old_recall)}\t\t|\t{format_float(new_recall)}\t\t|"
        f"\t{format_float_diff(old_recall, new_recall)}\t|"
    )
    print(
        f"|\tF1\t\t|\t{format_float(old_f1)}\t\t|\t{format_float(new_f1)}\t\t|"
        f"\t{format_float_diff(old_f1, new_f1)}\t|"
    )

    if not isinstance(old_f1, str) and not isinstance(new_f1, str):
        print()
        if new_f1 > old_f1:
            print(
                f"F1 📈 increased by {new_f1 - old_f1:0.3f}, up to {100*new_f1:0.1f}%, " +
                (
                    "which is within the margin of error." if new_f1 - old_f1 < F1_MIN_DIFF
                    else "which is a significant growth 🚀"
                )
            )
        elif new_f1 < old_f1:
            print(
                f"F1 📉 decreased by {old_f1 - new_f1:0.3f}, down to {100*new_f1:0.1f}%, " +
                (
                    "which is within the margin of error." if old_f1 - new_f1 < F1_MIN_DIFF
                    else "which is a significant fall."
                )
            )
        else:
            print("F1 didn't change")

