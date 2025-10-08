import os
from utils import load_matching_data

def show_request_and_adverts(requests_file, ads_file, matching_dict,save_to=None):
    """
    Displays all queries with their matching ads in the following format:
    1. <query>
       <advert 1>
       <advert 2>
       ...
    At the end, prints unmatched ads.
    Optionally saves the result to a file.
    """
    output_lines = [] 

    # load data
    with open(requests_file, "r", encoding="utf-8") as f:
        requests  = f.read().splitlines() 
    
    with open(ads_file, "r", encoding="utf-8") as f:
        ads = f.read().splitlines()

    matched_adverts = set()

    # Iterate through all requests
    for i, request_text in enumerate(requests, start=1):
        request_id = str(i)

        # add number of request and it's text
        output_lines.append(f"{i}. {request_text}")

        if request_id  in matching_dict:      # request in our matching dict
            for advert_id in matching_dict[request_id]:
                advert_index = int(advert_id)
                if 0 < advert_index < len(ads): 
                    output_lines.append(f"   {ads[advert_index - 1]}")
                    matched_adverts.add(advert_index)
                else:
                    output_lines.append(f"Advert [{advert_id}] not found in ads_db.txt")
        else:
            output_lines.append("No matching adverts")

        output_lines.append("")  # Blank line after each query block

    all_adverts = set(range(1, len(ads) + 1))

    # get list of unmatched adverts
    unmatched_adverts = sorted(list(all_adverts - matched_adverts))
    output_lines.append("Unmatched adverts:")

    if unmatched_adverts:
        for advert_index in unmatched_adverts:
            output_lines.append(f"   {ads[advert_index - 1]}")
    else:
        output_lines.append("All ads are matched")

    # combine and print
    result_text = "\n".join(output_lines)
    print(result_text)

    # save to file save_to
    if save_to:
        os.makedirs(os.path.dirname(save_to), exist_ok=True)
        with open(save_to, "w", encoding="utf-8") as f:
            f.write(result_text)
        print(f"\n✅ Result has been saved to: {save_to}")


if __name__ == '__main__':
    data = load_matching_data("../data/matching_db.txt")
    show_request_and_adverts(requests_file="../data/request_db.txt",ads_file="../data/ads_db.txt",matching_dict = data, save_to="../data/result.txt")
