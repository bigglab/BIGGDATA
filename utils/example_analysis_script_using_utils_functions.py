import sys
sys.path.append('/data/resources/software/BIGGDATA')
import utils.clustering as clustering
import utils.standardization as standardization


# read in data. can parse bigg, mixcr, or igfft files, but 'bigg', 'mixcr', or 'igfft' must be in filename
# will also collapse identical read sequences to imcrease efficiency downstream
df = standardization.read_annotation_file('my_annotation_file.mixcr.txt')

# cluster dataframe on whatever field you want (CDR3 etc). Can use 'greedy', 'agglomerative', or 'D Clonotyping' methods to cluster
clustered_df = clustering.cluster_dataframe(df, how='greedy', on='aaSeqCDR3', identiy=0.94)

# write dataframe to file
clustered_df.to_csv('my_clustered_file.txt', index=False)


# voila
