import pandas as pd

import vfb.neo4j.flybase2neo.feature_tools as feature_tools

TEMPLATE = "tmp/FBgn_template.tsv"

with open("tmp/mapped_FBgn_list.txt", 'r') as f:
    gene_list = f.read().splitlines()

fm = feature_tools.FeatureMover('http://pdb.virtualflybrain.org', 'vfb', 'vfb')
fm.feature_robot_template(gene_list, TEMPLATE, "reports/missing_FBgns.txt")

# Node label Gene. The release's polishing step also sets it on every FBgn class,
# but carrying it here means the genes are labelled even when polishing hasn't run,
# and VFB's hasScRNAseq gene labelling (Cluster -expresses-> :Gene) can rely on it.
template = pd.read_csv(TEMPLATE, sep="\t", dtype=str, keep_default_na=False)
template["node_label"] = "Gene"
template.loc[0, "node_label"] = "A http://n2o.neo/property/nodeLabel"
template.to_csv(TEMPLATE, sep="\t", index=False)
