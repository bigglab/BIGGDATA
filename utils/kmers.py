import os, sys 
import pandas as pd 
import numpy as np 
import random 
from collections import OrderedDict, defaultdict
import json 
import tempfile
import subprocess
import shlex

from models import *

from app import db



def sum_dicts(*dicts):
    ret = defaultdict(int)
    if type(dicts[0])==list:
        dicts = dicts[0]
    for d in dicts:
        for k, v in d.items():
            ret[k] += v
    return dict(ret)




class Kmer:
    id = int
    sequence = str
    length = int


class KmerCount:
    kmer_id = int
    allele_id = int
    value = int





# def run_test():
locus = db.session.query(Locus).filter(Locus.name=='A').first()
print locus
genes = locus.genes.all()
gene = genes[0]
print gene
# alleles = genes[0].alleles.all()
# print 'alleles: {}'.format(len(alleles))
# a = alleles[0]
# print a.kmer_counts(25, seq_type='nuc')


alleles = locus.alleles.all()
print 'alleles: {}'.format(len(alleles))

k_dicts = map(lambda a: a.kmer_counts(75, seq_type='nuc'), alleles)

combined_kmers = sum_dicts(k_dicts)
for k in sorted(combined_kmers, key=combined_kmers.get, reverse=True)[0:100]:
    print k, combined_kmers[k]




















#
#
#
# # needed imports
# from matplotlib import pyplot as plt
# from scipy.cluster.hierarchy import dendrogram, linkage
# import numpy as np
#
#
#
# # some setting for this notebook to actually show the graphs inline, you probably won't need this
# %matplotlib inline
# np.set_printoptions(precision=5, suppress=True)  # suppress scientific float notation
#
#
#
#
#
# # generate two clusters: a with 100 points, b with 50:
# np.random.seed(4711)  # for repeatability of this tutorial
# a = np.random.multivariate_normal([10, 0], [[3, 1], [1, 4]], size=[100,])
# b = np.random.multivariate_normal([0, 20], [[3, 1], [1, 4]], size=[50,])
# X = np.concatenate((a, b),)
# print X.shape  # 150 samples with 2 dimensions
# plt.scatter(X[:,0], X[:,1])
# plt.show()
#
#
#
#
# # generate the linkage matrix
# Z = linkage(X, 'ward')
#
# from scipy.cluster.hierarchy import cophenet
# from scipy.spatial.distance import pdist
#
# c, coph_dists = cophenet(Z, pdist(X))
# c
#
#
#
#
#
# idxs = [33, 68, 62]
# plt.figure(figsize=(10, 8))
# plt.scatter(X[:,0], X[:,1])  # plot all points
# plt.scatter(X[idxs,0], X[idxs,1], c='r')  # plot interesting points in red again
# plt.show()
#
#
#
# idxs = [33, 68, 62]
# plt.figure(figsize=(10, 8))
# plt.scatter(X[:,0], X[:,1])
# plt.scatter(X[idxs,0], X[idxs,1], c='r')
# idxs = [15, 69, 41]
# plt.scatter(X[idxs,0], X[idxs,1], c='y')
# plt.show()
#
#
#
#
# plt.title('Hierarchical Clustering Dendrogram (truncated)')
# plt.xlabel('sample index or (cluster size)')
# plt.ylabel('distance')
# dendrogram(
#     Z,
#     truncate_mode='lastp',  # show only the last p merged clusters
#     p=12,  # show only the last p merged clusters
#     leaf_rotation=90.,
#     leaf_font_size=12.,
#     show_contracted=True,  # to get a distribution impression in truncated branches
# )
# plt.show()
#
#
#
#
#
#
#
#
#
# def fancy_dendrogram(*args, **kwargs):
#     max_d = kwargs.pop('max_d', None)
#     if max_d and 'color_threshold' not in kwargs:
#         kwargs['color_threshold'] = max_d
#     annotate_above = kwargs.pop('annotate_above', 0)
#
#     ddata = dendrogram(*args, **kwargs)
#
#     if not kwargs.get('no_plot', False):
#         plt.title('Hierarchical Clustering Dendrogram (truncated)')
#         plt.xlabel('sample index or (cluster size)')
#         plt.ylabel('distance')
#         for i, d, c in zip(ddata['icoord'], ddata['dcoord'], ddata['color_list']):
#             x = 0.5 * sum(i[1:3])
#             y = d[1]
#             if y > annotate_above:
#                 plt.plot(x, y, 'o', c=c)
#                 plt.annotate("%.3g" % y, (x, y), xytext=(0, -5),
#                              textcoords='offset points',
#                              va='top', ha='center')
#         if max_d:
#             plt.axhline(y=max_d, c='k')
#     return ddata
#
#
#
# fancy_dendrogram(
#     Z,
#     truncate_mode='lastp',
#     p=12,
#     leaf_rotation=90.,
#     leaf_font_size=12.,
#     show_contracted=True,
#     annotate_above=10,  # useful in small plots so annotations don't overlap
# )
# plt.show()
#
#
#
#
#
#
#
#
#
#
#
#
# # set cut-off to 50
# max_d = 50  # max_d as in max_distance
#
#
#
#
#
#
#
#
#
#
#
#
# Z2 = linkage(X2, 'ward')
# plt.figure(figsize=(10,10))
# fancy_dendrogram(
#     Z2,
#     truncate_mode='lastp',
#     p=30,
#     leaf_rotation=90.,
#     leaf_font_size=12.,
#     show_contracted=True,
#     annotate_above=40,
#     max_d=170,
# )
# plt.show()
#
#
#
#
#
#
#
# from Bio import Entrez
# Entrez.email = "russdurrett@utexas.edu"
#
#
#
# records = Entrez.read(Entrez.esearch(db="gene", retmax=100, term='("Homo sapiens"[Organism]) AND ("IgG receptor"[All Fields] OR "IgA receptor"[All Fields] OR "IgD receptor"[All Fields] or "IgM receptor"[All Fields] OR "IgD receptor"[All Fields]) AND alive[prop] '))
# ids = records['IdList']
#
# for i in ids:
#   handle = Entrez.efetch(db="gene", id=i, rettype="gb", retmode="text")
#   print handle.readline()
#
# print records
# print ''
# print 'records: '.format(len(records))
# for i, record in enumerate(records):
#   print 'Record {}: {}'.format(i, records[record])
#
#
# handle.close()
#





