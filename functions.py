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


# need to rework for new annotation format: 
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


#####
#
# File Functions
#
#####

def parse_file_ext(path):

    if path.split('.')[-1] == 'gz':
        gzipped = True
    else:
        gzipped = False
    if gzipped: 
        ext = path.split('.')[-2]
    else:
        ext = path.split('.')[-1]
    ext_dict = tree()
    ext_dict['fastq'] = 'FASTQ'
    ext_dict['fq'] = 'FASTQ'
    ext_dict['fa'] = 'FASTA'
    ext_dict['fasta'] = 'FASTA'
    ext_dict['txt'] = 'TEXT'
    ext_dict['json'] = 'JSON'
    ext_dict['tab'] = 'TAB'
    ext_dict['csv'] = 'CSV'
    ext_dict['yaml'] = 'YAML'
    ext_dict['pileup'] = 'PILEUP'
    ext_dict['sam'] = 'SAM'
    ext_dict['bam'] = 'BAM'
    ext_dict['imgt'] = 'IMGT'
    ext_dict['gtf'] = 'GTF'
    ext_dict['gff'] = 'GFF'
    ext_dict['gff3'] = 'GFF3'
    ext_dict['bed'] = 'BED'
    ext_dict['wig'] = 'WIGGLE'
    ext_dict['py'] = 'PYTHON'
    ext_dict['rb'] = 'RUBY'
    file_type = ext_dict[ext]
    if isinstance(file_type, defaultdict):
        return None
    else:
        if gzipped: 
            return 'GZIPPED_{}'.format(file_type)
        else: 
            return file_type

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
        if value == None: 
            retval = []
        else: 
            for letter in value:
                    if _js_escapes.has_key(letter):
                            retval.append(_js_escapes[letter])
                    else:
                            retval.append(letter)

        return jinja2.Markup("".join(retval))

