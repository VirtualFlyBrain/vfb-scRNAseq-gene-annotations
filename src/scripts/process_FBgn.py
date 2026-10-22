import pandas as pd

FBgn_df = pd.read_csv('tmp/fbgn_fbtr_fbpp.tsv', sep='\t', skiprows=4, skipfooter=1, index_col=False, engine='python')

FBgn_list = list(FBgn_df['## FlyBase_FBgn'].unique())

# Every gene the expression data uses gets a Gene class, including current genes
# missing from fbgn_fbtr_fbpp (e.g. some non-coding CR genes), so that no
# expression edge points at a gene VFB does not have.
with open('tmp/vfb-RNAseq-genes.txt', 'r') as f:
    expressed = [g for g in f.read().splitlines() if g]
FBgn_list += sorted(set(expressed) - set(FBgn_list))

with open('tmp/mapped_FBgn_list.txt', 'w') as f:
    for fbgn in FBgn_list:
        f.write(fbgn + '\n')
