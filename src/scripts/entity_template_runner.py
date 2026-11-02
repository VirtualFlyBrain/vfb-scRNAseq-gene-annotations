"""ROBOT templates for the FlyBase stocks, strains and genetic entities that
vfb-scRNAseq's Samples link (its metadata/FlyBase_entity_list.txt), so VFB can
show their names and tell them apart.

- Genetic entities (FBal / FBti / FBtp / FBco) are Chado features: the same
  FeatureMover template as the genes (label, synonyms, SO type), plus node label
  Feature, which VFB's other FlyBase alleles / insertions / constructs carry (set by
  VFB_neo4j's FeatureMover.add_features) and VFBquery's stock queries key on.
- Stocks (FBst) are named individuals labelled "<genotype> (<collection>
  <stock number>)", e.g. "w[1118] (BDSC 3605)", typed with their Chado stock state
  (FBsv:0000002 'living stock') and node label Stock.
- Strains (FBsn) are named individuals labelled with the strain name, e.g.
  "DGRP-28", with FlyBase's synonyms, typed GENO:0000112 'strain or breed' and
  node label Strain.
- The FBsv terms used, with their is_a ancestors, are declared as classes from
  Chado (label, definition, parents): FBsv (FlyBase's stock vocabulary) is not
  published as an ontology, so this is VFB's only source for it.

Ids VFB_drivers already defines are dropped by the Makefile first, so no entity
gets a second label. Ids FlyBase doesn't have are listed in
reports/missing_FB_entities.txt.
"""
import collections
import os

import pandas as pd

import vfb.neo4j.flybase2neo.feature_tools as feature_tools

ENTITY_LIST = "tmp/FB_entity_list.txt"
FEATURE_TEMPLATE = "tmp/FB_feature_template.tsv"
STOCK_TEMPLATE = "tmp/FB_stock_template.tsv"
FBSV_TEMPLATE = "tmp/FBsv_template.tsv"
MISSING = "reports/missing_FB_entities.txt"
FEATURES_MISSING = "tmp/missing_FB_features.txt"

FLYBASE = "http://flybase.org/reports/"
OBO = "http://purl.obolibrary.org/obo/"
STRAIN_CLASS = OBO + "GENO_0000112"          # strain or breed

#: Short names for stock centres in stock labels; any other centre is named in full.
COLLECTIONS = {
    "Bloomington Drosophila Stock Center": "BDSC",
    "Vienna Drosophila Resource Center": "VDRC",
    "Kyoto Stock Center": "Kyoto",
    "National Institute of Genetics Fly Stocks": "NIG-Fly",
}


def robot_escape(column):
    """ROBOT template reads a backslash as an escape, so FlyBase symbols such as
    Scer\\GAL4 lost theirs ("ScerGAL4"); double it to keep it."""
    return column.astype(str).str.replace("\\", "\\\\", regex=False)


def in_list(ids):
    return "','".join(ids)


def fbsv_iri(accession):
    return OBO + "FBsv_" + accession


def write_template(path, header, rows):
    """A ROBOT template: column names, the ROBOT header row, then the rows."""
    body = pd.DataFrame.from_records(rows, columns=list(header)).apply(robot_escape)
    pd.concat([pd.DataFrame([header]), body]).to_csv(path, sep="\t", index=False)


with open(ENTITY_LIST) as f:
    ids = [i for i in f.read().splitlines() if i]
stocks = [i for i in ids if i.startswith("FBst")]
strains = [i for i in ids if i.startswith("FBsn")]
features = [i for i in ids if not i.startswith(("FBst", "FBsn"))]

fm = feature_tools.FeatureMover('http://pdb.virtualflybrain.org', 'vfb', 'vfb')
missing = []
fbsv_used = set()

# ---- Genetic entities: as the genes. An empty template still needs its header rows.
if os.path.exists(FEATURES_MISSING):
    os.remove(FEATURES_MISSING)                 # only written when something is missing
if features:
    fm.feature_robot_template(features, FEATURE_TEMPLATE, FEATURES_MISSING)
    if os.path.exists(FEATURES_MISSING):
        with open(FEATURES_MISSING) as f:
            missing += f.read().splitlines()
    # Chado types alleles `allele`, which FeatureMover maps to SO 'sequence
    # feature'; type them SO 'allele' as it does for alleles typed `gene`.
    ft = pd.read_csv(FEATURE_TEMPLATE, sep="\t", dtype=str, keep_default_na=False)
    is_allele = ft["iri"].str.contains("/FBal") & ft["feature_type"].str.endswith("SO_0000110")
    ft.loc[is_allele, "feature_type"] = OBO + "SO_0001023"
    ft["node_label"] = "Feature"
    ft.loc[0, "node_label"] = "A http://n2o.neo/property/nodeLabel"
    ft.iloc[1:] = ft.iloc[1:].apply(robot_escape)
    ft.to_csv(FEATURE_TEMPLATE, sep="\t", index=False)
else:
    write_template(FEATURE_TEMPLATE, {"iri": "ID", "label": "A rdfs:label"}, [])

# ---- Stocks and strains: named individuals, in one template.
header = collections.OrderedDict([
    ("iri", "ID"), ("type", "TYPE"), ("class", "TI %"), ("label", "A rdfs:label"),
    ("synonyms", "A oboInOwl:hasExactSynonym SPLIT=|"),
    ("node_label", "A http://n2o.neo/property/nodeLabel"),
    ("self_xref", "A http://n2o.neo/custom/self_xref")])
rows = []

if stocks:
    query = ("SELECT s.uniquename AS fbid, s.name, s.description, sc.uniquename AS collection, "
             "d.accession AS state "
             "FROM stock s "
             "JOIN cvterm st ON st.cvterm_id = s.type_id "
             "JOIN dbxref d ON d.dbxref_id = st.dbxref_id "
             "LEFT JOIN stockcollection_stock scs ON scs.stock_id = s.stock_id "
             "LEFT JOIN stockcollection sc ON sc.stockcollection_id = scs.stockcollection_id "
             "WHERE s.uniquename IN ('%s') ORDER BY fbid" % in_list(stocks))
    found = collections.OrderedDict()
    for r in fm.query_fb(query):
        found.setdefault(r["fbid"], r)          # first collection, if several
    for fbid in stocks:
        r = found.get(fbid)
        if r is None:
            missing.append(fbid)
            continue
        centre = COLLECTIONS.get(r["collection"], r["collection"])
        number = " ".join(x for x in (centre, r["name"]) if x)
        genotype = (r["description"] or "").strip()
        label = f"{genotype} ({number})" if genotype and number else (genotype or number or fbid)
        fbsv_used.add(r["state"])
        rows.append({
            "iri": FLYBASE + fbid, "type": "owl:NamedIndividual",
            "class": fbsv_iri(r["state"]), "label": label,
            "synonyms": "|".join(x for x in (genotype, number) if x and x != label),
            "node_label": "Stock", "self_xref": "FlyBase"})

if strains:
    names = {r["fbid"]: r["name"] for r in fm.query_fb(
        "SELECT uniquename AS fbid, name FROM strain "
        "WHERE uniquename IN ('%s') AND NOT is_obsolete" % in_list(strains))}
    synonyms = collections.defaultdict(set)
    for r in fm.query_fb(
            "SELECT s.uniquename AS fbid, sy.name FROM strain s "
            "JOIN strain_synonym ss ON ss.strain_id = s.strain_id "
            "JOIN synonym sy ON sy.synonym_id = ss.synonym_id "
            "WHERE s.uniquename IN ('%s')" % in_list(strains)):
        synonyms[r["fbid"]].add(r["name"])
    for fbid in strains:
        if fbid not in names:
            missing.append(fbid)
            continue
        rows.append({
            "iri": FLYBASE + fbid, "type": "owl:NamedIndividual",
            "class": STRAIN_CLASS, "label": names[fbid],
            "synonyms": "|".join(sorted(synonyms[fbid] - {names[fbid]})),
            "node_label": "Strain", "self_xref": "FlyBase"})

write_template(STOCK_TEMPLATE, header, rows)

# ---- FBsv classes used, with their is_a ancestors, from Chado.
fbsv_rows = {}
todo = set(fbsv_used)
while todo:
    terms = fm.query_fb(
        "SELECT d.accession, ct.name, ct.definition, pd.accession AS parent "
        "FROM cvterm ct "
        "JOIN dbxref d ON d.dbxref_id = ct.dbxref_id "
        "JOIN db ON db.db_id = d.db_id AND db.name = 'FBsv' "
        "LEFT JOIN cvterm_relationship r ON r.subject_id = ct.cvterm_id "
        "  AND r.type_id = (SELECT cvterm_id FROM cvterm WHERE name = 'is_a' "
        "                   AND cv_id = (SELECT cv_id FROM cv WHERE name = 'relationship')) "
        "LEFT JOIN cvterm p ON p.cvterm_id = r.object_id "
        "LEFT JOIN dbxref pd ON pd.dbxref_id = p.dbxref_id "
        "WHERE d.accession IN ('%s')" % in_list(sorted(todo)))
    todo = set()
    for t in terms:
        row = fbsv_rows.setdefault(t["accession"], {
            "iri": fbsv_iri(t["accession"]), "label": t["name"],
            "definition": (t["definition"] or "").strip(), "parents": set()})
        if t["parent"]:
            row["parents"].add(fbsv_iri(t["parent"]))
            if t["parent"] not in fbsv_rows:
                todo.add(t["parent"])
write_template(
    FBSV_TEMPLATE,
    collections.OrderedDict([("iri", "ID"), ("label", "A rdfs:label"),
                             ("definition", "A IAO:0000115"),
                             ("parents", "SC % SPLIT=|")]),
    [dict(r, parents="|".join(sorted(r["parents"]))) for _, r in sorted(fbsv_rows.items())])

with open(MISSING, "w") as f:
    f.writelines(m + "\n" for m in missing)
if missing:
    print("WARNING - FlyBase entities not found (see %s): %s" % (MISSING, missing))
print("FlyBase entities: %d features, %d stocks/strains, %d FBsv classes templated"
      % (len(features), len(rows), len(fbsv_rows)))
