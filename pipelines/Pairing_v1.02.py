import pandas as pd
from StringIO import StringIO
import os
import sys
import json
import VH_analysis
import VH_statistics as Vstatistics

#Pairing function for BCRseq data
#Requires modification of address for Usearch in line 145

def PairingPandas(fastq_files, clusters, groupname):
	cluster=clusters
	prefix=groupname
	readCutoff=1 #usually set to 1, which means there must be at least 2 reads for analysis
	
	#list of output files
	collapsed_nt_output=open(prefix+'_identical_nt_pairs.txt','w')
	clustered_nt_output=open(prefix+'_clustered_nt_pairs_over1read.txt','w')
	raw_clustered_nt_output=open(prefix+'_raw_clustered_nt_pairs_over1read.txt','w')
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
	
	#find any isotypes missed by MixCR
	print 'Analyzing for additional heavy chain isotyping.\n'
	df_main['VHIso']=df_main[['VHIso']].fillna(str('empty'))
	iso_before=(~df_main.VHIso.str.contains('empty')).sum()
	df_main['VHIso']=df_main.apply(lambda row: Vstatistics.find_isotype(row['IGH Sequence'],row['VHIso']),axis=1)
	iso_after=(~df_main.VHIso.str.contains('empty')).sum()
	print 'Additional isotypes defined: %s\n' %(iso_after-iso_before)
	
	#simplify isotype nomenclature
	iso_change_VH=lambda x : x['VHIso'].split('*')[0]
	df_main['VHIso']=df_main.apply(iso_change_VH,axis=1)
	iso_change_VL=lambda x : x['VL'][:3]
	df_main['VLIso']=df_main.apply(iso_change_VL,axis=1)
	
	print 'Number of correctly paired reads: %s\n' %len(df_main.index)
	numbers['ProductiveVHVL']=len(df_main.index)
	
	#redefine gene call strings (removes **)
	genes=['VH','DH','JH','VL','JL']
	for gene_desc in genes:
		df_main[gene_desc]=df_main[gene_desc].str.split('*').str[0]

	#calculate SHM
	df_main['VHmut']=df_main['VH_mismatch']/(df_main['VHEnd']-df_main['VHStart']+1)*100
	df_main['VLmut']=df_main['VL_mismatch']/(df_main['VLEnd']-df_main['VLStart']+1)*100

	#Collapse on identical CDRH3 + CDRL3 nt sequences
	df_main['Collapsed']=1
	df_main['Collapsed']=df_main.groupby(['CDRL3_NT','CDRH3_NT'])['Collapsed'].transform('count')
	df_main['VL_AvgSHM']=df_main.groupby(['CDRL3_NT','CDRH3_NT'])['VLmut'].transform('mean')
	df_main['VH_AvgSHM']=df_main.groupby(['CDRL3_NT','CDRH3_NT'])['VHmut'].transform('mean')

	#decrease number of decimals in SHM (just for output appearances)
	SHM_VH_dec=lambda x : round(x['VH_AvgSHM'],1)
	df_main['VH_AvgSHM']=df_main.apply(SHM_VH_dec,axis=1)
	SHM_VL_dec=lambda x : round(x['VL_AvgSHM'],1)
	df_main['VL_AvgSHM']=df_main.apply(SHM_VL_dec,axis=1)
		
	#create identical_nt_pairs file
	print 'Building paired output file.\n'
	df_collapsed=df_main[['Collapsed','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso']]
	df_collapsed=df_collapsed.sort_values(['Collapsed','CDRH3_AA'],ascending=[False,True]).drop_duplicates(['CDRH3_NT','CDRL3_NT'])
	df_collapsed.to_csv(collapsed_nt_output, sep='\t', index=None)
	
	print 'Number of collapsed pairs: %s\n' %len(df_collapsed.index)
	numbers['Collapsed']=len(df_collapsed.index)
	numbers['Collapsed_Repeated']=len(df_collapsed[df_collapsed.Collapsed>1].index)
	
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
	os.system("/home/gg-jm76798/Desktop/Lesson/Tools/usearch7 -cluster_smallmem clustered.fasta -minhsp 10 -minseqlength 10 -usersort -id {0} -centroids c.fa -uc clustered_output_file.uc".format(cluster))
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
	df_main['ClusterID']=df_main['Comboseq'].map(cluster_lookup)
	df_main['Clustered']=df_main[~df_main.ClusterID.isnull()].sort_values(['ClusterID','Collapsed','CDRH3_NT'],ascending=[True,False,True]).drop_duplicates(['Comboseq','ClusterID']).groupby(['ClusterID'])['Collapsed'].transform(sum)
	
	print 'Generating files.\n'

	df_main[['Clustered','Collapsed','ClusterID','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso']][df_main.Clustered>1].sort_values(['Clustered','ClusterID','Collapsed','CDRH3_NT'],ascending=[False,True,False,True]).groupby(['ClusterID']).head(1).to_csv(clustered_nt_output, index=None, sep='\t')
	df_main[['Clustered','Collapsed','ClusterID','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso']][df_main.Clustered>1].sort_values(['Clustered','ClusterID','Collapsed','CDRH3_NT'],ascending=[False,True,False,True]).drop_duplicates(['CDRH3_NT','CDRL3_NT','ClusterID']).to_csv(raw_clustered_nt_output, index=None, sep='\t')
	
	#create cluster specific files
	#df_main[['Clustered','Collapsed','ClusterID','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso','IGH Sequence','IGL Sequence']][df_main.ClusterID==1.0].sort_values(['Collapsed','Clustered','CDRH3_NT'],ascending=[False,False,True]).to_csv(open('ClusterID_1.txt','w'), index=None, sep='\t')
	
	print 'Processing complete.\n'
	
	df_basics=df_main[['Clustered','Collapsed','ClusterID','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso','IGH Sequence','IGL Sequence']][df_main.Clustered>1].sort_values(['Clustered','ClusterID','Collapsed','CDRH3_NT'],ascending=[False,True,False,True]).groupby(['ClusterID']).head(1)
	numbers['Clustered']=len(df_basics.index)
	
	#Perform calculations
	VH_analysis.prepare_VH_analysis(numbers,df_basics,prefix,cluster)
	
	
	
	
	
	#close files
	collapsed_nt_output.close()
	clustered_nt_output.close()
	raw_clustered_nt_output.close()
	
#python Pairing_v1.02.py R1.annotation R2.annotation -cluster 0.9 -group 'x'
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
		else:
			fastq_files.append(arguments[argnum])
			f = os.path.expanduser(fastq_files[-1])			
			if not os.path.isfile(f):
				raise Exception('The provided file {0} does not exist'.format(f))
			fastq_files[-1] = os.path.abspath(f)			
		argnum += 1	
	PairingPandas(fastq_files, cluster, groupname)
