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

# if '.fastq.gz' in read1:
#   ext = '.fastq.gz'
# else:
#   ext = '.fastq'

rule all:
#  input: "{}.mixcr.txt".format(read1.replace('_R1_001', '').replace('_R2_001', '').replace('.fastq.gz', '').replace('.fastq', ''))
#  # input: "{}.bigg.txt".format(read1.replace('_R1', '').replace('_R2', '').replace('.fastq.gz', '').replace('.fastq', ''))
    input: "{}.bigg.txt".format(sample)



rule standardize_output:
 output: "{sample}.bigg.txt"
 input: "{sample}.mixcr.txt"
 message: "standardizing {wildcards.sample}"
 run:
   df = build_annotation_dataframe_from_mixcr_file(input[0], require_annotations=['aaSeqCDR1', 'aaSeqCDR2', 'aaSeqCDR3', 'aaSeqFR4'])
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
  input: expand("{{sample}}_R{num}_001.fastq", num=['1','2'])
  log: "log/{}.pandaseq.log".format(sample)
  threads: THREADS
  message: "running pandaseq on sample {}".format(sample)
  shell: "pandaseq -f {input[0]} -r {input[1]} -F -T {threads} -A ea_util -w {output} -l 100 -o 10 2> {log}"


rule gunzip:
    output: "{anything}.fastq"
    input: "{anything}.fastq.gz"
    message: "gunzipping {input} to {output}"
    shell: "gunzip -c {input} > {output}"



