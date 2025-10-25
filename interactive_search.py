import readline  # modifies behavior of input(), adding history and handling arrows and backspase
import argparse
import json

from search_pipeline import searcher


AD_DB_PATH = "data/ads_db.txt"

METRICS_PATH = "metrics.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--thr",
        help="Threshold level for matching probability (0 - all ads, 1 - no ads)",
        default=-1,  # magic number to detect absence
        type=float,
    )
    args = parser.parse_args()
    if args.thr == -1:  # not specified
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            metrics_dict = json.load(f)
        opt_thr = metrics_dict["threshold"]
    else:
        opt_thr = args.thr
    if opt_thr < 0:
        print(f"Setting probability threshold from {thr} to min value: 0")
        opt_thr = 0
    if opt_thr > 1:
        print(f"Setting probability threshold from {thr} to max value: 1")
        opt_thr = 1
    print(f"Match probability threshold: {opt_thr}")

    print("Encoding ads...")
    with open(AD_DB_PATH, "r", encoding="utf-8") as f:
        ads = f.readlines()
    enc_ads = searcher.encode_strings(ads)

    while True:
        request = input("Enter your request (or just \"q\" to exit): ")
        if request == "q":
            break

        if len(request) == 0:
            print("(skipping empty request)")
            continue

        enc_req = searcher.encode_strings([request])[0]
        found_ad_idx_list = searcher.search(enc_req, enc_ads, opt_thr)
        if len(found_ad_idx_list) == 0:
            print("(no matches found)")
            continue

        for pt_idx, ad_idx in enumerate(found_ad_idx_list, start=1):
            print(f"\t{pt_idx}. {ads[ad_idx]}")
        print(f"({len(found_ad_idx_list)} advertisements found, {len(ads)} scanned)")

    print("Goodbye!")

