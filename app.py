#System Imports
import ast
import json
import static
import sys
import os
import errno
import time
import random
from shutil import copyfile
import operator
# import urllib
os.environ['http_proxy']=''
import urllib2
import itertools
import subprocess
import boto 
import math 
# from filechunkio import FileChunkIO 
from celery import Celery, states
from celery.exceptions import Ignore
from collections import defaultdict, OrderedDict
import collections
#Flask Imports
from werkzeug import secure_filename
from flask import Blueprint, render_template, flash, redirect, url_for
from flask import Flask, Blueprint, make_response, render_template, render_template_string, request, session, flash, redirect, url_for, jsonify, get_flashed_messages, send_from_directory
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask.ext.mail import Mail, Message
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask_bootstrap import Bootstrap
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_nav import Nav 
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape
# from render_utils import make_context, smarty_filter, urlencode_filter
import wtforms
from flask_wtf import Form
import random
import jinja2 
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSON, JSONB, ARRAY, BIT, VARCHAR, INTEGER, FLOAT, NUMERIC, OID, REAL, TEXT, TIME, TIMESTAMP, TSRANGE, UUID, NUMRANGE, DATERANGE
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker, scoped_session
from pymongo import MongoClient
import pymongo
 
# Local Imports - local imports go here to prevent circular imports 
from forms import *
from functions import * 
from models import * 

# Initialize Application
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
# Initialize extensions
bcrypt = Bcrypt(app)
nav = Nav() 
Bootstrap(app) 

db.init_app(app)
db.app = app 

# Celery configured for local RabbitMQ 
celery = Celery(app.name, broker='amqp://')
import celery_config 
celery.config_from_object('celery_config')
# CELERY QUEUE TO SEND JOBS TO - USE FOR DEVELOPMENT 
celery_queue = 'default'

# change celery_queue to anything celery -Q
# 

# @Dave - temporary edit for local environ
s3 = boto.connect_s3(app.config['AWSACCESSKEYID'], app.config['AWSSECRETKEY'])
s3_bucket = s3.get_bucket(app.config['S3_BUCKET'])

# Mongo DB for Legacy Sequence Data
mongo_connection_uri = 'mongodb://reader:cdrom@geordbas01.ccbb.utexas.edu:27017/'
login_manager = LoginManager()
login_manager.init_app(app)

# load template environment for cleaner routes 
templateLoader = jinja2.FileSystemLoader( searchpath="{}/templates".format(app.config['HOME']) )
templateEnv = jinja2.Environment( loader=templateLoader, extensions=['jinja2.ext.with_'])

# Add a custom filter to escape characters for Javascript/JQuery insertion
# Usage: {{ some.js_insertion_text | escapejs }}
# js_insertion_text = "$(this);" | escaptjs --> "$(this)\\u003B"  
app.jinja_env.filters['escapejs'] = jinja2_escapejs_filter

def include_file(name):
    return jinja2.Markup(loader.get_source(env, name)[0])
app.jinja_env.globals['include_file'] = include_file


def round_to_two(flt):
    out = round(flt, 2) 
    return out
app.jinja_env.globals['round_to_two'] = round_to_two

# os.environ['http_proxy'] = app.config['QUOTAGUARD_URL']
proxy = urllib2.ProxyHandler()
opener = urllib2.build_opener(proxy)

def include_external_html(url):
    print 'requesting url: {}'.format(url)
    try: 
        response = opener.open(url)
        # response = urllib2.urlopen(url)
        contents = response.read()
    except urllib2.URLError, error: 
        print "ERROR RETRIEVING: {}".format(error)
        return ''
    return response  

app.jinja_env.globals['include_external_html'] = include_external_html

# Flask-Login use this to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(email):
    user = db.session.query(User).filter_by(email=email).first()
    if user: 
        return user 
    else:
        return None

def retrieve_golden():

    # @Dave - quick edit b/c I don't have the gifs

    try:
        gifs_dir = '{}/static/goldens'.format(app.config['HOME'])
        gifs = os.listdir(gifs_dir)
        gif = random.choice(gifs)
        gif_path = url_for('static', filename='goldens/{}'.format(gif))
    except:
        gif_path = None
    return gif_path

@login_manager.unauthorized_handler
def unauthorized():
    gif_path=retrieve_golden()
    flash('You must login or register to view that page.','success')
    return redirect( url_for('frontend.login') )

def get_filepaths(directory_path):
    file_paths = []
    for root, directories, files in os.walk(directory_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths 

def get_dropbox_files(user):
    dropbox_path = user.dropbox_path
    dropbox_file_paths = get_filepaths(dropbox_path)
    dropbox_file_paths = [file_path for file_path in dropbox_file_paths if file_path not in [file.path for file in user.files]]
    return dropbox_file_paths

def tree(): return defaultdict(tree)

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

def parse_name_for_chain_type(name):
    if 'tcra' in name.lower() or 'alpha' in name.lower(): 
        chain = 'TCRA'
    if 'tcrb' in name.lower() or 'beta' in name.lower(): 
        chain = 'TCRB'
    if 'tcra' in name.lower() or 'alpha' in name.lower() and 'tcrb' in name.lower() or 'beta' in name.lower():
        chain = 'TCRA/B'
    if 'igh' in name.lower() or 'heavy' in name.lower(): 
        chain = 'HEAVY'
    if 'igl' in name.lower() or 'igk' in name.lower() or 'light' in name.lower(): 
        chain = 'LIGHT'
    if 'igl' in name.lower() or 'igk' in name.lower() or 'light' in name.lower() and 'igh' in name.lower() or 'heavy' in name.lower(): 
        chain = 'HEAVY/LIGHT'
    try: 
        chain
    except NameError: 
        chain = '' 
    return chain 

def link_file_to_user(path, user_id, name):
    file = File()
    file.name = name 
    file.path = path 
    file.user_id = user_id
    file.description = ''
    file.file_type = parse_file_ext(file.path)
    file.available = True 
    file.s3_status = ''
    file.chain = parse_name_for_chain_type(name)
    db.session.add(file)
    db.session.commit()
    return True

# returns a string if unable to create the user directories
# returns false otherwise. 
@celery.task
def instantiate_user_with_directories(new_user_id):
    new_user = db.session.query(User).filter(User.id==new_user_id).first()

    for path in new_user.all_paths:
        try: 
            if not os.path.isdir(path):
                os.makedirs(path)
                print 'Created new directory at {}'.format(path)
        except ValueError, error:
            return 'Failed to create directory {}: {}'.format(path, error)
    
    # COPY SOME EXAMPLE FILES TO PLAY WITH
    try:
        share_root = app.config['SHARE_ROOT'] 
        if os.path.isdir(share_root):
            files = os.listdir(share_root)
        else:
            return 'Warning: share root path "{}"" not found'.format(share_root)
        print 'copying these files to new users dropbox: {}'.format(','.join(files))
        for f in files: 
            fullfilepath = '{}/{}'.format(new_user.dropbox_path, f)
            copyfile('{}/{}'.format(share_root, f), '{}/{}'.format(new_user.dropbox_path, f))
            link_file_to_user(fullfilepath, new_user.id, f)
        return False 
    except ValueError, error:
        return 'Warning: unable to copy sample files into user\'s dropbox: {}'.format(error)

@celery.task(bind = True)
def migrate_user_files(self, user_id):
    current_user = db.session.query(User).filter(User.id==user_id).first()

    # First, synchronously instantiate user directories, if they do not exist
    directories_needed = False

    for path in current_user.all_paths:
        if not os.path.isdir(path):
            directories_needed = True
            #.apply_async((current_user.id, ), queue=celery_queue)

    if directories_needed:
        result = instantiate_user_with_directories(current_user.id)

        if result: # anything but false is an error:
            print "Error instantiating new user directories: {}".format(result)

    # need a better way of updating users if the new directory creation fails...
    files = current_user.files

    overall_success = True

    for file in files:
        file_path = file.path

        if current_user.root_path not in file_path: # this means the file has not been moved yet...

            file_path = file_path.replace('//', '/')
            source_path, filename = os.path.split(file_path)
            extended_path = source_path.replace(current_user.old_scratch_path, '')
            extended_path = extended_path.replace(current_user.scratch_path, '') # just in case the original is already correct

            destination_path = current_user.scratch_path + extended_path
            destination_path = destination_path.replace('//', '/')

            source_filename = source_path + '/' + filename
            destination_filename = destination_path + '/'+ filename
            destination_filename = destination_filename.replace('//', '/')

            # first make the source and destination file paths
            try:
                if not os.path.isdir(source_path):
                    os.makedirs(source_path)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise

            try:
                if not os.path.isdir(destination_path):
                    os.makedirs(destination_path)
            except OSError, e:
                if e.errno != errno.EEXIST:
                    raise

            copy_success = False

            try:
                message = 'Copying {} to {}'.format(source_filename, destination_filename)
                self.update_state(state = states.STARTED, meta={'status': message})

                if not os.access(source_path, os.R_OK):
                    print "Error: source path '{}' not readable.".format(source_path)
                    overall_success = False
                else:
                    if not os.path.isfile(source_filename):
                        print "Warning: source file '{}' not found.".format(source_filename)
                        overall_success = False

                    elif not os.path.isdir(destination_path):
                        print "Error: destination path '{}' not found.".format(destination_path)
                        overall_success = False

                    elif not os.access(destination_path, os.W_OK):
                        print "Error: destination path '{}' not writable.".format(destination_path)
                        overall_success = False

                    elif os.path.isfile(destination_filename):
                        print "Warning: destination filename '{}' already exists.".format(destination_filename) 
                        copy_success = True
                    else:
                        copyfile(source_filename, destination_filename)
                        print 'Finished copying {} to {}'.format(source_filename, destination_filename)
                        copy_success = True 

            except ValueError, error:
                print "Error: Unable to copy file: {}.".format(error)
                overall_success = False

            if copy_success:
                file.path = destination_filename
                db.session.commit()
                print 'Success: Updated file path in database.'

    if overall_success:
        db.session.commit()
        print 'Success: All files have been migrated.'


    return False 

@celery.task
def transfer_file_to_s3(file_id): 
    f = db.session.query(File).filter(File.id==file_id).first()
    if not f: 
        return False 
    else: 
        if f.path:
            if f.s3_path: 
                print 'transferring file from {} to {}'.format(f.path, f.s3_path)
            else: 
                f.s3_path = '{}'.format(f.path)
                print 'transferring file from {} to s3://{}/{}'.format(f.path, app.config['S3_BUCKET'], f.s3_path)
                f.s3_status = 'Staging'
                db.session.commit()
        file_size = os.stat(f.path).st_size
        print 'starting transfer of {} byte file'.format(file_size)
        def cb(complete, total): 
            f.s3_status = 'Transferred {} of {} bytes'.format(complete, total)
            db.session.commit()
        key = s3_bucket.new_key(f.s3_path)
        result = key.set_contents_from_filename(f.path, cb=cb, num_cb=10)
        key.set_canned_acl('public-read')
        f.s3_status = "AVAILABLE"
        db.session.commit()
        print "Transfer complete. {} bytes transferred from {}  to  {}".format(result, f.path, f.s3_path)
        return True 

def get_user_dataset_dict(user): 
    datadict = OrderedDict()
    for dataset in sorted(user.datasets, key=lambda x: x.id, reverse=True):
        if dataset.name != '__default__':
            datadict[dataset] = sorted(dataset.files.all(), key=lambda x: x.file_type)
    return datadict

@celery.task 
def import_from_sra(accession, name=None, user_id=57, chain=None, project_selection = None, dataset_selection = None):
    user = db.session.query(User).filter(User.id==user_id).first()

    if not user:
        print "Unable to find user with id {}.".format(user_id)
        return False

    # load projects and datasets
    # set the dataset options
    datasets = Set(user.datasets)
    datasets.discard(None)
    datasets.discard(user.default_dataset)
    datasets = sorted(datasets, key=lambda x: x.id, reverse=True)

    # get a list of user projects for the form
    projects = Set(user.projects)
    projects.discard(None)
    projects = sorted(projects, key=lambda x: x.id, reverse=True)


    # check if the user has selected the default project (i.e., the user has no projects)
    file_dataset = None
    if dataset_selection == 'new':
        # create a new project here with the name default, add the user and dataset to the new project
        new_dataset = Dataset()
        new_dataset.user_id = user.id
        new_dataset.populate_with_defaults(user)
        new_dataset.name = 'Dataset'
        db.session.add(new_dataset)
        db.session.flush()
        new_dataset.name = accession + '_' + str(new_dataset.id)
        new_dataset.directory = "{}/{}".format(user.scratch_path.rstrip('/') , new_dataset.name)
        file_dataset = new_dataset
        print 'New file will be added to dataset "{}".'.format(new_dataset.name)
        db.session.commit()

    else: # check if the user has selected a project which they have access to
        user_has_permission = False
        for dataset in user.datasets:
            if str(dataset.id) == dataset_selection:
                file_dataset = dataset
                user_has_permission = True

                # if user.default_dataset == None:
                #     d.cell_types_sequenced = [str(project.cell_types_sequenced)]
                #     d.species = project.species
        if not user_has_permission:
            print 'Error: you do not have permission to add a file to that dataset.'
    db.session.commit()


    # now do the same with projects, with the qualification that we add the dataset to the project if it's not there already
    # check if the user has selected the default project (i.e., the user has no projects)
    if file_dataset:
        if project_selection == 'new':
            # create a new project here with the name default, add the user and dataset to the new project
            new_project = Project()
            new_project.user_id = user.id
            new_project.project_name = 'Project'
            db.session.add(new_project)
            db.session.flush()
            new_project.project_name = 'Project ' + str(new_project.id)
            new_project.users = [user]
            new_project.datasets = [file_dataset]
            new_project.cell_types_sequenced = [str(file_dataset.cell_types_sequenced)]
            new_project.species = file_dataset.species

            db.session.commit()
        else: # check if the user has selected a project which they have access to
            user_has_permission = False
            for project in projects:
                if str(project.id) == project_selection:
                    if project.role(user) == 'Owner' or project.role(user) == 'Editor':
                        # if the dataset is not in the project, add it
                        if file_dataset not in project.datasets:
                            project.datasets.append(file_dataset)
                        user_has_permission = True

                        if user.default_dataset == None:
                            file_dataset.cell_types_sequenced = [str(project.cell_types_sequenced)]
                            file_dataset.species = project.species

                        db.session.commit()
            if not user_has_permission:
                print 'Error: you do not have permission to add a dataset to that project.'
            db.session.commit()        

    if not name: 
        name = accession 

    # modify the path with the new style, the new hotness if you will
    if file_dataset:
        path = '{}/{}/{}'.format(
            user.scratch_path.rstrip('/'),
            'Dataset_' + str(file_dataset.id), 
            accession)
    else:
        path = '{}/{}'.format(
            user.scratch_path.rstrip('/'), 
            accession)

#####
    # check if the file path we settled on is available.
    directory = os.path.dirname(path)
    if not os.path.exists(directory): 
        os.makedirs(directory)

    if os.path.isfile(path):
        path = os.path.splitext(path)[0] + '_1' + os.path.splitext(path)[1]

#####

    print 'Fetching SRA data from NCBI {}'.format(accession)
    command = "fastq-dump --gzip --skip-technical  --readids --dumpbase --defline-qual '+' --split-files -T -F --outdir {} {}".format(directory, accession) 
    response = os.system(command)
    if response == 0: 
        file_paths = []

        dirs = os.listdir('{}/{}'.format(directory, accession))
        if dirs == ['1']:
            file_paths = ['{}/{}/1/fastq.gz'.format(directory, accession)]
            filename_array = ['{}.fastq.gz'.format(accession)]
        if dirs == ['1','2'] or dirs == ['2','1']:
            file_paths = ['{}/{}/1/fastq.gz'.format(directory, accession), '{}/{}/2/fastq.gz'.format(directory, accession)]
            filename_array = ['{}.R1.fastq.gz'.format(accession), '{}.R2.fastq.gz'.format(accession)]
        else: 
            print 'Number of files from SRA export not one or two...'
            return False 
        print 'Writing sra output files to {}'.format(directory)
        dataset = import_files_as_dataset(file_paths, filename_array=filename_array, user_id=user_id, name=name, chain=chain, dataset = file_dataset)
        print 'Dataset from SRA Accession {} created for user {}'.format(accession, user.username) 
        return True
    else: 
        print 'SRA IMPORT DID NOT SUCCEED'
        return False

@celery.task 
def import_files_as_dataset(filepath_array, user_id, filename_array=None, chain=None, name=None, dataset = None):
    
    current_user = db.session.query(User).filter(User.id==user_id).first()

    if not current_user:
        print "Error: user with id {} not found.".format(user_id)
        return False

    if not dataset:
        d = Dataset()
        d.user_id = user_id
        d.name = name
        d.description = 'Dataset generated from file import'
        d.chain_types_sequenced = [chain]
        db.session.add(d)
        db.session.commit()
        d.directory = current_user.scratch_path.rstrip('/') + '/Dataset_' + str(d.id)
    else:
        d = dataset

    if not d.directory:
        d.directory = current_user.scratch_path.rstrip('/') + '/Dataset_' + str(d.id)
        db.session.commit()

    if not os.path.exists(d.directory):
        os.makedirs(d.directory)
    db.session.commit()

    files = []
    for index, filepath in enumerate(filepath_array):
        f = File()
        f.user_id = user_id 
        if filename_array and len(filename_array) == len(filepath_array):
            f.name = filename_array[index]
        else:
            f.name = filepath.split('/')[-1]
        f.file_type = parse_file_ext(f.name) 
        f.dataset_id = d.id
        # description = 
        f.available = True
        f.in_use = False
        f.status = 'AVAILABLE'
        f.path = filepath
        f.file_size = os.path.getsize(f.path)
        f.s3_available = False
        f.s3_status = ''
        f.s3_path = ''
        f.chain = chain
        # url = db.Column(db.String(256))
        f.command = 'metadata created to link existing file'
        f.created = 'now'
        # paired_partner = db.Column(db.Integer, db.ForeignKey('file.id'))
        # parent_id = db.Column(db.Integer, db.ForeignKey('file.id'))
        # analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
        files.append(f)
    for f in files: 
        db.session.add(f)
    db.session.commit()
    d.primary_data_files_ids = map(lambda f: f.id, files)
    db.session.commit()
    return True 

@celery.task
def download_file(url, path, file_id):
    print 'Using urllib2 to download file from {}'.format(url)

    # check if the directory for the file exists. If not, make the directory path with makedirs
    directory = os.path.dirname(path)
    if not os.path.exists(directory): 
        os.makedirs(directory)

    response = urllib2.urlopen(url)
    CHUNK = 16 * 1024
    with open(path, 'wb') as outfile: 
        while True: 
            chunk = response.read(CHUNK)
            if not chunk: break 
            outfile.write(chunk)
    f = db.session.query(File).filter(File.id==file_id).first()
    f.available = True
    f.file_size = os.path.getsize(f.path)
    db.session.commit()
    print 'File download complete.'
    return True 

@celery.task
def run_mixcr_with_dataset_id(dataset_id, analysis_name='', analysis_description='', user_id=6, trim=False, cluster=False):
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    print 'RUNNING MIXCR ON DATASET ID# {}: {}'.format(dataset_id, repr(dataset.__dict__))
    analysis = Analysis()
    analysis.db_status = 'WAITING'
    analysis.name = analysis_name
    analysis.description = analysis_description
    analysis.user_id = user_id
    analysis.dataset_id = dataset.id
    analysis.program = 'mixcr'
    analysis.started = 'now'
    analysis.params = {}
    analysis.status = 'QUEUED'
    analysis.responses = []
    analysis.available = False
    analysis.inserted_into_db = False
    db.session.add(analysis)
    db.session.commit()
    data_files_by_chain = {}
    for key, values in itertools.groupby(dataset.primary_data_files(), lambda x: x.chain): 
        data_files_by_chain[key] = list(values)
    print "Running mixcr in these batches of files (sorted by file.chain): {}".format(data_files_by_chain)
    for chain, files in data_files_by_chain.items(): 
        if trim: 
            print 'Running Trim on Files in Analysis {} before executing MixCR'.format(analysis.id)
            files = run_trim_analysis_with_files(analysis, files)
        print 'ABOUT TO RUN MIXCR ANAYSIS {} ON FILES FROM CHAIN {}'.format(repr(analysis), chain)
        run_mixcr_analysis_id_with_files(analysis.id, files)
        if cluster: 
            print 'Clustering Output Files'
            for file in files: 
                result = run_usearch_cluster_fast_on_analysis_file(analysis, file, identity=0.9)
    return True 

@celery.task
def run_mixcr_analysis_id_with_files(analysis_id, files):
    analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    dataset = analysis.dataset
    files_to_execute = []
    print 'RUNNING MIXCR ON THESE FILES: {}'.format(files)
    scratch_path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
    basename = files[0].path.split('/')[-1].split('.')[0]
    basepath = '{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    output_files = []
    # Instantiate Source Files
    alignment_file = File()
    alignment_file.user_id = dataset.user_id
    alignment_file.path = '{}.aln.vdjca'.format(basepath)
    alignment_file.name = "{}.aln.vdjca".format(basename)
    # MIGHT NEED TO ADD THIS ARGUMENT to align   -OjParameters.parameters.mapperMaxSeedsDistance=5
    alignment_file.command = 'mixcr align --save-description -f {} {}'.format(' '.join([f.path for f in files]), alignment_file.path)
    alignment_file.file_type = 'MIXCR_ALIGNMENTS'
    files_to_execute.append(alignment_file)    
    clone_index_file = File()
    clone_index_file.user_id = dataset.user_id
    clone_index_file.file_type = 'MIXCR_CLONE_INDEX'
    clone_index_file.path = '{}.aln.clns.index'.format(basepath)
    clone_index_file.name = '{}.aln.clns.index'.format(basename)
    clone_index_file.command = 'echo "Indexing Done On Clone Assemble Step"'
    clone_file = File()
    clone_file.user_id = dataset.user_id
    clone_file.file_type = 'MIXCR_CLONES'
    clone_file.path = '{}.aln.clns'.format(basepath)
    clone_file.name = '{}.aln.clns'.format(basename)
    clone_file.command = 'mixcr assemble  -OassemblingFeatures=VDJRegion --index {} -f {} {}'.format(clone_index_file.path, alignment_file.path, clone_file.path)
    files_to_execute.append(clone_file)
    files_to_execute.append(clone_index_file)
    db.session.add(alignment_file)
    db.session.add(clone_file)
    db.session.commit()
    # Commit To Get Parent IDs
    clone_output_file = File()
    clone_output_file.user_id = dataset.user_id    
    clone_output_file.parent_id = clone_file.id 
    clone_output_file.path = '{}.txt'.format(clone_file.path)
    clone_output_file.file_type = 'MIXCR_CLONES_TEXT'
    clone_output_file.name = '{}.txt'.format(clone_file.name)
    clone_output_file.command = 'mixcr exportClones -sequence -quality -s -f {} {}'.format(clone_file.path, clone_output_file.path)
    files_to_execute.append(clone_output_file)
    alignment_output_file = File()
    alignment_output_file.user_id = dataset.user_id    
    alignment_output_file.parent_id = alignment_file.id
    alignment_output_file.path = '{}.txt'.format(alignment_file.path)
    alignment_output_file.file_type = 'MIXCR_ALIGNMENT_TEXT'
    alignment_output_file.name = '{}.txt'.format(alignment_file.name)
    alignment_output_file.command = 'mixcr exportAlignments -cloneId {}  -s -f -readId -descrR1 -descrR2 --preset full  {} {}'.format(clone_index_file.path, alignment_file.path, alignment_output_file.path)
    files_to_execute.append(alignment_output_file)
    pretty_alignment_file = File()
    pretty_alignment_file.user_id = dataset.user_id    
    pretty_alignment_file.parent_id = alignment_file.id 
    pretty_alignment_file.path = '{}.pretty.txt'.format(alignment_file.path)
    pretty_alignment_file.file_type = 'MIXCR_PRETTY_ALIGNMENT_TEXT'
    pretty_alignment_file.name =  '{}.pretty.txt'.format(alignment_file.name)
    pretty_alignment_file.command = 'mixcr exportAlignmentsPretty {} {}'.format(alignment_file.path, pretty_alignment_file.path)
    files_to_execute.append(pretty_alignment_file)
    analysis.status = 'EXECUTING'
    db.session.commit()
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = files[0].chain
        print 'Executing: {}'.format(f.command)
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL 
        response = os.system(f.command)
        print 'Response: {}'.format(response)
        if response == 0: 
            f.available = True 
            f.file_size = os.path.getsize(f.path)
            db.session.commit()
        else:
            f.available = False
            analysis.status = 'FAILED'
            db.session.commit()
    print 'All commands in analysis {} have been executed.'.format(analysis)
    if set(map(lambda f: f.available, files_to_execute)) == {True}:
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'
    db.session.commit()
    # KICK OFF ASYNC DB INSERTS FROM OUTPUT FILES
    # parseable_mixcr_alignments_file_path = alignment_output_file.path
    # PARSE WITH parse_and_insert_mixcr_annotation_dataframe_from_file_path to speed up? 
    # if not analysis.status == 'FAILED': result = parse_and_insert_mixcr_annotations_from_file_path(parseable_mixcr_alignments_file_path, dataset_id=analysis.dataset.id, analysis_id=analysis.id)
    return True 

@celery.task
def parse_and_insert_mixcr_annotations_from_file_path(file_path, dataset_id=None, analysis_id=None):
    print 'Building annotations from mixcr output at {}, then inserting into postgres in batches'.format(file_path)
    if analysis_id: 
        analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    else: 
        analysis = None 
    if analysis: analysis.db_status = 'BUILDING ANNOTATIONS'
    if analysis: analysis.status = 'INSERTING TO DB'
    db.session.commit()
    annotations = build_annotations_from_mixcr_file(file_path, dataset_id=dataset_id, analysis_id=analysis_id)
    total_count = len(annotations) 
    if analysis: analysis.total_count = total_count
    db.session.commit()
    for i,a in enumerate(annotations): 
        db.session.add(a)
        if i % 1000 == 0:
            print "Inserting # {} and the previous 1000 annotations to postgres. Here's what it looks like: {}".format(i, a.__dict__)
            percent_done = float(i) / float(total_count)
            if analysis: analysis.db_status = '{} Annotations Inserted in DB,  {} Percent Done'.format(i, int(percent_done * 100))
            db.session.commit()
    if analysis: 
        analysis.db_status = 'Finished. {} Annotations Inserted'.format(len(annotations))
        analysis.status = 'Complete'
    db.session.commit()
    result = annotate_analysis_from_db.apply_async((analysis.id, ), queue=celery_queue)
    return len(annotations)


@celery.task
def parse_and_insert_mixcr_annotation_dataframe_from_file_path(file_path, dataset_id=None, analysis_id=None):
    print 'Building annotation dataframe from mixcr output at {}, then inserting into postgres'.format(file_path)
    if analysis_id: 
        analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    else: 
        analysis = None 
    if analysis: analysis.db_status = 'BUILDING ANNOTATIONS'
    if analysis: analysis.status = 'BUILDING DATABASE'
    db.session.commit()
    annotation_df = build_annotation_dataframe_from_mixcr_file(file_path, dataset_id=dataset_id, analysis_id=analysis_id)
    print "Inserting annotation dataframe to postgres"
    if analysis: analysis.total_count = len(annotation_df)
    if analysis: analysis.db_status = 'INSERTING'
    if analysis: analysis.status = 'INSERTING TO DB'
    db.session.commit()
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    annotation_df.to_sql('annotation', engine, if_exists='append')
    if analysis: 
        analysis.db_status = 'Finished. {} Annotations Inserted'.format(len(annotation_df))
    db.session.commit()
    result = annotate_analysis_from_db.apply_async((analysis.id, ), queue=celery_queue)
    return True



@celery.task
def annotate_analysis_from_db(analysis_id): 
    analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    if not analysis: 
        return False 
    else: 
        analysis.vdj_count = 0
        analysis.vj_count = 0
        analysis.tcra_count = 0
        analysis.tcrb_count = 0
        analysis.status = 'FINISHED'
        analysis.db_status = 'Inserted and Re-analyzed'
        analysis.available = True 
        db.session.commit()





@celery.task
def run_pandaseq_with_dataset_id(dataset_id, analysis_name='', analysis_description='', user_id=6, algorithm='pear'):
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    print 'RUNNING MIXCR ON DATASET ID# {}: {}'.format(dataset_id, repr(dataset.__dict__))
    analysis = Analysis()
    analysis.db_status = "We dont currently import raw or pandaseq'd FASTQ Data"
    analysis.name = analysis_name
    analysis.description = analysis_description
    analysis.user_id = user_id
    analysis.dataset_id = dataset.id
    analysis.program = 'pandaseq'
    analysis.started = 'now'
    analysis.params = {}
    analysis.status = 'QUEUED'
    analysis.responses = []
    analysis.available = False
    analysis.inserted_into_db = False
    db.session.add(analysis)
    data_files_by_chain = {}
    for key, values in itertools.groupby(dataset.primary_data_files(), lambda x: x.chain): 
        data_files_by_chain[key] = list(values)
    dataset.primary_data_files_ids = [] 
    db.session.add(dataset)
    db.session.commit()
    print "Running pandaseq in these batches of files (sorted by file.chain): {}".format(data_files_by_chain)
    for chain, files in data_files_by_chain.items(): 
        if len(files) == 2: 
            print 'ABOUT TO RUN PANDASEQ CONCATENATION ON {} FILES FROM CHAIN {}'.format(len(files), chain)
            run_pandaseq_analysis_with_files(analysis, files, algorithm=algorithm)
        else: 
            print 'bad request for pandaseq alignment of only {} files'.format(len(files))
    return True 



@celery.task
def run_pandaseq_analysis_with_files(analysis, files, algorithm='pear'):
    dataset = analysis.dataset
    files_to_execute = []
    print 'RUNNING PANDASEQ ON THESE FILES: {}'.format(files)
    scratch_path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
    basename = files[0].path.split('/')[-1].split('.')[0]
    basepath = '{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    output_files = []
    # Instantiate Source Files
    alignment_file = File()
    alignment_file.user_id = dataset.user_id
    alignment_file.path = '{}.pandaseq_{}.fastq'.format(basepath, algorithm)
    alignment_file.name = "{}.pandaseq_{}.fastq".format(basename, algorithm)
    alignment_file.command = 'pandaseq -f {} -r {} -F -T 4 -A {} -w {} 2> {}.log'.format(files[0].path, files[1].path, algorithm, alignment_file.path, alignment_file.path)
    alignment_file.file_type = 'PANDASEQ_ALIGNED_FASTQ'
    files_to_execute.append(alignment_file)
    analysis.status = 'EXECUTING'
    db.session.commit()
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = files[0].chain
        print 'Executing: {}'.format(f.command)
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL 
        response = os.system(f.command)
        print 'Response: {}'.format(response)
        if response == 0: 
            f.available = True 
            f.file_size = os.path.getsize(f.path)
            dataset.primary_data_files_ids = [f.id]
            db.session.commit()
        else:
            f.available = False
            analysis.status = 'FAILED'
            db.session.commit()
    print 'All commands in analysis {} have been executed.'.format(analysis)
    if set(map(lambda f: f.available, files_to_execute)) == {True}:
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'
    db.session.commit()
    # Make PandaSeq Alignment Primary Dataset Data Files! Currently done in dataset.primary_data_files() 
    return True 






def run_trim_analysis_with_files(analysis, files):
    dataset = analysis.dataset
    files_to_execute = []
    print 'RUNNING TRIMMAMATIC ON THESE FILES: {}'.format(files)
    scratch_path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
    basename = files[0].path.split('/')[-1].split('.')[0]
    basepath = analysis.directory   #'{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    output_files = []
    # Instantiate Source Files
    if len(files) == 1: 
        output_file = File()
        output_file.user_id = dataset.user_id
        output_file.path = '{}.trimmed.fastq'.format(basepath)
        output_file.name = "{}.trimmed.fastq".format(basename)
        output_file.command = '{} SE -phred33 -threads 4 {} {} ILLUMINACLIP:{}/TruSeq3-SE.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:50'.format(app.config['TRIMMAMATIC'], files[0].path, output_file.path, app.config['TRIMMAMATIC_ADAPTERS'])
        output_file.file_type = 'TRIMMED_FASTQ'
        files_to_execute.append(output_file)
    if len(files) == 2: 
        r1_output_file = File()
        r1_output_file.user_id = dataset.user_id
        r1_output_file.path = '{}.R1.trimmed.fastq'.format(basepath)
        r1_output_file.name = "{}.R2.trimmed.fastq".format(basename)
        r1_output_file.file_type = 'TRIMMED_FASTQ'
        r2_output_file = File()
        r2_output_file.user_id = dataset.user_id
        r2_output_file.path = '{}.R1.trimmed.fastq'.format(basepath)
        r2_output_file.name = "{}.R2.trimmed.fastq".format(basename)
        r2_output_file.file_type = 'TRIMMED_FASTQ'
        r1_output_file.command = '{} PE -phred33 -threads 4 {} {} {} {} {} {} ILLUMINACLIP:{}/TruSeq3-PE.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:50'.format(app.config['TRIMMAMATIC'], files[0].path, files[1].path, r1_output_file.path, '/dev/null', r2_output_file.path, '/dev/null', app.config['TRIMMAMATIC_ADAPTERS'])
        r2_output_file.command = ''
        files_to_execute.append(r1_output_file)
        files_to_execute.append(r2_output_file)
    analysis.status = 'EXECUTING TRIM'
    db.session.commit()
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = files[0].chain
        print 'Executing: {}'.format(f.command)
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL 
        response = os.system(f.command)
        print 'Response: {}'.format(response)
        if response == 0: 
            f.available = True 
            f.in_use = False
            f.file_size = os.path.getsize(f.path)
            db.session.commit()
            output_files.append(f)
        else:
            f.available = False
            f.in_use = False 
            analysis.status = 'FAILED'
            db.session.commit()
    print 'Trim job for analysis {} has been executed.'.format(analysis)
    return output_files 






def run_usearch_cluster_fast_on_analysis_file(analysis, file, identity=0.9):
    dataset = analysis.dataset
    files_to_execute = []
    print 'RUNNING USEARCH CLUSTERING ON THIS FILE: {}'.format(file)
    scratch_path = '/{}'.format('/'.join(file.path.split('/')[:-1]))
    basename = file.path.split('/')[-1].split('.')[0]
    basepath = '{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    output_files = []
    # Instantiate Source Files
    consensus_output_file = File()
    consensus_output_file.user_id = dataset.user_id
    consensus_output_file.path = '{}.uclust_consensus.fasta'.format(basepath)
    consensus_output_file.name = "{}.uclust_consensus.fasta".format(basename)
    consensus_output_file.command = ""
    consensus_output_file.file_type = 'CLUSTERED_CONSENSUS_FASTA'
    uclust_output_file = File()
    uclust_output_file.user_id = dataset.user_id
    uclust_output_file.path = '{}.uclust.tab'.format(basepath)
    uclust_output_file.name = "{}.uclust.tab".format(basename)
    uclust_output_file.command = ""
    uclust_output_file.file_type = 'UCLUST_OUTPUT_TAB_TEXT'
    centroid_output_file = File()
    centroid_output_file.user_id = dataset.user_id
    centroid_output_file.path = '{}.uclust_centroids.fasta'.format(basepath)
    centroid_output_file.name = "{}.uclust_centroids.fasta".format(basename)
    centroid_output_file.file_type = 'CLUSTERED_CENTROIDS_FASTA'
    centroid_output_file.command = "usearch -cluster_fast {} -id {} -centroids {} -consout {} -uc {}".format(file.path, identity, centroid_output_file.path, consensus_output_file.path, uclust_output_file.path)
    files_to_execute.append(centroid_output_file)
    files_to_execute.append(consensus_output_file)
    files_to_execute.append(uclust_output_file)
    analysis.status = 'EXECUTING USEARCH'
    db.session.commit()
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = file.chain
        print 'Executing: {}'.format(f.command)
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL 
        response = os.system(f.command)
        print 'Response: {}'.format(response)
        if response == 0: 
            f.available = True 
            f.in_use = False
            f.file_size = os.path.getsize(f.path)
            db.session.commit()
        else:
            f.available = False
            f.in_use = False 
            analysis.status = 'FAILED'
            db.session.commit()
    print 'Uclust job for analysis {} has been executed.'.format(analysis)
    return files_to_execute


@celery.task
def run_analysis(dataset_id, file_ids, user_id, analysis_type='IGFFT', analysis_name='', analysis_description='', trim=False, overlap=False, paired=False, cluster=False, cluster_setting=[0.85,0.9,.01]): 
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    print 'RUNNING {} ANALYSIS ON DATASET ID# {}: {}'.format(analysis_type, dataset_id, repr(dataset.__dict__))
    #CONSTRUCT AND SAVE ANALYSIS OBJECT
    analysis = Analysis()
    analysis.name = analysis_name
    analysis_description = analysis_description
    # analysis.db_status = 'WAITING'
    analysis.user_id = user_id
    analysis.dataset_id = dataset.id
    analysis.program = analysis_type
    analysis.started = 'now'
    analysis.files_to_analyze = map(lambda i: int(i), file_ids)
    analysis.params = {}
    analysis.status = 'QUEUED'
    analysis.responses = []
    analysis.available = False
    analysis.inserted_into_db = False
    db.session.add(analysis)
    db.session.commit()
    if dataset.directory:
        analysis.directory = dataset.directory + '/Analysis_' + str(analysis.id)
    else: 
        analysis.directory = analysis.dataset.user.scratch_path + '/Analysis_' + str(analysis.id)
    if not os.path.exists(analysis.directory):
        os.makedirs(analysis.directory)
    files = map(lambda x: db.session.query(File).filter(File.id==x).first(), file_ids)
    
    print 'Analysis Output Set To {}'.format(analysis.directory)
    print 'Using these files: {}'.format(files)
    if trim:
        print 'Running Trim on Files in Analysis {} before executing annotation'.format(analysis.id)
        analysis.status = 'TRIMMING FILES' 
        db.session.commit() 
        files = run_trim_analysis_with_files(analysis, files)
    # GENERATE OVERLAPS 
    # if overlap: 

    #Execute Analysis 
    # if analysis_type == 'MIXCR': 
    #     if overlap == True: 
    #         print 'ABOUT TO RUN MIXCR ANALYSIS {} ON FILES'.format(repr(analysis))
    #         run_mixcr_analysis_id_with_files(analysis.id, files)

    if analysis_type == 'IGFFT':
        files_for_analysis = [] 
        for file in files: 
            #IGFFT NEEDS UNCOMPRESSED FASTQs
            if file.file_type == 'GZIPPED_FASTQ': 
                new_file = File()
                new_file.user_id = user_id
                new_file.parent_id = file.id 
                new_file.path = analysis.directory + '/' + file.name.replace('.gz','')
                new_file.file_type = 'FASTQ'
                new_file.available = False
                new_file.name =  file.name.replace('.gz', '')
                new_file.command = 'gunzip -c {} > {}'.format(file.path, new_file.path)
                analysis.status = 'GUNZIPPING'
                db.session.commit()
                response = os.system(new_file.command)
                if response == 0: 
                    new_file.available = True 
                    db.session.add(new_file)
                    db.session.commit()
                    files_for_analysis.append(new_file)
                else: 
                    print 'ERROR GUNZIPPING FILE {}: '.format(file.path, new_file.command)
            else: 
                files_for_analysis.append(new_file)
        analysis.status = 'EXECUTING'
        db.session.add(analysis)
        db.session.commit()
        if files_for_analysis == []: files_for_analysis = files 
        annotated_files = run_igrep_annotation_on_dataset_files(dataset, files_for_analysis, user_id = dataset.user_id, overlap=overlap, paired=paired, cluster=cluster, cluster_setting=cluster_setting)
        print 'annotated files from igfft: {}'.format(annotated_files)
    # PAIR 
    # CLUSTER


def run_igrep_annotation_on_dataset_files(dataset, files, user_id, overlap=False, paired=False, cluster=False, cluster_setting=[0.85,0.9,.01]):
    # dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    print 'RUNNING IGREP IGFFT ON DATASET ID# {}: {}'.format(dataset.id, repr(dataset.__dict__))
    igrep_script_path = app.config['IGREP_PIPELINES']
    # LOAD IGREP SCRIPTS INTO PYTHON PATH

    if dataset.species == 'Human': species = 'homosapiens' 
    if dataset.species == 'Mouse': species = 'musmusculus' 
    annotated_files = []
    for file in files: 
        if file.chain == 'HEAVY': loci = 'igh'
        if file.chain == 'LIGHT': loci = 'igk,igl'
        if file.chain == 'HEAVY/LIGHT': loci = 'igh,igk,igl'

        # annotated_f = igfft.igfft_multiprocess(f.path, file_type='FASTQ', species=species, locus=loci, parsing_settings={'isotype': isotyping_barcodes, 'remove_insertions': remove_insertions}, num_processes=number_threads, delete_alignment_file=True)           
        # annotated_files.append(annotated_f[0])
        try: 
            species 
        except: 
            species = 'homosapiens'
        try: 
            loci 
        except: 
            loci = 'igh,igk,igl'
        script_command = 'python {}/gglab_igfft_single.py -species {} -locus {} {}'.format(igrep_script_path, species, loci, file.path)
        print 'executing script: {}'.format(script_command)
        response = os.system(script_command)
        new_file = File()
        new_file.user_id = user_id
        new_file.parent_id = file.id 
        new_file.dataset_id = dataset.id 
        new_file.name = file.name.replace('fastq','igfft.annotation')
        new_file.path = file.path.replace('fastq','igfft.annotation')
        new_file.file_type = 'IGFFT_ANNOTATION'
        new_file.created='now'
        new_file.available=True 
        db.session.add(new_file)
        db.session.commit()
        annotated_files.append(new_file)

    return annotated_files 


# should really break out tasks to celery_tasks.py or something 
@celery.task
def add(x, y):
    # some long running task here
    return x + y 

@celery.task
def send_async_email(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)

@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
    # total = 100 
    # for i in range(total): 
    #     message = ''
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}

# function to flash error messages from forms automatically
def flash_errors( form, category="warning" ):
    '''Flash all errors for a form.'''
    for field, errors in form.errors.items():
        for error in errors:
            flash("{0} - {1}".format( getattr( form, field ).label.text, error ), category )

# @Dave - function to create datasets from a JSON url
def create_datasets_from_JSON_url(url, project):
    # get the url
    # download the file
    # convert to a string
    # call create_datasets_from_JSON_string(json_string, project)
    pass

# @Dave - function to create datasets from a JSON file
# If the project is give, the datasets are added to the project
def create_datasets_from_JSON_string(json_string, project = None):

    json_counter = 0    
    json_expected_fields = ["LAB_NOTEBOOK_SOURCE", "SEQUENCING_SUBMISSION_NUMBER", 
        "CHAIN_TYPES_SEQUENCED", "CONTAINS_RNA_SEQ_DATA", "REVERSE_PRIMER_USED_IN_RT_STEP", 
        "LIST_OF_POLYMERASES_USED", "SEQUENCING_PLATFORM", "VH:VL_PAIRED", "PROJECT_NAME", 
        "TARGET_READS", "CELL_MARKERS_USED", "READ_ACCESS", "ADJUVANT", "CELL_TYPES_SEQUENCED", 
        "SPECIES", "PUBLICATIONS", "OWNERS_OF_EXPERIMENT", "CELL_SELECTION_KIT_NAME", 
        "ISOTYPES_SEQUENCED", "SAMPLE_PREPARATION_DATE", "GSAF_BARCODE", "MID_TAG", 
        "DESCRIPTION", "CELL_NUMBER", "PRIMER_SET_NAME", "LAB", "TEMPLATE_TYPE", "EXPERIMENT_NAME", 
        "PERSON_WHO_PREPARED_LIBRARY", "PAIRING_TECHNIQUE", "_id"]

    # The following fields are lists which are joined with a space, comma, or in a dictionary
    json_flatten_fields = ["SEQUENCING_SUBMISSION_NUMBER",  "MID_TAG", "DESCRIPTION", "PRIMER_SET_NAME", "LAB", "PERSON_WHO_PREPARED_LIBRARY"]
    json_comma_fields = ["CHAIN_TYPES_SEQUENCED", "LIST_OF_POLYMERASES_USED", "CELL_MARKERS_USED", "CELL_TYPES_SEQUENCED", "PUBLICATIONS", "ISOTYPES_SEQUENCED"]
    json_psp_fields = ["POST_SEQUENCING_PROCESSING:PHI_X_FILTER", "POST_SEQUENCING_PROCESSING:PROCESS_R1_R2_FILE", "POST_SEQUENCING_PROCESSING:QUALITY_FILTER"]

    try: json_data = json.loads(json_string)
    except ValueError, error: return "Error loading JSON: {}".format(error)

    if not json_data: return "Error: no JSON data found."
    if "user_data" not in json_data: return "No user_data field found in JSON data."

    user_data = json_data['user_data']
    if "description" not in user_data: return "No description of user_data found in JSON data."

    user_data_description = user_data['description']
    if 'GGLAB_DB_FIELDS' not in user_data_description: return "No GGLAB_DB_FIELDS in user_data description of JSON data."

    json_dataset_array = user_data_description['GGLAB_DB_FIELDS']
    for json_dataset in json_dataset_array:

        # first, check and make sure all of the fields we want are present
        for field in json_expected_fields:
            if field not in json_dataset:
                json_dataset[field] = ""
                print "Warning: field '{}' not found in GGLAB_DB_FIELDS".format(field)

        # next, some up with a name for the dataset
        dataset_name = None
        try:
            if json_dataset['DESCRIPTION'][1]:    
                dataset_name = json_dataset['DESCRIPTION'][1]
            else:
                dataset_name = 'Dataset ' + str(json_counter)
                json_counter = json_counter + 1 
        except:
            dataset_name = 'Dataset ' + str(json_counter)
            json_counter = json_counter + 1 

        post_sequencing_processing = {}
        for field in json_expected_fields:    
            if field in json_flatten_fields and type(json_dataset[field]) == list: # flatten lists here
                json_dataset[field] = " ".join(json_dataset[field])
            if field in json_comma_fields and type(json_dataset[field]) == list: # flatten comma lists here    
                json_dataset[field] = ", ".join(json_dataset[field])
            if field in json_psp_fields and field in json_dataset: # flatten special fields here
                post_sequencing_processing[field] = json_dataset[field]
        
        post_sequencing_processing = str(post_sequencing_processing)
        
        contains_rna_seq_data = False
        if json_dataset[ "CONTAINS_RNA_SEQ_DATA" ] == "True":
            contains_rna_seq_data = True

        new_dataset = Dataset()
        
        new_dataset.user_id = current_user.id
        new_dataset.name = dataset_name
        new_dataset.description = json_dataset[ "DESCRIPTION" ]
        new_dataset.ig_type = ""


        # special treatment for arrays
        try:
            new_dataset.cell_types_sequenced = ast.literal_eval(str(json_dataset[ "CELL_TYPES_SEQUENCED" ]))
        except:
            new_dataset.cell_types_sequenced = [str(json_dataset[ "CELL_TYPES_SEQUENCED" ])] 

        try: 
            new_dataset.chain_types_sequenced = ast.literal_eval(str(json_dataset[ "CHAIN_TYPES_SEQUENCED" ]))
        except: 
            new_dataset.chain_types_sequenced = [str(json_dataset[ "CHAIN_TYPES_SEQUENCED" ])]

        try:
            new_dataset.primary_data_files_ids = ast.literal_eval(str(dataset.primary_data_files_ids))
        except:
            if str(json_dataset[ "LAB_NOTEBOOK_SOURCE" ]).isdigit():
                new_dataset.primary_data_files_ids = [int(json_dataset[ "LAB_NOTEBOOK_SOURCE" ])]
            else:
                new_dataset.lab_notebook_source = json_dataset[ "LAB_NOTEBOOK_SOURCE" ]


        new_dataset.sequencing_submission_number = json_dataset[ "SEQUENCING_SUBMISSION_NUMBER" ]
        new_dataset.contains_rna_seq_data = contains_rna_seq_data
        new_dataset.reverse_primer_used_in_rt_step = json_dataset[ "REVERSE_PRIMER_USED_IN_RT_STEP" ]
        new_dataset.list_of_polymerases_used = json_dataset[ "LIST_OF_POLYMERASES_USED" ]
        new_dataset.sequencing_platform = json_dataset[ "SEQUENCING_PLATFORM" ]
        new_dataset.target_reads = json_dataset[ "TARGET_READS" ]
        new_dataset.cell_markers_used = json_dataset[ "CELL_MARKERS_USED" ]
        new_dataset.adjuvant = json_dataset[ "ADJUVANT" ]
        new_dataset.species = json_dataset[ "SPECIES" ]
        new_dataset.cell_selection_kit_name = json_dataset[ "CELL_SELECTION_KIT_NAME" ]
        new_dataset.isotypes_sequenced = json_dataset[ "ISOTYPES_SEQUENCED" ]
        new_dataset.sample_preparation_date = json_dataset[ "SAMPLE_PREPARATION_DATE" ]
        new_dataset.gsaf_barcode = json_dataset[ "GSAF_BARCODE" ]
        new_dataset.mid_tag = json_dataset[ "MID_TAG" ]
        new_dataset.cell_number = json_dataset[ "CELL_NUMBER" ]
        new_dataset.primer_set_name = json_dataset[ "PRIMER_SET_NAME" ]
        new_dataset.template_type = json_dataset[ "TEMPLATE_TYPE" ]
        new_dataset.experiment_name = json_dataset[ "EXPERIMENT_NAME" ]
        new_dataset.person_who_prepared_library = json_dataset[ "PERSON_WHO_PREPARED_LIBRARY" ]
        new_dataset.pairing_technique = json_dataset[ "PAIRING_TECHNIQUE" ]
        new_dataset.json_id = json_dataset[ "_id" ]
        new_dataset.paired = json_dataset[ "VH:VL_PAIRED" ]
        new_dataset.read_access = str(json_dataset[ "READ_ACCESS" ])
        new_dataset.owners_of_experiment = str(json_dataset[ "OWNERS_OF_EXPERIMENT" ])

        db.session.add(new_dataset)
        db.session.flush()
        db.session.refresh(new_dataset)

        if project:
            new_relationship = ProjectDatasets(new_dataset, project)
            db.session.add(new_relationship)
            db.session.flush()
        else:
            print "Warning: new dataset {} not added to any project".format(new_dataset.id)

        if current_user:
            current_user.datasets.append(new_dataset)
            db.session.flush()
            db.session.refresh(current_user)

    return None

######
#
# Imports @ End - to prevent circular imports
#
######

# import blueprint routes here
from frontend import *
from projects import *
app.register_blueprint(frontend)
app.register_blueprint(projects_blueprint)

nav.init_app(app)



if __name__ == '__main__':
    print 'Running application on port 5000......'
    app.run(host='0.0.0.0', port=5000, debug=True)


