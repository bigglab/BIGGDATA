#script to walk through a directory and import any paired read files

from collections import OrderedDict

d = '/data/russ/YoungOldSeqs'

datasets = OrderedDict()
for (path, names, files) in walk(d):
	if files!=[]: 
		r1s = [f for f in map(lambda s: path+'/'+s, files) if 'R1' in f and '.fastq' in f and 'filtered' not in f]
		r2s = [f for f in map(lambda s: path+'/'+s, files) if 'R2' in f and '.fastq' in f and 'filtered' not in f]
		for r1 in r1s: 
			r2 = r1.replace('R1', 'R2')
			if os.path.exists(r2) and os.path.exists(r1): 
				dataset_name = r1.split('.')[0].split('/')[-1].replace('_R1','')
				if 'pair' in r1 or 'pair' in path.lower(): 
					pairing = True 
				else: 
					pairing = False
				sample, seq_type = path.split('/')[-2:]
				datasets[(dataset_name, pairing)] = [r1,r2]

print datasets
current_datasets = [d[0] for d in db.session.query(Dataset.name).distinct().all()]
new_datasets = []
for (n,p), filepath_array in datasets.items(): 
  if n in current_datasets: 
      do_nothing = None
  else: 
      dataset_name = n
      print dataset_name
      paired = p
      print paired
      print filepath_array
      import_files_as_dataset.apply_async((), {'name':dataset_name,  'paired':paired, 'user_id':2, 'project':96, 'filepath_array':filepath_array})
      time.sleep(0.01)
      new_datasets.append(((n,p),filepath_array))





