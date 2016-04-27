import operator 
import json 


from models import * 

def _modify_function(f):
	"""A decorator function that replaces the function it wraps with a function that captures all information necessary to call the function again:
	the function name, its module, and the arguments it was called with. It then sends a POST request to the Immunogrep proxy server with
	the information, passed as a dictionary.
	"""
	@wraps(f)  # This decorator from functools takes care of keeping __name__ and similar attributes of the function f constant, despite being replaced by _post_args
	def _post_args(*args, **kwargs):
		"""This is the function that the module functions are replaced with.
		"""
		argument_dict = {}
		argument_dict['db_action'] = 'updates'
		argument_dict['module'] = inspect.getmodule(f).__name__
		argument_dict['command'] = f.__name__
		argument_dict['args'] = args
		argument_dict['kwargs'] = kwargs
		print "pre-arguments: ", argument_dict
		to_filename = argument_dict['kwargs'].pop('to_filename', None)
#		process_result = argument_dict['kwargs'].pop('process_result', None)
		print "arguments: ", argument_dict
		return _post_to_proxy("", argument_dict, to_filename=to_filename)  # <-- this line is new
#		db_response = _post_to_proxy("", argument_dict, to_filename=to_filename, process_result=process_result)  # <-- this line is new
#		if process_result:
#			return process_result(db_response)
#		else:
#			return db_response
		# return argument_dict
	return _post_args

#--- The flatten dictionary function should be put into some universal ImmunoGrep module, and shouldn't remain here.
#--- The code is included here for prototyping porpoises.
def flatten_dictionary(d):
	"""Input: a dictionary (only a useful function if it's a nested dictionary).
	Output: a flattened dictionary, where nested keys are represented in the flat structure with a . separating them.
	{a: 1, b: {c: 2, d: 3}} --> {a: 1, b.c: 2, b.c: 3}
	"""
	flattened_dict = {}
	def _interior_loop(d, parent_key):
		for key, value in d.items():
			parent_key = parent_key + [key]
			if isinstance(value, dict):
				for item in _interior_loop(value, parent_key[:]):
					yield item
				parent_key.pop()
			else:
				yield {'.'.join(parent_key): value}
				parent_key.pop()
	
	for key_value in _interior_loop(d, []):
		flattened_dict.update(key_value)
	return flattened_dict



def flatten_list(lst):
    return [item for sublist in lst for item in sublist]



def demultiplex_tuple_counts(d, reverse=False, index=0): 
    isotypes = [x for x in set(flatten_list([o[0] for o in d if o[0] != None])) if x != None]
    isotype_counts = {}
    for i in isotypes: 
        isotype_counts[i] = 0 
    for isos,c in d: 
        if not isos == None: 
            for i in isos: 
                if i in isotypes: 
                    isotype_counts[i] += c 
    isotype_data = sorted(isotype_counts.items(), key=operator.itemgetter(index), reverse=reverse)
    return isotype_data




######### 

# MODEL FUNCTIONS 

########## 


def build_exp_from_dict(dict): 
    ex = Experiment()
    for k,v in dict.iteritems():
        vetted_k = ''
        for c in k: 
            if c in ['$']:
                do_nothing = ''
            else: 
                vetted_k = ''.format(vetted_k, c)
        setattr(ex, k.lower(), v)
    return ex

def build_annotation_from_mongo_dict(d): 
    d = flatten_dictionary(d)
    nd = {}
    for k,v in d.iteritems(): 
        nd[k.lower()] = v 
    d = nd 
    ann = Annotation() 
    if d['analysis_name'] == 'IMGT': 
        print 'interpreting IMGT Annotation Record from flattened mongo sequence document' 
        print d
        ann.v_hits = OrderedDict()
        ann.d_hits = OrderedDict()
        ann.j_hits = OrderedDict()
        ann.c_hits = OrderedDict()
        for k,v in d.iteritems(): 
            if "_id" == k: ann._id = v
            if "seq_id" == k: ann.seq_id = v
            if "exp_id" == k: ann.exp_id = v
            if "analysis_name" == k: ann.analysis_name = v
            if "recombination_type" == k: ann.recombination_type = v
            if "data.cdr3.aa" == k: ann.cdr3_aa = v
            if "data.cdr3.nt" == k: ann.cdr3_nt = v
            if "data.jregion.fr4.aa" == k: ann.fr4_aa = v            
            if "data.jregion.fr4.nt" == k: ann.fr4_nt = v
            # if "data.notes" == k: ann.notes = v
            if "data.predicted_ab_seq.aa" == k: ann.aa = v
            if "data.predicted_ab_seq.nt" == k: ann.nt = v
            if "data.strand" == k: ann.strand = v
            if "data.vregion.cdr1.aa" == k: ann.cdr1_aa = v
            if "data.vregion.cdr1.nt" == k: ann.cdr1_nt = v
            if "data.vregion.cdr2.aa" == k: ann.cdr2_aa = v
            if "data.vregion.cdr2.nt" == k: ann.cdr2_nt = v
            if "data.vregion.fr1.aa" == k: ann.fr1_aa = v
            if "data.vregion.fr1.nt" == k: ann.fr1_nt = v
            if "data.vregion.fr2.aa" == k: ann.fr2_aa = v
            if "data.vregion.fr2.nt" == k: ann.fr2_nt = v
            if "data.vregion.fr3.aa" == k: ann.fr3_aa = v
            if "data.vregion.fr3.nt" == k: ann.fr3_nt = v
            if "data.vregion.shm.aa" == k: ann.shm_aa = v
            if "data.vregion.shm.nt" == k: ann.shm_nt = v
            # if "date_updated" == k: ann.date_updated = v
            # if "settings" == k: ann.settings = v

            if "data.vregion.vgenes" == k: 
                if "data.vregion.vgene_scores" in d: 
                    if len(v) == len(d["data.vregion.vgene_scores"]):
                        for i in range(0,len(v)):
                            ann.v_hits[v[i]] = d["data.vregion.vgene_scores"][i]
                    else: 
                        for i in range(0,len(v)):
                            ann.v_hits[v[i]] = d["data.vregion.vgene_scores"][0]
                else: 
                    for i in range(0,len(v)):
                        ann.v_hits[v[i]] 
                if len(ann.v_hits) > 0: 
                    ann.v_top_hit = ann.v_top_hit_locus = sorted(ann.v_hits, key=operator.itemgetter(1))[-1]
                    ann.v_top_hit_locus= trim_ig_locus_name(ann.v_top_hit_locus)
            if "data.dregion.dgenes" == k: 
                if "data.dregion.dgene_scores" in d: 
                    for i in range(0,len(v)):
                        ann.d_hits[v[i]] = d["data.dregion.dgene_scores"][i]
                else: 
                    for i in range(0,len(v)):
                        ann.d_hits[v[i]] = True 
                if len(ann.d_hits) > 0 : 
                    if ann.d_hits.values() == [True]: 
                        ann.d_top_hit = ann.d_top_hit_locus = ann.d_hits.keys()[0]
                    else: 
                        ann.d_top_hit = ann.d_top_hit_locus = sorted(ann.d_hits, key=operator.itemgetter(1))[-1]
                        ann.d_top_hit_locus= trim_ig_locus_name(ann.d_top_hit_locus)
            if "data.jregion.jgenes" == k: 
                if "data.jregion.jgene_scores" in d: 
                    if len(v) == len(d["data.jregion.jgene_scores"]):
                        for i in range(0,len(v)):
                            ann.j_hits[v[i]] = d["data.jregion.jgene_scores"][i]
                    else: 
                        for i in range(0,len(v)):
                            ann.j_hits[v[i]] = d["data.jregion.jgene_scores"][0]
                else: 
                    for i in range(0,len(v)):
                        if 'LESS' not in v[i]:
                            ann.j_hits[v[i]] = True 
                if len(ann.j_hits) > 0: 
                    ann.j_top_hit = ann.j_top_hit_locus = sorted(ann.j_hits, key=operator.itemgetter(1))[-1]
                    ann.j_top_hit_locus= trim_ig_locus_name(ann.j_top_hit_locus)
            # CONSTANT REGION FROM IMGT? 
            # if "data.cregion.cgenes" == k: 
            #     if "data.cregion.cgene_scores" in d: 
            #         for i in range(0,len(v)):
            #             ann.c_hits[v[i]] = d["data.cregion.cgene_scores"][i]
            #     else: 
            #         for i in range(0,len(v)):
            #             ann.c_hits[v[i]] 
                # if len(ann.c_hits) > 0: 
                #     ann.c_top_hit = sorted(ann.c_hits, key=operator.itemgetter(1))[-1][0]
                #     ann.c_top_hit_locus = ann.c_top_hit.split('-')[0].split('*')[0].split('.')[0]

            if "data.productive" == k: 
                if 'PRODUCTIVE' in v: 
                    ann.productive = True
                else: 
                    ann.productive = False 

        return ann 
    else: 
        print 'CAN NOT INTERPRET NON-IMGT DOCUMENTS (yet)'
        return False



def trim_ig_allele_name(long_name): 
    if long_name == None: return ''
    if '*' in long_name: long_name = [l for l in long_name.split('*') if 'IG' in l or 'TR' in l][0]
    return long_name

def trim_ig_locus_name(long_name): 
    # print 'trimming long name: {}'.format(long_name)
    if long_name == None: return ''
    if long_name == '*': return ''
    if long_name == '.': return ''
    if long_name == 'P': return ''
    if long_name == '-': return ''
    if long_name == ' ': return ''
    if '-' in long_name: long_name = [l for l in long_name.split('-') if 'IG' in l or 'TR' in l][0]
    if '*' in long_name: long_name = [l for l in long_name.split('*') if 'IG' in l or 'TR' in l][0]
    if '.' in long_name: long_name = [l for l in long_name.split('.') if 'IG' in l or 'TR' in l][0]
    if 'P' in long_name: long_name = [l for l in long_name.split('P') if 'IG' in l or 'TR' in l][0]
    if ' ' in long_name: long_name = [l for l in long_name.split(' ') if 'IG' in l or 'TR' in l][0]
    return long_name



def parse_alignments_from_mixcr_hits(hits): 
    try: 
        hits.split(',')
    except: 
        return None 
    else: 
        score_dict = OrderedDict()
        hs = hits.split(',')
        if len(hs) == 0: 
            return score_dict
        for h in hs: 
            if len(h.split('(')) != 2: 
                # print '!!!!!!! Empty h?:  {}'.format(h)
                continue
            gene,score = h.split('(')
            # short_gene = trim_ig_locus_name(gene)
            score = int(score.replace(')',''))
            score_dict[gene] = score 
        return score_dict 


def build_annotations_from_mixcr_file(file_path, dataset_id=None, analysis_id=None):
    f = open(file_path)
    headers = f.readline().split('\t')
    annotations = []
    for line in f.readlines():
        fields = line.split('\t')
        ann = Annotation() 
        ann.analysis_name = 'MIXCR'
        if dataset_id: ann.dataset_id = dataset_id 
        if analysis_id: ann.analysis_id = analysis_id
        for i,k in enumerate(headers): 

            # COULD USE THIS TO BUILD SEQUENCE DOCUMENTS
            if "Description R1" == k: ann.header = fields[i]
            if "Read(s) sequence" == k: ann.read_sequences   = fields[i]
            if "Read(s) sequence qualities" == k: ann.read_qualities   = fields[i]
            if "All V hits" == k: ann.v_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if "All D hits" == k: ann.d_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if "All J hits" == k: ann.j_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if "All C hits" == k: ann.c_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if len(ann.v_hits): ann.v_top_hit = trim_ig_allele_name(sorted(ann.v_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.v_hits): ann.v_top_hit_locus = trim_ig_locus_name(ann.v_top_hit)
            if len(ann.d_hits): ann.d_top_hit = trim_ig_allele_name(sorted(ann.d_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.d_hits): ann.d_top_hit_locus = trim_ig_locus_name(ann.d_top_hit)
            if len(ann.j_hits): ann.j_top_hit = trim_ig_allele_name(sorted(ann.j_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.j_hits): ann.j_top_hit_locus = trim_ig_locus_name(ann.j_top_hit)
            if len(ann.c_hits): ann.c_top_hit = trim_ig_allele_name(sorted(ann.c_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.c_hits): ann.c_top_hit_locus = trim_ig_locus_name(ann.c_top_hit)
            # if "All V alignments" == k: ann.   = fields[i]
            # if "All D alignments" == k: ann.   = fields[i]
            # if "All J alignments" == k: ann.   = fields[i]
            # if "All C alignments" == k: ann.   = fields[i]
            if "N. Seq. FR1" == k: ann.fr1_nt   = fields[i]
            # if "Min. qual. FR1" == k: ann.   = fields[i]
            if "N. Seq. CDR1" == k: ann.cdr1_nt   = fields[i]
            # if "Min. qual. CDR1" == k: ann.   = fields[i]
            if "N. Seq. FR2" == k: ann.fr2_nt   = fields[i]
            # if "Min. qual. FR2" == k: ann.   = fields[i]
            if "N. Seq. CDR2" == k: ann.cdr2_nt   = fields[i]
            # if "Min. qual. CDR2" == k: ann.   = fields[i]
            if "N. Seq. FR3" == k: ann.fr3_nt   = fields[i]
            # if "Min. qual. FR3" == k: ann.   = fields[i]
            if "N. Seq. CDR3" == k: ann.cdr3_nt   = fields[i]
            # if "Min. qual. CDR3" == k: ann.   = fields[i]
            if "N. Seq. FR4" == k: ann.fr4_nt   = fields[i]
            # if "Min. qual. FR4" == k: ann.   = fields[i]
            if "AA. Seq. FR1" == k: ann.fr1_aa   = fields[i]
            if "AA. Seq. CDR1" == k: ann.cdr1_aa   = fields[i]
            if "AA. Seq. FR2" == k: ann.fr2_aa   = fields[i]
            if "AA. Seq. CDR2" == k: ann.cdr2_aa   = fields[i]
            if "AA. Seq. FR3" == k: ann.fr3_aa   = fields[i]
            if "AA. Seq. CDR3" == k: ann.cdr3_aa   = fields[i]
            if "AA. Seq. FR4" == k: ann.fr4_aa   = fields[i]
            # if "Ref. points" == k: ann.   = fields[i]


            # if "data.productive" == k: 
            #     if 'PRODUCTIVE' in v: 
            #         ann.productive = True
            #     else: 
            #         ann.productive = False 

        annotations.append(ann)
    return annotations


def select_top_hit(hits):
    if hits !=  None :
        top_hit = trim_ig_allele_name(sorted(hits.items(), key=lambda x: x[1], reverse=True)[0][0])
        return top_hit
    else: 
        return None

def build_annotation_dataframe_from_mixcr_file(file_path, dataset_id=None, analysis_id=None):
    df = pd.read_table(file_path, low_memory=False)
    df['All V hits'] = df['All V hits'].apply(parse_alignments_from_mixcr_hits)
    df['All D hits'] = df['All D hits'].apply(parse_alignments_from_mixcr_hits)
    df['All J hits'] = df['All J hits'].apply(parse_alignments_from_mixcr_hits)
    df['All C hits'] = df['All C hits'].apply(parse_alignments_from_mixcr_hits)
    df['v_top_hit'] = df['All V hits'].apply(select_top_hit)
    df['v_top_hit_locus'] = df['v_top_hit'].apply(trim_ig_locus_name)
    df['d_top_hit'] = df['All D hits'].apply(select_top_hit)
    df['d_top_hit_locus'] = df['d_top_hit'].apply(trim_ig_locus_name)
    df['j_top_hit'] = df['All J hits'].apply(select_top_hit)
    df['j_top_hit_locus'] = df['j_top_hit'].apply(trim_ig_locus_name)
    df['c_top_hit'] = df['All C hits'].apply(select_top_hit)
    df['c_top_hit_locus'] = df['c_top_hit'].apply(trim_ig_locus_name)
    df['All V hits'] = df['All V hits'].apply(json.dumps)
    df['All D hits'] = df['All D hits'].apply(json.dumps)
    df['All J hits'] = df['All J hits'].apply(json.dumps)
    df['All C hits'] = df['All C hits'].apply(json.dumps)
    df['analysis_id'] = analysis_id
    df['dataset_id'] = dataset_id 


    column_reindex = {
    "Description R1":'header',
    'Read(s) sequence': 'read_sequences',
    'Read(s) sequence qualities': 'read_qualities',
    'All V hits':'v_hits',
    'All D hits':'d_hits',
    'All J hits':'j_hits',
    'All C hits':'c_hits',
    "N. Seq. FR1":'fr1_nt',
    "N. Seq. CDR1" : 'cdr1_nt',
    "N. Seq. FR2" : 'fr2_nt',
    "N. Seq. CDR2" : 'cdr2_nt',
    "N. Seq. FR3" : 'fr3_nt' ,
    "N. Seq. CDR3": 'cdr3_nt',
    "N. Seq. FR4" : 'fr4_nt',
    "AA. Seq. FR1"  : 'fr1_aa' ,
    "AA. Seq. CDR1" : 'cdr1_aa',
    "AA. Seq. FR2"  : 'fr2_aa' ,
    "AA. Seq. CDR2" : 'cdr2_aa',
    "AA. Seq. FR3"  : 'fr3_aa' ,
    "AA. Seq. CDR3" : 'cdr3_aa',
    "AA. Seq. FR4"  : 'fr4_aa' ,
    }
    df = df.rename(str, columns=column_reindex)
    cols = column_reindex.values() 
    cols.append('analysis_id')
    cols.append('dataset_id')
    cols.append('v_top_hit_locus')
    cols.append('d_top_hit_locus')
    cols.append('j_top_hit_locus')
    cols.append('c_top_hit_locus')
    cols.append('v_top_hit')
    cols.append('d_top_hit')
    cols.append('j_top_hit')
    cols.append('c_top_hit')
    df = df[cols]
    return df 

#####
#
# Jinja Custom Filter
#
#####

_js_escapes = {
        '\\': '\\u005C',
        '\'': '\\u0027',
        '"': '\\u0022',
        '>': '\\u003E',
        '<': '\\u003C',
        '&': '\\u0026',
        '=': '\\u003D',
        '-': '\\u002D',
        ';': '\\u003B',
        u'\u2028': '\\u2028',
        u'\u2029': '\\u2029'
}

# Escape every ASCII character with a value less than 32.
_js_escapes.update(('%c' % z, '\\u%04X' % z) for z in xrange(32))

def jinja2_escapejs_filter(value):
        retval = []
        for letter in value:
                if _js_escapes.has_key(letter):
                        retval.append(_js_escapes[letter])
                else:
                        retval.append(letter)

        return jinja2.Markup("".join(retval))

