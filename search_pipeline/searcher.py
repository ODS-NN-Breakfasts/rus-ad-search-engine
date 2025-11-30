from typing import List, Any

import rdflib
import pymorphy3

from search_pipeline import text_parser


ONTOLOGY = rdflib.Graph()
ONTOLOGY.parse(source="search_pipeline/ontology.ttl", format="turtle")
MORPH_AN = pymorphy3.MorphAnalyzer()
SIZE_RULE = text_parser.create_size_info_rule()
ONT_STAT = text_parser.calc_ontology_stat(ONTOLOGY)


def encode_strings(string_list: List[str]) -> List[Any]:
    encoded_list = [text_parser.extract_facts(string, ONTOLOGY, ONT_STAT, MORPH_AN, SIZE_RULE) for string in string_list]
    return encoded_list


def _are_facts_close(ont: Any, req_facts: List[Any], ad_facts: List[Any]):
    for req_fact in req_facts:
        for ad_fact in ad_facts:
            if req_fact.class_name != ad_fact.class_name:
                if text_parser._get_relation(ont, req_fact.parsed_name, ad_fact.parsed_name, is_attr=False) != 1:
                    continue
            ad_size = ad_fact.parsed_size_info
            req_size = req_fact.parsed_size_info
            if req_size is not None and ad_size is not None:
                if max(req_size) < min(ad_size) or min(req_size) > max(ad_size):
                    # any intersection of sized is a match, but no intersection means no match
                    continue
            is_match = True
            for attr_name in req_fact.props.keys():
                ad_attr = ad_fact.props.get(attr_name, None)
                req_attr = req_fact.props.get(attr_name, None)
                if req_attr is not None and ad_attr is not None:
                    # different attributes are not match, but if this attribute is omitted in request or ad, this is still match
                    if req_attr != ad_attr:
                        is_match = False
                        break
            if not is_match:
                continue
            # even one matched fact is complete match between request and ad
            return True
    return False


def get_probs(encoded_request: Any, encoded_ad_list: List[Any]) -> List[int]:
    probs = [1 if _are_facts_close(ONTOLOGY, encoded_request, enc_ad) else 0 for enc_ad in encoded_ad_list]
    return probs


def search(encoded_request: Any, encoded_ad_list: List[Any]) -> List[int]:
    probs = get_probs(encoded_request, encoded_ad_list)
    found_idx_list = []
    for idx, prob in enumerate(probs):
        if prob == 1:
            found_idx_list.append(idx)

    # return indexes sorted by largest probability
    return found_idx_list
