
import os
from models import *
from app import db
import tempfile
import shlex
import subprocess


pandaseq_executable = '/usr/local/bin/pandaseq'

def pandaseq_test(n=1000, min_overlap=20, min_length=75, dataset_id=None):

    if dataset_id:
        d = db.session.query(Dataset).get(dataset_id)
    else:
        d = db.session.query(Dataset).get(278)
    files = d.primary_data_files()
    if len(files)<2:
        print 'overlap analysis requires two read files identified with dataset.primary_data_files()'
        return False

    temp_files = []
    print 'sampling read files'
    temp_r1_file = tempfile.mktemp()
    temp_r2_file = tempfile.mktemp()
    temp_files.append(temp_r1_file)
    temp_files.append(temp_r2_file)
    if '.gz' in files[0].path:
        r1_command = 'gunzip -c {} | head -{} > {}'.format(files[0].path, n*4, temp_r1_file)
    else:
        r1_command = 'head -{} {} > {}'.format(n*4, files[0].path, temp_r1_file)
    if '.gz' in files[1].path:
        r2_command = 'gunzip -c {} | head -{} > {}'.format(files[1].path, n*4, temp_r2_file)
    else:
        r2_command = 'head -{} {} > {}'.format(n*4, files[1].path, temp_r2_file)

    print r1_command
    r1_command = shlex.split(r1_command)
    if '|' in r1_command:
        pipe_index = r1_command.index('|')
        carot_index = r1_command.index('>')
        gunzip_args = r1_command[:pipe_index]
        command_line_args = r1_command[(pipe_index + 1):carot_index]
        with open(r1_command[(carot_index + 1):][0], 'w') as temp_out_file:
            gunzip_process = subprocess.Popen(gunzip_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            command_line_process = subprocess.Popen(command_line_args, stdin=gunzip_process.stdout, stdout=temp_out_file,
                                                    stderr=subprocess.STDOUT)
            clp_result = command_line_process.wait()
            gunzip_process.stdout.close()
            temp_out_file.close()
    else:
        print "only supporting fastq.gz right now"

    print r2_command
    r2_command = shlex.split(r2_command)
    if '|' in r2_command:
        pipe_index = r2_command.index('|')
        carot_index = r1_command.index('>')
        gunzip_args = r2_command[:pipe_index]
        command_line_args = r2_command[(pipe_index + 1):carot_index]
        with open(r2_command[(carot_index + 1):][0], 'w') as temp_out_file:
            gunzip_process = subprocess.Popen(gunzip_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            command_line_process = subprocess.Popen(command_line_args, stdin=gunzip_process.stdout,
                                                        stdout=temp_out_file, stderr=subprocess.STDOUT)
            clp_result = command_line_process.wait()
            # print clp_result
            gunzip_process.stdout.close()
            temp_out_file.close()
    else:
        print 'only supporting fastq.gz right now'



    print 'pandaseq overlap with {}bp min length, {}bp min overlap'.format(min_length, min_overlap)
    temp_pandaseq_file = tempfile.mktemp()
    temp_files.append(temp_pandaseq_file)
    print 'writing pandaseq fasta output to temporary file {}'.format(temp_pandaseq_file)
    pandaseq_command = "{} -f {} -r {} -w {} -l {} -o {} 2>/dev/null > /dev/null".format(pandaseq_executable, temp_r1_file, temp_r2_file, temp_pandaseq_file, min_length, min_overlap)
    print pandaseq_command
    response = os.system(pandaseq_command)

    with open(temp_pandaseq_file) as f:
        pandaseq_count = 0
        for i, l in enumerate(f):
            if l[0]=='>':
                pandaseq_count+=1
    pandaseq_success_ratio = float(pandaseq_count) / float(n)
    print pandaseq_success_ratio


    for temp_file in temp_files:
        os.remove(temp_file)

    return pandaseq_success_ratio



def run_pandaseq_prediction(dataset_id=280):
    results = pd.DataFrame()
    for o in range(10, 110, 10):
        for l in range(100,160,10):
            result = pandaseq_test(n=1000, min_overlap=o, min_length=l, dataset_id=dataset_id)
            results.set_value(o,l,result)
    return results



Young1_Pair_VH_results = run_pandaseq_prediction(dataset_id=280)
Young1_Pair_KL_results = run_pandaseq_prediction(dataset_id=281)


print "Young1_Pair_VH:"
print Young1_Pair_VH_results

print ''
print "Young1_Pair_KL:"
print Young1_Pair_KL_results



# import time
# while True:
#     pandaseq_test()
#     time.sleep(5)