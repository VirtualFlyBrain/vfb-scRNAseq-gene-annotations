## Customize Makefile settings for VFB_scRNAseq_genes
## 
## If you need to customize your Makefile, make
## changes here rather than in the main Makefile

.PHONY: prepare_release_notest
# this prepares a release without running any tests - tests are very slow
prepare_release_notest: odkversion $(SRC) all_imports $(RELEASE_ASSETS)
	rm -f $(CLEANFILES) $(ALL_TERMS_COMBINED) &&\
	echo "Release files are now in $(RELEASEDIR) - now you should commit, push and make a release on your git hosting site such as GitHub or GitLab"


$(SRC): $(TMPDIR)/FBgns.owl $(TMPDIR)/GO_annotations.owl $(TMPDIR)/GG_annotations.owl
	$(ROBOT) merge \
		--input VFB_scRNAseq_genes-annotations.ofn \
		--input $< \
		--input $(TMPDIR)/GO_annotations.owl \
		--input $(TMPDIR)/GG_annotations.owl \
		--include-annotations true --collapse-import-closure false \
		convert --format ofn \
		-o $@ &&\
	rm -rf  $(TMPDIR)/FBgns.tsv $(SCRIPTSDIR)/vfb $(SPARQLDIR)/GO_subclasses.sparql $(SPARQLDIR)/GG_subclasses.sparql
	echo "\nOntology source file updated!\n"

# adding stripping label-annotated annotation axioms from merged import to requirements
$(ONT)-full.owl: strip_import_axioms

all_imports: strip_import_axioms

.PHONY: strip_import_axioms
strip_import_axioms: $(IMPORTDIR)/merged_import.owl
	cat $< | grep -v '^AnnotationAssertion[(]Annotation[(]rdfs:label' > $<.tmp &&\
	mv $<.tmp $<

# files for gene annotations
$(TMPDIR)/RNAseq_FBgn_list.txt: | $(TMPDIR)
	wget -O $(TMPDIR)/vfb-scRNAseq-genes.txt https://raw.githubusercontent.com/VirtualFlyBrain/vfb-scRNAseq-ontology/main/src/ontology/reports/FBgn_list.txt &&\
	wget -O $(TMPDIR)/vfb-EPseq-genes.txt https://raw.githubusercontent.com/VirtualFlyBrain/vfb-EPseq-ontology/main/src/ontology/reports/FBgn_list.txt &&\
	cat $(TMPDIR)/vfb-scRNAseq-genes.txt $(TMPDIR)/vfb-scRNAseq-genes.txt | sort | uniq > $@ &&\
	rm $(TMPDIR)/vfb-scRNAseq-genes.txt $(TMPDIR)/vfb-EPseq-genes.txt

$(TMPDIR)/mapped_FBgn_list.txt: | $(TMPDIR)
	wget -O $(TMPDIR)/FBgns.tsv.gz ftp://ftp.flybase.net/releases/current/precomputed_files/genes/fbgn_fbtr_fbpp_fb_*.tsv.gz &&\
	gzip -df $(TMPDIR)/FBgns.tsv.gz &&\
	python3 $(SCRIPTSDIR)/process_FBgn.py &&\
	echo "\nMapped FBgn list updated\n"

get_vfb_code:
	cd $(SCRIPTSDIR) &&\
	wget https://github.com/VirtualFlyBrain/VFB_neo4j/archive/master.tar.gz &&\
	mkdir -p vfb && tar --strip-components=5 -xvf master.tar.gz VFB_neo4j-master/src/uk/ac/ebi/vfb &&\
	rm master.tar.gz && cd ../ontology

$(TMPDIR)/FBgns.owl: get_vfb_code $(TMPDIR)/mapped_FBgn_list.txt | $(REPORTDIR)
	python3 -m pip install -r $(SCRIPTSDIR)/requirements.txt &&\
	python3 $(SCRIPTSDIR)/feature_template_runner.py &&\
	$(ROBOT) template --template $(TMPDIR)/FBgn_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $@ &&\
	echo "\nFBgn annotations updated\n"

$(TMPDIR)/GO_annotations.owl: $(TMPDIR)/RNAseq_FBgn_list.txt
	wget -O $(TMPDIR)/gene_association.tsv.gz ftp://ftp.flybase.net/releases/current/precomputed_files/go/gene_association.fb.gz &&\
	gzip -df $(TMPDIR)/gene_association.tsv.gz &&\
	python3 $(SCRIPTSDIR)/process_GO.py &&\
	$(ROBOT) query --input-iri http://purl.obolibrary.org/obo/go.owl \
		--query $(SPARQLDIR)/GO_subclasses.sparql $(TMPDIR)/GO_subclasses.tsv &&\
	python3 $(SCRIPTSDIR)/add_GO_node_labels.py &&\
	$(ROBOT) template --template $(TMPDIR)/GO_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $@ &&\
	echo "\nGO annotations updated\n"

$(TMPDIR)/GG_annotations.owl: $(TMPDIR)/RNAseq_FBgn_list.txt
	wget -O $(TMPDIR)/gene_group_data.tsv.gz ftp://ftp.flybase.net/releases/current/precomputed_files/genes/gene_group_data_fb_*.tsv.gz &&\
	gzip -df $(TMPDIR)/gene_group_data.tsv.gz &&\
	python3 $(SCRIPTSDIR)/process_GG.py &&\
	$(ROBOT) query --input $(COMPONENTSDIR)/gene_groups.obo \
		--query $(SPARQLDIR)/GG_subclasses.sparql $(TMPDIR)/GG_subclasses.tsv &&\
	python3 $(SCRIPTSDIR)/add_GG_node_labels.py &&\
	$(ROBOT) template --template $(TMPDIR)/GG_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $@ &&\
	echo "\nGene Group annotations updated\n"

# A new gene_group_*.obo file can be found at:
# https://svn.flybase.org/flybase/release_browse_lists/<latest FB release>/
# (requires login)
# This file is not expected to be updated often
# After copying to tmp (as 'gene_groups.obo'), the following goal should then be updated manually:
$(COMPONENTSDIR)/gene_groups.obo: $(TMPDIR)/gene_groups.obo
	python3 $(SCRIPTSDIR)/process_FBgg.py &&\
	echo "\nGene Group ontology updated\n"

# This file must be manually updated (see above)
$(TMPDIR)/gene_groups.obo:
	echo $@

