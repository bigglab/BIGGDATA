import pandas as pd
from StringIO import StringIO
import os
import json
import sys
import numpy as np
from Bio.Seq import Seq
from Bio.Alphabet import generic_dna, generic_protein

#compatible with Pairing_v1.02
#this is just a methods files called by Pairing_v1.02, VH_Analyzer_v1.04, VL_Analyzer_v1.04


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

def clonal_frequency(cluster_list):
	#returns clonal frequency dict
	freq=[]
	total=sum(cluster_list)
	for num in cluster_list:
		freq.append(num*100.0/total)
	return freq
	
	
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