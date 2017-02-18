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

  def kmer_counts(self, k, seq_type='nuc'):
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
      return None

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


  @classmethod
  def sum_dicts(*dicts):
      ret = defaultdict(int)
      for d in dicts:
          for k, v in d.items():
              ret[k] += v
      return dict(ret)

  @classmethod
  def combined_kmers(cls, *alleles, k=25, seq_type='nuc'):
      ret = defaultdict(int)
      for allele in alleles:
          counts = allele.kmer_counts(k, seq_type=seq_type):
          for k, v in counts.items():
              ret[k] += v
      return dict(ret)







# needed imports
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
import numpy as np



# some setting for this notebook to actually show the graphs inline, you probably won't need this
%matplotlib inline
np.set_printoptions(precision=5, suppress=True)  # suppress scientific float notation





# generate two clusters: a with 100 points, b with 50:
np.random.seed(4711)  # for repeatability of this tutorial
a = np.random.multivariate_normal([10, 0], [[3, 1], [1, 4]], size=[100,])
b = np.random.multivariate_normal([0, 20], [[3, 1], [1, 4]], size=[50,])
X = np.concatenate((a, b),)
print X.shape  # 150 samples with 2 dimensions
plt.scatter(X[:,0], X[:,1])
plt.show()




# generate the linkage matrix
Z = linkage(X, 'ward')

from scipy.cluster.hierarchy import cophenet
from scipy.spatial.distance import pdist

c, coph_dists = cophenet(Z, pdist(X))
c





idxs = [33, 68, 62]
plt.figure(figsize=(10, 8))
plt.scatter(X[:,0], X[:,1])  # plot all points
plt.scatter(X[idxs,0], X[idxs,1], c='r')  # plot interesting points in red again
plt.show()



idxs = [33, 68, 62]
plt.figure(figsize=(10, 8))
plt.scatter(X[:,0], X[:,1])
plt.scatter(X[idxs,0], X[idxs,1], c='r')
idxs = [15, 69, 41]
plt.scatter(X[idxs,0], X[idxs,1], c='y')
plt.show()




plt.title('Hierarchical Clustering Dendrogram (truncated)')
plt.xlabel('sample index or (cluster size)')
plt.ylabel('distance')
dendrogram(
    Z,
    truncate_mode='lastp',  # show only the last p merged clusters
    p=12,  # show only the last p merged clusters
    leaf_rotation=90.,
    leaf_font_size=12.,
    show_contracted=True,  # to get a distribution impression in truncated branches
)
plt.show()









def fancy_dendrogram(*args, **kwargs):
    max_d = kwargs.pop('max_d', None)
    if max_d and 'color_threshold' not in kwargs:
        kwargs['color_threshold'] = max_d
    annotate_above = kwargs.pop('annotate_above', 0)

    ddata = dendrogram(*args, **kwargs)

    if not kwargs.get('no_plot', False):
        plt.title('Hierarchical Clustering Dendrogram (truncated)')
        plt.xlabel('sample index or (cluster size)')
        plt.ylabel('distance')
        for i, d, c in zip(ddata['icoord'], ddata['dcoord'], ddata['color_list']):
            x = 0.5 * sum(i[1:3])
            y = d[1]
            if y > annotate_above:
                plt.plot(x, y, 'o', c=c)
                plt.annotate("%.3g" % y, (x, y), xytext=(0, -5),
                             textcoords='offset points',
                             va='top', ha='center')
        if max_d:
            plt.axhline(y=max_d, c='k')
    return ddata



fancy_dendrogram(
    Z,
    truncate_mode='lastp',
    p=12,
    leaf_rotation=90.,
    leaf_font_size=12.,
    show_contracted=True,
    annotate_above=10,  # useful in small plots so annotations don't overlap
)
plt.show()












# set cut-off to 50
max_d = 50  # max_d as in max_distance












Z2 = linkage(X2, 'ward')
plt.figure(figsize=(10,10))
fancy_dendrogram(
    Z2,
    truncate_mode='lastp',
    p=30,
    leaf_rotation=90.,
    leaf_font_size=12.,
    show_contracted=True,
    annotate_above=40,
    max_d=170,
)
plt.show()







from Bio import Entrez
Entrez.email = "russdurrett@utexas.edu"



records = Entrez.read(Entrez.esearch(db="gene", retmax=100, term='("Homo sapiens"[Organism]) AND ("IgG receptor"[All Fields] OR "IgA receptor"[All Fields] OR "IgD receptor"[All Fields] or "IgM receptor"[All Fields] OR "IgD receptor"[All Fields]) AND alive[prop] '))
ids = records['IdList']

for i in ids: 
  handle = Entrez.efetch(db="gene", id=i, rettype="gb", retmode="text")
  print handle.readline() 

print records 
print ''
print 'records: '.format(len(records))
for i, record in enumerate(records):
  print 'Record {}: {}'.format(i, records[record])


handle.close()






