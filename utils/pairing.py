import os, sys 
import pandas as pd 
import numpy as np 
import random 
from collections import OrderedDict
import json 

from utils.standardization import *



def pair_annotation_files(file1, file2): 
	df1 = read_annotation_dataframe(file1)
	df2 = read_annotation_dataframe(file2)
	return pair_annotation_dataframes(df1, df2)

def pair_annotation_dataframes(df1, df2): 
	print "{} annotations in file 1, {} in file 2".format(len(df1), len(df2))

	df1_h = df1[df1.apply(lambda r: r['v_top_hit'][:3]=='IGH', axis=1)]
	df2_h = df2[df2.apply(lambda r: r['v_top_hit'][:3]=='IGH', axis=1)]
	df1_l = df1[df1.apply(lambda r: r['v_top_hit'][:3]=='IGK' or r['v_top_hit'][:3]=='IGL', axis=1)]
	df2_l = df2[df2.apply(lambda r: r['v_top_hit'][:3]=='IGK' or r['v_top_hit'][:3]=='IGL', axis=1)]
	df_h = df1_h.append(df2_h)
	df_l = df1_l.append(df2_l)
	print '{} IGH annotations, {} IGL/L annotations'.format(len(df_h), len(df_l))

	df = pd.merge(df_h, df_l, on='readName', suffixes=['_h', '_l'], how='inner').set_index('readName')
	print '{} annotations after merging IGH to IGL/K on key readName'.format(len(df))

	#remove empty sequences
	df = df.dropna(subset=['aaFullSeq_h', 'aaFullSeq_l', 'aaSeqCDR3_h', 'aaSeqCDR3_l', 'nSeqCDR3_h', 'nSeqCDR3_l'], how='any')

	#clean sequences with indels in CDR3 
	df = df[df.apply(lambda r: '*' not in r['aaSeqCDR3_h'], axis=1)]
	df = df[df.apply(lambda r: '_' not in r['aaSeqCDR3_h'], axis=1)]
	df = df[df.apply(lambda r: '*' not in r['aaSeqCDR3_l'], axis=1)]
	df = df[df.apply(lambda r: '_' not in r['aaSeqCDR3_l'], axis=1)]

	#combine CDR3 nt sequences..? 
	df['aaSeqCDR3_combined']=df['nSeqCDR3_h'].map(str)+":"+df['nSeqCDR3_l'].map(str)

	# #find any isotypes missed by MixCR - that many to justify this routine?? 
	# print 'Analyzing for additional heavy chain isotyping.\n'
	# iso_nulls_before=df['c_top_hit_h'].isnull().sum()
	# df['c_top_hit_h']=df.apply(find_isotype, seq_index='nFullSeq_h', isotype_index='c_top_hit_h', axis=1)
	# iso_nulls_after=df['c_top_hit_h'].isnull().sum()
	# df['c_top_hit_locus_h'] = df.apply(lambda r: r['c_top_hit_h'] if pd.isnull(r['c_top_hit_locus_h']) else r['c_top_hit_locus_h'], axis=1)
	# print 'Additional isotypes defined: %s\n' %(iso_null_before-iso_nulls_after)

	dfg = df.groupby(['nSeqCDR3_h','nSeqCDR3_l'])
	df['readCount']=dfg['readCount_h'].transform('sum')
	df['v_region_shm_h']=dfg['v_region_shm_h'].transform('mean').apply(round, args=[1,])
	df['v_region_shm_l']=dfg['v_region_shm_l'].transform('mean').apply(round, args=[1,])
	df['j_region_shm_h']=dfg['j_region_shm_h'].transform('mean').apply(round, args=[1,])
	df['j_region_shm_l']=dfg['j_region_shm_l'].transform('mean').apply(round, args=[1,])
	df_collapsed = df.sort_values(['readCount', 'aaSeqCDR3_h'], ascending=[False, True]).drop_duplicates(['nSeqCDR3_h','nSeqCDR3_l'])

	print 'Number of collapsed pairs: %s\n' %len(df_collapsed.index)
	return df_collapsed 


# # sometimes MiXCR missed isotypes? 
# # are these primer sequences up to date? 
def find_isotype(row, seq_index='nFullSeq', isotype_index='c_top_hit'):
	seq,isotype = row[seq_index], row[isotype_index]
	if type(isotype) == str and 'I' in isotype:
		return isotype
	#these are all reverse complements of isotype specific primers
	else:
		if 'GGAGTGCATCCGCCCCAACC' in seq:
			return 'IGHM'
		elif 'GGCTTCTTCCCCCAGGAGCC' in seq:
			return 'IGHA'
		elif 'GCTTCCACCAAGGGCCCATC' in seq:
			return 'IGHG'
		else:
			return np.nan  



