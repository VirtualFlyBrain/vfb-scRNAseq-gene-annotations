## Customize Makefile settings for VFB_scRNAseq_genes
## 
## If you need to customize your Makefile, make
## changes here rather than in the main Makefile

.PHONY: prepare_release_notest
# this prepares a release without running any tests - tests are very slow
prepare_release_notest: odkversion $(SRC) all_imports $(RELEASE_ASSETS)
	rsync -R $(RELEASE_ASSETS) $(RELEASEDIR) &&\
	rm -f $(CLEANFILES) $(ALL_TERMS_COMBINED) &&\
	echo "Release files are now in $(RELEASEDIR) - now you should commit, push and make a release on your git hosting site such as GitHub or GitLab"


$(SRC): $(TMPDIR)/FBgns.owl $(TMPDIR)/GO_annotations.owl $(TMPDIR)/GG_annotations.owl $(TMPDIR)/FB_entities.owl
	$(ROBOT) merge \
		--input VFB_scRNAseq_genes-annotations.ofn \
		--input $< \
		--input $(TMPDIR)/GO_annotations.owl \
		--input $(TMPDIR)/GG_annotations.owl \
		--input $(TMPDIR)/FB_entities.owl \
		--include-annotations true --collapse-import-closure false \
		convert --format ofn \
		-o $@ &&\
	rm -rf  $(TMPDIR)/FBgns.tsv $(SCRIPTSDIR)/vfb $(SPARQLDIR)/GO_subclasses.sparql $(SPARQLDIR)/GG_subclasses.sparql
	echo "\nOntology source file updated!\n"

########## Installations

.PHONY: setup_venv
setup_venv:
	apt-get update
	apt-get -y install python3.12-venv
	python3 -m venv my-venv

install_requirements: setup_venv
	my-venv/bin/pip install -r $(SCRIPTSDIR)/requirements.txt

get_vfb_code:
	cd $(SCRIPTSDIR) &&\
	wget https://github.com/VirtualFlyBrain/VFB_neo4j/archive/master.tar.gz &&\
	mkdir -p vfb && tar --strip-components=5 -xvf master.tar.gz VFB_neo4j-master/src/uk/ac/ebi/vfb &&\
	rm master.tar.gz && cd ../ontology

# adding stripping label-annotated annotation axioms from merged import to requirements
$(ONT)-full.owl: strip_import_axioms

all_imports: strip_import_axioms

.PHONY: strip_import_axioms
strip_import_axioms: $(IMPORTDIR)/merged_import.owl
	cat $< | grep -v '^AnnotationAssertion[(]Annotation[(]rdfs:label' > $<.tmp &&\
	mv $<.tmp $<

# files for gene annotations
# Genes used by the scRNAseq and EPseq expression data. EPseq is moving from its old
# release files (src/ontology/reports/) to expression/ in the same repo (every
# project's genes); both lists are included until the old EPseq load is retired.
$(TMPDIR)/vfb-RNAseq-genes.txt: | $(TMPDIR)
	wget -O $(TMPDIR)/vfb-scRNAseq-new-genes.txt https://raw.githubusercontent.com/VirtualFlyBrain/vfb-scRNAseq/main/expression/FBgn_list.txt &&\
	wget -O $(TMPDIR)/vfb-EPseq-genes.txt https://raw.githubusercontent.com/VirtualFlyBrain/vfb-EPseq-ontology/main/src/ontology/reports/FBgn_list.txt &&\
	wget -O $(TMPDIR)/vfb-EPseq-new-genes.txt https://raw.githubusercontent.com/VirtualFlyBrain/vfb-EPseq-ontology/main/expression/FBgn_list.txt &&\
	cat $(TMPDIR)/vfb-scRNAseq-new-genes.txt $(TMPDIR)/vfb-EPseq-genes.txt $(TMPDIR)/vfb-EPseq-new-genes.txt | sort | uniq > $@ &&\
	rm $(TMPDIR)/vfb-scRNAseq-new-genes.txt $(TMPDIR)/vfb-EPseq-genes.txt $(TMPDIR)/vfb-EPseq-new-genes.txt

# FlyBase stocks (FBst), strains (FBsn) and genetic entities (FBal / FBti / FBtp /
# FBco) that vfb-scRNAseq's Samples link, labelled and typed from FlyBase Chado so VFB
# shows their names (stocks: FBsv 'living stock', whose FBsv classes come from Chado
# too as FBsv is not published; strains: GENO 'strain or breed'). Ids
# that VFB_drivers already defines are left to it, so none gets a second label.
$(TMPDIR)/FB_entity_list.txt: | $(TMPDIR)
	wget -O $(TMPDIR)/vfb-scRNAseq-FB-entities.txt https://raw.githubusercontent.com/VirtualFlyBrain/vfb-scRNAseq/main/metadata/FlyBase_entity_list.txt &&\
	wget -O $(TMPDIR)/VFB_drivers.owl http://virtualflybrain.org/data/VFB/OWL/VFB_drivers.owl &&\
	grep -oE 'FB(st|sn|al|ti|tp|co)[0-9]{7}' $(TMPDIR)/VFB_drivers.owl | sort -u > $(TMPDIR)/VFB_drivers_ids.txt &&\
	sort -u $(TMPDIR)/vfb-scRNAseq-FB-entities.txt | comm -23 - $(TMPDIR)/VFB_drivers_ids.txt > $@ &&\
	rm $(TMPDIR)/vfb-scRNAseq-FB-entities.txt $(TMPDIR)/VFB_drivers.owl $(TMPDIR)/VFB_drivers_ids.txt

$(TMPDIR)/FB_entities.owl: get_vfb_code install_requirements $(TMPDIR)/FB_entity_list.txt | $(REPORTDIR)
	my-venv/bin/python3 $(SCRIPTSDIR)/entity_template_runner.py &&\
	$(ROBOT) template --template $(TMPDIR)/FB_feature_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $(TMPDIR)/FB_features.owl &&\
	$(ROBOT) template --template $(TMPDIR)/FBsv_template.tsv \
		--output $(TMPDIR)/FBsv.owl &&\
	$(ROBOT) template --template $(TMPDIR)/FB_stock_template.tsv \
		--input $(TMPDIR)/FBsv.owl \
		--output $(TMPDIR)/FB_stocks.owl &&\
	$(ROBOT) merge --input $(TMPDIR)/FB_features.owl --input $(TMPDIR)/FBsv.owl \
		--input $(TMPDIR)/FB_stocks.owl \
		--output $@ &&\
	echo "\nFlyBase stock, strain and genotype entities updated\n"

# DOWNLOAD MANUALLY USING BROWSER:
# 1. gene groups obo file
# https://svn.flybase.org/flybase/release_browse_lists/<latest FB release>/ > tmp/gene_groups.obo
# then make components/gene_groups.obo
# from https://s3ftp.flybase.org/releases/current/precomputed_files/:
# all dated now (`current` in url doesn't work)
# 2. mapped FBgns
# https://s3ftp.flybase.org/releases/current/precomputed_files/genes/fbgn_fbtr_fbpp_<current>.tsv.gz > tmp/fbgn_fbtr_fbpp.tsv.gz
# 3. GAF
# https://s3ftp.flybase.org/releases/current/precomputed_files/go/gene_association.fb.gz > tmp/gene_association.tsv.gz
# 4. GG data
# https://s3ftp.flybase.org/releases/current/precomputed_files/genes/gene_group_data_<current>.tsv.gz > tmp/gene_group_data.tsv.gz
# scripted download from s3ftp doesn't work
# wget -O $(TMPDIR)/FBgns.tsv.gz https://s3ftp.flybase.org/releases/current/precomputed_files/genes/fbgn_fbtr_fbpp_fb_2025_02.tsv.gz
$(TMPDIR)/mapped_FBgn_list.txt: setup_venv $(TMPDIR)/vfb-RNAseq-genes.txt | $(TMPDIR)
	test -f $(TMPDIR)/fbgn_fbtr_fbpp.tsv || gzip -df $(TMPDIR)/fbgn_fbtr_fbpp.tsv.gz &&\
	my-venv/bin/python3 $(SCRIPTSDIR)/process_FBgn.py &&\
	echo "\nMapped FBgn list updated\n"

$(TMPDIR)/FBgns.owl: get_vfb_code install_requirements $(TMPDIR)/mapped_FBgn_list.txt | $(REPORTDIR)
	my-venv/bin/python3 $(SCRIPTSDIR)/feature_template_runner.py &&\
	$(ROBOT) template --template $(TMPDIR)/FBgn_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $@ &&\
	echo "\nFBgn annotations updated\n"

$(TMPDIR)/GO_annotations.owl: setup_venv $(TMPDIR)/vfb-RNAseq-genes.txt
	test -f $(TMPDIR)/gene_association.tsv || gzip -df $(TMPDIR)/gene_association.tsv.gz &&\
	my-venv/bin/python3 $(SCRIPTSDIR)/process_GO.py &&\
	$(ROBOT) query --input-iri http://purl.obolibrary.org/obo/go.owl \
		--query $(SPARQLDIR)/GO_subclasses.sparql $(TMPDIR)/GO_subclasses.tsv &&\
	my-venv/bin/python3 $(SCRIPTSDIR)/add_GO_node_labels.py &&\
	$(ROBOT) template --template $(TMPDIR)/GO_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $@ &&\
	echo "\nGO annotations updated\n"

$(TMPDIR)/GG_annotations.owl: setup_venv $(TMPDIR)/vfb-RNAseq-genes.txt
	test -f $(TMPDIR)/gene_group_data.tsv || gzip -df $(TMPDIR)/gene_group_data.tsv.gz &&\
	my-venv/bin/python3 $(SCRIPTSDIR)/process_GG.py &&\
	$(ROBOT) query --input $(COMPONENTSDIR)/gene_groups.obo \
		--query $(SPARQLDIR)/GG_subclasses.sparql $(TMPDIR)/GG_subclasses.tsv &&\
	my-venv/bin/python3 $(SCRIPTSDIR)/add_GG_node_labels.py &&\
	$(ROBOT) template --template $(TMPDIR)/GG_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $@ &&\
	echo "\nGene Group annotations updated\n"

# A new gene_group_*.obo file can be found at:
# https://svn.flybase.org/flybase/release_browse_lists/<latest FB release>/
# (requires login)
# After copying to tmp (as 'gene_groups.obo'), the following goal should then be updated manually:
$(COMPONENTSDIR)/gene_groups.obo: setup_venv $(TMPDIR)/gene_groups.obo
	my-venv/bin/python3 $(SCRIPTSDIR)/process_FBgg.py &&\
	echo "\nGene Group ontology updated\n"

# This file must be manually updated (see above)
$(TMPDIR)/gene_groups.obo:
	echo $@

