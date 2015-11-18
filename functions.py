import operator 
import json 



# USEFUL FUNCTIONS FROM CODE ON APPSOMA OR IGREP GITHUB





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


