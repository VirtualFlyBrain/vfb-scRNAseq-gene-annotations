import pandas as pd

with open("tmp/FBgn_list.txt", 'r') as f:
    gene_list = f.read().splitlines()
GG = pd.read_csv('tmp/gene_group_data.tsv', sep='\t', skiprows=8, index_col=False)

GG = GG.drop(['FB_group_symbol', 'FB_group_name', 'Parent_FB_group_id', 'Parent_FB_group_symbol', 'Group_member_FB_gene_symbol'], axis=1)
GG = GG.rename({'## FB_group_id': 'GG_ID', 'Group_member_FB_gene_id':'FBgn'}, axis=1)

GG = GG[GG['FBgn'].isin(gene_list)]

GG = GG.applymap(lambda x: 'http://flybase.org/reports/' + x)

empty_row = pd.DataFrame([[""] * len(GG.columns)], columns=GG.columns)
GG['FBgn'][0] = "ID"
GG['GG_ID'][0] = "SC \"part of\" some %"

GG.to_csv('tmp/GG_template.tsv', sep='\t', index=False)
