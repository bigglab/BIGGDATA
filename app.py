#System Imports
import json
import static
import sys
import os
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
from celery import Celery
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
 

# Initialize Application
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
# Initialize extensions
bcrypt = Bcrypt(app)
nav = Nav() 
Bootstrap(app) 

db = SQLAlchemy(app)

# Celery configured for local RabbitMQ 
celery = Celery(app.name, broker='amqp://')
import celery_config 
celery.config_from_object('celery_config')

# Local Imports - local imports go here to prevent circular imports 
from forms import *
from functions import * 
from models import * 

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
    gifs_dir = '{}/static/goldens'.format(app.config['HOME'])
    gifs = os.listdir(gifs_dir)
    gif = random.choice(gifs)
    gif_path = url_for('static', filename='goldens/{}'.format(gif))
    return gif_path

@login_manager.unauthorized_handler
def unauthorized():
    gif_path=retrieve_golden()
    return render_template("unauthorized.html", git_path=gif_path)

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
        datadict[dataset] = sorted(dataset.files.all(), key=lambda x: x.file_type)
    return datadict

@celery.task 
def import_from_sra(accession, name=None, user_id=57):
    user = db.session.query(User).filter(User.id==user_id).first()
    if not name: 
        name = accession 
    print 'Fetching SRA data from NCBI {}'.format(accession)
    command = 'fastq-dump --gzip --split-files -T --outdir {} {}'.format(user.scratch_path, accession) 
    response = os.system(command)
    if response == 0: 
        file_paths = []
        dirs = os.listdir('{}/{}'.format(user.scratch_path, accession))
        if dirs == ['1']:
            file_paths = ['{}/{}/1/fastq.gz'.format(user.scratch_path, accession)]
            filename_array = ['{}.fastq.gz'.format(accession)]
        if dirs == ['1','2'] or dirs == ['2','1']:
            file_paths = ['{}/{}/1/fastq.gz'.format(user.scratch_path, accession), '{}/{}/2/fastq.gz'.format(user.scratch_path, accession)]
            filename_array = ['{}.R1.fastq.gz'.format(accession), '{}.R2.fastq.gz'.format(accession)]
        else: 
            print 'Number of files from SRA export not one or two...'
            return False 
    print 'Writing sra output files to {}'.format(user.scratch_path)
    dataset = import_files_as_dataset(file_paths, filename_array=filename_array, user_id=user_id, name=name)
    print 'Dataset from SRA Accession {} created for user {}'.format(accession, user.username) 
    return True

@celery.task 
def import_files_as_dataset(filepath_array, filename_array=None, chain=None, user_id=57, name=None):
    d = Dataset()
    d.user_id = user_id
    d.name = name
    d.description = 'Dataset generated from file import'
    d.chain_types_sequenced = [chain]
    db.session.add(d)
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
    print 'urllib2 downloading file from {}'.format(url)
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
    alignment_file.path = '{}.aln.vdjca'.format(basepath)
    alignment_file.name = "{}.aln.vdjca".format(basename)
    # MIGHT NEED TO ADD THIS ARGUMENT to align   -OjParameters.parameters.mapperMaxSeedsDistance=5
    alignment_file.command = 'mixcr align --save-description -f {} {}'.format(' '.join([f.path for f in files]), alignment_file.path)
    alignment_file.file_type = 'MIXCR_ALIGNMENTS'
    files_to_execute.append(alignment_file)
    clone_file = File()
    clone_file.file_type = 'MIXCR_CLONES'
    clone_file.path = '{}.aln.clns'.format(basepath)
    clone_file.name = '{}.aln.clns'.format(basename)
    clone_file.command = 'mixcr assemble -f {} {}'.format(alignment_file.path, clone_file.path)
    files_to_execute.append(clone_file)
    db.session.add(alignment_file)
    db.session.add(clone_file)
    db.session.commit()
    # Commit To Get Parent IDs
    clone_output_file = File()
    clone_output_file.parent_id = clone_file.id 
    clone_output_file.path = '{}.txt'.format(clone_file.path)
    clone_output_file.file_type = 'MIXCR_CLONES_TEXT'
    clone_output_file.name = '{}.txt'.format(clone_file.name)
    clone_output_file.command = 'mixcr exportClones {} {}'.format(clone_file.path, clone_output_file.path)
    files_to_execute.append(clone_output_file)
    alignment_output_file = File()
    alignment_output_file.parent_id = alignment_file.id
    alignment_output_file.path = '{}.txt'.format(alignment_file.path)
    alignment_output_file.file_type = 'MIXCR_ALIGNMENT_TEXT'
    alignment_output_file.name = '{}.txt'.format(alignment_file.name)
    alignment_output_file.command = 'mixcr exportAlignments  -readId -descrR1 --preset full  {} {}'.format(alignment_file.path, alignment_output_file.path)
    files_to_execute.append(alignment_output_file)
    pretty_alignment_file = File()
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
    parseable_mixcr_alignments_file_path = alignment_output_file.path
    # PARSE WITH parse_and_insert_mixcr_annotation_dataframe_from_file_path to speed up? 
    if not analysis.status == 'FAILED': result = parse_and_insert_mixcr_annotation_dataframe_from_file_path(parseable_mixcr_alignments_file_path, dataset_id=analysis.dataset.id, analysis_id=analysis.id)
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
    db.session.commit()
    result = annotate_analysis_from_db.apply_async((analysis.id, ), queue='default')
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
    result = annotate_analysis_from_db.apply_async((analysis.id, ), queue='default')
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
    db.session.commit()
    data_files_by_chain = {}
    for key, values in itertools.groupby(dataset.primary_data_files(), lambda x: x.chain): 
        data_files_by_chain[key] = list(values)
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
    basepath = '{}/{}'.format(scratch_path, basename)
    print 'Writing output files to base name: {}'.format(basepath)
    output_files = []
    # Instantiate Source Files
    if len(files) == 1: 
        output_file = File()
        output_file.path = '{}.trimmed.fastq'.format(basepath)
        output_file.name = "{}.trimmed.fastq".format(basename)
        output_file.command = '{} SE -phred33 -threads 4 {} {} ILLUMINACLIP:{}/TruSeq3-SE.fa:2:30:10 LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:50'.format(app.config['TRIMMAMATIC'], files[0].path, output_file.path, app.config['TRIMMAMATIC_ADAPTERS'])
        output_file.file_type = 'TRIMMED_FASTQ'
        files_to_execute.append(output_file)
    if len(files) == 2: 
        r1_output_file = File()
        r1_output_file.path = '{}.R1.trimmed.fastq'.format(basepath)
        r1_output_file.name = "{}.R2.trimmed.fastq".format(basename)
        r1_output_file.file_type = 'TRIMMED_FASTQ'
        r2_output_file = File()
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
        else:
            f.available = False
            f.in_use = False 
            analysis.status = 'FAILED'
            db.session.commit()
    print 'Trim job for analysis {} has been executed.'.format(analysis)
    return files 






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
    consensus_output_file.path = '{}.uclust_consensus.fasta'.format(basepath)
    consensus_output_file.name = "{}.uclust_consensus.fasta".format(basename)
    consensus_output_file.command = ""
    consensus_output_file.file_type = 'CLUSTERED_CONSENSUS_FASTA'
    uclust_output_file = File()
    uclust_output_file.path = '{}.uclust.tab'.format(basepath)
    uclust_output_file.name = "{}.uclust.tab".format(basename)
    uclust_output_file.command = ""
    uclust_output_file.file_type = 'UCLUST_OUTPUT_TAB_TEXT'
    centroid_output_file = File()
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

# import blueprint routes here
from frontend import *
app.register_blueprint(frontend)
nav.init_app(app)



if __name__ == '__main__':
    print 'Running application on port 5000......'
    app.run(host='0.0.0.0', port=5000, debug=True)


