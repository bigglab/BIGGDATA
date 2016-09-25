import pandas as pd
from StringIO import StringIO
import os
import sys
import json
import VH_analysis
import VH_statistics as Vstatistics

#Designed to analyze heavy chain sequences, in particular to build full length antibody sequences
#Based on AA sequence

def VHPandas(fastq_files, groupname, CDR_list):
	search=str(CDR_list)
	prefix=groupname
	readCutoff=1 #usually set to 1, which means there must be at least 2 reads for analysis
	
	numbers=dict()
		
	#turn off chained assignment warnings
	pd.options.mode.chained_assignment = None
	
	#turn off truncation when printing sequences
	pd.set_option('display.max_colwidth', -1)
	
	#read in mixcr output file, use MiSeq identifier as index
	usefulcols=['Seqheader','Strand corrected sequence','Full AA','Locus','FirstVgene', 'FirstDgene', 'FirstJgene','Read(s) sequence qualities','AA. Seq. CDR1','AA. Seq. CDR2','AA. Seq. CDR3','VGENE: Germline start','VGENE: Germline end','VGENE: Mismatch','All C hits','Productivity']
	col_types={'Seqheader':str,'Strand corrected sequence':str,'Full AA':str,'Locus':str,'FirstVgene':str, 'FirstDgene':str, 'FirstJgene':str,'Read(s) sequence qualities':str,'AA. Seq. CDR1':str,'AA. Seq. CDR2':str,'AA. Seq. CDR3':str,'VGENE: Germline start':float,'VGENE: Germline end':float,'VGENE: Mismatch':float,'All C hits':str,'Productivity':str}
	
	print '\nReading in stitched files.\n'
	df_main=pd.read_csv(fastq_files[0], sep='\t', skiprows=[0], usecols=usefulcols, dtype=col_types)
	print 'Number of total reads post quality filter: %s\n' %len(df_main.index) 
	numbers['reads']=len(df_main.index)
	
	#remove final Miseq identifiers R1 and R2 for UTexas MiSeq
	df_main['Seqheader']=df_main['Seqheader'].str[:-8]
	
	#Rename columns
	#For UTexas:
	df_main=df_main.rename(columns={'Seqheader':'SeqID','Strand corrected sequence':'IG Sequence','Full AA':'AA Seq','FirstVgene':'VGene', 'FirstDgene':'DGene', 'FirstJgene':'JGene','Read(s) sequence qualities':'IG_Qual','AA. Seq. CDR1':'CDR1_AA','AA. Seq. CDR2':'CDR2_AA','AA. Seq. CDR3':'CDR3_AA','VGENE: Germline start':'VStart','VGENE: Germline end':'VEnd','VGENE: Mismatch':'V_mismatch','All C hits':'VIso'})
	
	#remove empty sequences
	df_main=df_main[df_main['IG Sequence'].notnull()]
	df_main=df_main[df_main['CDR3_AA'].notnull()]
	df_main=df_main.set_index('SeqID')

	#remove sequences with low quality CDR
	df_main=df_main[(df_main.Locus=='IGH')]
	df_main=df_main[~df_main.Productivity.str.contains('NO')]
	df_main=df_main[~df_main.CDR3_AA.str.contains('_')]
	df_main=df_main[~df_main.CDR3_AA.str.contains('\*')]
	
	#find any isotypes missed by MixCR
	print 'Analyzing for additional heavy chain isotyping.\n'
	df_main['VIso']=df_main[['VIso']].fillna(str('empty'))
	iso_before=(~df_main.VIso.str.contains('empty')).sum()
	df_main['VIso']=df_main.apply(lambda row: Vstatistics.find_isotype(row['IG Sequence'],row['VIso']),axis=1)
	iso_after=(~df_main.VIso.str.contains('empty')).sum()
	print 'Additional isotypes defined: %s\n' %(iso_after-iso_before)
	
	#simplify isotype nomenclature
	iso_change_V=lambda x : x['VIso'].split('*')[0]
	df_main['VIso']=df_main.apply(iso_change_V,axis=1)
	
	print 'Number of productive reads: %s\n' %len(df_main.index)
	numbers['ProductiveV']=len(df_main.index)
	
	#redefine gene call strings (removes **)
	genes=['VGene','DGene','JGene']
	for gene_desc in genes:
		df_main[gene_desc]=df_main[gene_desc].str.split('*').str[0]

	#calculate SHM
	df_main['Vmut']=df_main['V_mismatch']/(df_main['VEnd']-df_main['VStart']+1)*100

	#Collapse on identical AA sequences
	df_main['Collapsed']=1
	df_main['Collapsed']=df_main.groupby(['AA Seq'])['Collapsed'].transform('count')
	df_main['V_AvgSHM']=df_main.groupby(['AA Seq'])['Vmut'].transform('mean')

	#decrease number of decimals in SHM (just for output appearances)
	SHM_V_dec=lambda x : round(x['V_AvgSHM'],1)
	df_main['V_AvgSHM']=df_main.apply(SHM_V_dec,axis=1)
		
	#create identical_aa_pairs file
	print 'Building output file.\n'
	df_collapsed=df_main[['Collapsed','CDR1_AA','CDR2_AA','CDR3_AA','VGene','DGene','JGene','V_AvgSHM','VIso','AA Seq']]
	df_collapsed=df_collapsed.sort_values(['Collapsed','CDR3_AA','CDR2_AA','CDR1_AA'],ascending=[False,True,True,True]).drop_duplicates(['AA Seq'])
		
	
	print 'Number of collapsed sequences: %s\n' %len(df_collapsed.index)
	numbers['Collapsed']=len(df_collapsed.index)
	numbers['Collapsed_Repeated']=len(df_collapsed[df_collapsed.Collapsed>1].index)
	
	
	#output fasta file for clustering
	df_clustered=df_collapsed[['CDR3_AA']].drop_duplicates()
	clustered_fasta=open('clustered.fasta','w')
	CDR_Search=[]
	for index, row in df_clustered.iterrows():
		clustered_fasta.write('%s\n' %row[0])
	if search!='None':
		for line in open(search,'r'):
			CDR3=line.strip()
			CDR_Search.append(CDR3)
			clustered_fasta.write('%s\n' %CDR3)
	clustered_fasta.close()

	
	print '********************** Clustering **********************\n'
	#perform clustering using single linkage 1 AA distance levenshtein distance
	os.system("/home/gg-jm76798/Desktop/FinalizedScripts/CDR3_Clonotyping -f clustered.fasta > clusters.txt")
	
	#read in results
	cluster_lookup={}
	for line in open('clusters.txt','r'):
		words=line.strip().split('\t')
		CDR_list=words[0]
		cluster=words[1]
		cluster_lookup[CDR_list]=cluster
		
	print 'Sequences analyzed: %s\n' %len(cluster_lookup)

	#maps cluster ID to sequences
	df_main['ClusterID']=df_main['CDR3_AA'].map(cluster_lookup)
	df_main['Clustered']=df_main[~df_main.ClusterID.isnull()].sort_values(['ClusterID','Collapsed','CDR1_AA','CDR2_AA','CDR3_AA'],ascending=[True,False,True,True,True]).drop_duplicates(['CDR1_AA','CDR2_AA','CDR3_AA','ClusterID']).groupby(['ClusterID'])['Collapsed'].transform(sum)
	
	numbers['Clustered']=len(df_main[df_main.Clustered>1].drop_duplicates('ClusterID').index)
	print 'Clusters generated: %s\n' %numbers['Clustered']
	
	
	print '***************** Clustering Complete ******************\n'
	
	if search=='None':
		print 'Generating files.\n'
		#list of output files
		collapsed_AA_output=open(prefix+'_all_sequences.txt','w')
		clustered_AA_output=open(prefix+'_clustered_sequences.txt','w')
		clustered_AA_raw_output=open(prefix+'_clustered_raw_sequences.txt','w')
		
		#pandas to output files
		df_collapsed.to_csv(collapsed_AA_output, sep='\t', index=None)
		df_main[['Clustered','Collapsed','ClusterID','CDR1_AA','CDR2_AA','CDR3_AA','VGene','DGene','JGene','V_AvgSHM','VIso']][df_main.Clustered>1].sort_values(['Clustered','ClusterID','Collapsed','CDR1_AA','CDR2_AA','CDR3_AA'],ascending=[False,True,False,True,True,True]).groupby(['ClusterID']).head(1).to_csv(clustered_AA_output, index=None, sep='\t')
		df_main[['Clustered','Collapsed','ClusterID','CDR1_AA','CDR2_AA','CDR3_AA','VGene','DGene','JGene','V_AvgSHM','VIso']][df_main.Clustered>1].sort_values(['Clustered','ClusterID','Collapsed','CDR1_AA','CDR2_AA','CDR3_AA'],ascending=[False,True,False,True,True,True]).drop_duplicates(['CDR1_AA','CDR2_AA','CDR3_AA','ClusterID']).to_csv(clustered_AA_raw_output, index=None, sep='\t')
		
		print 'Processing complete.\n'
		df_basics=df_main[['Clustered','Collapsed','ClusterID','CDR1_AA','CDR2_AA','CDR3_AA','VGene','DGene','JGene','V_AvgSHM','VIso','AA Seq']][df_main.Clustered>1].sort_values(['Clustered','ClusterID','Collapsed','CDR1_AA','CDR2_AA','CDR3_AA'],ascending=[False,True,False,True,True,True]).groupby(['ClusterID']).head(1)
		
		#Perform calculations
		VH_analysis.prepare_VH_only_analysis(numbers,df_basics,prefix,cluster)
		
		#close all files
		collapsed_AA_output.close()
		clustered_AA_output.close()
		clustered_AA_raw_output.close()
	
	
	else:
		print 'Generating CDR matches.\n'
		count=1
		for CDR in CDR_Search:
			print 'File %s: %s' %(count,CDR)
			cluster=cluster_lookup[CDR]
			cluster_output=open('CDR_'+str(CDR)+'_sequences.txt','w')
			
			df_tiny=df_main[['Clustered','Collapsed','ClusterID','CDR1_AA','CDR2_AA','CDR3_AA','VGene','DGene','JGene','V_AvgSHM','VIso','AA Seq']][df_main.ClusterID==cluster].sort_values(['Clustered','ClusterID','Collapsed','CDR1_AA','CDR2_AA','CDR3_AA'],ascending=[False,True,False,True,True,True]).drop_duplicates(['AA Seq'])
			df_tiny.to_csv(cluster_output, index=None, sep='\t')
			print 'Number of different sequences: %s' %len(df_tiny.index)
			
			cluster_output.close()
			count+=1


	
#python NoPairing_VH_v1.04.py stitched.fastq -group 'x' -CDR {'None' or File}
if __name__ == "__main__":
	arguments = sys.argv[1:]
	argnum = 0
	fastq_files = []
	while True:
		if argnum >= len(arguments):
			break
		elif arguments[argnum] == '-group': 
			argnum += 1
			groupname = arguments[argnum]
		elif arguments[argnum] == '-CDR': 
			argnum += 1
			CDR_list = arguments[argnum]
		else:
			fastq_files.append(arguments[argnum])
			f = os.path.expanduser(fastq_files[-1])			
			if not os.path.isfile(f):
				raise Exception('The provided file {0} does not exist'.format(f))
			fastq_files[-1] = os.path.abspath(f)			
		argnum += 1	
	VHPandas(fastq_files, groupname,CDR_list)
