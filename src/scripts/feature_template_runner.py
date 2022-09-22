import vfb.neo4j.flybase2neo.feature_tools as feature_tools

with open("tmp/mapped_FBgn_list.txt", 'r') as f:
    gene_list = f.read().splitlines()

fm = feature_tools.FeatureMover('http://pdb.virtualflybrain.org', 'vfb', 'vfb')
fm.feature_robot_template(gene_list, "tmp/FBgn_template.tsv")


