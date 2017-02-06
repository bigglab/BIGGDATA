import os, sys 
import pandas as pd 
import numpy as np 
import random 
from collections import OrderedDict
import json 
import tempfile



def collapse_annotation_dataframe(df, on='aaFullSeq'):
		if len(df) == 0: return df.reindex(columns = df.columns.tolist() + ['collapsedCount'])
		# Remove duplicates and assign read counts.
		grouped = df.groupby(on, as_index=False, sort=False)
		df_collapsed = grouped.first()
		#if already collapsed by stanardization routine, readCount will be annotated
		if 'readCount' in df_collapsed.index.tolist(): 
			df_collapsed['collapsedCount'] = grouped['readCount'].transform('sum')
		elif 'collapsed' in df_collapsed.index.tolist(): 
			df_collapsed['collapsedCount'] = grouped['collapsed'].transform('sum')
		elif 'Collapsed' in df_collapsed.index.tolist(): 
			df_collapsed['collapsedCount'] = grouped['Collapsed'].transform('sum')
		elif 'collapsedCount' in df_collapsed.index.tolist(): 
			df_collapsed['collapsedCount'] = grouped['collapsedCount'].transform('sum')
		else: 
			df_collapsed['collapsedCount'] = grouped.size().tolist()
		return df_collapsed


def cluster_dataframe(df, cluster_cutoff=0.94, on='aaSeqCDR3', readCutoff=1, remove_temp_files=True): 
	df = collapse_annotation_dataframe(df, on=on)
	print '********************** Writing Fasta {} **********************'.format(on)
	temp_fasta_file = tempfile.NamedTemporaryFile(delete=False)
	for index, row in df.iterrows(): 
		temp_fasta_file.write('>{}\n'.format(index))
		temp_fasta_file.write('{}\n'.format(''.join(row[on])))
	temp_fasta_file.close()
	print 'fasta sequences for clustering written to temp file {}'.format(temp_fasta_file.name)
	print '********************** Sorting Fasta **********************'
	print 'Sorting fasta sequences by decreasing length (increases clustering accuracy)'
	temp_sorted_file = tempfile.mktemp()
	print 'writing sorted fasta file to {}'.format(temp_sorted_file)
	usearch_sort_command = "/data/resources/software/usearch -sortbylength {} -fastaout {} ".format(temp_fasta_file.name, temp_sorted_file)
	print usearch_sort_command
	os.system(usearch_sort_command)
	print '********************** Clustering **********************'
	temp_centroids_file = tempfile.mktemp()
	temp_clustered_output_file = tempfile.mktemp()
	print 'writing centroids to temporary file {}'.format(temp_centroids_file)
	print 'writing clustering output to temporary file {}'.format(temp_clustered_output_file)
	#perform clustering - usearch8 
	usearch_command = "/data/resources/software/usearch -cluster_smallmem {} -minhsp 10 -sortedby other -id {} -centroids {} -uc {}".format(temp_fasta_file.name, cluster_cutoff, temp_centroids_file, temp_clustered_output_file)
	print usearch_command
	os.system(usearch_command)
	print '***************** Clustering Complete *****************'
	clust_cols=['SeedorHit','clusterId','Length','Match', 'Blank1', 'Blank2','Blank3','Blank4','index_row','CDR_matchseq']
	clust_types={'SeedorHit':str,'clusterId':int,'Length':int,'Match':str, 'Blank1':str, 'Blank2':str,'Blank3':str,'Blank4':str,'readName':str,'CDR_matchseq':str}
	print '\nParsing clustering information.\n'
	cluster_results=pd.read_csv(temp_clustered_output_file, sep='\t', names=clust_cols)
	if remove_temp_files: 
		for filename in temp_fasta_file.name, temp_clustered_output_file, temp_centroids_file, temp_sorted_file: 
			os.remove(filename)
	cluster_results=cluster_results[['SeedorHit','clusterId','index_row']]
	cluster_results=cluster_results[cluster_results.SeedorHit != 'C']
	cluster_results.set_index('index_row', inplace=True)
	#redefine clusterID so it runs 1...x instead of 0...x
	cluster_results['clusterId']=cluster_results['clusterId'].astype(int)+1
	#maps cluster_results onto df 
	df = cluster_results.join(df)
	df['clusterSize'] = df[~df.clusterId.isnull()].groupby(['clusterId'])['collapsedCount'].transform(sum)  #.drop_duplicates(['Comboseq','ClusterID']) before goupby...
	print 'Generating dataframes for output.\n'
	clustered_df = df[df.clusterSize>=readCutoff].sort_values(['clusterSize','clusterId','collapsedCount'],ascending=[False,True,False]).groupby(['clusterId']).head(1).reset_index().drop(['index_row', 'SeedorHit'], 1) #     df[['clusterSize','collapsed','clusterId','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso']]   .to_csv(clustered_nt_output, index=None, sep='\t')
	# raw_clustered_nt_output = df[df.clusterSize>=1].sort_values(['clusterSize','clusterId','collapsed',on],ascending=[False,True,False,True]) # .drop_duplicates(['CDRH3_NT','CDRL3_NT','ClusterID']) #   df[['clusterSize','readCount','clusterId','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso']]      .to_csv(raw_clustered_nt_output, index=None, sep='\t')
	ordered_cols = ['clusterId', 'clusterSize', 'collapsedCount'] 
	output_cols = ordered_cols + [c for c in clustered_df.columns if c not in ordered_cols]
	print 'Processing complete.\n'
	return clustered_df[output_cols]



# has issues with similar named reads! can't subsample a file and compare without changing read IDs to not overlap 
def cluster_overlap(df1, df2, cluster_cutoff=0.94, on='aaSeqCDR3', readCutoff=1): 
	print '{} sequences in dataframe 1'.format(len(df1))
	print '{} sequences in dataframe 2'.format(len(df2))
	df1['group'] = 'A'
	df2['group'] = 'B'
	df_main = pd.concat([df1, df2])
	df_clustered = cluster_dataframe(df_main, cluster_cutoff=cluster_cutoff, on=on, readCutoff=1)
	df_clustered['clusterGroup'] = df_clustered.groupby('clusterId')['group'].transform(lambda gs: ''.join(sorted(set(gs.tolist()))))
	#print results
	print 'Summarizing results.\n'
	print ('A total collapsed: %s\n' %len(df1.index))
	print ('B total collapsed: %s\n' %len(df2.index))
	print ('A only clusters: %s\n' %len(df_clustered[df_clustered.clusterGroup=='A'].index))
	print ('B only clusters: %s\n' %len(df_clustered[df_clustered.clusterGroup=='B'].index))
	print ('Overlapped clusters: %s\n' %len(df_clustered[df_clustered.clusterGroup=='AB'].index))
	print ('Total clusters: %s\n' %len(df_clustered.index))
	return df_clustered 








