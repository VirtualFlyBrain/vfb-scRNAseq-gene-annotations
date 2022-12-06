import re

with open("tmp/gene_groups.obo", "r") as fr:
    gg_lines = fr.readlines()

new_gg_lines = []
for l in gg_lines:
    new_gg_lines.append(re.sub(r" (FBgg[0-9]+)", r" http://flybase.org/reports/\1", l))
    if "id:" in l:
        new_gg_lines.append("property_value: http://n2o.neo/custom/self_xref \"FlyBase\" xsd:string\n")

new_gg_lines.insert(3, "ontology: http://purl.obolibrary.org/obo/VFB_scRNAseq_genes/components/gene_groups.obo\n")

with open('components/gene_groups.obo', 'w') as fw:
    for l in new_gg_lines:
        fw.write(l)
