import sys, os, json 
import pandas as pd
import numpy as np
import warnings 

from StringIO import StringIO

from Bio.Seq import Seq
from Bio.Alphabet import generic_dna, generic_protein




def PairingPandas(annotation_files, clusters, groupname):
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
	

	print '\nReading in R1 files.\n'
	df_R1=pd.read_csv(annotation_files[0], sep='\t', index_col='readName')
	print 'Number of total R1 reads post quality filter: %s\n' %len(df_R1.index) 
	numbers['R1']=len(df_R1.index)
	
	print 'Reading in R2 files.\n'
	df_R2=pd.read_csv(annotation_files[1], sep='\t', index_col='readName')
	print 'Number of total R2 reads post quality filter: %s\n' %len(df_R2.index)
	numbers['R2']=len(df_R2.index)


df1 = pd.read_csv('/data/russ/Dataset_206/Analysis_313/517C_10K_R1.mixcr.bigg.txt',  sep='\t')
df2 = pd.read_csv('/data/russ/Dataset_206/Analysis_314/517C_10K_R2.mixcr.bigg.txt',  sep='\t')

df1['readName'] = df1['readName'].apply(lambda r: r.split(' ')[0])
df2['readName'] = df2['readName'].apply(lambda r: r.split(' ')[0])

# df1.set_index('readName', inplace=True)
# df2.set_index('readName', inplace=True)

df = pd.merge(df1, df2, on='readName', suffixes=['_1', '_2'])

	df_main=pd.merge(df_R1,df_R2, how='inner', on=['Seqheader'])
	



	#split R1 and R2 dataframes in Vh and Vl reads 
	df_R1_vh = 
	df_R1_vl = 
	df_R2_vh = 
	df_R2_vl = 

	df_vh = df_R1_vh + df_R2_vh 
	df_vl = df_R1_vl + df_R2_vl 

	#Rename columns
	#For UTexas: R1=Light chains; R2=Heavy chains
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
	df_main['ClusterID']=df_main['Comboseq'].map(cluster_lookup)
	df_main['Clustered']=df_main[~df_main.ClusterID.isnull()].sort_values(['ClusterID','Collapsed','CDRH3_NT'],ascending=[True,False,True]).drop_duplicates(['Comboseq','ClusterID']).groupby(['ClusterID'])['Collapsed'].transform(sum)
	
	print 'Generating files.\n'

	df_main[['Clustered','Collapsed','ClusterID','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso']][df_main.Clustered>1].sort_values(['Clustered','ClusterID','Collapsed','CDRH3_NT'],ascending=[False,True,False,True]).groupby(['ClusterID']).head(1).to_csv(clustered_nt_output, index=None, sep='\t')
	df_main[['Clustered','Collapsed','ClusterID','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso']][df_main.Clustered>1].sort_values(['Clustered','ClusterID','Collapsed','CDRH3_NT'],ascending=[False,True,False,True]).drop_duplicates(['CDRH3_NT','CDRL3_NT','ClusterID']).to_csv(raw_clustered_nt_output, index=None, sep='\t')
	
	print 'Processing complete.\n'
	
	df_basics=df_main[['Clustered','Collapsed','ClusterID','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM','VHIso','VLIso','IGH Sequence','IGL Sequence']][df_main.Clustered>1].sort_values(['Clustered','ClusterID','Collapsed','CDRH3_NT'],ascending=[False,True,False,True]).groupby(['ClusterID']).head(1)
	numbers['Clustered']=len(df_basics.index)
	
	#Perform calculations
	VH_analysis.prepare_VH_analysis(numbers,df_basics,prefix,cluster)
		
	#close files
	collapsed_nt_output.close()
	clustered_nt_output.close()
	raw_clustered_nt_output.close()
	
#python Pairing_v1.01.py R1.annotation R2.annotation -cluster 0.9 -group 'x'
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



#From VH_analysis.py from Jon
#compatible with Pairing_v1.01
def prepare_VH_analysis(numbers,df,prefix,clusters):
	
	Vstats=open(prefix+'_Analysis.txt','w')
	Vstats.write('name\t%s\n' %(prefix))
	Vstats.write('meta1\tClustering parameter:%s\n' %clusters)
	
	#Defined for UT, where IGH=Read2, IGL=Read1
	Vstats.write('meta2\tNumber of R1 reads post quality filter:\t%s\n' %numbers['R1'])
	R1_mean, R1_std = Vstatistics.len_reads(df['IGL Sequence'])
	Vstats.write('meta3\tAverage R1 read length (std):\t%s\t%s\n' %(R1_mean, R1_std))
	
	Vstats.write('meta4\tNumber of R2 reads post quality filter:\t%s\n' %numbers['R2'])
	R2_mean, R2_std = Vstatistics.len_reads(df['IGH Sequence'])
	Vstats.write('meta5\tAverage R2 read length (std):\t%s\t%s\n' %(R2_mean, R2_std))
	
	Vstats.write('meta6\tNumber of combined reads post quality filter:\t%s\n' %numbers['VHVL'])
	Vstats.write('meta7\tNumber of productive reads:\t%s\n' %numbers['ProductiveVHVL'])
	Vstats.write('meta8\tNumber of collapsed sequences:\t%s\n' %numbers['Collapsed'])
	Vstats.write('meta9\tNumber of collapsed sequences over 1 read:\t%s\n' %numbers['Collapsed_Repeated'])
	Vstats.write('meta10\tNumber of clustered sequences:\t%s\n' %numbers['Clustered'])
	
	#Perform calculations
	print 'Calculating VH statistics.\n'
				
	#calculate VH gene distribution
	Vstats.write('\nVH gene distribution\n')
	Vstats.write('\tgene\tcount\tpercent\n')
	Vstatistics.print_gene_hist(Vstatistics.VH_hist(df['VH']),Vstats,False,'VHlong')
		
	#calculate VH simple gene distribution
	Vstats.write('\nVH gene distribution\n')
	Vstats.write('\tgene\tcount\tpercent\n')
	Vstatistics.print_gene_hist(Vstatistics.VH_simple_hist(df['VH']),Vstats,False,'VHshort')
		
	#calculate JH gene distribution
	Vstats.write('\nJH gene distribution\n')
	Vstats.write('\tgene\tcount\tpercent\n')
	Vstatistics.print_gene_hist(Vstatistics.JH_simple_hist(df['JH']),Vstats,False,'JHgene')
	
	#calculate VL gene distribution
	Vstats.write('\nVL gene distribution\n')
	Vstats.write('\tgene\tcount\tpercent\n')
	Vstatistics.print_gene_hist(Vstatistics.VL_hist(df['VL']),Vstats,False,'VLlong')
	
	#calculate CDRH3 amino acid distribution
	Vstats.write('\nCDRH3 amino acid distribution\n')
	Vstats.write('\tAA\tcount\tpercent\n')
	Vstatistics.print_aa_hist_keyorder(Vstatistics.AA_hist(df['CDRH3_AA']),Vstats,False,'CDRH3aa')
		
	#calculate CDRH3 length distribution in amino acids
	Vstats.write('\n\nVH CDRH3 length distribution\n')
	Vstats.write('length(aa)\tcount\n')
	length_hist,length_all = Vstatistics.len_hist(df['CDRH3_AA'])
	Vstatistics.print_len_hist(length_hist,Vstats,False,'CDRH_len')
	
	Vstats.write('\n\nCDRH3 Length Data for Box Plots\n')
	Vstatistics.print_box_plot(length_all,Vstats,'CDRH3_len_box')
	
	#calculate CDRL3 length distribution in amino acids
	Vstats.write('\n\nVL CDRL3 length distribution\n')
	Vstats.write('length(aa)\tcount\n')
	length_hist,length_all = Vstatistics.len_hist(df['CDRL3_AA'])
	Vstatistics.print_len_hist(length_hist,Vstats,False,'CDRL_len')
		
	Vstats.write('\n\nCDRL3 Length Data for Box Plots\n')
	Vstatistics.print_box_plot(length_all,Vstats,'CDRL3_len_box')
		
	#calculate CDRH3 hydrophobicity
	Vstats.write('\n\nVH CDRH3 Hydrophobicity for Box Plots\n')
	Hydro_seqs=Vstatistics.AA_Hydrophobicity_hist(df['CDRH3_AA'])
	Vstatistics.print_box_plot(Hydro_seqs,Vstats,'CDRH3_hydro')
		
	#calculate VH SHM distribution
	Vstats.write('\n\nVH SHM Data for Box Plots\n')
	VH_SHM_all = Vstatistics.shm_hist(df['VH_AvgSHM'])
	Vstatistics.print_box_plot(VH_SHM_all,Vstats,'VH_shm_box')
	
	#calculate Vgene SHM distribution
	Vstats.write('\n\nVL SHM Data for Box Plots\n')
	VL_SHM_all = Vstatistics.shm_hist(df['VL_AvgSHM'])
	Vstatistics.print_box_plot(VL_SHM_all,Vstats,'VL_shm_box')





#From VH_statistics.py from Jon 
#compatible with Pairing_v1.01
def VH_hist(df):
	"""
	gene_list=['IGHV1','IGHV1-12','IGHV1-14','IGHV1-17','IGHV1-18','IGHV1-2','IGHV1-24','IGHV1-3','IGHV1-38-4','IGHV1-45','IGHV1-46','IGHV1-58',
	'IGHV1-67','IGHV1-68','IGHV1-69','IGHV1-69D','IGHV1-8','IGHV2-10','IGHV2-26','IGHV2-5','IGHV2-70','IGHV2-70D','IGHV3','IGHV3-11','IGHV3-13',
	'IGHV3-15','IGHV3-16','IGHV3-19','IGHV3-20','IGHV3-21','IGHV3-22','IGHV3-23','IGHV3-23D','IGHV3-25','IGHV3-29','IGHV3-30','IGHV3-32','IGHV3-33',
	'IGHV3-33-2','IGHV3-35','IGHV3-36','IGHV3-37','IGHV3-38','IGHV3-38-3','IGHV3-41','IGHV3-42','IGHV3-42D','IGHV3-43','IGHV3-43D','IGHV3-47',
	'IGHV3-48','IGHV3-49','IGHV3-50','IGHV3-52','IGHV3-53','IGHV3-54','IGHV3-57','IGHV3-6','IGHV3-60','IGHV3-62','IGHV3-63','IGHV3-64','IGHV3-64D',
	'IGHV3-65','IGHV3-66','IGHV3-69','IGHV3-7','IGHV3-71','IGHV3-72','IGHV3-73','IGHV3-74','IGHV3-75','IGHV3-76','IGHV3-79','IGHV3-9','IGHV4-28',
	'IGHV4-30-1','IGHV4-30-2','IGHV4-30-4','IGHV4-31','IGHV4-34','IGHV4-38-2','IGHV4-39','IGHV4-4','IGHV4-55','IGHV4-59','IGHV4-61','IGHV4-80',
	'IGHV5-10','IGHV5-51','IGHV5-78','IGHV6-1','IGHV7','IGHV7-27','IGHV7-40','IGHV7-40D','IGHV7-4-1','IGHV7-56','IGHV7-77','IGHV7-81']

	genes_hist=dict.fromkeys(gene_list)
	for genes in genes_hist:
		genes_hist[genes]=[0,0]
	"""
	genes_hist={}
	for seq in df:
		if seq in genes_hist:
			genes_hist[seq][0]+=1
		else:
			genes_hist[seq]=[1,0]
	
	sum=0
	for gene in genes_hist:
		sum+=genes_hist[gene][0]
	
	for gene in genes_hist:
		genes_hist[gene][1]=genes_hist[gene][0]*100.0/sum
	
	return genes_hist
	
def VH_simple_hist(df):
	gene_list=['IGHV1','IGHV2','IGHV3','IGHV4','IGHV5','IGHV6','IGHV7']

	genes_hist=dict.fromkeys(gene_list)
	for genes in genes_hist:
		genes_hist[genes]=[0,0]
	
	for seq in df:
		simple_seq=seq.split('-')[0]
		if simple_seq in genes_hist:
			genes_hist[simple_seq][0]+=1
	
	sum=0
	for gene in genes_hist:
		sum+=genes_hist[gene][0]
	
	for gene in genes_hist:
		genes_hist[gene][1]=genes_hist[gene][0]*100.0/sum
	
	return genes_hist

def JH_simple_hist(df):
	gene_list=['IGHJ1','IGHJ2','IGHJ3','IGHJ4','IGHJ5','IGHJ6']

	genes_hist=dict.fromkeys(gene_list)
	for genes in genes_hist:
		genes_hist[genes]=[0,0]
	
	for seq in df:
		simple_seq=seq.split('-')[0]
		if simple_seq in genes_hist:
			genes_hist[simple_seq][0]+=1
	
	sum=0
	for gene in genes_hist:
		sum+=genes_hist[gene][0]
	
	for gene in genes_hist:
		genes_hist[gene][1]=genes_hist[gene][0]*100.0/sum
	
	return genes_hist	

def VL_hist(df):
	
	genes_hist={}
	for seq in df:
		if seq in genes_hist:
			genes_hist[seq][0]+=1
		else:
			genes_hist[seq]=[1,0]
	
	sum=0
	for gene in genes_hist:
		sum+=genes_hist[gene][0]
	
	for gene in genes_hist:
		genes_hist[gene][1]=genes_hist[gene][0]*100.0/sum
	
	return genes_hist
	
def len_reads(fullseq_list):
	long_list=[]
	for seq in fullseq_list:
		long_list.append(len(seq))
	return np.mean(long_list), np.std(long_list)
	
	
def AA_hist(seq_list):
	aa={'I':[0,0], 'V':[0,0], 'L':[0,0], 'F':[0,0], 'C':[0,0], 'M':[0,0], 'A':[0,0], 'G':[0,0], 'T':[0,0], 
	'W':[0,0], 'S':[0,0], 'Y':[0,0], 'P':[0,0], 'H':[0,0], 'E':[0,0], 'Q':[0,0], 'D':[0,0], 'N':[0,0],
	'K':[0,0], 'R':[0,0], 'X':[0,0]}
	
	for seq in seq_list:
		for letter in seq:
			aa[letter][0]+=1
	
	sum=0
	for letter in aa:
		sum+=aa[letter][0]
	
	for letter in aa:
		aa[letter][1]=aa[letter][0]*100.0/sum
	
	return aa

def len_hist(seq_list):
	hist={}
	all_seq=[]
	
	for seq in seq_list:
		length=len(seq)
		all_seq.append(length)
		if length in hist:
			hist[length][0]+=1
		else:
			hist[length]=[1,0]
	sum=0
	for num in hist:
		sum+=hist[num][0]
	
	for num in hist:
		hist[num][1]=hist[num][0]*100.0/sum
	
	return hist,all_seq
	
def shm_hist(shm_list):
	all_seq=[]
	
	for seq in shm_list:
		all_seq.append(seq)
	
	return all_seq

def AA_Hydrophobicity_hist(seq_list):
	#returns average hydrophobicity using Kyte-Doolittle index
	hydro={'I':4.5, 'V':4.2, 'L':3.8, 'F':2.8, 'C':2.5, 'M':1.9, 'A':1.8, 'G':-0.4, 'T':-0.7, 
	'W':-0.9, 'S':-0.8, 'Y':-1.3, 'P':-1.6, 'H':-3.2, 'E':-3.5, 'Q':-3.5, 'D':-3.5, 'N':-3.5,
	'K':-3.9, 'R':-4.5, 'X':0}
	
	hydrophobic_allseqs=[]
	#makes list (single) of hydrophobicity of each aa in a sequence; calculates avg hydrophobicity of seq
	#makes 2nd list (hydrophobic_allseqs) of average single hydrophobicities to calculate overall mean and std
	for word in seq_list:
		single=[]
		for letter in word:
			single.append(hydro[letter])
		
		seq_hydrophobicity=np.mean(single)
		hydrophobic_allseqs.append(np.mean(single))
	
	return hydrophobic_allseqs

def find_reading_frame(nt):
		sequence=Seq(nt,generic_dna)
		if '*' not in sequence.translate():
			return sequence
		elif '*' not in sequence[1:].translate():
			return sequence[1:]
		elif '*' not in sequence[2:].translate():
			return sequence[2:]
		else:
			return Seq('NNN',generic_dna)

def find_isotype(seq,isotype):
	if 'I' in isotype:
		return isotype
	#these are all reverse complements of isotype specific primers
	else:
		if 'GGAGTGCATCCGCCCCAACC' in seq:
			iso='IGHM'
		elif 'GGCTTCTTCCCCCAGGAGCC' in seq:
			iso='IGHA'
		elif 'GCTTCCACCAAGGGCCCATC' in seq:
			iso='IGHG'
		else:
			iso='empty'
		return iso

#rev is boolean for reverse
def print_gene_hist(hist,filename,rev,tag):
	for key in sorted(hist, key=lambda i:i, reverse=rev):	
		filename.write('%s\t%s\t%s\t%s\n' %(tag,key,hist[key][0],round(hist[key][1],1)))
		
def print_len_hist(hist,filename,rev,tag):
	for key in sorted(hist, key=lambda i:int(i), reverse=rev):	
		filename.write('%s\t%s\t%s\t%s\n' %(tag,key,hist[key][0],round(hist[key][1],1)))

def print_box_plot(s,filename,tag):
	for key in s:
		filename.write('%s\t%s\n' %(tag,key))
		
def print_aa_hist_keyorder(hist,filename,rev,tag):
	for key in sorted(hist, key=lambda i:i, reverse=rev):	
		filename.write('%s\t%s\t%s\t%s\n' %(tag,key,hist[key][0],round(hist[key][1],1)))



#From SaturationCurves.py from Jon
#Compatible with Pairing_v1.01 pipeline
def PairingPandas(fastq_files, clusters, groupname,headnum):
	cluster=clusters
	prefix=groupname
	
	summary=open(prefix+'_Saturation_Analysis.txt','w')
	summary.write('%s\n' %prefix)
	
	#turn off chained assignment warnings
	pd.options.mode.chained_assignment = None
	
	#read in mixcr output file, use MiSeq identifier as index
	usefulcols=['Seqheader','Strand corrected sequence','Locus','FirstVgene', 'FirstDgene', 'FirstJgene','Read(s) sequence qualities','AA. Seq. CDR3','N. Seq. CDR3','VGENE: Germline start','VGENE: Germline end','VGENE: Mismatch','All C hits','Productivity']
	col_types={'Seqheader':str,'Strand corrected sequence':str,'Locus':str,'FirstVgene':str, 'FirstDgene':str, 'FirstJgene':str,'Read(s) sequence qualities':str,'AA. Seq. CDR3':str,'N. Seq. CDR3':str,'VGENE: Germline start':float,'VGENE: Germline end':float,'VGENE: Mismatch':float,'All C hits':str,'Productivity':str}
	
	print '\nReading in R1 files.\n'
	df_R1=pd.read_csv(fastq_files[0], sep='\t', skiprows=[0],usecols=usefulcols, dtype=col_types)
	print 'Number of total R1 reads post quality filter: %s\n' %len(df_R1.index) 
	summary.write('Number of total R1 reads post quality filter: %s\n' %len(df_R1.index))
	
	print 'Reading in R2 files.\n'
	df_R2=pd.read_csv(fastq_files[1], sep='\t', skiprows=[0],usecols=usefulcols, dtype=col_types)
	print 'Number of total R2 reads post quality filter: %s\n' %len(df_R2.index)
	summary.write('Number of total R2 reads post quality filter: %s\n' %len(df_R2.index))
	
	#remove final Miseq identifiers R1 and R2 for UTexas MiSeq
	df_R1['Seqheader']=df_R1['Seqheader'].str[:-8]
	df_R2['Seqheader']=df_R2['Seqheader'].str[:-8]

	print 'Processing quality paired sequences.\n'
	#Find intersection of both R1 and R2 files
	df_main=pd.merge(df_R1,df_R2, how='inner', on=['Seqheader'])
	
	#Rename columns
	#For UTexas: R1=Light chains; R2=Heavy chains
	df_main=df_main.rename(columns={'Seqheader':'SeqID','Strand corrected sequence_y':'IGH Sequence','Locus_y':'H_Locus','FirstVgene_y':'VH', 'FirstDgene_y':'DH', 'FirstJgene_y':'JH','Read(s) sequence qualities_y':'IGH_Qual','AA. Seq. CDR3_y':'CDRH3_AA','N. Seq. CDR3_y':'CDRH3_NT','VGENE: Germline start_y':'VHStart','VGENE: Germline end_y':'VHEnd','VGENE: Mismatch_y':'VH_mismatch','All C hits_y':'VHIso','Productivity_x':'Productivity','Strand corrected sequence_x':'IGL Sequence','Locus_x':'L_Locus','FirstVgene_x':'VL', 'FirstJgene_x':'JL','Read(s) sequence qualities_x':'IGL_Qual','AA. Seq. CDR3_x':'CDRL3_AA','N. Seq. CDR3_x':'CDRL3_NT','VGENE: Germline start_x':'VLStart','VGENE: Germline end_x':'VLEnd','VGENE: Mismatch_x':'VL_mismatch','All C hits_x':'VLIso'})
	
	print 'Number of combined reads post quality filter: %s\n' %len(df_main.index)
	summary.write('Number of combined reads post quality filter: %s\n' %len(df_main.index))
	
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

		#redefine gene call strings (removes **)
		genes=['VH','DH','JH','VL','JL']
		for gene_desc in genes:
			df_main_sub[gene_desc]=df_main_sub[gene_desc].str.split('*').str[0]

		#calculate SHM
		df_main_sub['VHmut']=df_main_sub['VH_mismatch']/(df_main_sub['VHEnd']-df_main_sub['VHStart']+1)*100
		df_main_sub['VLmut']=df_main_sub['VL_mismatch']/(df_main_sub['VLEnd']-df_main_sub['VLStart']+1)*100
		
		#Collapse on identical CDRH3 + CDRL3 nt sequences
		df_main_sub['Collapsed']=1
		df_main_sub['Collapsed']=df_main_sub.groupby(['CDRL3_NT','CDRH3_NT'])['Collapsed'].transform('count')
		df_main_sub['VL_AvgSHM']=df_main_sub.groupby(['CDRL3_NT','CDRH3_NT'])['VLmut'].transform('mean')
		df_main_sub['VH_AvgSHM']=df_main_sub.groupby(['CDRL3_NT','CDRH3_NT'])['VHmut'].transform('mean')

		#create identical_nt_pairs file
		print 'Building paired output file.\n'
		df_collapsed=df_main_sub[['Collapsed','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','VH','DH','JH','VL','JL','VH_AvgSHM','VL_AvgSHM']]
		df_collapsed=df_collapsed.sort_values(['Collapsed','CDRH3_AA'],ascending=[False,True]).drop_duplicates(['CDRH3_NT','CDRL3_NT'])
		#df_collapsed.to_csv(collapsed_nt_output, sep='\t', index=None)
		
		print 'Number of collapsed pairs: %s\n' %len(df_collapsed.index)
		summary.write('\t%s' %len(df_collapsed.index))
	
		#output fasta file for clustering
		df_clustered=df_collapsed[['Collapsed','CDRH3_NT','CDRL3_NT']]
		clustered_fasta=open('clustered.fasta','w')
		for index, row in df_clustered[(df_clustered['Collapsed']>1)].iterrows():
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

		summary.write('\t%s\n' %len(df_clustered.index))
		
		#delete dataframes for next loop
		del_list=[df_main_sub,df_collapsed,df_clustered]
		del df_main_sub
		del df_collapsed
		del df_clustered
	
	print 'Pairing complete.\n'
	summary.close()
	
#python SaturationCurves.py R1.annotation R2.annotation -cluster 0.9 -group 'x' -head 10000
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



#From Compare_Curves.py from Jon 
#Compatible with Pairing_v1.01
#Requires collapsed nucleotide files as input
def Compare(files,cluster,output):

	print 'Reading in File 1: %s.\n' %str(files[0])
	df_A=pd.read_csv(files[0], sep='\t')
	df_A['Group']='A'
	
	print 'Reading in File 2: %s.\n' %str(files[1])
	df_B=pd.read_csv(files[1], sep='\t')
	df_B['Group']='B'
	
	df_main=pd.concat([df_A,df_B])
	df_main['Comboseq']=df_main['CDRH3_NT']+':'+df_main['CDRL3_NT']
	
	df_main=df_main[['Collapsed','CDRH3_AA','CDRL3_AA','CDRH3_NT','CDRL3_NT','Comboseq','Group','VH_AvgSHM','VL_AvgSHM']]

	#output fasta file for clustering
	df_clustered=df_main[['Collapsed','CDRH3_NT','CDRL3_NT']]
	clustered_fasta=open('compare_clustered.fasta','w')
	for index, row in df_clustered[(df_clustered['Collapsed']>1)].iterrows():
		clustered_fasta.write('>%s:%s\n' %(row[1],row[2]))
		clustered_fasta.write('%s\n' %row[1])
	clustered_fasta.close()

	#perform clustering
	os.system("/home/gg-jm76798/Desktop/FinalizedScripts/usearch7 -cluster_smallmem compare_clustered.fasta -minhsp 10 -minseqlength 10 -usersort -id {0} -centroids c.fa -uc compare_clustered_output_file.uc".format(cluster))

	#read in results
	Clust_cols=['SeedorHit','ClusterID','Length','Match', 'Blank1', 'Blank2','Blank3','Blank4','Comboseq','CDR_matchseq']
	clust_types={'SeedorHit':str,'ClusterID':int,'Length':int,'Match':str, 'Blank1':str, 'Blank2':str,'Blank3':str,'Blank4':str,'Comboseq':str,'CDR_matchseq':str}

	print '\nParsing clustering information.\n'
	cluster_results=pd.read_csv('compare_clustered_output_file.uc', sep='\t', names=Clust_cols)
	cluster_results=cluster_results[['SeedorHit','ClusterID','Comboseq']]
	cluster_results=cluster_results[cluster_results.SeedorHit != 'C']

	#redefine clusterID so it runs 1...x instead of 0...x
	cluster_results['ClusterID']=cluster_results['ClusterID'].astype(int)+1

	#Prepares dictionary for mapping cluster numbers to sequences
	cluster_lookup=cluster_results.set_index('Comboseq')['ClusterID'].to_dict()

	#maps cluster ID to sequences
	df_main['ClusterID']=df_main['Comboseq'].map(cluster_lookup)
	df_main['Clustered']=1
	df_main['Clustered']=df_main.groupby(['ClusterID'])['Clustered'].transform('count')
	
	print '\nParsing group information.\n'
	#prepare dictionary to map groups back to cluster ID
	group_lookup=dict()
	df_small=df_main[['ClusterID','Group']].dropna(subset=['ClusterID']).drop_duplicates(['ClusterID','Group'])

	for id in sorted(df_small['ClusterID']):
		sub_df=df_small[df_small.ClusterID==id]
		grouplist=''.join(sub_df['Group'].tolist())
		
		if id not in group_lookup:
			group_lookup[id]=grouplist
	
	#maps clustered groups back to clusterID
	df_main['ClusterGroup']=df_main['ClusterID'].map(group_lookup)
	
	
	df_final=df_main[['Collapsed','ClusterID','Clustered','ClusterGroup','CDRH3_AA','CDRL3_AA','VH_AvgSHM','VL_AvgSHM']].drop_duplicates(['ClusterID','ClusterGroup']).fillna(0)

	#print results
	print 'Summarizing results.\n'
	summary=open('comparison_summary.txt','w')
	summary.write('File A: %s\n' %files[0])
	summary.write('File B: %s\n' %files[1])
	summary.write('Clustering: %s\n\n' %cluster)
	summary.write('A total collapsed: %s\n' %len(df_A.index))
	summary.write('B total collapsed: %s\n' %len(df_B.index))
	summary.write('A only clusters: %s\n' %len(df_final[df_final.ClusterGroup=='A'].index))
	summary.write('B only clusters: %s\n' %len(df_final[df_final.ClusterGroup=='B'].index))
	summary.write('Overlapped clusters: %s\n' %len(df_final[df_final.ClusterGroup=='AB'].index))
	summary.write('Total clusters: %s\n' %len(df_final.index))
	summary.close()
	
	if output: #if output of separate groups is desired
		Aonly=open('FileA_sequences.txt','w')
		Bonly=open('FileB_sequences.txt','w')
		AB=open('FileAB_overlapping_sequences.txt','w')
		
		df_final[df_final.ClusterGroup=='A'].to_csv(Aonly,sep='\t',index=None)
		df_final[df_final.ClusterGroup=='B'].to_csv(Bonly,sep='\t',index=None)
		df_final[df_final.ClusterGroup=='AB'].to_csv(AB,sep='\t',index=None)
		
		Aonly.close()
		Bonly.close()
		AB.close()

#type in >python Compare_Groups.py identical_nt_pairs-1.txt identical_nt_pairs-2.txt -cluster 0.9 -output True
#output defines whether to produce Aonly, Bonly, and overlapped lists of sequences
if __name__ == "__main__":
	arguments = sys.argv[1:]
	argnum = 0
	files = []
	while True:
		if argnum >= len(arguments):
			break
		if arguments[argnum] == '-cluster':
			argnum += 1
			cluster = arguments[argnum]
		elif arguments[argnum] == '-output':
			argnum += 1
			output = arguments[argnum]
		else:
			files.append(arguments[argnum])
			f = os.path.expanduser(files[-1])			
			if not os.path.isfile(f):
				raise Exception('The provided file {0} does not exist'.format(f))
			files[-1] = os.path.abspath(f)			
		argnum += 1	
	Compare(files, cluster,output)


#From Stats.py from Jon
class Stats:

	clusters = 0
	lengths = 0

	def __init__(self, filename):
		df = pandas.read_csv(filename, sep='\t')
		self.clusters = self.lengths = df.Clustered


	#Total clusters from PandaSeq output
	def totalClusters(self):
		return self.clusters.count()


	#Returns Big N50 cluster analysis
	#The number of clusters constituting the top 50 percent
	#of the total mass of clusters
	def N50(self):

		numlist = self.lengths.tolist()

		#Making file data useful (sorting)
		numlist.sort()
		newlist = []
		for x in numlist:
			newlist += [x]*x

		#returning N50 value
		if len(newlist) % 2 == 0:
			medianpos = len(newlist)/2
			return float(newlist[medianpos] + newlist[medianpos-1]) / 2
		else:
			medianpos = len(newlist)/2
			return newlist[medianpos]


	#Returns Little n50 cluster analysis
	#The smallest value above the N50 threshold
	def n50(self):

		n = self.N50()

		#return n50 value
		return self.lengths[self.lengths>n].count()


	#Returns the percent above the N50 threshold showing
	#data accuracy
	def percent(self):

		#Get n50 and total clusters
		littleN50 = self.n50()
		total = self.totalClusters()

		#return percentage
		return float(littleN50)/float(total)*100