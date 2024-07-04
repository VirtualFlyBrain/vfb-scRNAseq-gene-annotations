import pandas as pd

with open("tmp/vfb-RNAseq-genes.txt", 'r') as f:
    gene_list = f.read().splitlines()
GG = pd.read_csv('tmp/gene_group_data.tsv', sep='\t', skiprows=8, index_col=False)

GG = GG.drop(['FB_group_symbol', 'FB_group_name', 'Parent_FB_group_id', 'Parent_FB_group_symbol', 'Group_member_FB_gene_symbol'], axis=1)
GG = GG.rename({'## FB_group_id': 'GG_ID', 'Group_member_FB_gene_id':'FBgn'}, axis=1)

GG = GG[GG['FBgn'].isin(gene_list)]

GG = GG.applymap(lambda x: 'http://flybase.org/reports/' + x)

template_string_row = pd.DataFrame([["SC \"part of\" some %"] * len(GG.columns)], columns=GG.columns)
template_string_row['FBgn'][0] = "ID"

GG = pd.concat([template_string_row, GG]).reset_index(drop=True)

GG.to_csv('tmp/GG_template.tsv', sep='\t', index=False)

# write sparql query
functions = pd.read_csv('gene_functions.tsv', sep='\t')

pre_unique_GG = set(GG.loc[1:, 'GG_ID'])
unique_GG = ['<'+gg+'>' for gg in pre_unique_GG]
parents = set(functions.loc[:, 'term_id'])
parents_GG = ['<'+p+'>' for p in parents if 'http:' in p]

with open("../sparql/GG_subclasses.sparql", 'w') as file:
    file.write("prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n\n")
    file.write("SELECT ?child ?parent\n")
    file.write("WHERE { ?child rdfs:subClassOf+ ?parent \n")
    file.write("FILTER ( ?child IN (" + ', '.join(unique_GG) + ")\n")
    file.write("&& ?parent IN (" + ', '.join(parents_GG) + ") ) }")
