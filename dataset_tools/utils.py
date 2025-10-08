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

            request_part, adverts_part = map(str.strip, line.split("<=>"))
            adverts_ids = []
            requests_ids = []

            # parse lists of requests and adverts
            for part in request_part.split(","):
                part = part.strip()
                if "-" in part:  # the rang of numbers like 125-127
                    start, end = map(int, part.split("-"))
                    requests_ids.extend([str(i) for i in range(start, end + 1)])
                else:
                    requests_ids.append(part)            

            for part in adverts_part.split(","):
                part = part.strip()
                if "-" in part:  # the rang of numbers like 125-127
                    start, end = map(int, part.split("-"))
                    adverts_ids.extend([str(i) for i in range(start, end + 1)])
                else:
                    adverts_ids.append(part)

            # add new ads, if id is present
            for request in requests_ids:
                if request in all_data:
                    all_data[request].extend(adverts_ids)
                else:
                    all_data[request] = adverts_ids

    return all_data