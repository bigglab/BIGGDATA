import os, sys
# import pandas as pd
# import numpy as np

#sys.path.append('/data/resources/software/BIGGDATA')
#from utils.standardization import *


mixcr_output_presets = "/data/resources/software/BIGGDATA/utils/mixcr_output_presets.txt"



#set the number of threads to use for alignment and feature counting
THREADS=6

try:
  config['d']
except KeyError:
  print('error, d argument is null, please define the target directory containing your reads')
else:
  d = config['d']

files = os.listdir(d)

read1 = [f for f in files if 'R1' in f and '001.fastq' in f][0]
read2 = [f for f in files if 'R2' in f and '001.fastq' in f][0]

print('read one: {}'.format(read1))
print('read two: {}'.format(read2))

sample = read1.split('/')[-1].split('.')[0].split('_')[0]

print('sample name: {}'.format(sample))

print('moving to working directory: {}'.format(d))
os.chdir(d)


rule all:
    input: "{}.mixcr.txt".format(sample)


# does not currently work with python3, required for snakemake
#rule standardize_output:
# output: "{sample}.bigg.txt"
# input: "{sample}.mixcr.txt"
# message: "standardizing {wildcards.sample}"
# run:
#   df = build_annotation_dataframe_from_mixcr_file(input[0], require_annotations=['aaSeqCDR1', 'aaSeqCDR2', 'aaSeqCDR3', 'aaSeqFR4'])
#   df.to_csv(output[0], sep='\t', index=False)


rule mixcr_export:
  output: "{sample}.mixcr.txt"
  input: "{sample}.mixcr", mixcr_output_presets
  message: "exporting mixcr alignments to text file for sample {wildcards.sample}"
  shell: "/data/resources/software/mixcr-2.0.2/mixcr exportAlignments -s --preset-file {mixcr_output_presets}  {input[0]} {output}"


rule mixcr_alignment:
  output: "{sample}.mixcr"
  input: "{sample}.filtered.fastq"
  threads: THREADS
  message: "running mixcr on sample {wildcards.sample}"
  shell: "/data/resources/software/mixcr-2.0.2/mixcr align -t {threads} -OjParameters.parameters.mapperMaxSeedsDistance=5 --chains IGH,IGL,IGK --species hsa --save-description -f {input} {output}"


# QUALITY FILTER READS

rule quality_filter:
  output: "{sample}.filtered.fastq"
  input: "{sample}.merged.fastq"
  log: "log/{wildcards.sample}.filter.log"
  message: "running filtering on {wildcards.sample} with {threads} threads, {input} to {output}"
  shell: " fastq_quality_filter -q 20 -p 50 -i {input} -o {output} -Q 33 "


# MERGE OVERLAPPING READS
#rule pandaseq:
#  output: "{sample}.merged.fastq"
#  input: expand("{{sample}}_R{num}.fastq", num=['1','2'])
#  log: "log/{}.pandaseq.log".format(sample)
#  threads: THREADS
#  message: "running pandaseq on sample {}".format(sample)
#  shell: "pandaseq -f {input[0]} -r {input[1]} -F -T {threads} -A ea_util -w {output} -l 100 -o 10 2> {log}"


rule usearch_mergefastq:
    output: "{sample}.merged.fastq"
    input: expand("{{sample}}_R{num}.fastq", num=['1','2'])
    log: "log/{}.usearch_mergefastq.log".format(sample)
    threads: THREADS
    message: "running usearch mergefastq on sample {}".format(sample)
    shell: "/stor/work/Georgiou/BIGGDATA/data/resources/software/usearch  -fastq_mergepairs {input[0]} -reverse {input[1]} -fastqout {output} 2> {log}"



# Trim Illumina Adapters: pandaseq currently fails when presented unpaired reads....
#rule trim:
#    output: "{read}.trimmed.fastq"
#    input: "{read}.fastq"
#    log: "log/{}.trimmamatic.log".format(sample)
#    shell: "java -jar /data/resources/software/Trimmomatic-0.35/trimmomatic-0.35.jar SE -phred33 -threads 4 {input} {output} ILLUMINACLIP:/data/resources/software/Trimmomatic-0.35/adapters/TruSeq3-SE.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:50"


# PREPARE READS:

read1_els = read1.split('/')[-1].split('.')[0].split('_')
sample = read1_els[0]
ilmn_sample = read1_els[1]
ilmn_lane = read1_els[2]
read_num = read1_els[3]
fastq_num = read1_els[4]


rule rename_fastq1:
    output: "{}_R{}.fastq".format(sample, '1')
    input: "{}_{}_{}_R{}_{}.fastq".format(sample, ilmn_sample, ilmn_lane, '1', fastq_num)
    log: "copying {wildcards.input} to {wildcards.output}"
    shell: "cp {input} {output}"


rule rename_fastq2:
    output: "{}_R{}.fastq".format(sample, '2')
    input: "{}_{}_{}_R{}_{}.fastq".format(sample, ilmn_sample, ilmn_lane, '2', fastq_num)
    log: "copying {wildcards.input} to {wildcards.output}"
    shell: "cp {input} {output}"


rule gunzip:
    output: "{anything}.fastq"
    input: "{anything}.fastq.gz"
    message: "gunzipping {input} to {output}"
    shell: "gunzip -c {input} > {output}"

