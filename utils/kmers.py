import os, sys 
import pandas as pd 
import numpy as np 
import random 
from collections import OrderedDict, defaultdict
import json 
import tempfile
import subprocess
import shlex

import models

class AlleleKmer(models.Allele):

  def count_kmers(self, k, seq_type='nuc'):
    #Count kmer occurrences in a given allele.
      #Returns:  counts : dictionary, {'string': int}
    if seq_type=='nuc': 
      seq = self.sequence_nuc 
    elif seq_type=='gene': 
      seq = self.sequence_gene
    elif seq_type=='prot':
      seq = self.sequence_prot
    else: 
      seq = self.sequence
    if 'seq' not in locals(): 
      return False 

    print seq 
    read = seq
    counts = {}
    num_kmers = len(read) - k + 1
    for i in range(num_kmers):
        kmer = read[i:i+k]
        if kmer not in counts:
            counts[kmer] = 0
        counts[kmer] += 1
    return counts


def sum_dicts(*dicts):
    ret = defaultdict(int)
    for d in dicts:
        for k, v in d.items():
            ret[k] += v
    return dict(ret)




