import numpy as np
import sklearn


def calc_optimal_threshold(probs, true_markup, n_requests, n_ads):
    assert isinstance(probs, np.ndarray) and probs.shape == (n_requests, n_ads)

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
