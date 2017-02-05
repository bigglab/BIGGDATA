

def clonotype_seqs(dfShort, percentIdentity, dbfilename, tabfilename, append=False, low_read_count=1):
    '''
        This is our function for going through the results file and clonotyping sequences by their CDRH3.
        Assumptions:
        df => a dataframe that has already been collapsed by unique sequences and all the TAGS are properly formated and filters passed     
    '''

    '''     ok, for now we'll start with a dictionary (dfDict) of DFs and the keys are IDs, like "HD1_D273_VH"
    remember to leave/set numbers as integers/floats, not string...'''

    table_output = tabfilename
    fasta_output = dbfilename

    # Generate alist of unique CDR3s
    print('Generating unique CDR3 list')
    cdr3List = dfShort[dfShort['READS'] >= low_read_count]['CDR3.AA'].unique()
    # not used yet
    # read_count_by_cdr3 = dfShort.groupby(['CDR3.AA']).agg({'READS': 'sum'})
    print('Running clonotyping')
    # Call clonotyping
    # CDR3s = cdr3List
    sample_output_file = os.path.join(os.path.dirname(table_output), 'cdr3list.txt')
    with open(sample_output_file, 'w') as writecdr3:
        for cd in cdr3List:
            writecdr3.write(cd + '\n')
    output_file_cdr3_result = os.path.join(os.path.dirname(table_output), 'cdr3_clonotype_list.txt')
    run_clonotype_command = '{3} --file {0} --thresh {1} --output {2}'.format(sample_output_file, str(1 - percentIdentity), output_file_cdr3_result, clonotype_location )
    error = subprocess.call(run_clonotype_command, shell=True)
    if error != 0:
        raise Exception('Error occurred when running clonotyping')
    """
    # Generate clonotyping dict
    # clonotyped CDR3s are in clonoDict
    #clonoDict = {}
    #with open(output_file_cdr3_result) as clono_file:
    #   for clonotypes_created in clono_file:
    #       if not clonotypes_created.strip():
    #           continue
    #       clonotypes_created = clonotypes_created.strip().split('\t')
    #       clonoDict[clonotypes_created[0]] = clonotypes_created[1]cd
    #clonoDict = pd.DataFrame(clonoDict)
    """
    clonoDict = pd.read_csv(output_file_cdr3_result, sep='\t', skip_blank_lines=True, header=None, names=['CDR3.AA', 'Clonotype'])

    # Create a clonotype field in the dataframe
    # dfClono = dfShort.apply(lambda x: clono(x), axis=1)  # => instead of this, lets use a dataframe merge function
    print('Appending clono')
    dfClono = pd.merge(dfShort, clonoDict, on='CDR3.AA', how='left')
    dfClono.fillna('', inplace=True)
    dfClono = dfClono[dfClono['READS'] >= low_read_count].sort_values(['READS'], ascending=False)       
    dfClono['Clonotype'] = dfClono['Clonotype'].astype(int)     

    # NOW lets figure out how we should reorder columns in dataframe based on the order we want them to appear in the FASTA file
    current_columns = list(dfClono.columns)
    output_fields = copy.deepcopy(default_order_of_fields)
    for col in current_columns:
        if col not in output_fields:
            # add a new column from dataframe to our output
            output_fields.append(col)
    # Now make sure all columns exist in dataframe
    for col in output_fields:
        if col not in current_columns:
            dfClono[col] = ''
    
    # Now reorder columns
    dfClono = dfClono[output_fields]
    # Finally RENAME COLUMNS AND ENSURE NO COLUMN NAMES HAVE A '_' IN IT; we do this because the FASTA file is delimited by '_'
    renamecol = {r: r.replace('_', '') for r in dfClono.columns}
    dfClono.rename(columns=renamecol, inplace=True)
    dfClono.set_index('ABSEQ.AA', inplace=True)
    dfClono.drop('index', axis=1, inplace=True)
    # new_field_order = list(dfClono.columns)

    # Export DF
    mode = 'a' if append is True else 'w'
    header = False if append is True else True
    print('Exporting MS DB as TAB')
    dfClono.to_csv(table_output, sep='\t', mode=mode, header=header)

    print('Exporting MS DB as FASTA')
    """
    # For some reason its super super slow to export dataframe this way. is this because it is not using c?
    dfClono = dfClono.astype(str)
    with open(fasta_output, mode) as output:
        if mode == 'w':
            output.write('#' + '_'.join(new_field_order) + '\n')
        for row in dfClono.iterrows():
            header = row[1].str.cat(sep='_')  # '_'.join(row[1].astype(str))
            # output.write('>'+row[1]['ID']+'_'+row[1]['CDR1_Sequence.AA']+'\n'+row[0]+'\n')
            output.write('>{0}\n{1}\n'.format(header, row[0]))
    """
    # Try doing it with AWK instead
    tab_to_fasta(table_output, fasta_output, "_", append=append)

