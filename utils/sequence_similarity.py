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




#
# # def run_test():
# locus = db.session.query(Locus).filter(Locus.name=='A').first()
# print locus
# genes = locus.genes.all()
# gene = genes[0]
# print gene
# # alleles = genes[0].alleles.all()
# # print 'alleles: {}'.format(len(alleles))
# # a = alleles[0]
# # print a.kmer_counts(25, seq_type='nuc')
#
#
# alleles = locus.alleles.all()
# print 'alleles: {}'.format(len(alleles))
#
# k_dicts = map(lambda a: a.kmer_counts(75, seq_type='nuc'), alleles)
#
# combined_kmers = sum_dicts(k_dicts)
# for k in sorted(combined_kmers, key=combined_kmers.get, reverse=True)[0:100]:
#     print k, combined_kmers[k]






from scipy.cluster.hierarchy import dendrogram, linkage
import numpy as np

#
#
# import distance
#
# print distance.levenshtein("lenvestein", "levenshtein")
# print distance.hamming("hamming", "hamning")

#
# # locus 29, IGKL
# locus = db.session.query(Locus).get(29)
# alleles = locus.alleles.all()
# print '{} alleles'.format(len(alleles))

# for seq in map(lambda a: a.sequence, alleles):
#     print seq


import jellyfish
import editdistance

def allele_similarity(alleles, method=jellyfish.hamming_distance):
    if type(method)==str:
        if method=='hamming':
            method = jellyfish.hamming_distance
        elif method=='levenshtein':
            # method = jellyfish.levenshtein_distance
            method = editdistance.eval # 4x faster
        elif method=='damerau_levenshtien':
            method = jellyfish.damerau_levenshtein_distance
        elif method=='jaro':
            method = jellyfish.jaro_distance
    else:
            method = method
    assert method(unicode('A'),unicode('B'))==1, 'allele_similarity method does not support method(str1,str2) call'

    result = pd.DataFrame()
    for x in alleles:
        for y in alleles:
            r = method(unicode(x.sequence), unicode(y.sequence))
            result.set_value(x.name, y.name, r)

    # print result
    print "generated allele distance table with method: {}".format(str(method))
    print "shape: {}".format(result.shape)
    return result



from scipy.cluster.hierarchy import cophenet
from scipy.spatial.distance import pdist

def allele_dendrogram(allele_similarity, linkage_method='ward', title='Hierarchical Clustering Dendrogram'):
    X = allele_similarity
    Z = linkage(X, linkage_method)
    # test correlation between linkage and distance
    c, coph_dists = cophenet(Z, pdist(X))



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


    def allele_dendrogram_call(*args, **kwargs):
        max_d = kwargs.pop('max_d', None)
        if max_d and 'color_threshold' not in kwargs:
            kwargs['color_threshold'] = max_d
        annotate_above = kwargs.pop('annotate_above', 0)

        ddata = dendrogram(*args, **kwargs)

        if not kwargs.get('no_plot', False):
            plt.title(title)
            plt.xlabel('distance')
            plt.ylabel('allele or (cluster size)')
            for i, d, c in zip(ddata['icoord'], ddata['dcoord'], ddata['color_list']):
                if not kwargs.get('orientation', 'left'):
                    x = 0.5 * sum(i[1:3])
                    y = d[1]
                    if y > annotate_above:
                        plt.plot(x, y, 'o', c=c)
                        plt.annotate("%.3g" % y, (x, y), xytext=(0, -5),
                                     textcoords='offset points',
                                     va='top', ha='center')
                    if max_d:
                        plt.axhline(y=max_d, c='k')
                else:
                    y = 0.5 * sum(i[1:3])
                    x = d[1]
                    if x > annotate_above:
                        plt.plot(x, y, 'o', c=c)
                        plt.annotate("%.3g" % x, (x, y), xytext=(0, -5),
                                     textcoords='offset points',
                                     va='top', ha='center')

                    if max_d:
                        plt.axvline(x=max_d, c='k')
        return ddata



    plt.figure(figsize=(10,10))
    allele_dendrogram_call(
        Z,
        truncate_mode='lastp',
        p=30,
        orientation='left',
        leaf_rotation=0.,
        leaf_font_size=12.,
        show_contracted=True,
        annotate_above=50,
        max_d=50,
        labels=X.index
    )
    plt.show()


    return True












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





