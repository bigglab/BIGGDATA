import os, sys
import pandas as pd 
import numpy as np 

sys.path.append('/data/resources/software/BIGGDATA')
from utils.standardization import *



#set the number of threads to use for alignment and feature counting 
THREADS=6

try: 
  config['READ_ONE']
except KeyError: 
  print('key error on read1...')
else: 
  read1 = config['READ_ONE']


try: 
  config['READ_TWO']
except KeyError: 
  print('key error on read2...')
else: 
  read2 = config['READ_TWO']



print('read one: {}'.format(read1))
print('read two: {}'.format(read2))


sample = read1.split('/')[-1].split('.')[0].replace('_R1', '').replace('_R2', '')

print('sample name: {}'.format(sample))

if '.fastq.gz' in read1: 
  ext = '.fastq.gz'
else: 
  ext = '.fastq'

rule all: 
  input: "{}.bigg.txt".format(read1.replace('_R1', '').replace('_R2', '').replace('.fastq.gz', '').replace('.fastq', ''))
 # input: "{}.bigg.txt".format(sample)


# run standardize_output: 
#   output: "{sample}.bigg.txt"
#   input 


mixcr_output_presets = "/data/resources/software/BIGGDATA/mixcr_output_presets.txt"
# mixcr_output_presets = "mixcr_output_presets.txt"



rule standardize_output: 
  output: "{sample}.bigg.txt"
  input: "{sample}.mixcr.txt"
  message: "standardizing {wildcards.sample}"
  run: 
    df = build_annotation_dataframe_from_mixcr_file(input[0]) 
    df.to_csv(output[0], sep='\t', index=False)


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



rule quality_filter: 
  output: "{sample}.filtered.fastq"
  input: "{sample}.merged.fastq"
  log: "log/{wildcards.sample}.filter.log"
  message: "running filtering on {wildcards.sample} with {threads} threads, {input} to {output}"
  shell: " fastq_quality_filter -q 20 -p 50 -i {input} -o {output} -Q 33 "


rule pandaseq: 
  output: "{sample}.merged.fastq"
  input: expand("{{sample}}_R{num}{ext}", ext=[ext], num=['1','2'])
  log: "log/{}.pandaseq.log".format(sample)
  threads: THREADS
  message: "running pandaseq on sample {}".format(sample)
  shell: "pandaseq -f {input[0]} -r {input[1]} -F -T {threads} -A ea_util -w {output} -l 100 -o 10 2> {log}"





