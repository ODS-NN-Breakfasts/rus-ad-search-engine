def load_matching_data(file_name):
    """
    Upload the file with matching information and parse it.
    The file should contain information in the following format:
        357 <=> 122,123,126-127,172
    Output - dictionary in the following format:
        {"357": ["122", "123", "126", "127", "172"], ...}
    """
    all_data = {}

    with open(file_name, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "<=>" not in line:
                continue

            query_id, ads_part = map(str.strip, line.split("<=>"))
            ad_ids = []

            for part in ads_part.split(","):
                part = part.strip()
                if "-" in part:  # the rang of numbers like 125-127
                    start, end = map(int, part.split("-"))
                    ad_ids.extend([str(i) for i in range(start, end + 1)])
                else:
                    ad_ids.append(part)

            # add new ads, if id is present
            if query_id in all_data:
                all_data[query_id].extend(ad_ids)
            else:
                all_data[query_id] = ad_ids

    return all_data