import os, sys 
import pandas as pd 
import numpy as np 
import random 
from collections import OrderedDict
import json 
import tempfile
import subprocess
import shlex


def collapse_annotation_dataframe(df, on='aaFullSeq', keep_group_tag=None):
		if len(df) == 0: return df.reindex(columns = df.columns.tolist() + ['collapsedCount'])
		# Remove duplicates and assign read counts.
		if keep_group_tag != None: print 'Keeping separate groups on key {}'.format(keep_group_tag)
		if keep_group_tag==None: 
			grouped = df.groupby(by=on, as_index=False, sort=False)
		else: 
			if type(on)==type([]): 
				on.append(keep_group_tag) 
			else:
				on = [on, keep_group_tag]
			grouped = df.groupby(by=on, as_index=False, sort=False)
		df_collapsed = grouped.first()
		#if already collapsed by standardization routine, readCount will be annotated
		if 'collapsedCount' in df_collapsed.index.tolist():
			df_collapsed['collapsedCount'] = grouped['collapsedCount'].transform('sum')
		else: 
			df_collapsed['collapsedCount'] = grouped.size().tolist()
		df_collapsed = df_collapsed.sort_values('collapsedCount', ascending=False)
		return df_collapsed


# agglomerative non-greedy clustering with minimum identity to one sequence in cluster satisfying linkage. can also run with max or avg linkage...
def cluster_dataframe(df, identity=0.94, on='aaSeqCDR3', how="greedy", linkage='min', read_cutoff=1, group_tag=None, remove_temp_files=False, max_sequences_per_cluster_to_report=1):
	print "#####  {} Total Annotations Being Clustered  #####".format(len(df))
	print 'No group_tag specified....' if group_tag==None else 'Keeping and tagging read counts by groups tagged "{}"'.format(group_tag)
	if on not in df.columns:
		if on + '_h' in df.columns:
			on = on+'_h'
		elif on + '_l' in df.columns:
			on = on+'_l'
	df = collapse_annotation_dataframe(df, on=on, keep_group_tag=group_tag)
	print "#####  {} Annotations After Collapsing On Identical {}  #####".format(len(df), on)
	print 'Sorting annotations based on length of {} (leads to more accurate clustering with greedy algorithm)'.format(on)
	df['tmp_on_col'] = df[on].str.replace('*','').str.replace('_','')
	df['tmp_on_length'] = df['tmp_on_col'].str.len()
	df = df[df['tmp_on_length']>1] 
	df = df.sort_values('tmp_on_length', ascending=False).reset_index(drop=True).drop('tmp_on_length', axis=1)

	if how=='agglomerative': 
		print '********************** Writing Fasta {} **********************'.format(on)
		temp_fasta_file = tempfile.NamedTemporaryFile(delete=False)
		for index, row in df.iterrows(): 
			temp_fasta_file.write('>{}\n'.format(index))
			temp_fasta_file.write('{}\n'.format(row['tmp_on_col']))
			last_index = index
		temp_fasta_file.close()
		df = df.drop('tmp_on_col', axis=1)
		print '{} fasta sequences for clustering written to temp file {}'.format(last_index+1, temp_fasta_file.name)
		print '**************** Clustering With Agglomerative Algorithm ***************'
		temp_distmatrix_file = tempfile.mktemp()
		temp_clustered_output_file = tempfile.mktemp()
		print 'writing centroids to temporary file {}'.format(temp_distmatrix_file)
		print 'writing clustering output to temporary file {}'.format(temp_clustered_output_file)
		#perform clustering - uses usearch8 
		usearch_command = "/data/resources/software/usearch -cluster_agg {} -id {} -linkage {} -distmxout {} -clusterout {} ".format(temp_fasta_file.name, identity, linkage, temp_distmatrix_file, temp_clustered_output_file)
		print usearch_command
		command_line_args = shlex.split(usearch_command)
		command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )
		for line in iter(command_line_process.stdout.readline, b''):
			line = line.rstrip()
			print line
		response, error = command_line_process.communicate()
		command_line_process.stdout.close()
		command_line_process.wait()		
		print '***************** Clustering Complete *****************'
		clust_cols=['clusterId', 'index_row']
		clust_types={'clusterId':int, 'index_row':int}
		cluster_results=pd.read_csv(temp_clustered_output_file, sep='\t', names=clust_cols, dtype=clust_types)
		if remove_temp_files: 
			for filename in temp_fasta_file.name, temp_clustered_output_file, temp_distmatrix_file: 
				os.remove(filename)
		cluster_results.set_index('index_row', inplace=True)
		#redefine clusterID so it runs 1...x instead of 0...x
		cluster_results['clusterId']=cluster_results['clusterId'].astype(int)+1
		#drop previous clustering columns: 
		if 'clusterId' in df.columns: df.drop('clusterId', axis=1,inplace=True)
		#maps cluster_results onto df 
		df = cluster_results.join(df)

	elif how=='greedy': 
		print '********************** Writing Fasta {} **********************'.format(on)
		temp_fasta_file = tempfile.NamedTemporaryFile(delete=False)
		for index, row in df.iterrows(): 
			temp_fasta_file.write('>{}\n'.format(index))
			temp_fasta_file.write('{}\n'.format(row['tmp_on_col']))
			last_index = index
		temp_fasta_file.close()
		df = df.drop('tmp_on_col', axis=1)
		print '{} fasta sequences for clustering written to temp file {}'.format(last_index+1, temp_fasta_file.name)
		print '**************** Clustering With Greedy Algorithm **********************'
		temp_centroids_file = tempfile.mktemp()
		temp_clustered_output_file = tempfile.mktemp()
		print 'writing centroids to temporary file {}'.format(temp_centroids_file)
		print 'writing clustering output to temporary file {}'.format(temp_clustered_output_file)
		#perform clustering - uses usearch8 
		usearch_command = "/data/resources/software/usearch -cluster_smallmem {} -minhsp 10 -sortedby length -id {} -centroids {} -uc {} ".format(temp_fasta_file.name, identity, temp_centroids_file, temp_clustered_output_file)
		print usearch_command
		command_line_args = shlex.split(usearch_command)
		command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )
		for line in iter(command_line_process.stdout.readline, b''):
			line = line.rstrip()
			print line 
		response, error = command_line_process.communicate()
		command_line_process.stdout.close()
		command_line_process.wait()
		print '***************** Clustering Complete *****************'
		clust_cols=['SeedorHit','clusterId','Length','Match', 'Blank1', 'Blank2','Blank3','Blank4','index_row','CDR_matchseq']
		# clust_types={'SeedorHit':str,'clusterId':int,'Length':int,'Match':str, 'Blank1':str, 'Blank2':str,'Blank3':str,'Blank4':str,'readName':str,'CDR_matchseq':str}
		cluster_results=pd.read_csv(temp_clustered_output_file, sep='\t', names=clust_cols)
		if remove_temp_files: 
			for filename in temp_fasta_file.name, temp_clustered_output_file, temp_centroids_file: 
				os.remove(filename)
		cluster_results=cluster_results[['SeedorHit','clusterId','index_row']]
		cluster_results=cluster_results[cluster_results.SeedorHit != 'C'].drop('SeedorHit', 1)
		cluster_results.set_index('index_row', inplace=True)
		#redefine clusterID so it runs 1...x instead of 0...x
		cluster_results['clusterId']=cluster_results['clusterId'].astype(int)+1
		#drop previous clustering columns: 
		if 'clusterId' in df.columns: df.drop('clusterId', axis=1,inplace=True)
		#maps cluster_results onto df 
		df = cluster_results.join(df)

	elif how=='D': 
		print '********************** Writing {} Sequences **********************'.format(on)
		temp_seq_file = tempfile.NamedTemporaryFile(delete=False)
		for index, row in df.iterrows():
			temp_seq_file.write('{}\n'.format(''.join(row['tmp_on_col'])))
			last_index = index
		temp_seq_file.close()
		df = df.drop('tmp_on_col', axis=1)
		print '{} sequences for clustering written to temp file {}'.format(last_index+1, temp_seq_file.name)
		print '**************** Clustering With D Algorithm ***************'
		temp_clustered_output_file = tempfile.mktemp()
		print 'writing clustering output to temporary file {}'.format(temp_clustered_output_file)
		clonotype_location = "/data/resources/software/CDR3_Clonotyping"
		run_clonotype_command = '{} --file {} --thresh {} --output {}'.format(clonotype_location, temp_seq_file.name, str(1 - float(identity)), temp_clustered_output_file)
		command_line_args = shlex.split(run_clonotype_command)
		command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )
		for line in iter(command_line_process.stdout.readline, b''):
			line = line.rstrip()
			print line
		response, error = command_line_process.communicate()
		command_line_process.stdout.close()
		command_line_process.wait()		
		print '***************** Clustering Complete *****************'
		clonoDict = pd.read_csv(temp_clustered_output_file, sep='\t', skip_blank_lines=True, header=None, names=[on, 'clusterId'], dtype={on: str, 'clusterId':int})
		# if remove_temp_files: 
		# 	for filename in temp_seq_file.name, temp_clustered_output_file, temp_distmatrix_file: 
		# 		os.remove(filename)
		print('Appending clonotypes to dataframe')
		if 'clusterId' in df.columns: df.drop('clusterId', 1)
		df = pd.merge(df, clonoDict, on=on, how='left')
		# df.fillna('', inplace=True)

	else: 
		print "MUST SPECIFY 'agglomerative' OR 'greedy' OR 'D' IN HOW ARGUMENT TO cluster_dataframe()"
		return None 

	# to allow for re-clustering: 
	if 'clusterSize' in df.columns: 
		size_key='clusterSize' 
	else: 
		size_key='collapsedCount'
	df['clusterSize'] = df[~df.clusterId.isnull()].groupby(['clusterId'])[size_key].transform(sum)
	print 'Generating clustered dataframe for output.'
	if group_tag==None: 
		if 'group' not in df.columns:
			df['group'] = 'Group1'
			group_tag='group'
		else: 
			group_tag='group'
	df['groupClusterSize'] = df.groupby([group_tag, 'clusterId'])[size_key].transform(sum)
	df['groupClusterSizeTag'] = df[group_tag] + ":" + df['groupClusterSize'].astype(str) + "reads"
	concat_sizes = lambda sizes: "%s" % '|'.join(set(sizes))
	df['group_tag'] = df.groupby('clusterId')['groupClusterSizeTag'].transform(concat_sizes)
	# report only max_sequences_per_cluster_to_report number of hits
	clustered_df = df[df.clusterSize>=read_cutoff].sort_values(['clusterSize', 'collapsedCount', 'clusterId'],ascending=[False,False,True]).groupby(['clusterId']).head(max_sequences_per_cluster_to_report).reset_index() #     df[['clusterSize','collapsed','clusterId','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso']]   .to_csv(clustered_nt_output, index=None, sep='\t')
	for x in ['groupClusterSize', 'groupClusterSizeTag', 'index_row', 'index', '']: 
		if x in clustered_df.columns: clustered_df.drop(x, axis=1, inplace=True)
	ordered_cols = ['clusterId', 'clusterSize', 'collapsedCount'] 
	output_cols = ordered_cols + [c for c in clustered_df.columns if c not in ordered_cols]
	clustered_df = clustered_df[output_cols]
	clustered_df = clustered_df.sort_values('clusterSize', ascending=False)
	print 'Clustering and processing complete.'
	return clustered_df






# has issues with similar named reads! can't subsample a file and compare without changing read IDs to not overlap 
def cluster_overlap(df1, df2, identity=0.94, on='aaSeqCDR3', read_cutoff=1): 
	print '{} sequences in dataframe 1'.format(len(df1))
	print '{} sequences in dataframe 2'.format(len(df2))
	df1['group'] = 'A'
	df2['group'] = 'B'
	df_main = pd.concat([df1, df2])
	df_clustered = cluster_dataframe(df_main, identity=identity, on=on, read_cutoff=1)
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









