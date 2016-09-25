import pandas as pd
from StringIO import StringIO
import os
import sys
import json

#Compatible with Pairing_v1.02 pipeline

def PairingPandas(fastq_files, clusters, groupname,headnum):
	cluster=clusters
	prefix=groupname
	
	summary=open(prefix+'_Saturation_Analysis.txt','w')
	summary.write('%s\n' %prefix)
	
	cluster=clusters
	prefix=groupname
	readCutoff=1 #usually set to 1, which means there must be at least 2 reads for analysis
	
	numbers=dict()
		
	#turn off chained assignment warnings
	pd.options.mode.chained_assignment = None
	
	#turn off truncation when printing sequences
	pd.set_option('display.max_colwidth', -1)
	
	#read in mixcr output file, use MiSeq identifier as index
	usefulcols=['Seqheader','Strand corrected sequence','Locus','FirstVgene', 'FirstDgene', 'FirstJgene','Read(s) sequence qualities','AA. Seq. CDR3','N. Seq. CDR3','VGENE: Germline start','VGENE: Germline end','VGENE: Mismatch','All C hits','Productivity']
	col_types={'Seqheader':str,'Strand corrected sequence':str,'Locus':str,'FirstVgene':str, 'FirstDgene':str, 'FirstJgene':str,'Read(s) sequence qualities':str,'AA. Seq. CDR3':str,'N. Seq. CDR3':str,'VGENE: Germline start':float,'VGENE: Germline end':float,'VGENE: Mismatch':float,'All C hits':str,'Productivity':str}
	
	print '\nReading in R1 files.\n'
	df_R1=pd.read_csv(fastq_files[0], sep='\t', skiprows=[0],usecols=usefulcols, dtype=col_types)
	print 'Number of total R1 reads post quality filter: %s\n' %len(df_R1.index) 
	numbers['R1']=len(df_R1.index)
	
	print 'Reading in R2 files.\n'
	df_R2=pd.read_csv(fastq_files[1], sep='\t', skiprows=[0],usecols=usefulcols, dtype=col_types)
	print 'Number of total R2 reads post quality filter: %s\n' %len(df_R2.index)
	numbers['R2']=len(df_R2.index)
	
	#create new dataframes for VH and VL sequences
	#this unlinks R1 and R2 from VH and VL
	df_VH_R1=df_R1[df_R1.Locus=='IGH']
	df_VL_R1=df_R1[((df_R1.Locus=='IGK')|(df_R1.Locus=='IGL'))]
	df_VH_R2=df_R2[df_R2.Locus=='IGH']
	df_VL_R2=df_R2[((df_R2.Locus=='IGK')|(df_R2.Locus=='IGL'))]
	
	#combines VH and VL dataframes
	df_VH=pd.concat([df_VH_R1,df_VH_R2])
	df_VL=pd.concat([df_VL_R1,df_VL_R2])
	
	#remove final Miseq identifiers R1 and R2 for UTexas MiSeq
	df_VH['Seqheader']=df_VH['Seqheader'].str[:-8]
	df_VL['Seqheader']=df_VL['Seqheader'].str[:-8]
	
	#delete duplicates to remove VH:VH and VL:VL pairs
	df_VH=df_VH.drop_duplicates(subset='Seqheader')
	df_VL=df_VL.drop_duplicates(subset='Seqheader')
	
	print 'Processing quality paired sequences.\n'
	#Find intersection of both R1 and R2 files
	df_main=pd.merge(df_VL,df_VH, how='inner', on=['Seqheader'])
	
	#Rename columns
	df_main=df_main.rename(columns={'Seqheader':'SeqID','Strand corrected sequence_y':'IGH Sequence','Locus_y':'H_Locus','FirstVgene_y':'VH', 'FirstDgene_y':'DH', 'FirstJgene_y':'JH','Read(s) sequence qualities_y':'IGH_Qual','AA. Seq. CDR3_y':'CDRH3_AA','N. Seq. CDR3_y':'CDRH3_NT','VGENE: Germline start_y':'VHStart','VGENE: Germline end_y':'VHEnd','VGENE: Mismatch_y':'VH_mismatch','All C hits_y':'VHIso','Productivity_x':'Productivity','Strand corrected sequence_x':'IGL Sequence','Locus_x':'L_Locus','FirstVgene_x':'VL', 'FirstJgene_x':'JL','Read(s) sequence qualities_x':'IGL_Qual','AA. Seq. CDR3_x':'CDRL3_AA','N. Seq. CDR3_x':'CDRL3_NT','VGENE: Germline start_x':'VLStart','VGENE: Germline end_x':'VLEnd','VGENE: Mismatch_x':'VL_mismatch','All C hits_x':'VLIso'})
	
	print 'Number of combined reads post quality filter: %s\n' %len(df_main.index)
	numbers['VHVL']=len(df_main.index)
	
	#remove empty sequences
	df_main=df_main[df_main['IGH Sequence'].notnull() & df_main['IGL Sequence'].notnull()]
	df_main=df_main[df_main['CDRH3_AA'].notnull() & df_main['CDRL3_AA'].notnull() & df_main['CDRH3_NT'].notnull() & df_main['CDRL3_NT'].notnull()]
	df_main=df_main.set_index('SeqID')
	df_main['Comboseq']=df_main.CDRH3_NT.map(str)+":"+df_main.CDRL3_NT.map(str)

	#remove VH:VH or VL:VL pairs
	df_main=df_main[((df_main.L_Locus=='IGK') | (df_main.L_Locus=='IGL')) & (df_main.H_Locus=='IGH')]
	df_main=df_main[~df_main.Productivity.str.contains('NO')]
	df_main=df_main[~df_main.CDRH3_AA.str.contains('_')]
	df_main=df_main[~df_main.CDRL3_AA.str.contains('_')]
	df_main=df_main[~df_main.CDRH3_AA.str.contains('\*')]
	df_main=df_main[~df_main.CDRL3_AA.str.contains('\*')]
	
	print 'Number of correctly paired reads: %s\n' %len(df_main.index)
	summary.write('Number of combined reads post quality filter: %s\n' %len(df_main.index))
	summary.write('Sequences\tCollapsed\tClustered\n')
	
	
	headstart=int(headnum)
	headend=len(df_main.index)
	head_interval=int(headnum)
	repeat=range(headstart,headend,head_interval)
	repeat.append(headend)
	
	for num in repeat:
		
		#to normalize all comparisons to number of quality VH:VL reads
		summary.write('%s' %num)
		df_main_sub=df_main.sample(num)

		
		#Collapse on identical CDRH3 + CDRL3 nt sequences
		df_main_sub['Collapsed']=1
		df_main_sub['Collapsed']=df_main_sub.groupby(['CDRL3_NT','CDRH3_NT'])['Collapsed'].transform('count')

		#create identical_nt_pairs file
		print 'Building paired output file.\n'
		df_collapsed=df_main_sub[['Collapsed','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL']]
		df_collapsed=df_collapsed.sort_values(['Collapsed','CDRH3_AA'],ascending=[False,True]).drop_duplicates(['CDRH3_NT','CDRL3_NT'])
		
		
		print 'Number of collapsed pairs: %s\n' %len(df_collapsed.index)
		summary.write('\t%s' %len(df_collapsed.index))
	
		#output fasta file for clustering
		df_clustered=df_collapsed[['Collapsed','CDRH3_NT','CDRL3_NT']]
		df_clustered=df_clustered[df_clustered.Collapsed>readCutoff]
		clustered_fasta=open('clustered.fasta','w')
		for index, row in df_clustered.iterrows():
			clustered_fasta.write('>%s:%s\n' %(row[1],row[2]))
			clustered_fasta.write('%s\n' %row[1])
		clustered_fasta.close()

		print '********************** Clustering **********************'
		#perform clustering
		os.system("/home/gg-jm76798/Desktop/FinalizedScripts/usearch7 -cluster_smallmem clustered.fasta -minhsp 10 -minseqlength 10 -usersort -id {0} -centroids c.fa -uc clustered_output_file.uc".format(cluster))
		print '***************** Clustering Complete *****************'
		
		#read in results
		Clust_cols=['SeedorHit','ClusterID','Length','Match', 'Blank1', 'Blank2','Blank3','Blank4','Comboseq','CDR_matchseq']
		clust_types={'SeedorHit':str,'ClusterID':int,'Length':int,'Match':str, 'Blank1':str, 'Blank2':str,'Blank3':str,'Blank4':str,'Comboseq':str,'CDR_matchseq':str}

		print '\nParsing clustering information.\n'
		cluster_results=pd.read_csv('clustered_output_file.uc', sep='\t', names=Clust_cols)
		cluster_results=cluster_results[['SeedorHit','ClusterID','Comboseq']]
		cluster_results=cluster_results[cluster_results.SeedorHit != 'C']

		#redefine clusterID so it runs 1...x instead of 0...x
		cluster_results['ClusterID']=cluster_results['ClusterID'].astype(int)+1

		#Prepares dictionary for mapping cluster numbers to sequences
		cluster_lookup=cluster_results.set_index('Comboseq')['ClusterID'].to_dict()

		#maps cluster ID to sequences
		df_main_sub['ClusterID']=df_main_sub['Comboseq'].map(cluster_lookup)
		df_main_sub['Clustered']=1
		df_main_sub['Clustered']=df_main_sub.groupby(['ClusterID'])['Clustered'].transform('count')
		df_clustered=df_main_sub.drop_duplicates(['ClusterID'])
		
		print 'Generating files.\n'

		summary.write('\t%s\n' %len(df_clustered.index))
		
		#delete dataframes for next loop
		del_list=[df_main_sub,df_collapsed,df_clustered]
		del df_main_sub
		del df_collapsed
		del df_clustered
	
	print 'Pairing complete.\n'
	summary.close()
	
#python SaturationCurves_v1.02.py R1.annotation R2.annotation -cluster 0.9 -group 'x' -head 10000
#head defines the step number for the productive VH:VL reads. 10,000 is recommended for first pass.
if __name__ == "__main__":
	arguments = sys.argv[1:]
	argnum = 0
	fastq_files = []
	while True:
		if argnum >= len(arguments):
			break
		if arguments[argnum] == '-cluster':
			argnum += 1
			cluster = arguments[argnum]
		elif arguments[argnum] == '-group': 
			argnum += 1
			groupname = arguments[argnum]
		elif arguments[argnum] == '-head': 
			argnum += 1
			headnum = arguments[argnum]
		else:
			fastq_files.append(arguments[argnum])
			f = os.path.expanduser(fastq_files[-1])			
			if not os.path.isfile(f):
				raise Exception('The provided file {0} does not exist'.format(f))
			fastq_files[-1] = os.path.abspath(f)			
		argnum += 1	
	PairingPandas(fastq_files, cluster, groupname,headnum)
