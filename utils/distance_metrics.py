from collections import OrderedDict
import pandas as pd 
import numpy as np
import random 


#This is a collection of metrics to determine similarity of IG/TCR Repertoires 
#they can be used without counts


# Jaccard Similarity - species in common / total species. Can weigh by counts if counts column is given
def jaccard_df_similarity(df1, df2, keys=['CDRH3 AA'], downsample=None, counts=None): 
	dfx = downsample_df(df1, downsample)
	dfy = downsample_df(df2, downsample)
	if counts==None: # calculate sizes from numbers of rows instead of counts column - 1 each for pre-clustered data
		x = dfx.groupby(keys).size()
		y = dfy.groupby(keys).size()
	else: # calculate sizes from sums of counts per species 
		x = dfx.groupby(keys)[counts].sum()
		y = dfy.groupby(keys)[counts].sum()
	z = x.to_frame().join(y.to_frame(), rsuffix='x', how='outer')
	z.columns = ['x', 'y']
	# union = sum of all species seen in both repertoires 
	union = z.dropna(how='any').sum().sum()
	# intersection is sum of all species in both repertoires 
	intersection = z.sum().sum()
	return float(union) / intersection 



def braycurtis_df_similarity(df1, df2, keys=['CDRH3 AA'], downsample=None, counts=None): 
	dfx = downsample_df(df1, downsample)
	dfy = downsample_df(df2, downsample)
	if counts==None: # calculate sizes from numbers of rows instead of counts column 
		x = dfx.groupby(keys).size()
		y = dfy.groupby(keys).size()
	else: 
		x = dfx.groupby(keys)[counts].sum()
		y = dfy.groupby(keys)[counts].sum()
	z = x.to_frame().join(y.to_frame(), rsuffix='x', how='outer').fillna(0)
	r = float(z.min(axis=1).sum()*2)/z.sum().sum()
	return r


def czekanowski_df_dissimilarity(df1, df2, keys=['CDRH3 AA'], downsample=None, counts=None): 
	dfx = downsample_df(df1, downsample)
	dfy = downsample_df(df2, downsample)
	if counts==None: # calculate sizes from numbers of rows instead of counts column 
		x = dfx.groupby(keys).size()
		y = dfy.groupby(keys).size()
	else: 
		x = dfx.groupby(keys).sum(counts)
		y = dfy.groupby(keys).sum(counts)
	z = x.to_frame().join(y.to_frame(), rsuffix='x', how='outer').fillna(0)
	z.columns = ['x', 'y']
	r = float(abs(z['x']-z['y']).sum())/len(z)
	return r


def sanders_percent_similarity(df1, df2, keys=['CDRH3 AA'], downsample=None, counts=None): 
	dfx = downsample_df(df1, downsample)
	dfy = downsample_df(df2, downsample)
	if counts==None: # calculate sizes from numbers of rows instead of counts column 
		x = dfx.groupby(keys).size()/len(dfx)
		y = dfy.groupby(keys).size()/len(dfy)
	else: 
		x = dfx.groupby(keys).sum(counts)/dfx[counts].sum()
		y = dfy.groupby(keys).sum(counts)/dfy[counts].sum() 
	z = x.to_frame().join(y.to_frame(), rsuffix='x', how='outer').fillna(0)
	z.columns = ['x', 'y']
	r = z.min(axis=1).sum()
	return r


def canberra_metric_dissimilarity(df1, df2, keys=['CDRH3 AA'], downsample=None, counts=None): 
	dfx = downsample_df(df1, downsample)
	dfy = downsample_df(df2, downsample)
	if counts==None: # calculate sizes from numbers of rows instead of counts column 
		x = dfx.groupby(keys).size()
		y = dfy.groupby(keys).size()
	else: 
		x = dfx.groupby(keys).sum(counts)
		y = dfy.groupby(keys).sum(counts)
	z = x.to_frame().join(y.to_frame(), rsuffix='x', how='outer').fillna(0)
	z.columns = ['x', 'y']
	r = float((abs(z['x']-z['y'])/(z['x']+z['y'])).sum())/len(z)
	return r 




def downsample_df(df, i=None):
	if not i==None: 
 		return df.sample(min(i, len(df)))
 	else: 
 		return df 








###### Functions to manipulate data after read-in. Mainly to simplify columns with multiple gene hits


#splits a string column and makes replicated rows with each entry 
def split_column(dataframe, column_name, sep=','): 
	header = dataframe.columns
	dataframe['ids_tmp'] = dataframe.index
	split_df = pd.concat([pd.Series(row['ids_tmp'], str(row[column_name]).split(sep)) for _, row in dataframe.iterrows()]).reset_index().drop_duplicates()
	split_df.columns = [column_name, 'ids_tmp']
	dataframe = dataframe.drop(column_name, axis=1)
	dataframe = pd.merge(dataframe, split_df, on='ids_tmp')
	dataframe = dataframe.filter(header)
	return dataframe

def split_columns(dataframe, column_names=['VHgene', 'DHgene', 'JHgene', 'VLgene', 'JLgene'], sep=','):
	for column in column_names: 
		dataframe = split_column(dataframe, column, sep=sep)
	return dataframe 


#splits a string column and just takes the first item 
def simplify_column(dataframe, column_name, sep=','): 
	header = dataframe.columns
	dataframe['tmp_col'] = dataframe[column_name].apply(lambda x: x.split(sep)[0] if type(x)==str else x)
	# dataframe['tmp_col'] = dataframe.VHgene.str.split(sep).apply(lambda x: x[0])
	dataframe = dataframe.drop(column_name, axis=1)
	dataframe = dataframe.rename(columns={'tmp_col': column_name})
	# dataframe = pd.merge(dataframe, split_df, on='ids_tmp')
	# dataframe = dataframe.filter(header)
	return dataframe

def simplify_columns(dataframe, column_names=['VHgene', 'DHgene', 'JHgene', 'VLgene', 'JLgene'], sep=','):
	for column in column_names: 
		dataframe = simplify_column(dataframe, column, sep=sep)
	return dataframe 


# expand df with Total Reads broken down, more intuitive format for population similarity
def expand_df(df, key='Total Counts'): 
	return df.loc[np.repeat(df.index.values,df['Total Counts'].astype(int))]




