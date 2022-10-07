## Customize Makefile settings for VFB_scRNAseq_genes
## 
## If you need to customize your Makefile, make
## changes here rather than in the main Makefile


# files for gene annotations
$(TMPDIR)/scRNAseq_FBgn_list.txt: | $(TMPDIR)
	wget -O $@ https://raw.githubusercontent.com/VirtualFlyBrain/vfb-scRNAseq-ontology/main/src/ontology/reports/FBgn_list.txt

$(TMPDIR)/mapped_FBgn_list.txt: | $(TMPDIR)
	wget -O $(TMPDIR)/FBgns.tsv.gz ftp://ftp.flybase.net/releases/current/precomputed_files/genes/fbgn_fbtr_fbpp_fb_*.tsv.gz &&\
	gzip -df $(TMPDIR)/FBgns.tsv.gz &&\
	python3 $(SCRIPTSDIR)/process_FBgn.py &&\
	rm $(TMPDIR)/FBgns.tsv &&\
	echo "\nMapped FBgn list updated\n"

$(TMPDIR)/FBgns.owl: $(TMPDIR)/mapped_FBgn_list.txt
	python3 -m pip install -r $(SCRIPTSDIR)/requirements.txt &&\
	svn export https://github.com/VirtualFlyBrain/VFB_neo4j/trunk/src/uk/ac/ebi/vfb $(SCRIPTSDIR)/vfb &&\
	python3 $(SCRIPTSDIR)/feature_template_runner.py &&\
	$(ROBOT) template --template $(TMPDIR)/FBgn_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $@ &&\
	rm -r $(SCRIPTSDIR)/vfb
	echo "\nFBgn annotations updated\n"

$(TMPDIR)/GO_annotations.owl: $(TMPDIR)/scRNAseq_FBgn_list.txt
	wget -O $(TMPDIR)/gene_association.tsv.gz ftp://ftp.flybase.net/releases/current/precomputed_files/go/gene_association.fb.gz &&\
	gzip -df $(TMPDIR)/gene_association.tsv.gz &&\
	python3 $(SCRIPTSDIR)/process_GO.py &&\
	$(ROBOT) template --template $(TMPDIR)/GO_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $@ &&\
	echo "\nGO annotations updated\n"

$(TMPDIR)/GG_annotations.owl: $(TMPDIR)/scRNAseq_FBgn_list.txt
	wget -O $(TMPDIR)/gene_group_data.tsv.gz ftp://ftp.flybase.net/releases/current/precomputed_files/genes/gene_group_data_fb_*.tsv.gz &&\
	gzip -df $(TMPDIR)/gene_group_data.tsv.gz &&\
	python3 $(SCRIPTSDIR)/process_GG.py &&\
	$(ROBOT) template --template $(TMPDIR)/GG_template.tsv \
		--input-iri http://purl.obolibrary.org/obo/ro.owl \
		--output $@ &&\
	echo "\nGene Group annotations updated\n"

$(SRC): $(TMPDIR)/FBgns.owl $(TMPDIR)/GO_annotations.owl $(TMPDIR)/GG_annotations.owl
	$(ROBOT) merge \
		--input VFB_scRNAseq_genes-annotations.ofn \
		--input $< \
		--input $(TMPDIR)/GO_annotations.owl \
		--input $(TMPDIR)/GG_annotations.owl \
		--include-annotations true --collapse-import-closure false \
		convert --format ofn \
		-o $@ &&\
	echo "\nOntology source file updated!\n"

# A new gene_group_*.obo file can be found at:
# https://svn.flybase.org/flybase/release_browse_lists/<latest FB release>/
# (requires login)
# This file is not expected to be updated often
# After copying to tmp (as 'gene_groups.obo'), the following should then be run manually:
$(COMPONENTSDIR)/gene_groups.obo: $(TMPDIR)/gene_groups.obo
	sed -e 's/\ FBgg/\ http\:\/\/flybase\.org\/reports\/FBgg/' \
	-e '4 i ontology: http://purl.obolibrary.org/obo/VFB_scRNAseq_genes/components/gene_groups.obo' \
	$< > $@ &&\
	echo "\nGene Group ontology updated\n"

# This file must be manually updated (see above)
$(TMPDIR)/gene_groups.obo:
	echo $@

