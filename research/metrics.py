def confusion_matrix_micro(mapping, predictions, n_ads, n_requests):
    """
    Counts micro-averaged True Positive, False Positive, True Negative, False Negative metrics.
    :param mapping: result of dataset_tools.utils.load_matching_data
    :param predictions: in the same format as mapping
    :param n_ads: amount of ads in ads_db.txt
    :param n_requests: amount of requests in requests_db.txt
    :return: dict of metrics
    """
    micro_metrics = {"TP": 0,
                     "FP": 0,
                     "TN": 0,
                     "FN": 0
                     }

    for request_i in range(1, n_requests + 1):
        request_i = str(request_i)

        # NO MAPPING, NO PREDICTIONS
        if (request_i not in mapping) and (request_i not in predictions):
            TN = n_ads
            micro_metrics["TN"] += TN

        # MAPPING, NO PREDICTIONS
        elif (request_i in mapping) and (request_i not in predictions):
            FN = len(mapping[request_i])  # only negatives are present
            TN = n_ads - FN
            micro_metrics["FN"] += FN
            micro_metrics["TN"] += TN

        # PREDICTIONS, NO MAPPING
        elif (request_i not in mapping) and (request_i in predictions):
            FP = len(predictions[request_i])  # only positives are present
            TN = n_ads - FP
            micro_metrics["FP"] += FP
            micro_metrics["TN"] += TN

        # MAPPING, PREDICTIONS
        else:
            mapping_indices = mapping[request_i]
            prediction_indices = predictions[request_i]
            TP, FP, TN, FN = 0, 0, 0, 0

            for prediction_i in range(1, n_ads + 1):
                prediction_i = str(prediction_i)

                # INDEX IS ABSENT BOTH IN MAPPING AND IN PREDICTIONS
                if (prediction_i not in mapping_indices) and (prediction_i not in prediction_indices):
                    TN += 1

                # INDEX IS PRESNT IN MAPPING AND ABSENT IN PREDICTIONS
                elif (prediction_i in mapping_indices) and (prediction_i not in prediction_indices):
                    FN += 1

                # INDEX IS PRESNT IN PREDICTIONS AND ABSENT IN MAPPING
                elif (prediction_i not in mapping_indices) and (prediction_i in prediction_indices):
                    FP += 1

                # INDEX IS PRESENT BOTH IN MAPPING AND IN PREDICTIONS
                else:
                    TP += 1

            micro_metrics["TP"] += TP
            micro_metrics["FP"] += FP
            micro_metrics["TN"] += TN
            micro_metrics["FN"] += FN

    return micro_metrics


def evaluate(confusion_matrix, ndigits=None):
    """
    Counts confusion matrix-based metrics from accuracy to F-score.
    :param ndigits: number of digits after point
    :param confusion_matrix: dict of metrics from confusion_matrix fn
    :return: dic
    """
    metrics = {"accuracy": 0,
               "precision": 0,
               "recall": 0,
               "f1": 0
               }

    accuracy = confusion_matrix["TP"] + confusion_matrix["TN"] / sum(confusion_matrix.values())
    precision = confusion_matrix["TP"] / (confusion_matrix["TP"] + confusion_matrix["FP"])
    recall = confusion_matrix["TP"] / (confusion_matrix["TP"] + confusion_matrix["FN"])
    f1 = 2 * (precision * recall) / (precision + recall)

    if ndigits:
        metrics["accuracy"] = round(accuracy, ndigits)
        metrics["precision"] = round(precision, ndigits)
        metrics["recall"] = round(recall, ndigits)
        metrics["f1"] = round(f1, ndigits)
    else:
        metrics["accuracy"] = accuracy
        metrics["precision"] = precision
        metrics["recall"] = recall
        metrics["f1"] = f1
    return metrics
