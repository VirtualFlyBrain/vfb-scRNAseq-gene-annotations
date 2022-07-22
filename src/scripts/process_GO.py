import pandas as pd

with open("tmp/FBgn_list.txt", 'r') as f:
    gene_list = f.read().splitlines()
GAF = pd.read_csv('tmp/gene_association.tsv', sep='\t', skiprows=5, header=None, names=['DB', 'FBgn', 'gene_symbol', 'relationship', 'GO', 'xref', 'evidence', 'annotation_id', 'aspect', 'gene_name', 'gene_synonyms', 'gene_type', 'taxon', 'date', 'assigned_by', 'empty1', 'empty2'], index_col=False)

GAF = GAF.drop(['DB', 'gene_symbol', 'evidence', 'annotation_id', 'gene_name', 'gene_synonyms', 'gene_type', 'taxon', 'date', 'assigned_by', 'empty1', 'empty2'], axis=1)

GAF = GAF[(GAF['FBgn'].isin(gene_list)) & (GAF['aspect']=='F') & (~GAF['relationship'].str.contains('NOT'))]
GAF = GAF.drop(['aspect'], axis=1)

GAF['FBgn'] = GAF['FBgn'].apply(lambda x: 'http://flybase.org/reports/' + x)
GAF['xref'] = GAF['xref'].apply(lambda x: x.replace('FB:', 'FlyBase:'))

GAF_by_rel = GAF.pivot(columns='relationship', values='GO')
GAF = GAF.join(GAF_by_rel).drop(['relationship', 'GO'], axis=1)
new_cols = list(GAF.columns)
new_cols.remove('FBgn')
new_cols.remove('xref')

empty_row = pd.DataFrame([[""] * len(GAF.columns)], columns=GAF.columns)
GAF = empty_row.append(GAF, ignore_index=True)
GAF['FBgn'][0] = 'ID'
GAF['xref'][0] = '>A oboInOwl:hasDbXref SPLIT=|'

for col in new_cols:
    GAF.insert(GAF.columns.get_loc(col) + 1, col + "_ref", GAF.xref)
    GAF[col][0] = 'SC \"' + col.replace('_', ' ') + '\" some %'
GAF = GAF.drop(['xref'], axis=1)

GAF.to_csv('tmp/GO_template.tsv', sep='\t', index=False)
