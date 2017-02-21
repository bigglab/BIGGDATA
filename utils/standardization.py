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
 'collapsedCount',
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


# igfft_dtypes = {"Header": str,
# "SEQ_ID": str,
# "Sequence": str,
# "Quality_Score": str,
# "Document_Header": str,
# "Strand_Corrected_Sequence": str,
# "Notes": str,
# "Errors": str,
# "Command": str,
# "Recombination_Type": str,
# "Percent_Identity": np.float64,
# "Alignment_Length": np.float64,
# "Direction": str,
# "Locus": str,
# "Chain": str,
# "Codon_Start": str,
# "Query_Start": str,
# "Query_End": str,
# "Codon_Frame": str,
# "5_Prime_Annotation": str,
# "3_Prime_Annotation": str,
# "Stop_Codon": bool,
# "CDR3_Junction_In_Frame": bool,
# "Full_Length": bool,
# "Productive": str,
# "Full_Length_Sequence.NT": str,
# "Full_Length_Sequence.AA": str,
# "Top_V-Gene_Hits": str,
# "V-Gene_Alignment_Scores": str,
# "Top_J-Gene_Hits": str,
# "J-Gene_Alignment_Scores": str,
# "FR1_Sequence.NT": str,
# "CDR1_Sequence.NT": str,
# "FR2_Sequence.NT": str,
# "CDR2_Sequence.NT": str,
# "FR3_Sequence.NT": str,
# "CDR3_Sequence.NT": str,
# "FR4_Sequence.NT": str,
# "FR1_Sequence.AA": str,
# "CDR1_Sequence.AA": str,
# "FR2_Sequence.AA": str,
# "CDR2_Sequence.AA": str,
# "FR3_Sequence.AA": str,
# "CDR3_Sequence.AA": str,
# "FR4_Sequence.AA": str,
# "FR1_Sequence.NT.Gapped": str,
# "CDR1_Sequence.NT.Gapped": str,
# "FR2_Sequence.NT.Gapped": str,
# "CDR2_Sequence.NT.Gapped": str,
# "FR3_Sequence.NT.Gapped": str,
# "FR1_Sequence.AA.Gapped": str,
# "CDR1_Sequence.AA.Gapped": str,
# "FR2_Sequence.AA.Gapped": str,
# "CDR2_Sequence.AA.Gapped": str,
# "FR3_Sequence.AA.Gapped": str,
# "VRegion.SHM.NT": np.float64,
# "VRegion.SHM.Per_nt": np.float64,
# "Reading_Frames: FR1,CDR1,FR2,CDR2,FR3,CDR3,FR4": str,
# "VGENE: Total_Matches": np.float64,
# "VGENE: Total_Mismatches": np.float64,
# "VGENE: Total_Indel": np.float64,
# "JRegion.SHM.NT": np.float64,
# "JRegion.SHM.Per_nt": np.float64,
# "JGENE: Total_Matches": np.float64,
# "JGENE: Total_Mismatches": np.float64,
# "JGENE: Total_Indel": np.float64,
# "VGENE_Matches: FR1,CDR1,FR2,CDR2,FR3,CDR3": str,
# "VGENE_Mismatches: FR1,CDR1,FR2,CDR2,FR3,CDR3": str,
# "VGENE_Indels: FR1,CDR1,FR2,CDR2,FR3,CDR3": str,
# "VGENE: Query_Start": str,
# "VGENE: Query_End": str,
# "VGENE: Query_FR1_Start::End": str,
# "VGENE: Query_CDR1_Start::End": str,
# "VGENE: Query_FR2_Start::End": str,
# "VGENE: Query_CDR2_Start::End": str,
# "VGENE: Query_FR3_Start::End": str,
# "VGENE: Germline_Start": str,
# "VGENE: Germline_End": str,
# "JGENE: Query_Start": str,
# "JGENE: Query_End": str,
# "JGENE: Germline_Start": str,
# "JGENE: Germline_End": str,
# "VGENE: Alignment_Sequence_Query": str,
# "VGENE: Alignment_Sequence_Germline": str,
# "VGENE: Alignment_FR1_Start::End": str,
# "VGENE: Alignment_CDR1_Start::End": str,
# "VGENE: Alignment_FR2_Start::End": str,
# "VGENE: Alignment_CDR2_Start::End": str,
# "VGENE: Alignment_FR3_Start::End": str,
# "JGENE: Alignment_Sequence_Query": str,
# "JGENE: Alignment_Sequence_Germline": str,
# "Isotype": str,
# "Isotype mismatches": str,
# "Isotype percent similarity": str,
# "Isotype barcode direction": str}
#

igfft_dtypes = {
 'Alignment_Length': np.float64,
 'CDR1_Sequence.AA': str,
 'CDR1_Sequence.NT': str,
 'CDR2_Sequence.AA': str,
 'CDR2_Sequence.NT': str,
 'CDR3_Sequence.AA': str,
 'CDR3_Sequence.NT': str,
 'Chain': str,
 'Direction': str,
 'FR1_Sequence.AA': str,
 'FR1_Sequence.NT': str,
 'FR2_Sequence.AA': str,
 'FR2_Sequence.NT': str,
 'FR3_Sequence.AA': str,
 'FR3_Sequence.NT': str,
 'FR4_Sequence.AA': str,
 'FR4_Sequence.NT': str,
 'Full_Length': bool,
 'Full_Length_Sequence.AA': str,
 'Full_Length_Sequence.NT': str,
 'Header': str,
 'Isotype': str,
 'Isotype percent similarity': str,
 'J-Gene_Alignment_Scores': str,
 'JGENE: Total_Indel': np.float64,
 'JGENE: Total_Matches': np.float64,
 'JGENE: Total_Mismatches': np.float64,
 'JRegion.SHM.NT': np.float64,
 'JRegion.SHM.Per_nt': np.float64,
 'Locus': str,
 'Percent_Identity': np.float64,
 'Productive': str,
 'Quality_Score': str,
 'Recombination_Type': str,
 'Sequence': str,
 'Top_J-Gene_Hits': str,
 'Top_V-Gene_Hits': str,
 'V-Gene_Alignment_Scores': str,
 'VGENE: Total_Indel': np.float64,
 'VGENE: Total_Matches': np.float64,
 'VGENE: Total_Mismatches': np.float64,
 'VRegion.SHM.NT': np.float64,
 'VRegion.SHM.Per_nt': np.float64
}



def build_annotation_dataframe_from_igfft_file(file_path, rmindels=True, append_ms_peptides=False, require_annotations=['aaSeqFR1', 'aaSeqCDR1', 'aaSeqFR2', 'aaSeqCDR2', 'aaSeqFR3', 'aaSeqCDR3', 'aaSeqFR4']):
    print "Parsing {} to standardized BIGG format".format(file_path)
    df = pd.read_table(file_path, dtype=igfft_dtypes, error_bad_lines=False,  usecols=igfft_dtypes.keys(),) # nrows=100) #, low_memory=False)
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
    }
    df = df.rename(str, columns=column_reindex)
    full_length = len(df)
    print '{}: {} annotations total'.format(file_path, full_length)
    df = df.dropna(subset=['Top_V-Gene_Hits', 'Top_J-Gene_Hits'], how='any')
    if require_annotations != False:
        df = df.dropna(subset=require_annotations, how='any')
    print "{}: {} annotations pass require_annotations {} and V-Hit and J-Hit filter".format(file_path, len(df), require_annotations)
    if len(df)==0:
        print '{}: returning empty dataframe'.format(file_path)
        return pd.DataFrame(columns=clean_annotation_dataframe_columns)
    # these routines take too long! chunk to provide updates
    chunk_size = 10000
    df_input = df
    df_output = pd.DataFrame(columns=df_input.columns)
    print "{}: working on {} annotations in {} chunks".format(file_path, len(df_input), len(df_input)/chunk_size+1)
    for k, df in df.groupby(np.arange(len(df)) // 10000):
        print "{} annotations parsed, {}% done".format(k*chunk_size, round(k*chunk_size/float(full_length)*100, 2))
        df = df.copy()
        df['c_top_hit'] = df.apply(split_on_comma_and_take_first, col='Isotype', axis=1)
        df['c_top_hit_locus'] = df['c_top_hit']
        df['cBestIdentityPercent'] = df.apply(split_on_comma_and_take_first_float, col='Isotype percent similarity', axis=1)
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
        df_output = pd.concat([df_output, df])
    df_output = collapse_annotation_dataframe(df_output)
    df_output = df_output[clean_annotation_dataframe_columns]
    return df_output

def split_on_comma_and_take_first(row, col='Isotype'): 
  return str(row[col]).split(',')[0]

def split_on_comma_and_take_first_float(row, col='Isotype percent similarity'): 
  return float(split_on_comma_and_take_first(row, col=col))


mixcr_dtypes = {"descrR1" : str, 
"readSequence" : str, 
"allVHitsWithScore" : str, 
"allDHitsWithScore" : str, 
"allJHitsWithScore" : str, 
"allCHitsWithScore" : str, 
"allVAlignments" : str, 
"allDAlignments" : str, 
"allJAlignments" : str, 
"allCAlignments" : str, 
"nSeqFR1" : str, 
"nSeqCDR1" : str, 
"nSeqFR2" : str, 
"nSeqCDR2" : str, 
"nSeqFR3" : str, 
"nSeqCDR3" : str, 
"nSeqFR4" : str, 
"qualFR1" : str, 
"qualCDR1" : str, 
"qualFR2" : str, 
"qualCDR2" : str, 
"qualFR3" : str, 
"qualCDR3" : str, 
"qualFR4" : str, 
"aaSeqFR1" : str, 
"aaSeqCDR1" : str, 
"aaSeqFR2" : str, 
"aaSeqCDR2" : str, 
"aaSeqFR3" : str, 
"aaSeqCDR3" : str, 
"aaSeqFR4" : str, 
"vBestIdentityPercent": np.float64,
"dBestIdentityPercent": np.float64,
"jBestIdentityPercent": np.float64,
"cBestIdentityPercent": np.float64}


def build_annotation_dataframe_from_mixcr_file(file_path, rmindels=True, append_ms_peptides=False, require_annotations=['aaSeqFR1', 'aaSeqCDR1', 'aaSeqFR2', 'aaSeqCDR2', 'aaSeqFR3', 'aaSeqCDR3', 'aaSeqFR4']):
    print "Parsing {} to standardized BIGG format".format(file_path)
    df = pd.read_table(file_path, dtype=mixcr_dtypes, error_bad_lines=False)  # , low_memory=False)
    full_length = len(df)
    print '{}: {} annotations total'.format(file_path, full_length)
    if require_annotations != False:
        df = df.dropna(subset=require_annotations, how='any')
        print "{}: {} annotations pass require_annotations {}".format(file_path, len(df), require_annotations)
    if len(df)==0:
        print '{}: returning empty dataframe'.format(file_path)
        return pd.DataFrame(columns=clean_annotation_dataframe_columns)
    # these routines take too long! chunk to provide updates
    chunk_size = 10000
    df_input = df
    df_output = pd.DataFrame(columns=df_input.columns)
    print "{}: working on {} annotations in {} chunks".format(file_path, len(df_input), len(df_input)/chunk_size+1)
    for k, df in df.groupby(np.arange(len(df)) // 10000):
        print "{} annotations parsed, {}% done".format(k*chunk_size, round(k*chunk_size/float(full_length)*100, 2))
        df = df.copy()
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
        df_output = pd.concat([df_output, df])
    df_output = collapse_annotation_dataframe(df_output)
    df_output = df_output[clean_annotation_dataframe_columns]
    return df_output


def append_cterm_peptides_for_mass_spec(dataframe): 
    # Append tryptic C-term to full length sequences.
    appendSeq = pd.Series(data = '', index=dataframe.index)
    appendSeq[dataframe['v_top_hit'].str.startswith('IGL')] = 'GQPK'
    appendSeq[dataframe['v_top_hit'].str.startswith('IGK')] = 'R'
    appendSeq[dataframe['v_top_hit'].str.startswith('IGH')] = 'ASTK' # need to vet gene names start with IGH... 
    dataframe['aaFullSeq'] = dataframe['aaFullSeq'] + appendSeq
    return dataframe


def collapse_annotation_dataframe(df, on='aaFullSeq'):
    if len(df) == 0: return df.reindex(columns = df.columns.tolist() + ['collapsedCount'])
    # Remove duplicates and assign read counts.
    grouped = df.groupby(on, as_index=False, sort=False)
    df_collapsed = grouped.first()
    df_collapsed['collapsedCount'] = grouped.size().tolist()
    return df_collapsed
    


annotation_dataframe_dtypes = {
    "readName": str, 
    "collapsedCount": int, 
    "readSequence": str, 
    "v_top_hit": str, 
    "v_top_hit_locus": str, 
    "d_top_hit": str, 
    "d_top_hit_locus": str, 
    "j_top_hit": str, 
    "j_top_hit_locus": str, 
    "c_top_hit": str, 
    "c_top_hit_locus": str, 
    "nFullSeq": str, 
    "aaFullSeq": str, 
    "nSeqFR1": str, 
    "nSeqCDR1": str, 
    "nSeqFR2": str, 
    "nSeqCDR2": str, 
    "nSeqFR3": str, 
    "nSeqCDR3": str, 
    "nSeqFR4": str, 
    "qualFR1": str, 
    "qualCDR1": str, 
    "qualFR2": str, 
    "qualCDR2": str, 
    "qualFR3": str, 
    "qualCDR3": str, 
    "qualFR4": str, 
    "aaSeqFR1": str, 
    "aaSeqCDR1": str, 
    "aaSeqFR2": str, 
    "aaSeqCDR2": str, 
    "aaSeqFR3": str, 
    "aaSeqCDR3": str, 
    "aaSeqFR4": str, 
    "v_region_shm": np.float64, 
    "j_region_shm": np.float64}



def read_annotation_file(file_path): 
  if 'bigg' in file_path.lower(): 
    df = pd.read_table(file_path, dtype=annotation_dataframe_dtypes)
    df['readName'] = df['readName'].apply(lambda n: n.split(' ')[0])
    return df
  elif 'mixcr' in file_path.lower(): 
    df = build_annotation_dataframe_from_mixcr_file(file_path, rmindels=True, append_ms_peptides=False, require_annotations=['aaSeqCDR3'])
    return df 
  elif 'igfft' in file_path.lower():
    df = build_annotation_dataframe_from_igfft_file(file_path, rmindels=True, append_ms_peptides=False, require_annotations=['aaSeqCDR3'])
    return df 
  else: 
    df = pd.read_table(file_path)
    return df 




