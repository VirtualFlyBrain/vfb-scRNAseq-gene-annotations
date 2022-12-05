import pandas as pd
import numpy

with open("tmp/scRNAseq_FBgn_list.txt", 'r') as f:
    gene_list = f.read().splitlines()
GAF = pd.read_csv('tmp/gene_association.tsv', sep='\t', skiprows=5, header=None, names=['DB', 'FBgn', 'gene_symbol', 'relationship', 'GO', 'xref', 'evidence', 'annotation_id', 'aspect', 'gene_name', 'gene_synonyms', 'gene_type', 'taxon', 'date', 'assigned_by', 'empty1', 'empty2'], index_col=False)

# remove cols that we are not going to use
GAF = GAF.drop(['DB', 'gene_symbol', 'evidence', 'annotation_id', 'gene_name', 'gene_synonyms', 'gene_type', 'taxon', 'date', 'assigned_by', 'empty1', 'empty2'], axis=1)

# remove NOT annotations
GAF = GAF[(GAF['FBgn'].isin(gene_list)) & (GAF['aspect']=='F') & (~GAF['relationship'].str.contains('NOT'))]
GAF = GAF.drop(['aspect'], axis=1)

# edit refs to FlyBase
GAF['FBgn'] = GAF['FBgn'].apply(lambda x: 'http://flybase.org/reports/' + x)
GAF['xref'] = GAF['xref'].apply(lambda x: x.replace('FB:', 'FlyBase:'))

# make columns for each relationship type
GAF_by_rel = GAF.pivot(columns='relationship', values='GO')
GAF = GAF.join(GAF_by_rel).drop(['relationship', 'GO'], axis=1)
new_cols = list(GAF.columns)
new_cols.remove('FBgn')
new_cols.remove('xref')

# Add template instruction row
empty_row = pd.DataFrame([[""] * len(GAF.columns)], columns=GAF.columns)
GAF = pd.concat([empty_row, GAF], ignore_index=True)
GAF['FBgn'][0] = 'ID'
GAF['xref'][0] = '>A oboInOwl:hasDbXref SPLIT=|'

# split refs by relationship
for col in new_cols:
    GAF.insert(GAF.columns.get_loc(col) + 1, col + "_ref", GAF.xref)
    GAF[col][0] = 'SC \"' + col.replace('_', ' ') + '\" some %'
GAF = GAF.drop(['xref'], axis=1)

GAF.to_csv('tmp/GO_template.tsv', sep='\t', index=False)

# write sparql query
functions = pd.read_csv('gene_functions.tsv', sep='\t')

GO_cols = [col for col in GAF.columns if '%' in GAF.loc[0, col]]
all_GO = GAF.loc[1:, GO_cols].to_numpy().ravel()
unique_GO = list(set(all_GO[~pd.isnull(all_GO)]))
parents = set(functions.loc[:, 'term_id'])
parents_GO = [p for p in parents if 'GO:' in p]

with open("../sparql/GO_subclasses.sparql", 'w') as file:
    file.write("prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n")
    file.write("prefix GO: <http://purl.obolibrary.org/obo/GO_>\n\n")
    file.write("SELECT ?child ?parent\n")
    file.write("WHERE { ?child rdfs:subClassOf+ ?parent \n")
    file.write("FILTER ( ?child IN (" + ', '.join(unique_GO) + ")\n")
    file.write("&& ?parent IN (" + ', '.join(parents_GO) + ") ) }")
