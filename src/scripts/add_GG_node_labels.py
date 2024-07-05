import pandas as pd

# files
functions = pd.read_csv('gene_functions.tsv', sep='\t')
existing_template = pd.read_csv('tmp/GG_template.tsv', sep='\t')
subclass_map = pd.read_csv('tmp/GG_subclasses.tsv', sep='\t')

# make iri:label map
subclass_map = subclass_map.map(lambda x: x.lstrip('<').rstrip('>'))
functions_merged = functions.merge(subclass_map, how='left', left_on='term_id', right_on='?parent')
merged_1 = functions_merged.loc[:,['term_id','label']]
merged_1 = merged_1.rename({'term_id': 'GG_ID', 'label': 'node_labels'}, axis=1)
merged_2 = functions_merged.loc[:,['?child','label']]
merged_2 = merged_2.rename({'?child': 'GG_ID', 'label': 'node_labels'}, axis=1)
label_map = pd.concat([merged_1, merged_2], ignore_index=True).drop_duplicates()
label_map = (label_map.groupby(['GG_ID']).agg({'node_labels': lambda x: "|".join(x)}).reset_index())

# merge labels into exisitng template
new_template = existing_template.merge(label_map, how='left', on='GG_ID')
new_template.loc[0, 'node_labels'] = "A http://n2o.neo/property/nodeLabel SPLIT=|"

new_template.to_csv('tmp/GG_template.tsv', sep='\t', index=False)
