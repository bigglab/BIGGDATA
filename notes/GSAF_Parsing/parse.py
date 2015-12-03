import json 

l = open('multiple_datasets_per_r1r2.metadata.json').read()
j = json.loads(l)

samples_json = j['user_data']['description']['GGLAB_DB_FIELDS']