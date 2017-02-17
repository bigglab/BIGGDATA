
def split_locus(x):
	xsplit = x.split('*')[0]
	xsplit = xsplit.split('(')[0]
	xsplit = xsplit.split('*')[0]
	xsplit = xsplit.split('/')[0]
	xsplit = xsplit.split('-')[0]
	match = re.match(r"([a-z]+)([0-9]+)", xsplit, re.I)
	if match: 
		return match.group(1)
	else: 
		return xsplit


def split_gene(x):
	xsplit = x.split('*')[0]
	xsplit = xsplit.split('/')[0]
	xsplit = xsplit.split('-')[0]
	return xsplit

# df['locus'] = df.allele_name.apply(split_locus)
# df['gene'] = df['allele_name'].apply(split_gene)



def fix_cd(row): 
	if 'CD' in row.locus: 
		return row.locus 
	else: 
		return row.gene



# Need to populate gene and locus tables first for these: 

def find_gene_id(g): 
	try: 
		i = gene[gene.name==g]['id'].iloc[0]
	except IndexError: 
		print 'not in genes: {}'.format(g)
	else: 
		return i

def find_locus_id(row): 
	try: 
		i = locus[locus.name==row['locus']]['id'].iloc[0]
	except IndexError: 
		if row['gene'] == 'CD1D': 
			i = 45
		elif row['gene'] == 'CD8A': 
			i = 46 
		else: 
				match = re.match(r"([a-z]+)([0-9]+)", row['locus'], re.I)
				if match: 
					print 'looking rather for {}'.format(match.group(1))
					i = locus[locus.name==match.group(1)]['id'].iloc[0]
				else: 
					print 'not in locus: {}'.format(row['locus'])
		if i: 
			return i 
	else: 
		return i




def find_source_id(source_name): 
	if source_name=='IMGT_RefSeq': 
		i = 2 
	else: 
		i = 1 
	return i 






