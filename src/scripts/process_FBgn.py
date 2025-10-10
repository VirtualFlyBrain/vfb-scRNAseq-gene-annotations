import pandas as pd

FBgn_df = pd.read_csv('tmp/fbgn_fbtr_fbpp.tsv', sep='\t', skiprows=4, skipfooter=1, index_col=False, engine='python')

FBgn_list = list(FBgn_df['## FlyBase_FBgn'].unique())

with open('tmp/mapped_FBgn_list.txt', 'w') as f:
    for fbgn in FBgn_list:
        f.write(fbgn + '\n')
