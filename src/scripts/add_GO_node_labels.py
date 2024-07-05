import pandas as pd

# files
functions = pd.read_csv('gene_functions.tsv', sep='\t')
existing_template = pd.read_csv('tmp/GO_template.tsv', sep='\t')
subclass_map = pd.read_csv('tmp/GO_subclasses.tsv', sep='\t')

# make iri:label map
subclass_map = subclass_map.map(lambda x: x.rstrip('>').replace("<http://purl.obolibrary.org/obo/GO_", "GO:"))
functions_merged = functions.merge(subclass_map, how='left', left_on='term_id', right_on='?parent')
merged_1 = functions_merged.loc[:,['term_id','label']]
merged_1 = merged_1.rename({'term_id': 'GO_ID', 'label': 'node_labels'}, axis=1)
merged_2 = functions_merged.loc[:,['?child','label']]
merged_2 = merged_2.rename({'?child': 'GO_ID', 'label': 'node_labels'}, axis=1)
label_map = pd.concat([merged_1, merged_2], ignore_index=True).drop_duplicates()
label_map = (label_map.groupby(['GO_ID']).agg({'node_labels': lambda x: "|".join(x)}).reset_index())
label_dict = dict(zip(label_map.loc[:,'GO_ID'],label_map.loc[:,'node_labels']))

# merge labels into exisitng template
GO_cols = [col for col in existing_template.columns if '%' in existing_template.loc[0, col]]
new_template = existing_template
new_template['node_labels'] = ''

def f(ID, labels):
    if ID and not labels and ID in label_dict.keys():
        return label_dict[ID]

for col in GO_cols:
    new_template['node_labels'] = new_template.apply(lambda x: f(x[col], x['node_labels']), axis=1)

new_template.loc[0, 'node_labels'] = "A http://n2o.neo/property/nodeLabel SPLIT=|"

new_template.to_csv('tmp/GO_template.tsv', sep='\t', index=False)
