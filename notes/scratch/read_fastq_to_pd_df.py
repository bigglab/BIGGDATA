

def read_fastq(file, chunk=100000):    
    reader = pd.read_csv(file, chunksize=chunk,sep='\n', header=None)
    def rowgroups(ind):
        return ind%4
    def make_table(df):
       """
           Note: this is different than the method i told you on the phone where instead you would use               groupby:
                
                   Using groupby it would be something like this .... maybe it is better dunno, ive used both

                   new_df = pd.DataFrame(df.groupby(lambda x=x%4).groups).rename({0:'header', 1:'seq', 3: 'qual'}).drop(2,axis=1)

       """

        df['readnum'] = df.index.map(lambda x: x/4)
        df['linenum'] = df.index.map(lambda x: x%4)
        df = df.pivot(index='readnum', columns='linenum', values=0).rename(columns={0: 'header', 1: 'seq', 3: 'qual'}).drop(2, axis=1)        
        return df

    fastq_table = pd.concat([make_table(df) for df in reader])
    gc.collect()
    return fastq_table