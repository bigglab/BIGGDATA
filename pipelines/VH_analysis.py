import pandas as pd
from StringIO import StringIO
import os
import sys
import json
import VH_statistics as Vstatistics
from Bio.Seq import Seq
from Bio.Alphabet import generic_dna, generic_protein

#compatible with Pairing_v1.02, VH_Analyzer_v1.04, VL_Analyzer_v1.04
#This is just a methods file

def prepare_VH_analysis(numbers,df,prefix,clusters):
	
	Vstats=open(prefix+'_Analysis.txt','w')
	Vstats.write('name\t%s\n' %(prefix))
	Vstats.write('meta1\tClustering parameter:%s\n' %clusters)
	
	#Defined for UT, where IGH=Read2, IGL=Read1
	Vstats.write('meta2\tNumber of R1 reads post quality filter:\t%s\n' %numbers['R1'])
	R1_mean, R1_std = Vstatistics.len_reads(df['IGL Sequence'])
	Vstats.write('meta3\tAverage R1 read length (std):\t%s\t%s\n' %(round(R1_mean,0), round(R1_std,0)))
	
	Vstats.write('meta4\tNumber of R2 reads post quality filter:\t%s\n' %numbers['R2'])
	R2_mean, R2_std = Vstatistics.len_reads(df['IGH Sequence'])
	Vstats.write('meta5\tAverage R2 read length (std):\t%s\t%s\n' %(round(R2_mean,0), round(R2_std,0)))
	
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

def prepare_VH_only_analysis(numbers,df,prefix,clusters):
	
	Vstats=open(prefix+'_Analysis.txt','w')
	Vstats.write('name\t%s\n' %(prefix))
	Vstats.write('meta1\tClustering parameter:%s\n' %clusters)
	
	#Defined for UT
	Vstats.write('meta2\tNumber of reads post quality filter:\t%s\n' %numbers['reads'])
	
	Vstats.write('meta7\tNumber of productive reads:\t%s\n' %numbers['ProductiveV'])
	Vstats.write('meta8\tNumber of collapsed sequences:\t%s\n' %numbers['Collapsed'])
	Vstats.write('meta9\tNumber of collapsed sequences over 1 read:\t%s\n' %numbers['Collapsed_Repeated'])
	Vstats.write('meta10\tNumber of clustered sequences:\t%s\n' %numbers['Clustered'])
	
	#Perform calculations
	print 'Calculating VH statistics.\n'
				
	#calculate VH gene distribution
	Vstats.write('\nVH gene distribution\n')
	Vstats.write('\tgene\tcount\tpercent\n')
	Vstatistics.print_gene_hist(Vstatistics.VH_hist(df['VGene']),Vstats,False,'VHlong')
		
	#calculate VH simple gene distribution
	Vstats.write('\nVH gene distribution\n')
	Vstats.write('\tgene\tcount\tpercent\n')
	Vstatistics.print_gene_hist(Vstatistics.VH_simple_hist(df['VGene']),Vstats,False,'VHshort')
		
	#calculate JH gene distribution
	Vstats.write('\nJH gene distribution\n')
	Vstats.write('\tgene\tcount\tpercent\n')
	Vstatistics.print_gene_hist(Vstatistics.JH_simple_hist(df['JGene']),Vstats,False,'JHgene')
	
	#calculate CDRH3 amino acid distribution
	Vstats.write('\nCDRH3 amino acid distribution\n')
	Vstats.write('\tAA\tcount\tpercent\n')
	Vstatistics.print_aa_hist_keyorder(Vstatistics.AA_hist(df['CDR3_AA']),Vstats,False,'CDRH3aa')
		
	#calculate CDRH3 length distribution in amino acids
	Vstats.write('\n\nVH CDRH3 length distribution\n')
	Vstats.write('length(aa)\tcount\n')
	length_hist,length_all = Vstatistics.len_hist(df['CDR3_AA'])
	Vstatistics.print_len_hist(length_hist,Vstats,False,'CDRH_len')
	
	Vstats.write('\n\nCDRH3 Length Data for Box Plots\n')
	Vstatistics.print_box_plot(length_all,Vstats,'CDR3_len_box')
		
	#calculate CDRH3 hydrophobicity
	Vstats.write('\n\nVH CDRH3 Hydrophobicity for Box Plots\n')
	Hydro_seqs=Vstatistics.AA_Hydrophobicity_hist(df['CDR3_AA'])
	Vstatistics.print_box_plot(Hydro_seqs,Vstats,'CDRH3_hydro')
		
	#calculate VH SHM distribution
	Vstats.write('\n\nVH SHM Data for Box Plots\n')
	VH_SHM_all = Vstatistics.shm_hist(df['V_AvgSHM'])
	Vstatistics.print_box_plot(VH_SHM_all,Vstats,'V_shm_box')

def prepare_VL_only_analysis(numbers,df,prefix,clusters):
	
	Vstats=open(prefix+'_Analysis.txt','w')
	Vstats.write('name\t%s\n' %(prefix))
	Vstats.write('meta1\tClustering parameter:%s\n' %clusters)
	
	#Defined for UT
	Vstats.write('meta2\tNumber of reads post quality filter:\t%s\n' %numbers['reads'])
	
	Vstats.write('meta7\tNumber of productive reads:\t%s\n' %numbers['ProductiveV'])
	Vstats.write('meta8\tNumber of collapsed sequences:\t%s\n' %numbers['Collapsed'])
	Vstats.write('meta9\tNumber of collapsed sequences over 1 read:\t%s\n' %numbers['Collapsed_Repeated'])
	Vstats.write('meta10\tNumber of clustered sequences:\t%s\n' %numbers['Clustered'])
	
	#Perform calculations
	print 'Calculating VL statistics.\n'
				
	#calculate VL gene distribution
	Vstats.write('\nVL gene distribution\n')
	Vstats.write('\tgene\tcount\tpercent\n')
	Vstatistics.print_gene_hist(Vstatistics.VH_hist(df['VGene']),Vstats,False,'VLlong')
	
	#calculate CDRL3 amino acid distribution
	Vstats.write('\nCDRL3 amino acid distribution\n')
	Vstats.write('\tAA\tcount\tpercent\n')
	Vstatistics.print_aa_hist_keyorder(Vstatistics.AA_hist(df['CDR3_AA']),Vstats,False,'CDRL3aa')
		
	#calculate CDRL3 length distribution in amino acids
	Vstats.write('\n\nVL CDRL3 length distribution\n')
	Vstats.write('length(aa)\tcount\n')
	length_hist,length_all = Vstatistics.len_hist(df['CDR3_AA'])
	Vstatistics.print_len_hist(length_hist,Vstats,False,'CDRL_len')
	
	Vstats.write('\n\nCDRH3 Length Data for Box Plots\n')
	Vstatistics.print_box_plot(length_all,Vstats,'CDR3_len_box')
		
	#calculate CDRL3 hydrophobicity
	Vstats.write('\n\nVH CDRL3 Hydrophobicity for Box Plots\n')
	Hydro_seqs=Vstatistics.AA_Hydrophobicity_hist(df['CDR3_AA'])
	Vstatistics.print_box_plot(Hydro_seqs,Vstats,'CDR3_hydro')
		
	#calculate VH SHM distribution
	Vstats.write('\n\nVL SHM Data for Box Plots\n')
	VL_SHM_all = Vstatistics.shm_hist(df['V_AvgSHM'])
	Vstatistics.print_box_plot(VL_SHM_all,Vstats,'V_shm_box')