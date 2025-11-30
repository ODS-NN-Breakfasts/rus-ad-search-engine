from yargy.tokenizer import Tokenizer as YrgTokenizer
from yargy.interpretation import fact as yrg_fact, attribute as yrg_attr
from yargy.pipelines import morph_pipeline as yrg_morph_pipeline
from yargy import rule as yrg_rule, or_ as yrg_r_or, and_ as yrg_r_and
from yargy.predicates import \
    eq as yrg_rp_eq, gte as yrg_rp_gte, lte as yrg_rp_lte, type as yrg_rp_type, caseless as yrg_rp_caseless, \
    in_caseless as yrg_rp_in_caseless, custom as yrg_rp_custom, normalized as yrg_rp_normalized
from yargy import Parser as YrgParser
import razdel

from search_pipeline import cloth_handler


def calc_ontology_stat(ont):
    res = ont.query(
        "SELECT DISTINCT ?main_obj "
        "WHERE { "
        "    ?main_obj local:is_included local:parsed_objects . "
        "    FILTER (NOT EXISTS {?main_obj local:is_subclass ?parent_obj .}) "
        "}"
    )
    obj_root_name_list = [row[0].n3(ont.namespace_manager) for row in res]
    all_obj_name_set = set()
    for root_obj_name in obj_root_name_list:
        res = ont.query(
            "SELECT DISTINCT ?name "
            "WHERE { "
            f"    {root_obj_name} local:has_name ?name . "
            "}"
        )
        all_obj_name_set |= set(row[0].toPython() for row in res)
        res = ont.query(
            "SELECT DISTINCT ?name "
            "WHERE { "
            "    ?main_obj local:is_included local:parsed_objects . "
            f"    ?main_obj local:is_subclass+ {root_obj_name} . "
            "    ?main_obj local:has_name ?name . "
            "}"
        )
        all_obj_name_set |= set(row[0].toPython() for row in res)

    name_obj_map = {}
    for obj_name in all_obj_name_set:
        res = ont.query(
            "SELECT ?main_obj "
            "WHERE { "
            "    ?main_obj local:is_included local:parsed_objects . "
            f"    ?main_obj local:has_name \"{obj_name}\" . "
            "}"
        )
        out_list = [row[0].n3(ont.namespace_manager) for row in res]
        name_obj_map[obj_name] = out_list

    res = ont.query(
        "SELECT DISTINCT ?main_obj "
        "WHERE { "
        "    ?main_obj local:is_included local:parsed_attributes . "
        "    FILTER (NOT EXISTS {?main_obj local:is_subclass ?parent_obj .}) "
        "}"
    )
    attr_root_name_list = [row[0].n3(ont.namespace_manager) for row in res]
    all_attr_name_set = set()
    for root_attr_name in attr_root_name_list:
        res = ont.query(
            "SELECT DISTINCT ?name "
            "WHERE { "
            f"    {root_attr_name} local:has_name ?name . "
            "}"
        )
        all_attr_name_set |= set(row[0].toPython() for row in res)
        res = ont.query(
            "SELECT DISTINCT ?name "
            "WHERE { "
            "    ?main_obj local:is_included local:parsed_attributes . "
            f"    ?main_obj local:is_subclass+ {root_attr_name} . "
            "    ?main_obj local:has_name ?name . "
            "}"
        )
        all_attr_name_set |= set(row[0].toPython() for row in res)

    name_attr_map = {}
    for attr_name in all_attr_name_set:
        res = ont.query(
            "SELECT ?main_obj "
            "WHERE { "
            "    ?main_obj local:is_included local:parsed_attributes . "
            f"    ?main_obj local:has_name \"{attr_name}\" . "
            "}"
        )
        out_list = [row[0].n3(ont.namespace_manager) for row in res]
        assert len(out_list) == 1
        name_attr_map[attr_name] = out_list[0]

    return {
        "obj_name_set": all_obj_name_set,
        "name_obj_map": name_obj_map,
        "attr_name_set": all_attr_name_set,
        "name_attr_map": name_attr_map,
    }


def _tokenize_and_split_by_sentence(text):
    s_toks = []
    for sentence in razdel.sentenize(text):
        s_toks.append(list(tok.text for tok in razdel.tokenize(sentence.text)))

    all_toks = []
    sentence_ranges = []
    sent_offset = 0
    for toks in s_toks:
        all_toks += toks
        sentence_ranges.append((sent_offset, sent_offset + len(toks)))
        sent_offset += len(toks)

    return all_toks, sentence_ranges


def _get_relation(ont, name1, name2, is_attr):
    if name1 == name2:
        return 0
    parsed_class_str = "local:parsed_objects" if not is_attr else "local:parsed_attributes"
    res = ont.query(
        "SELECT DISTINCT ?main_obj "
        "WHERE { "
        "    ?main_obj local:is_subclass+ ?parent_obj ."
        f"    ?main_obj local:is_included {parsed_class_str} . "
        f"    ?parent_obj local:is_included {parsed_class_str} . "
        f"    ?parent_obj local:has_name \"{name1}\" . "
        f"    ?main_obj local:has_name \"{name2}\" . "
        "}"
    )
    if len(res) > 0:
        return 1
    res = ont.query(
        "SELECT DISTINCT ?main_obj "
        "WHERE { "
        "    ?main_obj local:is_subclass+ ?parent_obj ."
        f"    ?main_obj local:is_included {parsed_class_str} . "
        f"    ?parent_obj local:is_included {parsed_class_str} . "
        f"    ?parent_obj local:has_name \"{name2}\" . "
        f"    ?main_obj local:has_name \"{name1}\" . "
        "}"
    )
    if len(res) > 0:
        return -1
    return None


def _get_all_word_relations(text, ont, ont_stat, morph_an, size_rule):
    SEPARATOR_TOKS = [",", ";", ":", "и", "с", "со", "+"]

    toks, sentence_ranges = _tokenize_and_split_by_sentence(text)
    relation_list = []

    for tok_idx, tok in enumerate(toks):
        if tok in SEPARATOR_TOKS:
            relation_list.append({"rel": "syntax:sep", "from": tok_idx, "to": tok_idx})

    size_parser = YrgParser(size_rule)
    matches = size_parser.findall(text)
    for m in matches:
        pos = 0
        is_size_found = False
        tok_idx = 0
        while tok_idx < len(toks):
            tok = toks[tok_idx]
            pos = text.find(tok, pos)
            assert pos >= 0
            if (pos >= m.span.start and pos < m.span.stop) or (pos + len(tok) >= m.span.stop and not is_size_found):
                relation_list.append({"rel": "ont:size", "from": tok_idx, "to": tok_idx})
                is_size_found = True
            else:
                if is_size_found:
                    # workaround for size ranges, because rule always selects shortest match span and ranges like "80-90" become "80"
                    if tok == "-":
                        relation_list.append({"rel": "ont:size", "from": tok_idx, "to": tok_idx})
                        tok_idx += 1
                        if tok_idx < len(toks) and toks[tok_idx].isdigit():
                            relation_list.append({"rel": "ont:size", "from": tok_idx, "to": tok_idx})
                            tok_idx += 1
                    break
            tok_idx += 1
        assert is_size_found

    normed_toks = [morph_an.parse(tok)[0].normal_form for tok in toks]
    obj_toks = [(idx, tok) for idx, tok in enumerate(normed_toks) if tok in ont_stat["obj_name_set"]]
    for (tok_idx, tok) in obj_toks:
        relation_list.append({"rel": f"ont:obj:{ont_stat['name_obj_map'][tok][0]}", "from": tok_idx, "to": tok_idx})
        for (dep_tok_idx, dep_tok) in obj_toks:
            if dep_tok == tok:
                continue
            dep_code = _get_relation(ont, tok, dep_tok, is_attr=False)
            if dep_code is None:
                continue
            elif dep_code == 1:
                relation_list.append({"rel": "ont:rel:obj_inst", "from": tok_idx, "to": dep_tok_idx})
            elif dep_code == -1:
                relation_list.append({"rel": "ont:rel:obj_inst", "from": dep_tok_idx, "to": tok_idx})
            else:
                raise ValueError(f"Unknown dependency: {dep_code} for {tok} and {dep_tok}")

    attr_toks = [(idx, tok) for idx, tok in enumerate(normed_toks) if tok in ont_stat["attr_name_set"]]
    for (tok_idx, tok) in attr_toks:
        relation_list.append({"rel": f"ont:attr:{ont_stat['name_attr_map'][tok]}", "from": tok_idx, "to": tok_idx})
        for (dep_tok_idx, dep_tok) in obj_toks:
            if dep_tok == tok:
                continue
            dep_code = _get_relation(ont, tok, dep_tok, is_attr=True)
            if dep_code is None:
                continue
            elif dep_code == 1:
                relation_list.append({"rel": "ont:rel:attr_inst", "from": tok_idx, "to": dep_tok_idx})
            elif dep_code == -1:
                relation_list.append({"rel": "ont:rel:attr_inst", "from": dep_tok_idx, "to": tok_idx})
            else:
                raise ValueError(f"Unknown dependency: {dep_code} for {tok} and {dep_tok}")

    return relation_list, toks, sentence_ranges


def extract_facts(text, ont, ont_stat, morph_an, size_rule):

    def _infer_macro_relations(rel_list, sentence_ranges):
        macro_rels = []

        # same sentence
        for sent_range in sentence_ranges:
            sent_idx_list = list(range(sent_range[0], sent_range[1]))
            size_info_cnt = 0
            obj_cnt = 0
            tok_type = None
            first_type = None
            last_size_info_idx = -1
            for idx in sent_idx_list:
                idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == idx]
                if "ont:size" in idx_rels:
                    if tok_type != 'size':  # size info can contain multiple tokens
                        size_info_cnt += 1
                    tok_type = 'size'
                    last_size_info_idx = idx
                elif any(rel.startswith("ont:obj:") for rel in idx_rels):  # any() returns False on empty input
                    obj_cnt += 1  # object is identified by single token
                    tok_type = 'obj'
                else:
                    tok_type = None
                if first_type is None and tok_type is not None:
                    first_type = tok_type

            if obj_cnt > 0:
                obj_tok_idx_list = sorted(
                    [rel["to"] for rel in rel_list if rel["rel"].startswith("ont:obj:") and rel["to"] in sent_idx_list]
                )
                if obj_cnt == 1:
                    assert len(obj_tok_idx_list) == 1
                    obj_tok_idx = obj_tok_idx_list[0]
                    for tok_idx in sent_idx_list:
                        idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == tok_idx]
                        if any(rel.startswith("ont:attr:") for rel in idx_rels):  # any() returns False on empty input
                            macro_rels.append({"rel": "prop", "from": tok_idx, "to": obj_tok_idx})
                else:
                    for tok_idx in range(obj_tok_idx_list[0]):
                        idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == tok_idx]
                        if any(rel.startswith("ont:attr:") for rel in idx_rels):  # any() returns False on empty input
                            macro_rels.append({"rel": "prop", "from": tok_idx, "to": obj_tok_idx_list[0]})
                    for idx_idx in range(1, len(obj_tok_idx_list)):
                        sep_idx_list = []
                        for tok_idx in range(obj_tok_idx_list[idx_idx - 1] + 1, obj_tok_idx_list[idx_idx]):
                            idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == tok_idx]
                            if "syntax:sep" in idx_rels:
                                sep_idx_list.append(tok_idx)
                        if len(sep_idx_list) == 0:
                            sep_idx_list = [obj_tok_idx_list[idx_idx - 1]]
                        if len(sep_idx_list) > 1:
                            sep_idx_list = [obj_tok_idx_list[idx_idx - 1]]

                        for tok_idx in range(obj_tok_idx_list[idx_idx - 1] + 1, sep_idx_list[0]):
                            idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == tok_idx]
                            if any(rel.startswith("ont:attr:") for rel in idx_rels):  # any() returns False on empty input
                                macro_rels.append({"rel": "prop", "from": tok_idx, "to": obj_tok_idx_list[idx_idx - 1]})
                        for tok_idx in range(sep_idx_list[0] + 1, obj_tok_idx_list[idx_idx]):
                            idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == tok_idx]
                            if any(rel.startswith("ont:attr:") for rel in idx_rels):  # any() returns False on empty input
                                macro_rels.append({"rel": "prop", "from": tok_idx, "to": obj_tok_idx_list[idx_idx]})
                    for tok_idx in range(obj_tok_idx_list[-1] + 1, sent_idx_list[-1]):
                        idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == tok_idx]
                        if any(rel.startswith("ont:attr:") for rel in idx_rels):  # any() returns False on empty input
                            macro_rels.append({"rel": "prop", "from": tok_idx, "to": obj_tok_idx_list[-1]})

            if size_info_cnt > 0 and obj_cnt > 0:
                last_size_info_start_idx = None
                last_assign_tok_idx = 0
                is_size_info_continues = False
                if first_type == 'obj':
                    for idx_idx, idx in enumerate(sent_idx_list):
                        idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == idx]
                        if "ont:size" in idx_rels:
                            if not is_size_info_continues:
                                last_size_info_start_idx = idx
                            for obj_idx in sent_idx_list[last_assign_tok_idx:idx_idx]:
                                obj_idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == obj_idx]
                                if any(rel.startswith("ont:obj:") for rel in obj_idx_rels):  # any() returns False on empty input
                                    macro_rels.append({"rel": "size", "from": idx, "to": obj_idx})
                            is_size_info_continues = True
                        else:
                            if is_size_info_continues:
                                last_assign_tok_idx = idx_idx
                            is_size_info_continues = False
                        if idx > last_size_info_idx and any(rel.startswith("ont:obj:") for rel in idx_rels):
                            for size_idx in range(last_size_info_start_idx, last_size_info_idx + 1):
                                macro_rels.append({"rel": "size", "from": size_idx, "to": idx})
                else:
                    for idx_idx, idx in enumerate(sent_idx_list):
                        idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == idx]
                        if any(rel.startswith("ont:obj:") for rel in idx_rels):  # any() returns False on empty input
                            is_size_info_continues = False
                            for size_idx in sent_idx_list[last_assign_tok_idx:idx_idx]:
                                size_idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == size_idx]
                                if "ont:size" in size_idx_rels:
                                    macro_rels.append({"rel": "size", "from": size_idx, "to": idx})
                        else:
                            if "ont:size" in idx_rels:
                                if not is_size_info_continues:
                                    last_assign_tok_idx = idx_idx
                                is_size_info_continues = True
                        # even if sentence is ended by size info, it is dropped, because all objects were defined by previous size infos

        # different sentences
        dangling_prop_idx_list = []
        no_size_sent_list = []
        size_sent_list = []
        for idx in range(len(toks)):
            idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == idx]
            if any(rel.startswith("ont:attr:") for rel in idx_rels):  # any() returns False on empty input
                if not any(mrel["from"] == idx for mrel in macro_rels if mrel["rel"] == "prop"):
                    dangling_prop_idx_list.append(idx)
            if any(rel.startswith("ont:obj:") for rel in idx_rels):  # any() returns False on empty input
                if not any(mrel["to"] == idx for mrel in macro_rels if mrel["rel"] == "size"):
                    for sent_idx, sent_range in enumerate(sentence_ranges):
                        if idx >= sent_range[0] and idx < sent_range[1]:
                            no_size_sent_list.append(sent_idx)
                            break
            if "ont:size" in idx_rels:
                for sent_idx, sent_range in enumerate(sentence_ranges):
                    if idx >= sent_range[0] and idx < sent_range[1]:
                        size_sent_list.append(sent_idx)
                        break
        for prop_idx in dangling_prop_idx_list:
            obj_found = False
            for tok_idx in range(prop_idx - 1, -1, -1):
                idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == tok_idx]
                if any(rel.startswith("ont:obj:") for rel in idx_rels):  # any() returns False on empty input
                    macro_rels.append({"rel": "prop", "from": prop_idx, "to": tok_idx})
                    obj_found = True
                    break
            if not obj_found:
                for tok_idx in range(prop_idx + 1, len(toks)):
                    idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == tok_idx]
                    if any(rel.startswith("ont:obj:") for rel in idx_rels):  # any() returns False on empty input
                        macro_rels.append({"rel": "prop", "from": prop_idx, "to": tok_idx})
                        break
        if len(size_sent_list) > 0 and len(no_size_sent_list) > 0:
            for no_size_sent_idx in no_size_sent_list:
                closest_size_sent_idx = min(
                    [(abs(size_sent_idx - no_size_sent_idx), size_sent_idx) for size_sent_idx in size_sent_list], key=lambda x: x[0]
                )[1]
                size_idx_list = [
                    idx for idx in list(range(sentence_ranges[closest_size_sent_idx][0], sentence_ranges[closest_size_sent_idx][1]))
                    if "ont:size" in [rel["rel"] for rel in rel_list if rel["to"] == idx]
                ]
                for idx in list(range(sentence_ranges[no_size_sent_idx][0], sentence_ranges[no_size_sent_idx][1])):
                    idx_rels = [rel["rel"] for rel in rel_list if rel["to"] == idx]
                    if any(rel.startswith("ont:obj:") for rel in idx_rels):  # any() returns False on empty input
                        # according to the processing above, all objects in sentence are not connected to size info, so no check is needed
                        for size_idx in size_idx_list:
                            macro_rels.append({"rel": "size", "from": size_idx, "to": idx})

        return macro_rels

    def _normalize_attr(ont, morph_an, attr_name):
        norm_attr_name = morph_an.parse(attr_name)[0].normal_form
        res = ont.query(
            "SELECT DISTINCT ?attr_obj ?class_obj "
            "WHERE { "
            "    VALUES ?class_obj {local:gender local:season local:material} "
            "    ?attr_obj local:is_included ?class_obj . "
            "    ?attr_obj local:is_included local:parsed_attributes . "
            f"    ?attr_obj local:has_name \"{norm_attr_name}\" . "
            "}"
        )
        assert len(res) == 1
        res = list(res)
        attr_obj = res[0][0].n3(ont.namespace_manager)
        attr_type = res[0][1].n3(ont.namespace_manager)
        if attr_type == "local:gender":
            key = "gender"
            if attr_obj == "local:Man":
                val = cloth_handler.ClothFact.Gender.MAN
            elif attr_obj == "local:Woman":
                val = cloth_handler.ClothFact.Gender.WOMAN
            elif attr_obj == "local:Unisex":
                val = cloth_handler.ClothFact.Gender.UNISEX
            else:
                raise ValueError(f"Unknown gender object: {attr_obj}")
        elif attr_type == "local:season":
            key = "season"
            if attr_obj == "local:DemiSeason":
                val = cloth_handler.ClothFact.Season.DEMI_SEASON
            elif attr_obj == "local:Winter":
                val = cloth_handler.ClothFact.Season.WINTER
            elif attr_obj == "local:Summer":
                val = cloth_handler.ClothFact.Season.SUMMER
            else:
                raise ValueError(f"Unknown season object: {attr_obj}")
        elif attr_type == "local:material":
            key = "material"
            val = attr_obj
        else:
            raise ValueError(f"Unknown attribute type: {attr_type}")
        return key, val

    relation_list, toks, sentence_ranges = _get_all_word_relations(text, ont, ont_stat, morph_an, size_rule)
    macro_rel_list = _infer_macro_relations(relation_list, sentence_ranges)

    out_obj_list = []
    for idx in range(len(toks)):
        rels = [rel["rel"] for rel in relation_list if rel["to"] == idx]
        obj_rel_list = [rel for rel in rels if rel.startswith("ont:obj:")]
        assert len(obj_rel_list) <= 1
        if len(obj_rel_list) == 1:
            prop_dict = {}
            for m_rel in macro_rel_list:
                if m_rel["rel"] == "prop" and m_rel["to"] == idx:
                    k, v = _normalize_attr(ont, morph_an, toks[m_rel["from"]])
                    prop_dict[k] = v

            size_text = ""
            for m_rel in macro_rel_list:
                if m_rel["rel"] == "size" and m_rel["to"] == idx:
                    tok = toks[m_rel["from"]]
                    size_text += f" {tok}" if len(size_text) > 0 and not tok.startswith("-") else tok
            if len(size_text) > 0:
                parser = YrgParser(size_rule)
                matched_trees = list(parser.findall(size_text))
                assert len(matched_trees) > 0
                # we take only the longest match, from left to right
                matched_trees = sorted(matched_trees, key=lambda m: (m.span.stop - m.span.start, m.span.start), reverse=True)
                size_info = matched_trees[0].fact
            else:
                size_info = None
            out_obj_list.append(
                cloth_handler.ClothFact(obj_rel_list[0], toks[idx], size_info, prop_dict)
            )

    return out_obj_list


def create_size_info_rule():
    # === indirect size and gender information ===

    o_size_indirect_info = yrg_fact(
        "size_indirect_info", ["keyword", "year_info_from_y", "year_info_from_m", "year_info_to_y", "year_info_to_m"]
    )
    r_size_gender_indirect_info = yrg_rule(
        yrg_r_or(
            yrg_rp_caseless("на"),
            yrg_rp_caseless("для"),
        ).optional(),
        yrg_morph_pipeline([
            "мальчик",
            "девочка",
            "мужчина",
            "женщина",
            "ребёнок",
            "взрослый",
            "школьник",
            "школьница",
        ]).interpretation(o_size_indirect_info.keyword.normalized()),
    )
    r_size_year_info = yrg_r_or(
        yrg_rule(
            yrg_rp_type("INT").interpretation(o_size_indirect_info.year_info_from_y),
            yrg_rule(
                yrg_rp_eq("-"),
                yrg_rp_type("INT").interpretation(o_size_indirect_info.year_info_to_y)
            ).optional(),
            yrg_morph_pipeline(["лет", "год"]),
        ),
        yrg_rule(
            yrg_rp_type("INT").interpretation(o_size_indirect_info.year_info_from_m),
            yrg_rule(
                yrg_rp_eq("-"),
                yrg_rp_type("INT").interpretation(o_size_indirect_info.year_info_to_m)
            ).optional(),
            yrg_morph_pipeline(["месяц", "мес"]),
        ),
    ).interpretation(o_size_indirect_info)
    r_size_year_gender_indirect_info = yrg_rule(
        r_size_gender_indirect_info,
        r_size_year_info.optional(),
    ).interpretation(o_size_indirect_info)

    # === direct size and gender information ===

    o_size_number = yrg_fact("size_number", ["int_part", "frac_part"])
    r_size_number = yrg_rule(
        yrg_r_and(
            yrg_rp_gte(cloth_handler.MIN_CLOTHES_SIZE_INT),
            yrg_rp_lte(cloth_handler.MAX_CLOTHES_SIZE_INT),
        ).interpretation(o_size_number.int_part),
        yrg_r_or(
            yrg_rule(
                yrg_rp_eq("."),
                yrg_rp_type("INT").interpretation(o_size_number.frac_part),
            ),
            yrg_rule(
                yrg_rp_caseless("с"),
                yrg_rp_caseless("половиной")
            ).interpretation(o_size_number.frac_part.const("5")),
        ).optional(),
    ).interpretation(o_size_number)
    o_size_number_list = yrg_fact("size_number_list", ["from_info", "to_info"])
    r_size_number_list = yrg_rule(
        r_size_number.interpretation(o_size_number_list.from_info),
        yrg_rule(
            yrg_rp_eq("-"),  # all types of dashes are converted to "-" on preprocessing
            r_size_number.interpretation(o_size_number_list.to_info),
        ).optional(),
    ).interpretation(o_size_number_list)

    o_size_letters = yrg_fact("size_letters", ["letters"])
    r_size_letters = yrg_rule(
        yrg_r_and(   # tokenizer splits numbers from letters, so 10XL becomes '10', 'XL'
            yrg_rp_gte(2),
            yrg_rp_lte(cloth_handler.MAX_CLOTHES_SIZE_X_COUNT),
        ).optional(),
        yrg_rp_custom(lambda tok: cloth_handler.ClothFact._is_size_letters(tok)),
    ).interpretation(o_size_letters.letters).interpretation(o_size_letters)
    o_size_letters_list = yrg_fact("size_letters_list", ["from_info", "to_info"])
    r_size_letters_list = yrg_rule(
        r_size_letters.interpretation(o_size_letters_list.from_info),
        yrg_rule(
            yrg_rp_eq("-"),  # all types of dashes are converted to "-" on preprocessing
            r_size_letters.interpretation(o_size_letters_list.to_info),
        ).optional(),
    ).interpretation(o_size_letters_list)

    n_size_word = yrg_r_or(
        yrg_rule(yrg_rp_normalized("размер")),
        yrg_rule(
            yrg_rp_caseless("р"),
            yrg_rp_eq(".").optional()
        ),
    )
    o_size_direct_values = yrg_fact("size_direct_values", ["direct_values"])
    r_size_direct_values = yrg_r_or(
        yrg_rule(
            n_size_word.optional(),
            yrg_r_or(
                r_size_number_list,
                r_size_letters_list,
            ).interpretation(o_size_direct_values.direct_values),
            n_size_word.optional(),
        ),
        yrg_rule(
            r_size_number_list,
            n_size_word,
        ).interpretation(o_size_direct_values.direct_values),
    ).interpretation(o_size_direct_values)

    # === general size information ===

    o_size_info = yrg_fact("size_info", ["direct_values", "indirect_values"])
    r_size_info = yrg_r_or(
        r_size_year_gender_indirect_info.interpretation(o_size_info.indirect_values),
        r_size_direct_values.interpretation(o_size_info.direct_values),
    ).interpretation(o_size_info)

    return r_size_info
