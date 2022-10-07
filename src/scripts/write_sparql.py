import pandas as pd

GG = pd.read_csv('tmp/GG_template.tsv', sep='\t').applymap(str)
GO = pd.read_csv('tmp/GO_template.tsv', sep='\t').applymap(str)
functions = pd.read_csv('gene_functions.tsv', sep='\t')

pre_unique_GG = set(GG.loc[1:, 'GG_ID'])
unique_GG = ['<'+gg+'>' for gg in pre_unique_GG]
GO_cols = [col for col in GO.columns if '%' in GO.loc[0, col]]
unique_GO = list(pd.unique(GO.loc[1:, GO_cols].values.ravel('K')))
unique_GO.remove('nan')
parents = set(functions.loc[:, 'term_id'])
parents_GG = ['<'+p+'>' for p in parents if 'http:' in p]
parents_GO = [p for p in parents if 'GO:' in p]

with open("../sparql/GO_subclasses.sparql", 'w') as file:
    file.write("prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n")
    file.write("prefix GO: <http://purl.obolibrary.org/obo/GO_>\n\n")
    file.write("SELECT ?child ?parent\n")
    file.write("WHERE { ?child rdfs:subClassOf+ ?parent \n")
    file.write("FILTER ( ?child IN (" + ', '.join(unique_GO) + ")\n")
    file.write("&& ?parent IN (" + ', '.join(parents_GO) + ") ) }")

with open("../sparql/GG_subclasses.sparql", 'w') as file:
    file.write("prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n\n")
    file.write("SELECT ?child ?parent\n")
    file.write("WHERE { ?child rdfs:subClassOf+ ?parent \n")
    file.write("FILTER ( ?child IN (" + ', '.join(unique_GG) + ")\n")
    file.write("&& ?parent IN (" + ', '.join(parents_GG) + ") ) }")