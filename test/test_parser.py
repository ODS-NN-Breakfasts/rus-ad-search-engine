from collections import namedtuple
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import rdflib
import pymorphy3

from search_pipeline import text_parser
from search_pipeline import cloth_handler


ONTOLOGY = rdflib.Graph()
ONTOLOGY.parse(source="search_pipeline/ontology.ttl", format="turtle")
MORPH_AN = pymorphy3.MorphAnalyzer()
SIZE_RULE = text_parser.create_size_info_rule()
ONT_STAT = text_parser.calc_ontology_stat(ONTOLOGY)
SizeInfo = namedtuple('size_info', ["direct_values", "indirect_values"])
SizeIndirectInfo = namedtuple('size_indirect_info', ["keyword", "year_info_from_y", "year_info_from_m", "year_info_to_y", "year_info_to_m"])


def _show_facts(string):
    facts = text_parser.extract_facts(string, ONTOLOGY, ONT_STAT, MORPH_AN, SIZE_RULE)
    for i, fact in enumerate(facts, start=1):
        print(f"Fact {i}: {str(fact)}")
    s_str = "s" if len(facts) != 1 else ""
    print(f"{len(facts)} fact{s_str} found")


def _ensure_parsed(string, true_info_list):

    def _compare_facts(f1, f2):
        res = f1.class_name == f2.class_name
        res = res and f1.parsed_name == f2.parsed_name
        res = res and f1.size_info.direct_values == f2.size_info.direct_values
        if f1.size_info.indirect_values is not None and f2.size_info.indirect_values is not None:
            res = res and f1.size_info.indirect_values.keyword == f2.size_info.indirect_values.keyword
            res = res and f1.size_info.indirect_values.year_info_from_y == f2.size_info.indirect_values.year_info_from_y
            res = res and f1.size_info.indirect_values.year_info_from_m == f2.size_info.indirect_values.year_info_from_m
            res = res and f1.size_info.indirect_values.year_info_to_y == f2.size_info.indirect_values.year_info_to_y
            res = res and f1.size_info.indirect_values.year_info_to_m == f2.size_info.indirect_values.year_info_to_m
        else:
            res = res and (f1.size_info.indirect_values is None and f2.size_info.indirect_values is None)
        res = res and f1.props == f2.props
        return res

    facts = text_parser.extract_facts(string, ONTOLOGY, ONT_STAT, MORPH_AN, SIZE_RULE)
    assert len(facts) == len(true_info_list)
    if __debug__:
        handled_facts = set()
        for true_fact, true_size_info in true_info_list:
            is_matched = False
            for fact in facts:
                if _compare_facts(fact, true_fact) and fact not in handled_facts:
                    assert fact.parsed_size_info == true_size_info
                    handled_facts.add(fact)
                    is_matched = True
                    break
            assert is_matched, f"True fact {true_fact} is not matched"


def test_text_parsing():
    fact_list_1 = [
        (
            cloth_handler.ClothFact(
                class_name="ont:obj:local:obj1256N",
                parsed_name="вещи",
                size_info=SizeInfo(
                    direct_values=None,
                    indirect_values=SizeIndirectInfo(
                        keyword="девочка",
                        year_info_from_y=None,
                        year_info_from_m=None,
                        year_info_to_y=None,
                        year_info_to_m=None,
                    ),
                ),
                prop_dict={
                    "gender": cloth_handler.ClothFact.Gender.WOMAN,
                },
            ),
            (18, 43),
        ),
        (
            cloth_handler.ClothFact(
                class_name="ont:obj:local:obj147510N",
                parsed_name="юбка",
                size_info=SizeInfo(
                    direct_values=None,
                    indirect_values=SizeIndirectInfo(
                        keyword="девочка",
                        year_info_from_y=None,
                        year_info_from_m=None,
                        year_info_to_y=None,
                        year_info_to_m=None,
                    ),
                ),
                prop_dict={
                    "gender": cloth_handler.ClothFact.Gender.WOMAN,
                },
            ),
            (18, 43),
        ),
        (
        cloth_handler.ClothFact(
                class_name="ont:obj:local:obj108393N",
                parsed_name="джинсы",
                size_info=SizeInfo(
                    direct_values=None,
                    indirect_values=SizeIndirectInfo(
                        keyword="девочка",
                        year_info_from_y=None,
                        year_info_from_m=None,
                        year_info_to_y=None,
                        year_info_to_m=None,
                    ),
                ),
                prop_dict={
                    "gender": cloth_handler.ClothFact.Gender.WOMAN,
                    "season": cloth_handler.ClothFact.Season.DEMI_SEASON,
                },
            ),
            (18, 43),
        ),
        (
            cloth_handler.ClothFact(
                class_name="ont:obj:local:obj108468N",
                parsed_name="кофты",
                size_info=SizeInfo(
                    direct_values=None,
                    indirect_values=SizeIndirectInfo(
                        keyword="девочка",
                        year_info_from_y=None,
                        year_info_from_m=None,
                        year_info_to_y=None,
                        year_info_to_m=None,
                    ),
                ),
                prop_dict={
                    "gender": cloth_handler.ClothFact.Gender.WOMAN,
                },
            ),
            (18, 43),
        ),
    ]

    _ensure_parsed("Отдам вещи на девочку р 80-92. Большая юбка, зелёные осенние джинсы и красные кофты", fact_list_1)
    _ensure_parsed("Отдам вещи на девочку р 80-92, большая юбка, зелёные осенние джинсы и красные кофты", fact_list_1)
    _ensure_parsed("Отдам вещи на девочку р 80-92: большая юбка, зелёные осенние джинсы и красные кофты", fact_list_1)
    _ensure_parsed("отдам вещи на девочку р 80-92. большая юбка, зелёные осенние джинсы и красные кофты", fact_list_1)

    print("ALL TESTS HAVE PASSED!")


if __name__ == "__main__":
    test_text_parsing()
