import os, sys 
import pandas as pd 
import numpy as np 
import random 
from collections import OrderedDict
import json 


#Sometimes we need to retranslate FR4 in new mixcr output... 
codon_aa_dict = {"UUU":"F", "UUC":"F", "UUA":"L", "UUG":"L",
       "UCU":"S", "UCC":"S", "UCA":"S", "UCG":"S",
       "UAU":"Y", "UAC":"Y", "UAA":"*", "UAG":"*",
       "UGU":"C", "UGC":"C", "UGA":"*", "UGG":"W",
       "CUU":"L", "CUC":"L", "CUA":"L", "CUG":"L",
       "CCU":"P", "CCC":"P", "CCA":"P", "CCG":"P",
       "CAU":"H", "CAC":"H", "CAA":"Q", "CAG":"Q",
       "CGU":"R", "CGC":"R", "CGA":"R", "CGG":"R",
       "AUU":"I", "AUC":"I", "AUA":"I", "AUG":"M",
       "ACU":"T", "ACC":"T", "ACA":"T", "ACG":"T",
       "AAU":"N", "AAC":"N", "AAA":"K", "AAG":"K",
       "AGU":"S", "AGC":"S", "AGA":"R", "AGG":"R",
       "GUU":"V", "GUC":"V", "GUA":"V", "GUG":"V",
       "GCU":"A", "GCC":"A", "GCA":"A", "GCG":"A",
       "GAU":"D", "GAC":"D", "GAA":"E", "GAG":"E",
       "GGU":"G", "GGC":"G", "GGA":"G", "GGG":"G",}

def translate_human_nt(string):
    if not type(string) == str: return ''
    string = string.replace('T', 'U', 999) 
    start = 0 
    final = ''
    while start+2 < len(string):
        codon = string[start:start+3]
        final = final + codon_aa_dict[codon]
        start+=3
    return final


def trim_ig_allele_name(long_name): 
    if long_name == None: return ''
    if '*' in long_name: long_name = [l for l in long_name.split('*') if 'IG' in l or 'TR' in l][0]
    return long_name

def trim_ig_locus_name(long_name): 
    # print 'trimming long name: {}'.format(long_name)
    if long_name == None: return ''
    if long_name == '*': return ''
    if long_name == '.': return ''
    if long_name == 'P': return ''
    if long_name == '-': return ''
    if long_name == ' ': return ''
    if '-' in long_name: long_name = [l for l in long_name.split('-') if 'IG' in l or 'TR' in l][0]
    if '*' in long_name: long_name = [l for l in long_name.split('*') if 'IG' in l or 'TR' in l][0]
    if '.' in long_name: long_name = [l for l in long_name.split('.') if 'IG' in l or 'TR' in l][0]
    if 'P' in long_name: long_name = [l for l in long_name.split('P') if 'IG' in l or 'TR' in l][0]
    if ' ' in long_name: long_name = [l for l in long_name.split(' ') if 'IG' in l or 'TR' in l][0]
    return long_name



def parse_alignments_from_mixcr_hits(hits): 
    try: 
        hits.split(',')
    except: 
        return None 
    else: 
        score_dict = OrderedDict()
        hs = hits.split(',')
        if len(hs) == 0: 
            return score_dict
        for h in hs: 
            if len(h.split('(')) != 2: 
                # print '!!!!!!! Empty h?:  {}'.format(h)
                continue
            gene,score = h.split('(')
            # short_gene = trim_ig_locus_name(gene)
            score = int(score.replace(')',''))
            score_dict[gene] = score 
        return score_dict 

def select_top_hit(hits):
    if hits !=  None :
        top_hit = trim_ig_allele_name(sorted(hits.items(), key=lambda x: x[1], reverse=True)[0][0])
        return top_hit
    else: 
        return None

def parse_alignments_from_IGFFT_hits_and_scores(hits, scores): 
       hits = hits.split(',')
       scores = scores.split(',')
       return(zip(hits, scores))

def parse_v_alignments_from_IGFFT_dataframe(row): 
       hits = row['Top_V-Gene_Hits'].split(',')
       scores = row['V-Gene_Alignment_Scores'].split(',')
       return(OrderedDict(zip(hits, scores)))

def parse_j_alignments_from_IGFFT_dataframe(row): 
       hits = row['Top_J-Gene_Hits'].split(',')
       scores = row['J-Gene_Alignment_Scores'].split(',')
       return(OrderedDict(zip(hits, scores)))

def parse_full_length_nt_seq_from_annotation_dataframe(row): 
    #return row['nSeqFR1'] + row['nSeqCDR1'] + row['nSeqFR2'] + row['nSeqCDR2'] + row['nSeqFR3'] + row['nSeqCDR3'] + row['nSeqFR4']
    return ''.join(row[['nSeqFR1', 'nSeqCDR1', 'nSeqFR2', 'nSeqCDR2', 'nSeqFR3', 'nSeqCDR3', 'nSeqFR4']].dropna().values.astype(str))

def parse_full_length_aa_seq_from_annotation_dataframe(row): 
    #return row['aaSeqFR1'] + row['aaSeqCDR1'] + row['aaSeqFR2'] + row['aaSeqCDR2'] + row['aaSeqFR3'] + row['aaSeqCDR3'] + row['aaSeqFR4']
    return ''.join(row[['aaSeqFR1', 'aaSeqCDR1', 'aaSeqFR2', 'aaSeqCDR2', 'aaSeqFR3', 'aaSeqCDR3', 'aaSeqFR4']].dropna().values.astype(str))


def parse_mixcr_alignment_string_to_shm(alignment):
    #only consider the first alignment 
    alignment = alignment.split(';')[0] 
    #different fields of alignment are separated by '|'
    sub_strings = alignment.split('|')
    germ_start = sub_strings[0]
    germ_end = sub_strings[1]
    query_start = sub_strings[3]
    query_end = sub_strings[4]
    algn_len = sub_strings[2]
    alignment_string = sub_strings[5]
    num_mismatch = alignment_string.count('S')
    num_del = alignment_string.count('D')
    num_ins = alignment_string.count('I')
    shm = (num_mismatch+num_del+num_ins)/float(algn_len)*100
    return shm

# def parse_mixcr_vAlignment_to_shm(row):
#     alignment = row['vAlignment']
#     return parse_mixcr_alignment_string_to_shm(alignment)

# def parse_mixcr_jAlignment_to_shm(row):
#     alignment = row['jAlignment']
#     return parse_mixcr_alignment_string_to_shm(alignment)

def clean_null_string(string): 
    if string == 'null': 
        return None
    else: 
        return string 

clean_annotation_dataframe_columns = [
 'readName',
 'readCount',
 'readSequence',
 'v_top_hit',
 'v_top_hit_locus',
 'd_top_hit',
 'd_top_hit_locus',
 'j_top_hit',
 'j_top_hit_locus',
 'c_top_hit',
 'c_top_hit_locus',
 'nFullSeq',
 'aaFullSeq',
 'nSeqFR1',
 'nSeqCDR1',
 'nSeqFR2',
 'nSeqCDR2',
 'nSeqFR3',
 'nSeqCDR3',
 'nSeqFR4',
 'qualFR1',
 'qualCDR1',
 'qualFR2',
 'qualCDR2',
 'qualFR3',
 'qualCDR3',
 'qualFR4',
 'aaSeqFR1',
 'aaSeqCDR1',
 'aaSeqFR2',
 'aaSeqCDR2',
 'aaSeqFR3',
 'aaSeqCDR3',
 'aaSeqFR4',
 'v_region_shm',
 'j_region_shm',
]


def build_annotation_dataframe_from_igfft_file(file_path, rmindels=True, append_ms_peptides=False, require_annotations=['aaSeqFR1', 'aaSeqCDR1', 'aaSeqFR2', 'aaSeqCDR2', 'aaSeqFR3', 'aaSeqCDR3', 'aaSeqFR4']):
    df = pd.read_table(file_path) #, low_memory=False)
    column_reindex = {
          'Header' : 'readName',
          'Sequence' : 'readSequence',
          'FR1_Sequence.NT' : 'nSeqFR1',
          'CDR1_Sequence.NT' : 'nSeqCDR1',
          'FR2_Sequence.NT' : 'nSeqFR2',
          'CDR2_Sequence.NT' : 'nSeqCDR2',
          'FR3_Sequence.NT' : 'nSeqFR3',
          'CDR3_Sequence.NT' : 'nSeqCDR3',
          'FR4_Sequence.NT' : 'nSeqFR4',
          'FR1_Sequence.AA' : 'aaSeqFR1',
          'CDR1_Sequence.AA' : 'aaSeqCDR1',
          'FR2_Sequence.AA' : 'aaSeqFR2',
          'CDR2_Sequence.AA' : 'aaSeqCDR2',
          'FR3_Sequence.AA' : 'aaSeqFR3',
          'CDR3_Sequence.AA' : 'aaSeqCDR3',
          'FR4_Sequence.AA' : 'aaSeqFR4',
          'Isotype' : 'c_top_hit',
          'Isotype percent similarity' : 'cBestIdentityPercent',
    }
    df = df.rename(str, columns=column_reindex)
    if require_annotations != False: df = df.dropna(subset=require_annotations, how='any')
    df = df.dropna(subset=['Top_V-Gene_Hits', 'Top_J-Gene_Hits'], how='any')
    df['c_top_hit_locus'] = df['c_top_hit'] 
    df['allVHitsWithScore'] = df.apply(parse_v_alignments_from_IGFFT_dataframe, axis=1)
    df['allJHitsWithScore'] = df.apply(parse_j_alignments_from_IGFFT_dataframe, axis=1)
    df['allDHitsWithScore'] = ''
    df['allCHitsWithScore'] = ''
    df['v_top_hit'] = df['allVHitsWithScore'].apply(select_top_hit)
    df['v_top_hit_locus'] = df['v_top_hit'].apply(trim_ig_locus_name)
    df['j_top_hit'] = df['allJHitsWithScore'].apply(select_top_hit)
    df['j_top_hit_locus'] = df['j_top_hit'].apply(trim_ig_locus_name)
    df['allVHitsWithScore'] = df['allVHitsWithScore'].apply(json.dumps).apply(clean_null_string)
    df['allJHitsWithScore'] = df['allJHitsWithScore'].apply(json.dumps).apply(clean_null_string)
    df['d_top_hit'] = None
    df['d_top_hit_locus'] = None
    df['nFullSeq'] = df.apply(parse_full_length_nt_seq_from_annotation_dataframe, axis=1) if len(df) >=1 else ''
    df['aaFullSeq'] = df.apply(parse_full_length_aa_seq_from_annotation_dataframe, axis=1) if len(df) >=1 else ''
    df = df[~df['aaFullSeq'].str.contains('\*|_')] if rmindels == True else df
    df = append_cterm_peptides_for_mass_spec(df) if append_ms_peptides == True else df
    df['v_region_shm'] = df['VRegion.SHM.Per_nt']
    df['j_region_shm'] = df['JRegion.SHM.Per_nt']
    df['qualFR1'] = None
    df['qualCDR1'] = None
    df['qualFR2'] = None
    df['qualCDR2'] = None
    df['qualFR3'] = None
    df['qualCDR3'] = None
    df['qualFR4'] = None
    df = collapse_annotation_dataframe(df)
    df = df[clean_annotation_dataframe_columns]
    return df 



def build_annotation_dataframe_from_mixcr_file(file_path, rmindels=True, append_ms_peptides=False, require_annotations=['aaSeqFR1', 'aaSeqCDR1', 'aaSeqFR2', 'aaSeqCDR2', 'aaSeqFR3', 'aaSeqCDR3', 'aaSeqFR4']):
    df = pd.read_table(file_path) #, low_memory=False)
    if require_annotations != False: df = df.dropna(subset=require_annotations, how='any')
    df['readSequence'] = df['readSequence']
    df['readName'] = df['descrR1']
    df['allVHitsWithScore'] = df['allVHitsWithScore'].apply(parse_alignments_from_mixcr_hits)
    df['allDHitsWithScore'] = df['allDHitsWithScore'].apply(parse_alignments_from_mixcr_hits)
    df['allJHitsWithScore'] = df['allJHitsWithScore'].apply(parse_alignments_from_mixcr_hits)
    df['allCHitsWithScore'] = df['allCHitsWithScore'].apply(parse_alignments_from_mixcr_hits)
    df['v_top_hit'] = df['allVHitsWithScore'].apply(select_top_hit)
    df['v_top_hit_locus'] = df['v_top_hit'].apply(trim_ig_locus_name)
    df['d_top_hit'] = df['allDHitsWithScore'].apply(select_top_hit)
    df['d_top_hit_locus'] = df['d_top_hit'].apply(trim_ig_locus_name)
    df['j_top_hit'] = df['allJHitsWithScore'].apply(select_top_hit)
    df['j_top_hit_locus'] = df['j_top_hit'].apply(trim_ig_locus_name)
    df['c_top_hit'] = df['allCHitsWithScore'].apply(select_top_hit)
    df['c_top_hit_locus'] = df['c_top_hit'].apply(trim_ig_locus_name)
    df['allVHitsWithScore'] = df['allVHitsWithScore'].apply(json.dumps).apply(clean_null_string)
    df['allDHitsWithScore'] = df['allDHitsWithScore'].apply(json.dumps).apply(clean_null_string)
    df['allJHitsWithScore'] = df['allJHitsWithScore'].apply(json.dumps).apply(clean_null_string)
    df['allCHitsWithScore'] = df['allCHitsWithScore'].apply(json.dumps).apply(clean_null_string)
    df['v_region_shm'] = df['allVAlignments'].apply(parse_mixcr_alignment_string_to_shm)
    df['j_region_shm'] = df['allJAlignments'].apply(parse_mixcr_alignment_string_to_shm)
    # retranslate FR4 region in mixcr output. Don't love this, but its unfortunately necessary as mixcr will annotation aaSeqFR4 as something like AKEAL_SPSPQ:
    df['aaSeqFR4'] = df['nSeqFR4'].apply(translate_human_nt)
    df['nFullSeq'] = df.apply(parse_full_length_nt_seq_from_annotation_dataframe, axis=1) if len(df) >=1 else ''
    df['aaFullSeq'] = df.apply(parse_full_length_aa_seq_from_annotation_dataframe, axis=1) if len(df) >=1 else ''
    df = df[~df['aaFullSeq'].str.contains('\*|_')] if rmindels == True else df
    df = append_cterm_peptides_for_mass_spec(df) if append_ms_peptides == True  else df
    df = collapse_annotation_dataframe(df)
    df = df[clean_annotation_dataframe_columns] 
    return df 


def append_cterm_peptides_for_mass_spec(dataframe): 
    # Append tryptic C-term to full length sequences.
    appendSeq = pd.Series(data = '', index=dataframe.index)
    appendSeq[dataframe['v_top_hit'].str.startswith('IGL')] = 'GQPK'
    appendSeq[dataframe['v_top_hit'].str.startswith('IGK')] = 'R'
    appendSeq[dataframe['v_top_hit'].str.startswith('IGH')] = 'ASTK' # need to vet gene names start with IGH... 
    dataframe['aaFullSeq'] = dataframe['aaFullSeq'] + appendSeq
    return dataframe


def collapse_annotation_dataframe(df, on='aaFullSeq'):
    if len(df) == 0: return df 
    # Remove duplicates and assign read counts.
    grouped = df.groupby(on, as_index=False, sort=False)
    df_collapsed = grouped.first()
    df_collapsed['readCount'] = grouped.size().tolist()
    return df_collapsed
    

