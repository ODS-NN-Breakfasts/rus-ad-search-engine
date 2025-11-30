import ruwordnet  # https://github.com/avidale/python-ruwordnet
import rdflib


INITIAL_WORDS = ["одежда"]


def make_ontology(wn, ont_g, init_word_list):

    def _ont_obj(ent):
        return rdflib.URIRef("http://localhost/obj" + ent.id.replace("-", ""))

    for init_word in init_word_list:
        for sense in wn.get_senses(init_word):
            print(f"Initial word info: {sense.synset} <= {sense.synset.hypernyms}")

    o_ln = rdflib.Namespace("http://localhost/")
    ont_g.bind("local", o_ln)
    o_rel_sub = o_ln.is_subclass
    o_rel_incl = o_ln.is_included
    o_rel_name = o_ln.has_name
    o_rel_part = o_ln.has_part
    o_po = o_ln.parsed_objects

    top_entities = set()
    for w in init_word_list:
        for ent in wn.get_synsets(w):
            top_entities.add(ent)
    #        top_entities |= set(ent.domains)

    entities_to_process = top_entities.copy()
    processed_ents = set()
    while len(entities_to_process) > 0:
        ent = entities_to_process.pop()

        o_ent = _ont_obj(ent)

        for hyp_ent in ent.hyponyms:
            if hyp_ent in processed_ents:
                continue
            ont_g.add((_ont_obj(hyp_ent), o_rel_sub, o_ent))
            entities_to_process.add(hyp_ent)

        for part_ent in ent.meronyms:
            if part_ent in processed_ents:
                continue
            ont_g.add((o_ent, o_rel_part, _ont_obj(part_ent)))
            entities_to_process.add(part_ent)

        for name_ent in ent.senses:
            ont_g.add((o_ent, o_rel_name, rdflib.Literal(name_ent.name.lower())))
        ont_g.add((o_ent, o_rel_incl, o_po))
        print(ent)

        processed_ents.add(ent)

    return ont_g


if __name__ == "__main__":
    wn = ruwordnet.RuWordNet(filename_or_session="research/ruwordnet-2021.db")
    #initial_ont = (
    #    "@prefix local: <http://localhost/> ."
    #)
    ont_g = rdflib.Graph()
    #ont_g.parse(data=initial_ont, format="turtle")
    ont_g = make_ontology(wn, ont_g, INITIAL_WORDS)
    ont_g.serialize(destination="raw_ontology.ttl")
    print("Done")
