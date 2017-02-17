
import os
from models import *
from app import db
import tempfile
import shlex
import subprocess


def pandaseq_test(n=1000):
    d = db.session.query(Dataset).get(278)
    files = d.primary_data_files()

    print d.__dict__
    print ''
    print files
    if len(files)<2:
        print 'overlap analysis requires two read files identified with dataset.primary_data_files()'
        return False
    print 'sampling read files'
    temp_r1_file = tempfile.mktemp()
    temp_r2_file = tempfile.mktemp()
    if '.gz' in files[0].path:
        r1_command = 'gunzip -c {} | head -{} > {}'.format(files[0].path, n, temp_r1_file)
    else:
        r1_command = 'head -{} {} > {}'.format(n, files[0].path, temp_r1_file)
    if '.gz' in files[1].path:
        r2_command = 'gunzip -c {} | head -{} > {}'.format(files[1].path, n, temp_r2_file)
    else:
        r2_command = 'head -{} {} > {}'.format(n, files[1].path, temp_r2_file)

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
            print command_line_process.wait()
            gunzip_process.stdout.close()
            # command_line_process.stdout.close()
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
            print command_line_process.wait()
            gunzip_process.stdout.close()
            temp_out_file.close()
            # command_line_process.stdout.close()
    else:
        print 'only supporting fastq.gz right now'


    time.sleep(1)

    print 'pandaseq overlap with 75bp min length, 20bp min overlap'
    temp_pandaseq_file = tempfile.mktemp()
    print 'writing pandaseq fasta output to temporary file {}'.format(temp_pandaseq_file)
    pandaseq_command = "pandaseq -f {} -r {} -w {} ".format(temp_r1_file, temp_r2_file, temp_pandaseq_file)
    print pandaseq_command
    pandaseq_command = shlex.split(pandaseq_command)
    command_line_process = subprocess.Popen(pandaseq_command)
    response, error = command_line_process.communicate()
    command_line_process.stdout.close()
    command_line_process.wait()
    print response

import time
while True:
    pandaseq_test()
    time.sleep(5)