import readline  # modifies behavior of input(), adding history and handling arrows and backspase
import argparse
import json

import rdflib

from search_pipeline import searcher


AD_DB_PATH = "data/ads_db.txt"

METRICS_PATH = "metrics.json"
ONTOLOGY_PATH = "search_pipeline/ontology.ttl"

ONT_G = rdflib.Graph()
ONT_G.parse(source=ONTOLOGY_PATH, format="turtle")

global_cache = {"text": "", "opts": [], "def_opts": [], "def_attrs": []}


def input_completer_func(text, state):
    if len(global_cache["def_attrs"]) == 0:
        res = ONT_G.query(
            "SELECT DISTINCT (MIN(?name) AS ?minName) "
            "WHERE { "
            "    ?attr_obj local:is_included local:parsed_attributes . "
            "    ?attr_obj local:has_name ?name . "
            "} GROUP BY ?attr_obj"
        )
        global_cache["def_attrs"] += [row[0].toPython() for row in res]

    if len(text.strip()) == 0:
        if len(global_cache["def_opts"]) == 0:
            res = ONT_G.query(
                "SELECT DISTINCT ?name "
                "WHERE { "
                "    ?main_obj local:is_included local:parsed_objects . "
                "    ?main_obj local:is_subclass local:obj1256N . "
                "    ?main_obj local:has_name ?name . "
                "}"
            )
            global_cache["def_opts"] = [row[0].toPython() for row in res]
        options = global_cache["def_opts"]
        return options[state]
    else:
        if global_cache["text"] != text:
            options = []

            if text.rstrip().endswith(":"):
                instance_req_flag = True
                text = text.rstrip()[:-1]
            else:
                instance_req_flag = False

            if text.rstrip().endswith(","):
                part_req_flag = True
                text = text.rstrip()[:-1]
            else:
                part_req_flag = False

            obj_name = text.rstrip()

            res = ONT_G.query(
                "SELECT DISTINCT ?main_obj_name "
                "WHERE { "
                "    ?main_obj local:is_included local:parsed_objects . "
                "    ?main_obj local:has_name ?main_obj_name . "
                f"    FILTER strStarts(?main_obj_name, \"{obj_name}\") "
                "}"
            )
            found_obj_list = list(sorted(set([row[0].toPython() for row in res])))
            options += [row[0].toPython() for row in res if row[0].toPython() != obj_name]

            if len(found_obj_list) >= 1:
                if instance_req_flag:
                    res = ONT_G.query(
                        "SELECT DISTINCT ?name "
                        "WHERE { "
                        "    ?main_obj local:is_included local:parsed_objects . "
                        f"    ?main_obj local:has_name \"{found_obj_list[0]}\" . "
                        "    ?inst_obj local:is_subclass+ ?main_obj . "
                        "    ?inst_obj local:is_included local:parsed_objects . "
                        "    ?inst_obj local:has_name ?name . "
                        "}"
                    )
                    options = [obj_name + ": " + row[0].toPython() + " [inst]" for row in res]
                    if len(options) == 0:
                        options = [obj_name + ": [no instances found]"]

                if part_req_flag:
                    res = ONT_G.query(
                        "SELECT DISTINCT ?name "
                        "WHERE { "
                        "    ?main_obj local:is_included local:parsed_objects . "
                        f"    ?main_obj local:has_name \"{found_obj_list[0]}\" . "
                        "    ?main_obj local:has_part+ ?part_obj . "
                        "    ?part_obj local:is_included local:parsed_objects . "
                        "    ?part_obj local:has_name ?name . "
                        "}"
                    )
                    options = [obj_name + ", " + row[0].toPython() + " [part]" for row in res]
                    if len(options) == 0:
                        options = [obj_name + ": [no parts found]"]

                if len(found_obj_list) == 1 and not instance_req_flag and not part_req_flag:
                    options += [obj_name + " " + attr_name + " [attr]" for attr_name in global_cache["def_attrs"]]

            global_cache["text"] = text
            global_cache["opts"] = options
        else:
            options = global_cache["opts"]

        if state < len(options):
            return options[state]
        else:
            return None


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
        print(f"Setting probability threshold from {opt_thr} to min value: 0")
        opt_thr = 0
    if opt_thr > 1:
        print(f"Setting probability threshold from {opt_thr} to max value: 1")
        opt_thr = 1
    print(f"Match probability threshold: {opt_thr}")

    print("Encoding ads...")
    with open(AD_DB_PATH, "r", encoding="utf-8") as f:
        ads = f.readlines()
    enc_ads = searcher.encode_strings(ads)

    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims("")
    readline.set_completer(input_completer_func)
    while True:
        request = input("Enter your request, \": <tab>\" for instance list, \", <tab>\" for part list, or just \"q\" [\"й\"] to exit: ")
        if request == "q" or request == "й":
            break

        if len(request) == 0:
            print("(skipping empty request)")
            continue

        enc_req = searcher.encode_strings([request])[0]
        print(f"dbg req: {[str(fact) for fact in enc_req]}")
        found_ad_idx_list = searcher.search(enc_req, enc_ads)
        if len(found_ad_idx_list) == 0:
            print("(no matches found)")
            continue

        for pt_idx, ad_idx in enumerate(found_ad_idx_list, start=1):
            print(f"\t{pt_idx}. {ads[ad_idx]}")
            print(f"dbg ad: {[str(fact) for fact in enc_ads[ad_idx]]}\n\n")
        print(f"({len(found_ad_idx_list)} advertisements found, {len(ads)} scanned)")

    print("Goodbye!")

