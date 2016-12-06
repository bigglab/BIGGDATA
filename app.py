#System Imports
import ast
import errno
import json
import logging
import os
import random
import re
import static
import sys
import tarfile
import time
from shutil import copyfile
import operator
import datetime as dt
import shlex
import hashlib
os.environ['http_proxy']=''
import urllib2
import itertools
import subprocess
import boto 
import math 
# from filechunkio import FileChunkIO 
from celery import Celery, Task, states
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger, ColorFormatter

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

#####
#
# Add IGREP binaries to system path
#
#####
sys.path.append('/data/resources/software/IGREP/common_tools/')
import immunogrep_msdb
import immunogrep_gglab_pairing as pairing
import immunogrep_ngs_pair_tools as processing



# Initialize Application
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
# Initialize extensions
bcrypt = Bcrypt(app)
nav = Nav() 
Bootstrap(app) 

db.init_app(app)
db.app = app 

mail = Mail(app)

#####
#
# Information about the Flask-SQLAlchemy API here: http://flask-sqlalchemy.pocoo.org/2.1/api/
#
#####

engine = db.engine
Session = sessionmaker(bind=engine)

# Session Scope
# Allows automation of session creation and closure.
# Usage:
# with session_scope() as session:
#     session.flush() # etc, etc...
from contextlib import contextmanager
@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()

    event.listen(session, 'before_flush', validate_file_object)
    event.listen(session, 'before_commit', validate_file_object)

    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def expunge_session_objects(session):
    obj_list = []
    for obj in session:
        session.refresh(obj)
        session.expunge(obj)
        obj_list.append(obj)
    return obj_list

def add_session_objects(session, obj_list):
    for obj in obj_list:
        session.add(obj)

def run_my_program():
#    print 'Creating new file.'
    with session_scope() as session:
        new_file = File()
        new_file.name = 'Test.'
        session.add(new_file)
    return

#run_my_program()

#####


# Celery configured for local RabbitMQ 
celery = Celery(app.name, broker='amqp://')
import celery_config 
celery.config_from_object('celery_config')

# CELERY QUEUE TO SEND JOBS TO - USE FOR DEVELOPMENT 
celery_queue = 'default'

# Add a celery logger.
# Usage:
#   logger.info('Your log message here.')
celery_logger = get_task_logger(__name__)

# change celery_queue to anything celery -Q

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


def initiate_celery_task_logger(logger_id, logfile):
    logger = get_task_logger( logger_id )
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    logger.handlers = []
    handler = logging.FileHandler( logfile )
    handler.setLevel( logging.INFO )

    formatter = ColorFormatter
    format = '[%(asctime)s: %(levelname)s] %(message)s'
    handler.setFormatter( formatter(format, use_color = False) )
    logger.addHandler(handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    format = '%(name)s: %(message)s'
    stdout_handler.setFormatter(formatter(format, use_color = True) )
    stdout_handler.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)

    return logger

# Base Class used for returning complex values
class ReturnValue():
    def __init__(self, return_string, **kwargs):
        self.return_string = return_string
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return self.return_string

# Used to redirect stdout to the logger
class LoggerWriter:
    def __init__(self, logger, level = logging.INFO):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message != '\n':
            self.logger.log(self.level, message)

# Used to redirect stdout to the logger
class VHVLPairingLoggerWriter(LoggerWriter):
    def __init__(self, logger, level = logging.INFO, task = None):
        self.logger = logger
        self.level = level
        self.task = task
        self.tracking_status = False

    def write(self, message):

        if self.task:
            # progress_pattern = re.compile('Processed (\d+) sequences')
            # pattern_match =  progress_pattern.match(message)
            # if pattern_match:

            #     progress = pattern_match.group(1)

            #     self.logger.info( "Pattern matched: {}".format(message) )

            #     if not self.tracking_status:
            #         self.tracking_status = True
            #     self.task.update_state(state='STATUS', meta={'status': message.strip() })


            # else:
            #     if self.tracking_status:
            #         self.tracking_status = False
            #         self.task.update_state(state='ANALYZING')
            LoggerWriter.write(self, message)

        else:
            LoggerWriter.write(self, message)



# Base Class used to log celery tasks to the database
class LogTask(Task):
    abstract = True

    user_found = False
    user_id = None
    celery_task = None
    logger = None
    request_id = None
    logfile = None

    # points to the top-level task if this is a child task
    # if this is the top-level task, parent_task == None
    parent_task = None
    maintain_log = True

    # points to the actual top-level task, either self or parent_task
    task = None

    def __call__(self, *args, **kw):

        # if a logger is passed in the kwargs, don't need to log this task separately
        if 'parent_task' in kw:
            self.maintain_log = False
            self.parent_task = kw['parent_task']
            self.logger = self.parent_task.logger
            self.request_id = self.parent_task.request_id
            celery_task = self.parent_task.celery_task
            del kw['parent_task']
            self.task = self.parent_task
        else:
            self.task = self

            self.celery_task = CeleryTask()
            logger_id = self.request.id
            self.request_id = self.request.id

            self.user_found = False
            with session_scope() as session:

                if 'user_id' in kw:
                    user_id = kw['user_id']
                    self.user_id = user_id
                    celery_logger.debug( 'User Id: {}'.format( user_id ) )
                    
                    try:
                        user = session.query(User).filter_by( id = user_id ).first()
                    except:
                        time.sleep(1)
                        user = session.query(User).filter_by( id = user_id ).first()

                    if user:
                        self.user_found = True
                        logfile = '{}/{}.log'.format( user.path.rstrip('/') , logger_id )
                        celery_logger.debug( 'Starting log file at {}'.format( logfile ) )
                    else:
                        user_found = False
                        celery_logger.warning( 'Warning({}): User ID ({}) not found. The decorator "log_celery_task" cannot log information without a user_id passed parametrically to the function decorated.'.format(f.func_name, kw['user_id']) )

                        if not os.path.isdir('/data/logs/'):
                            os.makedirs('/data/logs/')

                        logfile = '/data/logs/{}.log'.format( request_id )
                else:
                    celery_logger.warning( 'Warning({}): The decorator "log_celery_task" cannot log information without a user_id passed parametrically to the function decorated.'.format(self.__class__.__name__) )

                    if not os.path.isdir('/data/logs/'):
                        os.makedirs('/data/logs/')

                    logfile = '/data/logs/{}.log'.format( self.request_id )

                logger = initiate_celery_task_logger( logger_id = logger_id , logfile = logfile )
                self.logger = logger
                self.logfile = logfile

                # Initiate Database Record
                if self.user_found:
                    self.celery_task = CeleryTask()
                    self.celery_task.user_id = user_id
                    self.celery_task.name = self.__name__
                    self.celery_task.async_task_id = self.request_id
                    result = celery.AsyncResult(self.request_id)
                    self.celery_task.status = 'STARTED'

                    session.add(self.celery_task)
                    session.commit()

                    # send the object to a persistent state
                    session.expunge(self.celery_task)

                self.update_state(state='STARTED', meta={ 'status': 'Task Started' })

        return_value = self.run(*args, **kw)

        # If this is the top-level task, ensure the return value is JSON serializable (repr)
        if self.parent_task == None:
            return repr(return_value)
        else:
            return return_value

    def on_failure(self, exc, task_id, args, kwargs, einfo): 
        
        if self.maintain_log:
            with session_scope() as session:

                # Close Database Record
                if self.user_found:

                    exception_type_name = einfo.type.__name__
                    if exception_type_name == 'Exception':
                        exception_type_name = 'Error'

                    result = celery.AsyncResult(task_id)

                    # We are in a new session, so we have to re-add our persistent object
                    session.add(self.celery_task)

                    self.celery_task.status = 'FAILURE'
                    self.celery_task.result = '{}: {}'.format( exception_type_name , exc ) 
                    self.celery_task.is_complete = True                
                    self.celery_task.failed = True                

                    if self.celery_task.analysis:
                        analysis = self.celery_task.analysis

                        if not analysis.async_task_id:
                            analysis.async_task_id = self.request_id
                        if analysis.status == None or analysis.status in pending_analysis_states:
                            analysis.status = 'FAILURE'
                        analysis.finished = 'now'
                        analysis.error = self.celery_task.result
                        analysis.active_command = None
                        analysis.available = False

                        analysis_file_name_prefix = analysis.name.replace(' ', '_')

                        # Need a directory to save any logs
                        if not analysis.directory:
                            analysis.create_analysis_directory()

                        if analysis.directory:
                            # Save the log file
                            if self.logfile and os.path.isfile(self.logfile):
                                analysis_logfile_path = '{}/{}.log'.format( analysis.directory.rstrip('/'), analysis_file_name_prefix )
                                copyfile( self.logfile, analysis_logfile_path )
                            if os.path.isfile( analysis_logfile_path ):
                                analysis.log_file = File( path = analysis_logfile_path, file_type = 'LOG', dataset_id = analysis.dataset_id, analysis_id = analysis.id, user_id = self.user_id )

                            # Save the trackback
                            if einfo and einfo.traceback:
                                analysis_traceback_path = '{}/{}_traceback.txt'.format( analysis.directory.rstrip('/'), analysis_file_name_prefix )

                                with open(analysis_traceback_path, "w") as traceback_file:
                                    traceback_file.write(einfo.traceback)

                                if os.path.isfile( analysis_traceback_path ):
                                    analysis.traceback_file = File( path = analysis_traceback_path, file_type = 'TRACEBACK', dataset_id = analysis.dataset_id, analysis_id = analysis.id, user_id = self.user_id )

                    session.commit()

    def on_success(self, retval, task_id, args, kwargs):
        if self.maintain_log:

            with session_scope() as session:

                # Close Database Record
                if self.user_found:
                    result = celery.AsyncResult(task_id)
                    print 'On Success Result Status: {}'.format( result.status )

                    # We are in a new session, so we have to re-add our persistent object
                    session.add(self.celery_task)

                    session.merge(self.celery_task)                
                    self.celery_task.status = 'SUCCESS'
                    self.celery_task.result = str(retval)
                    self.celery_task.is_complete = True                

                    if self.celery_task.analysis:
                        analysis = self.celery_task.analysis

                        if not analysis.async_task_id:
                            analysis.async_task_id = self.request_id

                        if analysis.status == None or self.celery_task.analysis.status in pending_analysis_states:
                            analysis.status = 'SUCCESS'
                        analysis.finished = 'now'
                        analysis.active_command = None
                        analysis.available = True

                        analysis_file_name_prefix = analysis.name.replace(' ', '_')

                        # Need a directory to save any logs
                        if not analysis.directory:
                            analysis.create_analysis_directory()

                        if analysis.directory:
                            # Save the log file
                            if self.logfile and os.path.isfile(self.logfile):
                                analysis_logfile_path = '{}/{}.log'.format( analysis.directory.rstrip('/'), analysis_file_name_prefix )
                                copyfile( self.logfile, analysis_logfile_path )
                            if os.path.isfile( analysis_logfile_path ):
                                analysis.log_file = File( path = analysis_logfile_path, file_type = 'LOG', analysis_id = analysis.id, user_id = self.user_id )
                                if analysis.dataset:
                                    analysis.log_file.dataset_id = analysis.dataset.id

                    session.commit()

    # override update_state so that it goes to the appropriate task
    def update_state(self, *args, **kwargs):
        if self.parent_task:
            return self.parent_task.update_state(*args, **kwargs)
        else:
            return Task.update_state(self, *args, **kwargs)

    def set_analysis_id(self, analysis_id):
        task = self.task
        if task.maintain_log:

            with session_scope() as session:

                # Get Database Record
                if task.user_found:

                    print "Adding analysis id {} to celery task.".format(analysis_id)

                    # We are in a new session, so we have to re-add our persistent object
                    session.add(task.celery_task)
                    session.merge(task.celery_task)

                    task.celery_task.analysis_id = analysis_id
                    session.commit()

                    # send the object to a persistent state
                    session.expunge(task.celery_task)

def get_filepaths(directory_path):
    file_paths = []
    for root, directories, files in os.walk(directory_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths 

def get_files(user):
    path = user.path
    paths = get_filepaths(path)
    paths = [file_path for file_path in paths if file_path not in [file.path for file in user.files]]
    return paths

def get_dropbox_files(user):
    path = user.dropbox_path
    paths = get_filepaths(path)
    paths = [file_path for file_path in paths if file_path not in [file.path for file in user.files]]
    return paths

def tree(): return defaultdict(tree)

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
    # try:
        # share_root = app.config['SHARE_ROOT'] 
        # if os.path.isdir(share_root):
        #     files = os.listdir(share_root)
        # else:
        #     return 'Warning: share root path "{}"" not found'.format(share_root)
    #     print 'copying these files to new users dropbox: {}'.format(','.join(files))
    #     for f in files: 
    #         fullfilepath = '{}/{}'.format(new_user.path, f)
    #         copyfile('{}/{}'.format(share_root, f), '{}/{}'.format(new_user.path, f))
    #         link_file_to_user(fullfilepath, new_user.id, f)
    #     return False 
    # except ValueError, error:
    #     return 'Warning: unable to copy sample files into user\'s dropbox: {}'.format(error)

# @celery.task(base= LogTask, bind = True)
# def transfer_file_to_s3(self, file_id, user_id = None):
#     logger = self.logger
#     f = db.session.query(File).filter(File.id==file_id).first()
#     if not f: 
#         raise Exception( "File with ID ({}) not found.".format(file_id) )
#     else: 
#         if f.path:
#             if f.s3_path: 
#                 logger.info ('Transferring file from {} to {}'.format(f.path, f.s3_path) )
#             else: 
#                 f.s3_path = '{}'.format(f.path)
#                 logger.info( 'Transferring file from {} to s3://{}/{}'.format(f.path, app.config['S3_BUCKET'], f.s3_path) ) 
#                 f.s3_status = 'Staging'
#                 db.session.commit()
#         file_size = os.stat(f.path).st_size
#         logger.info ( 'starting transfer of {} byte file'.format(file_size) )
#         def cb(complete, total): 
#             f.s3_status = 'Transferred {} of {} bytes'.format(complete, total)
#             db.session.commit()
#         key = s3_bucket.new_key(f.s3_path)
#         result = key.set_contents_from_filename(f.path, cb=cb, num_cb=10)
#         key.set_canned_acl('public-read')
#         f.s3_status = "AVAILABLE"
#         db.session.commit()
#         return "Transfer complete. {} bytes transferred from {}  to  {}".format(result, f.path, f.s3_path)

def get_user_dataset_dict(user): 
    datadict = OrderedDict()
    for dataset in sorted(user.datasets, key=lambda x: x.id, reverse=True):
        if dataset.name != '__default__':
            datadict[dataset] = sorted(dataset.files.all(), key=lambda x: x.file_type)
    return datadict

@celery.task(base= LogTask, bind = True)
def import_from_sra(self, accession, name=None, user_id=57, chain=None, project_selection = None, dataset_selection = None):
    logger = self.logger
    user = db.session.query(User).filter(User.id==user_id).first()

    if not user:
        raise Exception( "Unable to find user with id {}.".format(user_id) )

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
        new_dataset.directory = "{}/Dataset_{}".format(user.path.rstrip('/') , new_dataset.id)
        file_dataset = new_dataset
        logger.info( 'New file will be added to dataset "{}".'.format(new_dataset.name) )
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
            logger.error( 'You do not have permission to add a file to dataset ({}).'.format(dataset_selection) )
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
                logger.error( 'Error: you do not have permission to add a dataset to that project ({}).'.format( project_selection ) )
            db.session.commit()        

    if not name: 
        name = accession 

    # modify the path with the new style, the new hotness if you will
    if file_dataset:
        path = '{}/{}/{}'.format(
            user.path.rstrip('/'),
            'Dataset_' + str(file_dataset.id), 
            accession)
    else:
        path = '{}/{}'.format(
            user.path.rstrip('/'), 
            accession)

    # check if the file path we settled on is available.
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        logger.info( 'Creating directory {}'.format(directory) ) 
        os.makedirs(directory)

    if os.path.isfile(path):
        path = os.path.splitext(path)[0] + '_1' + os.path.splitext(path)[1]

    logger.info( 'Fetching SRA data from NCBI {}'.format(accession) )
    command = "fastq-dump -I --gzip --defline-qual '+' --split-files -T --outdir {} {}".format(directory, accession)
    
    logger.info( command ) 

    # response = os.system(command)
    command_line_args = shlex.split(command)
    command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )
    for line in iter(command_line_process.stdout.readline, b''):
        line = line.strip()
        logger.info( line.strip() )
    response, error = command_line_process.communicate()
    command_line_process.stdout.close()
    command_line_process.wait()

    if error == None: 
        file_paths = []
        dirs = os.listdir('{}/{}'.format(directory, accession))
        if dirs == ['1']:

            # flatten and clean up the directory tree:
            source = '{}/{}/1/fastq.gz'.format(directory, accession)
            destination = '{}/{}_1_fastq.gz'.format(directory, accession)
            os.rename( source, destination )

            file_paths = [ destination ]
            filename_array = ['{}_1_.fastq.gz'.format(accession)]

            os.rmdir( '{}/{}/1/'.format(directory, accession) )
            os.rmdir( '{}/{}/'.format(directory, accession) )


        if dirs == ['1','2'] or dirs == ['2','1']:

            file_paths = []
            filename_array = []

            for directory_number in dirs:

                # flatten and clean up the directory tree:
                source = '{}/{}/{}/fastq.gz'.format(directory, accession, directory_number)
                destination = '{}/{}_{}_fastq.gz'.format(directory, accession, directory_number)
                os.rename( source, destination )

                file_paths.append( destination )
                filename_array.append( '{}_{}_.fastq.gz'.format(accession, directory_number) )

                os.rmdir( '{}/{}/{}/'.format(directory, accession, directory_number) )

            os.rmdir( '{}/{}/'.format(directory, accession) )


        else: 
            raise Exception( 'Number of files from SRA export not one or two...' )
        logger.info( 'Writing sra output files to {}'.format(directory) )
        return_value = import_files_as_dataset(file_paths, filename_array=filename_array, user_id=user_id, name=name, chain=chain, dataset = file_dataset, parent_task = self)
        logger.info( 'SRA import complete.' )

        file_ids = return_value.file_ids

        return ReturnValue('Dataset from SRA Accession {} created for user {}'.format(accession, user.username), file_ids = file_ids )
    else: 
        raise Exception( 'fastq-dump command failed:'.format(error) )

@celery.task( base = LogTask, bind = True ) 
def import_files_as_dataset(self, filepath_array, user_id, filename_array=None, chain=None, name=None, dataset = None ):
    logger = self.logger

    current_user = db.session.query(User).filter(User.id==user_id).first()

    if not current_user:
        raise Exception( "Error: user with id {} not found.".format(user_id) )

    if not dataset:
        d = Dataset()
        d.user_id = user_id
        d.name = name
        d.description = 'Dataset generated from file import'
        d.chain_types_sequenced = [chain]
        db.session.add(d)
        db.session.commit()
        d.directory = current_user.path.rstrip('/') + '/Dataset_' + str(d.id)
    else:
        d = dataset

    if not d.directory:
        d.directory = current_user.path.rstrip('/') + '/Dataset_' + str(d.id)
        db.session.commit()

    if not os.path.exists(d.directory):
        logger.info('Making directory {}'.format( d.directory ) )
        os.makedirs(d.directory)
    db.session.commit()

    files = []
    file_ids = []
    file_str = ''
    file_count = 0
    for index, filepath in enumerate(filepath_array):
        f = File()
        f.user_id = user_id 
        if filename_array and len(filename_array) == len(filepath_array):
            f.name = filename_array[index]
        else:
            f.name = filepath.split('/')[-1]
        f.file_type = parse_file_ext(f.name)
        file_str = file_str + ', ' + f.name 
        f.dataset_id = d.id
        # description = 
        f.available = True
        f.in_use = False
        f.status = 'AVAILABLE'
        f.path = filepath
        f.file_size = os.path.getsize(f.path)
        f.chain = chain
        # url = db.Column(db.String(256))
        f.command = 'metadata created to link existing file'
        f.created = 'now'
        # paired_partner = db.Column(db.Integer, db.ForeignKey('file.id'))
        # parent_id = db.Column(db.Integer, db.ForeignKey('file.id'))
        # analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))
        files.append(f)
        db.session.add(f)
        db.session.commit()
        db.session.refresh(f)
        file_ids.append(f.id)


    db.session.commit()
    d.primary_data_files_ids = map(lambda f: f.id, files)
    db.session.commit()
    file_str.lstrip(', ')
    return ReturnValue('{} files were added to Dataset {} (): {}'.format( file_count, d.id, d.directory, file_str ), file_ids = file_ids )


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@celery.task(base= LogTask, bind = True)
def download_file(self, url, path, file_id, checksum=None, user_id = None):
    logger = self.logger

    logger.info ( 'Downloading file from: {}'.format(url) )

    # check if the directory for the file exists. If not, make the directory path with makedirs
    directory = os.path.dirname(path)
    if not os.path.exists(directory): 
        logger.info ( 'Creating directory: {}'.format(directory) )
        os.makedirs(directory)

    logger.info ( 'Downloading file to directory: {}'.format(directory) )

    # you can try the following large files
    # ftp://ftp.ddbj.nig.ac.jp/ddbj_database/dra/fastq/SRA143/SRA143000/SRX478835/SRR1179882_2.fastq.bz2
    # http://hgdownload.cse.ucsc.edu/goldenPath/hg38/bigZips/refMrna.fa.gz
    response = urllib2.urlopen(url)
    total_size = response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    logger.info ( 'Target file size: {}'.format(total_size) )

    # Initiate the download bar
    # self.update_state(state='PROGRESS', meta={'status': 'Downloading', 'current' : str(0), 'total' : str(1), 'units' : 'bytes' })

    CHUNK = 16 * 1024
    with open(path, 'wb') as outfile: 
        while True: 
            chunk = response.read(CHUNK)
            if not chunk: break 
            outfile.write(chunk)
            bytes_so_far += len( chunk )

            # Send a progress message with the number of bytes downloaded.
            # self.update_state(state='PROGRESS', meta={'status': 'Downloading', 'current' : str(bytes_so_far), 'total' : str(total_size), 'units' : 'bytes' })

    # This status will take down the progress bar and show that the download is complete.
    # self.update_state(state='SUCCESS', meta={'status': 'Download complete.'} )

    f = db.session.query(File).filter(File.id==file_id).first()

    if os.path.isfile(f.path):
        if checksum: 
            if md5(f.path) == checksum: 
                logger.info('File {} Checksums Agree {}'.format(f.path, checksum))
                f.available = True
            else: 
                logger.warning('File {} Checksums Disagree!'.format(f.path))
                f.available = False
        f.file_size = os.path.getsize(f.path)
        logger.info ('Download finished.')
    else:
        # Alternatively, delete file here
        f.available = False
        f.file_size = 0
        logger.error('Failed to download file {}: file not found.'.format(f.path) )

    db.session.commit()
    return 'File download complete.'

@celery.task ( base = LogTask , bind = True )
def run_mixcr_with_dataset_id(self, dataset_id, analysis_name='', analysis_description='', user_id=6, trim=False, cluster=False):

    logger = self.logger

    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    logger.info( 'Running MiXCR on Dataset {}.'.format(dataset_id ) )
    analysis = Analysis()
    analysis.async_task_id = self.task.request_id
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
    analysis.directory = '{}/Analysis_{}/'.format( dataset.directory.rstrip('/'), analysis.id ) 
    db.session.add(analysis)
    db.session.commit()
    self.set_analysis_id( int( analysis.id ) )

    data_files_by_chain = {}
    for key, values in itertools.groupby(dataset.primary_data_files(), lambda x: x.chain): 
        data_files_by_chain[key] = list(values)
    logger.debug( "Running MiXCR in these batches of files (sorted by file.chain): {}".format(data_files_by_chain) )
    for chain, files in data_files_by_chain.items(): 
        if trim: 
            logger.info( 'Running Trim on Files in Analysis {} before executing MiXCR'.format(analysis.id) )
            return_value = run_trim_analysis_with_files(analysis.id, [file.id for file in files], logger)
            file_ids = return_value.file_ids
            files = [db.session.query(File).get(file_id) for file_id in file_ids]
        logger.info ( 'About to run MiXCR analysis {} on files from chain {}.'.format(repr(analysis), chain) )
        run_mixcr_analysis_id_with_files(analysis.id, [file.id for file in files], parent_task = self)
        if cluster: 
            logger.info( 'Clustering output files.' )
            for file in files: 
                result = run_usearch_cluster_fast_on_analysis_file(analysis, file, identity=0.9)
    return  'MiXCR analysis completed successfully.'

@celery.task(base = LogTask, bind = True)
def run_mixcr_analysis_id_with_files(self, analysis_id, file_ids, species = None, loci=None):

    logger = self.logger
    self.set_analysis_id(analysis_id)

    analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    files = [db.session.query(File).get(file_id) for file_id in file_ids]
    dataset = analysis.dataset

    if species == None:
        if dataset.species == 'Human': species = 'hsa' 
        elif dataset.species == 'Mouse': species = 'mmu' 
        else: species = 'hsa'
    elif species == 'M. musculus':
        species = 'mmu'
    elif species == 'H. sapiens':
        species = 'hsa'
    else:
        species = 'hsa'

    if loci == None: 
        loci = 'ALL'
    else: 
        loci = ','.join(loci)

    if not analysis:
        raise Exception('MixCR Exception: Analysis with ID {} cannot be found.'.format(analysis_id))
    analysis_name = 'Analysis_{}'.format(analysis_id)

    files_to_execute = []
    logger.info( 'Running MiXCR on these files: {}'.format(files) )
    
    path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
    path = path.replace('///','/')
    path = path.replace('//','/')

    #basename = files[0].path.split('/')[-1].split('.')[0]
    basename = analysis_name
    basepath = '{0}/{1}'.format(analysis.directory, analysis_name)
    logger.info( 'Writing output files to base name: {}'.format(basepath) )
    output_files = []

    print 'Path: {}'.format(path)
    print 'Base Path: {}'.format(basepath)
    print 'Base Name: {}'.format(basename)

    # Instantiate Source Files
    alignment_file = File()
    alignment_file.user_id = dataset.user_id
    alignment_file.path = '{}.aln.vdjca'.format(basepath)
    alignment_file.name = "{}.aln.vdjca".format(basename)
    # MIGHT NEED TO ADD THIS ARGUMENT to align (from costas)   -OjParameters.parameters.mapperMaxSeedsDistance=5 
    alignment_file.command = '{} align -t 6 -OjParameters.parameters.mapperMaxSeedsDistance=5 --chains {} --species {} --save-description -f {} {}'.format(app.config['MIXCR'], loci, species, ' '.join([f.path for f in files]), alignment_file.path)

    alignment_file.file_type = 'MIXCR_ALIGNMENTS'
    files_to_execute.append(alignment_file)    
    # clone_index_file = File()
    # clone_index_file.user_id = dataset.user_id
    # clone_index_file.file_type = 'MIXCR_CLONE_INDEX'
    # clone_index_file.path = '{}.aln.clns.index'.format(basepath)
    # clone_index_file.name = '{}.aln.clns.index'.format(basename)
    # clone_index_file.command = 'echo "Indexing Done On Clone Assemble Step"'
    clone_file = File()
    clone_file.user_id = dataset.user_id
    clone_file.file_type = 'MIXCR_CLONES'
    clone_file.path = '{}.aln.clns'.format(basepath)
    clone_file.name = '{}.aln.clns'.format(basename)
    clone_file.command = '{} assemble  -OassemblingFeatures=VDJRegion -f {} {}'.format(app.config['MIXCR'], alignment_file.path, clone_file.path)
    files_to_execute.append(clone_file)
    # files_to_execute.append(clone_index_file)
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
    clone_output_file.command = '{} exportClones -sequence -quality -s --preset full {} {}'.format(app.config['MIXCR'], clone_file.path, clone_output_file.path)
    files_to_execute.append(clone_output_file)
    alignment_output_file = File()
    alignment_output_file.user_id = dataset.user_id    
    alignment_output_file.parent_id = alignment_file.id
    alignment_output_file.path = '{}.txt'.format(alignment_file.path)
    alignment_output_file.file_type = 'MIXCR_ALIGNMENT_TEXT'
    alignment_output_file.name = '{}.txt'.format(alignment_file.name)
    alignment_output_file.command = '{} exportAlignments  -s -readId -descrR1 --preset full  {} {}'.format(app.config['MIXCR'], alignment_file.path, alignment_output_file.path)
    files_to_execute.append(alignment_output_file)
    # pretty_alignment_file = File()
    # pretty_alignment_file.user_id = dataset.user_id    
    # pretty_alignment_file.parent_id = alignment_file.id 
    # pretty_alignment_file.path = '{}.pretty.txt'.format(alignment_file.path)
    # pretty_alignment_file.file_type = 'MIXCR_PRETTY_ALIGNMENT_TEXT'
    # pretty_alignment_file.name =  '{}.pretty.txt'.format(alignment_file.name)
    # pretty_alignment_file.command = 'mixcr exportAlignmentsPretty {} {}'.format(alignment_file.path, pretty_alignment_file.path)
    # files_to_execute.append(pretty_alignment_file)
    analysis.status = 'EXECUTING'
    db.session.commit()

    output_file_ids = []
    execution_error = False

    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = files[0].chain
        logger.info( 'Executing: {}'.format(f.command) )
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()

        # MAKE THE CALL *****
        #response = os.system(f.command)
        error = None
        try:
            command_line_args = shlex.split(f.command)
            command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )

            for line in iter(command_line_process.stdout.readline, b''):
                line = line.strip()

                tracking_percent = False
                tracking = True 
                if 'Exception' in line:
                    logger.error( line )
                    execution_error = True
                elif 'Error' in line:
                    logger.error( line )
                    execution_error = True
                elif ('Alignment:' in line) & ('%' in line):
                    tracking_percent = True
                    tracking_status, line = line.split(':', 1)
                    if line.endswith('%'):
                        percent = line.replace('%', '')
                        eta = ''
                    else:
                        percent, eta = line.split('%', 1)
                        eta = ' ({})'.format( eta.strip() )
                    self.update_state(state='PROGRESS',
                            meta={'status': '{}{}'.format( tracking_status , eta ) , 'current' : float(percent), 'total' : 100, 'units' : '%' })

                    print '{} ({}): {}/{}'.format( tracking_status , eta, percent, 100 )
                else:
                    if tracking_percent:
                        tracking_percent = False
                        self.update_state(state='ANALYZING',
                                meta={'status': tracking_status, 'current' : 100, 'total' : 100, 'units' : '%' })
                        logger.info( '{} complete.'.format( tracking_status ) )

                    logger.info( line )

            response, error = command_line_process.communicate()
            command_line_process.stdout.close()
            command_line_process.wait()
        except subprocess.CalledProcessError as error:
            error = error.output
            logger.error(error)

        if tracking_percent:
            tracking_percent = False
            self.update_state(state='ANALYZING',
                    meta={'status': tracking_status, 'current' : 100, 'total' : 100, 'units' : '%' })
            logger.info( '{} complete.'.format( tracking_status ) )

        if error == None and os.path.isfile(f.path): 
            f.available = True 
            f.file_size = os.path.getsize(f.path)
            db.session.commit()
            db.session.refresh(f)
            output_file_ids.append(f.id)
        else:
            if error != None:
                logger.error( error )
            elif os.path.isfile(f.path):
                logger.error( 'Error: Unable to find output file {}'.format(f.path) )
            f.available = False
            analysis.status = 'FAILED'
            db.session.commit()
    logger.info( 'All commands in analysis {} have been executed.'.format(analysis) )
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
    if execution_error:
        logger.warning('There were one or more errors executing MiXCR. See task output for details')
        return ReturnValue('MiXCR encountered errors while processing.', file_ids = output_file_ids)
    else:
        return ReturnValue('MiXCR analysis completed successfully.', file_ids = output_file_ids)


# While Abstar has pairing ability (it uses PANDAseq), this function presumes that all files have already
# been preprocessed (e.g., all pairing has already been performed by PANDAseq)
@celery.task(base = LogTask, bind = True)
def run_abstar_analysis_id_with_files(self, user_id = None, analysis_id = None, file_ids = [], species = None):
    logger = self.logger
    self.set_analysis_id(analysis_id)

    with session_scope() as session:
        analysis = session.query(Analysis).filter(Analysis.id==analysis_id).first()
        files = [session.query(File).get(file_id) for file_id in file_ids]
        dataset = analysis.dataset

        if species == None:
            if dataset.species == 'Human': species = 'human' 
            elif dataset.species == 'Mouse': species = 'mouse' 
            else: species = 'human'
        elif species == 'M. musculus':
            species = 'mouse'
        elif species == 'H. sapiens':
            species = 'human'
        else:
            species = 'human'

        if not analysis:
            raise Exception('Abstar Exception: analysis with ID {} not found.'.format(analysis_id) )
        analysis_name = 'Analysis_{}'.format(analysis_id)

        files_to_execute = []
        logger.debug( 'Running Abstar on these files: {}'.format(files) )
        
        path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
        path = path.replace('///','/')
        path = path.replace('//','/')

        basename = analysis_name
        basepath = analysis.directory
        logger.debug( 'Writing output files to base name: {}'.format(basepath) )
        files_to_execute = []

        # abstar -i /path/to/mydata.fasta -t /path/to/temp/ -o /path/to/output/
        # -s macaque -s human (default) -s mouse

        for file in files:
            if file.file_type == 'GZIPPED_FASTQ':
                logger.warning('Cannot run Abstar analysis with zipped files, skipping file {}'.format(file.path) )
            else:
                new_file = File()
                new_file.user_id = dataset.user_id

                new_file.path = '{}/{}'.format(basepath.rstrip('/'), os.path.splitext(file.name)[0]+".json")
                new_file.name = "{}".format(os.path.splitext(file.name)[0]+".json")
                new_file.command = 'abstar -i {0} -t {1} -o {1} -s {2}'.format(file.path, analysis.directory, species)
                new_file.file_type = 'ABSTAR_ALIGNMENTS'
                new_file.dataset_id = analysis.dataset_id 
                new_file.analysis_id = analysis.id 
                new_file.chain = file.chain

                session.add(new_file)
                session.commit()
                session.refresh(new_file)
                files_to_execute.append(new_file)    

        session_objects = expunge_session_objects(session)

    output_file_ids = []


    # Run the commands
    for file in files_to_execute:
        logger.info( 'Executing: {}'.format(file.command) )

        # MAKE THE CALL *****
        #response = os.system(f.command)
        error = None
        try:
            command_line_args = shlex.split(file.command)
            command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )

            line = ''
            vdj_started = False
            vdj_finished = False

            vdj_progress_pattern = re.compile('\(([0-9]*)/([0-9]*)\)([^0-9]+)([0-9]+%)')

            process_executing = True

            while process_executing:

                #nextline = command_line_process.stdout.readline()
                char = command_line_process.stdout.read(1)
                line = line + char

                if not vdj_started:
                    if char == '\n':

                        if 'Running VDJ' in line:
                            vdj_started = True

                        logger.info(line.rstrip())
                        line = ''

                elif vdj_finished:
                    if char == '\n':
                        logger.info(line.rstrip())
                        line = ''
                else:
                    if char == '\n':
                        vdj_finished = True
                        self.update_state(state='ANALYZING')
                        logger.info(line.rstrip())
                        line = ''

                    elif char == '%':
                        line = line.strip()
                        progress_match =  vdj_progress_pattern.match(line)
                        
                        if progress_match:
                            current_job = progress_match.group(1)
                            total_jobs = progress_match.group(2)
                            current_percent = progress_match.group(4).rstrip('%')

                            self.update_state(state='PROGRESS',
                                meta={'status': '{}/{} jobs '.format( current_job , total_jobs ) , 'current' : int(current_percent), 'total' : 100, 'units' : '%' })

                        sys.stdout.flush()
                        line = ''

                if command_line_process.poll() is not None:
                    process_executing = False
                    break
                    sys.stdout.flush()
                   
            response, error = command_line_process.communicate()
            command_line_process.stdout.close()
            command_line_process.wait()
            return_code = command_line_process.returncode

        except subprocess.CalledProcessError as error:
            error = error.output
            logger.error(error)

        if error == None and return_code == 0: 
            if os.path.isfile(file.path):
                file.available = True 
                file.file_size = os.path.getsize(file.path)
                output_file_ids.append(file.id)
            else:
                file.available = False
                analysis.status = 'FAILED'
                logger.error('Abstar Error: failed to create output file {}'.format(file.path) )

        else:
            file.available = False
            analysis.status = 'FAILED'
    logger.info( 'All commands in analysis {} have been executed.'.format(analysis) )
    if set(map(lambda file: file.available, files_to_execute)) == {True}:
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'

    # Save all the changes that were made
    with session_scope() as session:
        add_session_objects(session, session_objects)
        session.commit()

    # KICK OFF ASYNC DB INSERTS FROM OUTPUT FILES
    # parseable_mixcr_alignments_file_path = alignment_output_file.path
    # PARSE WITH parse_and_insert_mixcr_annotation_dataframe_from_file_path to speed up? 
    # if not analysis.status == 'FAILED': result = parse_and_insert_mixcr_annotations_from_file_path(parseable_mixcr_alignments_file_path, dataset_id=analysis.dataset.id, analysis_id=analysis.id)
    return ReturnValue('Abstar analysis completed successfully.', file_ids = output_file_ids)

@celery.task(base = LogTask, bind = True)
def parse_and_insert_mixcr_annotations_from_file_path(self, file_path, dataset_id=None, analysis_id=None):
    logger = self.logger

    print 'Building annotations from MiXCR output at {}, then inserting into postgres in batches'.format(file_path)
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
        analysis.status = 'COMPLETE'
    db.session.commit()
    result = annotate_analysis_from_db.apply_async((analysis.id, ), queue=celery_queue)
    return len(annotations)

@celery.task(base = LogTask, bind = True)
def parse_and_insert_mixcr_annotation_dataframe_from_file_path(self, file_path, dataset_id=None, analysis_id=None):
    logger = self.logger

    print 'Building annotation dataframe from MiXCR output at {}, then inserting into postgres'.format(file_path)
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


@celery.task(base = LogTask, bind = True)
def run_pandaseq_with_dataset_id(self, dataset_id, analysis_id=None, analysis_name='', analysis_description='Pandaseq Alignment Consensus', file_ids=[], user_id=2, minimum_length=100, minimum_overlap=10, algorithm='pear'):
    logger = self.logger
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    files = [db.session.query(File).get(file_id) for file_id in file_ids]
    logger.info( 'Running PANDAseq on Dataset {}.'.format( dataset_id ) )

    if analysis_id: 
        analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    else: 
        analysis = Analysis()
        if analysis_name == '': 
            analysis_name = 'Analysis_{}'.format(analysis.id)
        analysis.async_task_id = self.task.request_id    
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
        db.session.refresh(analysis)
        analysis.directory = '{}/Analysis_{}/'.format( dataset.directory.rstrip('/'), analysis.id )
        if not os.path.isdir(analysis.directory):
            os.mkdir(analysis.directory)


    if len(files) != 2: 
        logger.error( 'Bad request for pandaseq alignment of only {} files'.format(len(files)) )

    else: 
        logger.info( 'Running PANDAseq concatenation on these {} files: {}'.format(len(files), ', '.join( [file.name for file in files] ) ))

        files_to_execute = []
        path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
        path = path.replace('//','/')
        basename = analysis_name
        if basename == '' or basename == None: 
            basename = 'Analysis_{}'.format(analysis.id)
        basepath = '{0}/{1}'.format(analysis.directory.rstrip('/'), basename)
        logger.info( 'Writing output files to base name: {}'.format(basepath) )

        # Instantiate Output Files
        alignment_file = File()
        alignment_file.user_id = dataset.user_id
        alignment_file.path = '{}.pandaseq_{}.fastq'.format(basepath, algorithm)
        alignment_file.name = "{}.pandaseq_{}.fastq".format(basename, algorithm)
        alignment_file.command = 'pandaseq -f {} -r {} -F -T 4 -A {} -w {} -l {} -o {} 2> {}.log'.format(files[0].path, files[1].path, algorithm, alignment_file.path, minimum_length, minimum_overlap, alignment_file.path)
        alignment_file.file_type = 'PANDASEQ_ALIGNED_FASTQ'
        files_to_execute.append(alignment_file)
        analysis.status = 'EXECUTING'
        db.session.commit()

        for f in files_to_execute:
            f.command = f.command.encode('ascii')
            f.dataset_id = analysis.dataset_id 
            f.analysis_id = analysis.id 
            f.chain = files[0].chain
            logger.info( 'Executing: {}'.format(f.command) )
            analysis.active_command = f.command
            f.in_use = True 
            db.session.add(f)
            db.session.commit()
            # MAKE THE CALL
            #response = os.system(f.command)
            #print 'Response: {}'.format(response)
            
            error = None
            lowq_errors = 0 
            try:
                command_line_args = shlex.split(f.command)
                command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )

                start = dt.datetime.now()

                for line in iter(command_line_process.stdout.readline, b''):
                    line = line.strip()
                    if 'ERR' in line or '* * *' in line:
                        if 'LOWQ' in line: 
                            lowq_errors += 1 
                        else: 
                            logger.error(line)
                    elif 'STAT' in line:
                        try:
                            if 'READS' in line:
                                current = dt.datetime.now()
                                elapsed = (current - start).seconds
                                line_parts = line.split('READS', 1)
                                reads = line_parts[1].strip()
                                status = 'Time Elapsed: {} - Number of Reads: {}'.format(elapsed, reads)
                                self.update_state(state='STATUS', meta={'status': status })
                        except:
                            pass

                self.update_state(state='SUCCESS',
                    meta={'status': 'PANDAseq complete.' })

                response, error = command_line_process.communicate()
                command_line_process.stdout.close()
                command_line_process.wait()
            except subprocess.CalledProcessError as error:
                error = error.output
                logger.error(error)
            if lowq_errors != 0: 
                logger.error('Pandaseq Run Encountered {} Low-Quality-Read Errors'.format(lowq_errors))
            if error == None:
                if os.path.isfile(f.path): 
                    f.available = True 
                    f.file_size = os.path.getsize(f.path)
                    dataset.primary_data_files_ids = [f.id]
                    db.session.commit()
                    db.session.refresh(f)
                    output_file_ids = [f.id]
                else:
                    f.available = False
                    analysis.status = 'FAILED'
                    db.session.commit()
                    logger.error('PANDAseq Error: unable to create file {}'.format(f.path) )

            else:
                f.available = False
                analysis.status = 'FAILED'
                db.session.commit()
                logger.error(error)

        ##### ***** Need to Check Output Files Here ***** #####

    logger.info( 'All commands in analysis {} have been executed.'.format(analysis) )
    if set(map(lambda f: f.available, files_to_execute)) == {True}:
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'
    db.session.commit()

    return ReturnValue('PANDAseq analysis complete.', file_ids = output_file_ids)




def run_trim_analysis_with_files(analysis_id = None, file_ids = None, logger = celery_logger, trim_illumina_adapters = True, trim_slidingwindow = True, trim_slidingwindow_size = 4, trim_slidingwindow_quality = 15):
    analysis = db.session.query(Analysis).get(analysis_id)

    files = map(lambda x: db.session.query(File).filter(File.id==x).first(), file_ids)

    if not analysis:
        raise Exception( 'Analysis with ID {} not found.'.format(analysis_id) )
    analysis_name = 'Analysis_{}'.format(analysis.id)

    dataset = analysis.dataset
    files_to_execute = []
    logger.info( 'Running Trimmomatic on files {}.'.format( ', '.join( [str(file.id) for file in files] ) ) )
    path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
    path = path.replace('//', '/')

    basename = files[0].path.split('/')[-1].split('.')[0]
    basepath = '{0}/{1}'.format(analysis.directory, analysis_name)
    logger.info( 'Writing output files to base name: {}'.format(basepath) )
    output_file_ids = []

    if len(files) == 0 or len(files) > 2:
        raise Exception('Can only run Trimmomatic on 1 or 2 files, not on {} files.'.format( str(len(files) ) ) )

    illumina_command = ''
    if trim_illumina_adapters:
        illumina_command = 'ILLUMINACLIP:{}/TruSeq3-SE.fa:2:30:10 '.format( app.config['TRIMMOMATIC_ADAPTERS'] )

    sliding_window_command = ''
    if trim_slidingwindow:
        sliding_window_command = 'SLIDINGWINDOW:{}:{} '.format(trim_slidingwindow_size, trim_slidingwindow_quality)


    # Instantiate Source Files
    if len(files) == 1: 
        output_file = File()
        output_file.user_id = dataset.user_id
        output_file.path = '{}.trimmed.fastq'.format(basepath)
        output_file.name = "{}.trimmed.fastq".format(basename)

        # #3 is the illumina clip command
        output_file.command = '{0} SE -phred33 -threads 4 {1} {2} {3}LEADING:3 TRAILING:3 {4}MINLEN:50'.format(app.config['TRIMMOMATIC'], files[0].path, output_file.path, illumina_command, sliding_window_command)
        output_file.file_type = 'TRIMMED_FASTQ'
        files_to_execute.append(output_file)

        paired = False

    if len(files) == 2: 
        r1_output_file = File()
        r1_output_file.user_id = dataset.user_id
        r1_output_file.path = '{}.R1.trimmed.fastq'.format(basepath)
        r1_output_file.name = "{}.R1.trimmed.fastq".format(basename)
        r1_output_file.file_type = 'TRIMMED_FASTQ'
        r2_output_file = File()
        r2_output_file.user_id = dataset.user_id
        r2_output_file.path = '{}.R2.trimmed.fastq'.format(basepath)
        r2_output_file.name = "{}.R2.trimmed.fastq".format(basename)
        r2_output_file.file_type = 'TRIMMED_FASTQ'
        r1_output_file.command = '{0} PE -phred33 -threads 4 {1} {2} {3} {4} {5} {6} {7}LEADING:3 TRAILING:3 {8}MINLEN:50'.format(app.config['TRIMMOMATIC'], files[0].path, files[1].path, r1_output_file.path, '/dev/null', r2_output_file.path, '/dev/null', illumina_command, sliding_window_command)
        r2_output_file.command = ''
        files_to_execute.append(r1_output_file)
        files_to_execute.append(r2_output_file)

        paired = True

    analysis.status = 'EXECUTING TRIM'
    db.session.commit()
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        f.chain = files[0].chain
        logger.info( 'Executing: {}'.format(f.command) )
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        
        # MAKE THE CALL
        if f.command != '': 
            logger.info( f.command )

            error = None
            try:
                command_line_process = subprocess.Popen( shlex.split( f.command ) , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )

                for line in iter(command_line_process.stdout.readline, b''):
                    logger.info(line.strip())

                response, error = command_line_process.communicate()
                command_line_process.stdout.close()
                command_line_process.wait()
            except subprocess.CalledProcessError as error:
                error = error.output
                logger.error(error)

            response = command_line_process.returncode

            if response == 0: 
                f.available = True 
                f.in_use = False
                f.file_size = os.path.getsize(f.path)
                db.session.commit()
                db.session.refresh(f)

            else:
                f.available = False
                f.in_use = False 
                analysis.status = 'FAILED'
                db.session.commit()
                logger.error( 'Error trimming file {}: {}'.format(file.path, error) )

    if paired:
        db.session.refresh(r1_output_file)
        output_file_ids.append(r1_output_file.id)
        db.session.refresh(r2_output_file)
        output_file_ids.append(r2_output_file.id)
    else:
        db.session.refresh(output_file)
        output_file_ids.append(output_file.id)


    logger.info( 'Trim job for analysis {} has been executed.'.format(analysis) )
    return ReturnValue( 'Success', file_ids = output_file_ids)


# Quality filtering with fastx_toolkit on  % of read above certain PHRED threshold
@celery.task(base = LogTask, bind = True)
def run_quality_filtering_with_dataset_id(self, dataset_id, analysis_id=None, analysis_name='', analysis_description='Fastq Quality Filter', file_ids=[], minimum_percentage=50, minimum_quality=20):
    logger = self.logger
    dataset = db.session.query(Dataset).filter(Dataset.id==dataset_id).first()
    files = [db.session.query(File).get(file_id) for file_id in file_ids]
    logger.info( 'Running Quality Filter on Dataset {}.'.format( dataset_id ) )

    if analysis_id: 
        analysis = db.session.query(Analysis).filter(Analysis.id==analysis_id).first()
    else: 
        analysis = Analysis()
        if analysis_name == '': 
            analysis_name = 'Analysis_{}'.format(analysis.id)
        analysis.async_task_id = self.task.request_id    
        analysis.name = analysis_name
        analysis.description = analysis_description
        analysis.user_id = user_id
        analysis.dataset_id = dataset.id
        analysis.program = 'quality_filter'
        analysis.started = 'now'
        analysis.params = {}
        analysis.status = 'QUEUED'
        analysis.responses = []
        analysis.available = False
        analysis.inserted_into_db = False
        db.session.add(analysis)
        db.session.commit()
        db.session.refresh(analysis)
        analysis.directory = '{}/Analysis_{}/'.format( dataset.directory.rstrip('/'), analysis.id )
        if not os.path.isdir(analysis.directory):
            os.mkdir(analysis.directory)


    logger.info( 'Running Quality Filtering with {}% bases above PHRED {} on these files: {}'.format(minimum_percentage, minimum_quality, ', '.join( [file.name for file in files] ) ))

    files_to_execute = []
    output_file_ids = [] 
    for file in files: 
        path = '/{}'.format('/'.join(file.path.split('/')[:-1]))
        path = path.replace('//','/')
        basename = file.path.split('/')[-1].split('.')[0]
        # basepath = '{0}/{1}'.format(analysis.directory, analysis_name)
        if basename == '' or basename == None: 
            basename = 'Analysis_{}'.format(analysis.id)
        basepath = '{0}/{1}'.format(analysis.directory.rstrip('/'), basename)
        logger.info( 'Writing output files to base name: {}'.format(basepath) )

        # Instantiate Output Files
        filtered_file = File()
        filtered_file.user_id = dataset.user_id
        filtered_file.path = '{}.filtered_q{}p{}.fastq'.format(basepath, minimum_quality, minimum_percentage)
        filtered_file.name = '{}.filtered_q{}p{}.fastq'.format(basename, minimum_quality, minimum_percentage)
        filtered_file.command = 'fastq_quality_filter -q {} -p {} -i {} -o {} -Q 33 '.format(minimum_quality, minimum_percentage,  file.path, filtered_file.path) #-Q 33 for more recent Illumina quality outputs
        filtered_file.file_type = 'FASTQ'
        files_to_execute.append(filtered_file)
        analysis.status = 'EXECUTING'
        db.session.commit()

    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        f.dataset_id = analysis.dataset_id 
        f.analysis_id = analysis.id 
        # f.chain = files[0].chain
        logger.info( 'Executing: {}'.format(f.command) )
        analysis.active_command = f.command
        f.in_use = True 
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL
        #response = os.system(f.command)
        #print 'Response: {}'.format(response)
        
        error = None
        try:
            command_line_args = shlex.split(f.command)
            command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )

            start = dt.datetime.now()

            for line in iter(command_line_process.stdout.readline, b''):
                line = line.strip()
                logger.info(line)
                # if 'ERR' in line or '* * *' in line:
                #     if 'LOWQ' in line: 
                #         lowq_errors += 1 
                #     else: 
                #         logger.error(line)
                # elif 'STAT' in line:
                #     try:
                #         if 'READS' in line:
                #             current = dt.datetime.now()
                #             elapsed = (current - start).seconds
                #             line_parts = line.split('READS', 1)
                #             reads = line_parts[1].strip()
                #             status = 'Time Elapsed: {} - Number of Reads: {}'.format(elapsed, reads)
                #             self.update_state(state='STATUS', meta={'status': status })
                #     except:
                #         pass

            # self.update_state(state='SUCCESS',
            #     meta={'status': 'PANDAseq complete.' })

            response, error = command_line_process.communicate()
            command_line_process.stdout.close()
            command_line_process.wait()
        except subprocess.CalledProcessError as error:
            error = error.output
            logger.error(error)
        if error == None:
            if os.path.isfile(f.path): 
                f.available = True 
                f.file_size = os.path.getsize(f.path)
                dataset.primary_data_files_ids = [f.id]
                db.session.commit()
                db.session.refresh(f)
                output_file_ids.append(f.id)
            else:
                f.available = False
                analysis.status = 'FAILED'
                db.session.commit()
                logger.error('Quality Filtering Error: unable to create file {}'.format(f.path) )

        else:
            f.available = False
            analysis.status = 'FAILED'
            db.session.commit()
            logger.error(error)

    ##### ***** Need to Check Output Files Here ***** #####

    logger.info( 'Filtering steps for analysis {} have been executed.'.format(analysis) )
    if set(map(lambda f: f.available, files_to_execute)) == {True}:
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'
    db.session.commit()

    return ReturnValue('Quality Filtering complete.', file_ids = output_file_ids)




# Standalone celery task to run MSDB analysis on a dataset. 
# This adds a new analysis if analysis = 'new' is passed or analysis_id == None
# Calls run_msdb_with_analysis_id
@celery.task(base = LogTask, bind = True)
def run_msdb_with_dataset_id(self, user_id=6, dataset_id = None, analysis_id = None, file_ids = [], analysis_name='', analysis_description='', cluster_percent = 0.9, must_be_present = ['CDR3']):

    logger = self.logger
    logger.info('Preparing for IGREP MSDB algorithm...')

    annotated_files = []
    annotated_file_formats = []
    file_paths_to_analyze = []

    with session_scope() as session:

        # Get the DB objects
        user = session.query(User).get(user_id)
        if dataset_id != None: dataset = session.query(Dataset).get(dataset_id)
        else: dataset = None

        # Determine if a new analysis is needed
        if analysis_id and analysis_id != 'new':
            analysis = session.query(Analysis).get(analysis_id)
            output_directory = analysis.directory
        else: # no analysis provided, so we have to create a new analysis

            # determine the analysis directory
            if dataset_id != None and dataset:
                directory = dataset.directory
            else: #create a new directory
                directory = user.path

            analysis = generate_new_analysis(user = user, dataset = dataset, directory = directory, directory_prefix = 'MSDB_Analysis_', session = session, async_task_id = self.task.request_id)

            # Set analysis database values
            if analysis_description != '': analysis.description = analysis_description
            else: analysis.description = 'MSDB Analysis Results'
            if analysis_name != '': analysis.name = analysis_name
            else: analysis.name = 'Pairing Analysis {}'.format( str(analysis.id) )

            analysis.program = 'IGREP MSDB'

        # Set local values
        analysis_id = analysis.id
        self.set_analysis_id(analysis_id)
        output_directory = analysis.directory

        # Set analysis database values
        analysis.started = 'now'
        analysis.files_to_analyze = map(lambda i: int(i), file_ids)
        analysis.params = {}
        analysis.status = 'QUEUED'
        analysis.responses = []
        analysis.available = False
        analysis.inserted_into_db = False
        session.add(analysis)
        session.commit()


        prefix_output_files = analysis.name.replace(' ', '_')
        self.set_analysis_id(analysis_id)

        if file_ids:
            files = map(lambda x: session.query(File).filter(File.id==x).first(), file_ids)
        elif dataset_id != None and dataset:
            files = dataset.files
            file_ids = [file.id for file in files]

    return_value = run_msdb_with_analysis_id(analysis_id = analysis_id, file_ids = file_ids, user_id= user_id, cluster_percent = cluster_percent, must_be_present = must_be_present, parent_task = self.task)
    file_ids = return_value.file_ids

    return return_value


# Returns a ReturnValue with field file_ids which reflects only the new files added during the analysis
@celery.task(base = LogTask, bind = True)
def run_msdb_with_analysis_id(self, analysis_id = None, file_ids = [], user_id = None, cluster_percent = 0.9, must_be_present = ['CDR3']):

    logger = self.logger

    logger.info('Running MSDB analysis. ')

    igfft_msdb_fields = {
        'ABSEQ.AA': "Full_Length_Sequence.AA",
        'CDR3.AA': 'CDR3_Sequence.AA',
        'VREGION.VGENES': 'Top_V-Gene_Hits',
        'JREGION.JGENES': 'Top_J-Gene_Hits',
        'ISOTYPE.GENES': "Isotype",
        'DREGION.DGENES': '',
        'RECOMBINATIONTYPE': 'Recombination_Type', # this is not necessary as the program will guess it if not provided
        'VREGION.CDR1.AA': "CDR1_Sequence.AA",
        'VREGION.CDR2.AA': "CDR2_Sequence.AA",
        'VREGION.SHM.NT_PER': "VRegion.SHM.Per_nt",
        'JREGION.SHM.NT_PER': "JRegion.SHM.Per_nt", 
    }

    file_paths_to_analyze = []
    files_in_directory = []

    analysis_directory = None

    with session_scope() as session:
        analysis = session.query(Analysis).get(analysis_id)
        user = session.query(User).get(user_id)

        if analysis: 
            dataset_id = analysis.dataset.id
            dataset = analysis.dataset
            analysis_directory = analysis.directory
        else:
            analysis_directory = user.path

        if file_ids == []:
            files = dataset.files
        else:
            files = session.query(File).filter(File.id.in_(file_ids)).all()
        
        user = session.query(User).get(user_id)

        for file in files:
            if file.file_type == 'IGFFT_ANNOTATION':
                file_paths_to_analyze.append(file.path)

        # prefix for analysis result files
        prefix = None
        if analysis:
            prefix = analysis.name.replace(' ','_')

    if file_paths_to_analyze == []:
        logger.warning('No output files from IGREP analysis were found. Skipping mass spec analysis.')
        return ReturnValue('No MSDB analysis was performed.', file_ids = [])
    else:
        # for file_path in file_paths_to_analyze:
            # immunogrep_msdb.generate_msdb_file(file_path, 'TAB', translate_fields=igfft_msdb_fields, output_folder_path= analysis_directory, cluster_id = cluster_percent, must_be_present=['CDR3'])
    
        files_in_directory = Set(next(os.walk(analysis_directory))[2])

        # Briefly pass all STDOUT to the logger
        saved_stdout = sys.stdout
        sys.stdout = VHVLPairingLoggerWriter( logger, task = self )

        immunogrep_msdb.generate_msdb_file(input_files = file_paths_to_analyze, filetype = 'TAB', translate_fields=igfft_msdb_fields, output_folder_path= analysis_directory, cluster_id = cluster_percent, must_be_present=['CDR3'])

        # Restore STDOUT to the console
        sys.stdout = saved_stdout

        new_files_in_directory = Set(next(os.walk(analysis_directory))[2]) - files_in_directory

        return_value = add_directory_files_to_database(directory = analysis_directory, description = 'MSDB analysis result.', dataset_id = dataset_id, analysis_id = analysis_id, user_id = user_id, file_names = new_files_in_directory, prefix = prefix, logger = logger)
        file_ids = return_value.file_ids

        logger.info( 'MSDB analysis complete. {} files were produced.'.format(len(file_ids)) )

        return ReturnValue('MSDB analysis complete. {} files were produced.'.format(len(file_ids)), file_ids = [] )


        # immunogrep_msdb.generate_msdb_file('SRR1525444.R1.igfft.annotation', 'TAB', translate_fields=igfft_msdb_fields, output_folder_path='/data/russ/scratch/SRR1525444_14/Analysis_99', must_be_present=['CDR3'])

        # Main function for generating a FASTA mass spec db file using annotation. User passes in a list of input files generated from an annotation program,
        # and this function will output a FASTA file that can be used as a reference db for identifying peptides from mass spec. It will also generate a summary file
        # describing which filters were passed.

        # Parameters
        # ----------
        # input_files : list of strings
        #     corresponding to filepaths for each annotated file.
        #     .. note::IMGT filepath format
        #         If the input files come from IMGT analyses, then input_files can either be a list of lists (i.e. 11 files per experiment) or a single list of all experiment filenames
        #         (i.e. program will split files into proper experiments)
        # filetype : string, default None
        #     Describes the filetype of the input files. file type can be either TAB, CSV, FASTA, FASTQ, IMGT
        # output_folder_path : string
        #     Filepath for returning results. If not defined, will make a new folder
        # dbidentifier : string, default None
        #     A string identifier to label the mass spec database file
        # dataset_tags : list of strings; default None
        #     If defined, then this will be used as the identifier for each file/dataset. If Not defined (dataset_tags is None) then the experiment identifier will be equal to the filepath
        #     names defined by input_files.
        #     .. important::
        #         If defined, the length of the string must be equal to the length of the input files/each unique dataset provided
        #     .. note::
        #         The following characters are replaced from the tags: '_', ' ',':', '|' and ',' are replaced by '-'
        # translate_fields : dict, default {}
        #     This defines which fields in the file corresponds to fields we need for the analysis.
        #     key = field we use in the program, value = field name in the provided file(s)
        #     If empty, then this variable will assume the field names are the exact same as the fields we use in this program (see default_fields)
        # cluster_id : float, default 0.9 - INPUT default 0.9
        #     The percent identity required for clonotyping
        # must_be_present : list of strings, default ['CDR1','CDR2','CDR3']
        #     This will define which CDR fields MUST be present in the sequence to be considered for analysis.
        #     .. note::Fields
        #         Only CDR1, CDR2, and CDR3 can be defined in this list
        #     .. note::CDR3
        #         CDR3 will ALWAYS be required for this analysis
        # use_vl_sequences : boolean, default False
        #     If True, then any VL sequences detected in the provided experiments will be appended to the database file.
        #     If False, then the program will append a default VL sequence list generated by Sebastian and stored in the database
        # low_read_count : int, default 1     
        #     filter for >= read count

        # Outputs
        # -------
        # Path of the FASTA db file created    

# Celery task to run VH/VL pairing analysis on a dataset or multiple datasets.
# If dataset_id == None, add files to user.path/Pairing_Analysis_#
# This adds a new analysis if analysis = 'new' is passed or analysis_id == None
# Calls run_msdb_with_analysis_id
@celery.task(base = LogTask, bind = True)
def run_pair_vhvl_with_dataset_id(self, user_id=6, dataset_id = None, analysis_id = None, file_ids = [], analysis_name='', analysis_description='', vhvl_min = 0.96, vhvl_max = 0.96, vhvl_step = 0.0):

    logger = self.logger
    logger.info('Running IGREP VH/VL pairing algorithm...')

    annotated_files = []
    annotated_file_formats = []
    file_paths_to_analyze = []

    with session_scope() as session:

        # Get the DB objects
        user = session.query(User).get(user_id)
        if dataset_id != None: dataset = session.query(Dataset).get(dataset_id)
        else: dataset = None

        # Determine if a new analysis is needed
        if analysis_id and analysis_id != 'new':
            analysis = session.query(Analysis).get(analysis_id)
            output_directory = analysis.directory
        else: # no analysis provided, so we have to create a new analysis

            # determine the analysis directory
            if dataset_id != None and dataset:
                directory = dataset.directory
            else: #create a new directory
                directory = user.path

            analysis = generate_new_analysis(user = user, dataset = dataset, directory = directory, directory_prefix = 'Pairing_Analysis_', session = session, async_task_id = self.task.request_id)

            # Set analysis database values
            if analysis_description != '': analysis.description = analysis_description
            else: analysis.description = 'IGREP VH/VL Pairing Analysis Results'
            if analysis_name != '': analysis.name = analysis_name
            else: analysis.name = 'Pairing Analysis {}'.format( str(analysis.id) )

            analysis.program = 'IGREP Pairing'


        # Set local values
        analysis_id = analysis.id
        self.set_analysis_id(analysis_id)

        output_directory = analysis.directory

        # Set analysis database values
        analysis.started = 'now'
        analysis.files_to_analyze = map(lambda i: int(i), file_ids)
        analysis.params = {}
        analysis.status = 'QUEUED'
        analysis.responses = []
        analysis.available = False
        analysis.inserted_into_db = False
        session.add(analysis)
        session.commit()

        prefix_output_files = analysis.name.replace(' ', '_')

        if file_ids:
            files = map(lambda x: session.query(File).filter(File.id==x).first(), file_ids)
        elif dataset_id != None and dataset:
            files = dataset.files
            file_ids = [file.id for file in files]

        for file in files:
            if file.file_type == 'IGFFT_ANNOTATION':
                annotated_files.append(file.path)
                annotated_file_formats.append('TAB')


    if annotated_files != []:
        
        files_in_directory = Set(next(os.walk(output_directory))[2])

        # Briefly pass all STDOUT to the logger
        saved_stdout = sys.stdout
        sys.stdout = VHVLPairingLoggerWriter( logger, task = self )

        cluster_setting = [vhvl_min, vhvl_max, vhvl_step]
        pairing.RunPairing(annotated_files, annotated_file_formats= annotated_file_formats, analysis_method='GEORGIOU_INHOUSE', output_folder_path=output_directory, prefix_output_files= prefix_output_files, cluster_cutoff=cluster_setting, annotation_cluster_setting= 0.9)

        # Restore STDOUT to the console
        sys.stdout = saved_stdout

        new_files_in_directory = Set(next(os.walk(output_directory))[2]) - files_in_directory

        return_value = add_directory_files_to_database(directory = output_directory, description = 'IGREP pairing result.', dataset_id = dataset_id, analysis_id = analysis_id, user_id = user_id, file_names = new_files_in_directory, logger = logger)
        file_ids = return_value.file_ids

        logger.info('IGREP VH/VL pairing algorithm complete.')
        return ReturnValue('IGREP VH/VL pairing analysis complete. {} files were produced.'.format(len(file_ids)), file_ids = file_ids )

    else:
        logger.warning('No annotated files were found to analyze.')


    return ReturnValue('IGREP VH/VL pairing analysis complete. {} files were produced.'.format(len(file_ids)), file_ids = [] )

# Returns a ReturnValue with field file_ids which reflects only the new files added during the analysis
@celery.task(base = LogTask, bind = True)
def run_pair_vhvl_with_analysis_id(self, analysis_id = None, file_ids = [], user_id = None, vhvl_min = 0.96, vhvl_max = 0.96, vhvl_step = 0.0):

    logger = self.logger

    with session_scope() as session:
        output_directory = analysis.directory
        analysis = session.query(Analysis).get(analysis_id)

        output_directory = analysis.directory 

        annotated_files = []
        annotated_file_formats = []

        if file_ids != []:
            files = map(lambda x: session.query(File).filter(File.id==x).first(), file_ids)

            for file in files:
                if file.file_type == 'IGFFT_ANNOTATION':
                    annotated_files.append(file.path)
                    annotated_file_formats.append('TAB')

        prefix_output_files = analysis.name.replace(' ', '_')

    if annotated_files != []:
            
        files_in_directory = Set(next(os.walk(output_directory))[2])

        # Briefly pass all STDOUT to the logger
        saved_stdout = sys.stdout
        sys.stdout = VHVLPairingLoggerWriter( logger, task = self )

        cluster_setting = [vhvl_min, vhvl_max, vhvl_step]
        pairing.RunPairing(annotated_files, annotated_file_formats= annotated_file_formats, analysis_method='GEORGIOU_INHOUSE', output_folder_path=output_directory, prefix_output_files= prefix_output_files, cluster_cutoff=cluster_setting, annotation_cluster_setting= 0.9)

        # Restore STDOUT to the console
        sys.stdout = saved_stdout

        new_files_in_directory = Set(next(os.walk(output_directory))[2]) - files_in_directory

        return_value = add_directory_files_to_database(directory = output_directory, description = 'IGREP VH/VL pairing result.', dataset_id = dataset_id, analysis_id = analysis_id, user_id = user_id, file_names = new_files_in_directory, logger = logger)
        file_ids = return_value.file_ids

        logger.info('IGREP VH/VL pairing algorithm complete.')
        return ReturnValue('IGREP VH/VL pairing analysis complete. {} files were produced.'.format(len(file_ids)), file_ids = file_ids )

    else:
        logger.warning('No annotated files were found to analyze.')


        return ReturnValue('IGREP VH/VL pairing analysis complete. {} files were produced.'.format(len(file_ids)), file_ids = [] )


def run_usearch_cluster_fast_on_analysis_file(analysis, file, identity=0.9):
    dataset = analysis.dataset
    files_to_execute = []
    print 'RUNNING USEARCH CLUSTERING ON THIS FILE: {}'.format(file)
    path = '/{}'.format('/'.join(file.path.split('/')[:-1]))
    basename = file.path.split('/')[-1].split('.')[0]
    basepath = '{}/{}'.format(path, basename)
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

@celery.task(base = LogTask, bind = True)
def run_analysis(self, analysis_id = None, dataset_id = None, file_ids = [], user_id = None, analysis_type='IGFFT', analysis_name='', analysis_description='', trim=False, overlap=False, paired=False, cluster=False, cluster_setting=[0.85,0.9,.01]): 

    logger = self.logger
    logger.info( 'Running {} analysis on dataset {}.'.format(analysis_type, dataset_id ) )

    ##### Start a new db session: #####
    with session_scope() as session:

        dataset = session.query(Dataset).get(dataset_id)
        if not dataset:
            raise Exception( 'Dataset {} not found.'.format( dataset_id ) )

        if analysis_id:
            analysis = session.query(Analysis).get(analysis_id)
            if not analysis:
                raise Exception( 'Analysis {} not found.'.format( analysis_id ) )
        else:
            analysis = Analysis()

        #CONSTRUCT AND SAVE ANALYSIS OBJECT
        analysis.async_task_id = self.task.request_id
        analysis.name = analysis_name
        analysis.description = analysis_description
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
        session.add(analysis)
        session.commit()
        self.set_analysis_id( int(analysis.id) )

        if dataset.directory:
            analysis.directory = dataset.directory.rstrip('/') + '/Analysis_' + str(analysis.id)
        else: 
            analysis.directory = analysis.dataset.user.path.rstrip('/') + '/Analysis_' + str(analysis.id)
        if not os.path.exists(analysis.directory):
            logger.info ( 'Making analysis directory {}'.format( analysis.directory ) )
            os.makedirs(analysis.directory)
        files = map(lambda x: session.query(File).filter(File.id==x).first(), file_ids)


        logger.info( 'Analysis Output Set To {}'.format(analysis.directory) )
        logger.info( 'Using these files: {}'.format(files) )
        
        if trim:
            logger.info( 'Running Trim on Files in Analysis {} before executing annotation'.format(analysis.id) )
            analysis.status = 'TRIMMING FILES' 
            session.commit() 
            return_value = run_trim_analysis_with_files( analysis.id, file_ids, logger)


            files = [session.query(File).get(file_id) for file_id in return_value.file_ids]

        # persist the analysis and files objs after the session closes:
        file_ids = [file.id for file in files]

        session_objects = expunge_session_objects(session)

    ##### End Session #####

    gzipped_file_ids = [file.id for file in files if file.file_type == 'GZIPPED_FASTQ'] 
    unzipped_file_ids = [file.id for file in files] - gzipped_file_ids

    file_ids_for_analysis = unzipped_file_ids
    if gzipped_file_ids != []: 
        return_value = unzip_files( user_id = user_id, file_ids = gzipped_file_ids, destination_directory = analysis.directory, logger = logger)
        file_ids_for_analysis.append( return_value.file_ids )


    ##### Add all of the file changes to the database #####
    analysis.status = 'EXECUTING'
    with session_scope() as session:
        add_session_objects(session, session_objects)
        session.commit()
    ##### End session #####

    return_value = run_igrep_annotation_on_dataset_files(dataset_id, file_ids_for_analysis, user_id = user_id, overlap=overlap, paired=paired, cluster=cluster, cluster_setting=cluster_setting, logger = logger, parent_task = self)
    annotated_file_ids = return_value.file_ids
    #logger.info( 'Annotated file ids from igfft: {}'.format(', '.join(annotated_files) ), file_ids = annotated_file_ids )
    return ReturnValue( 'Annotated file ids from igfft: {}'.format(', '.join(annotated_files) ), file_ids = annotated_file_ids )

    # PAIR 


    # CLUSTER


# Provided with a list of file ids, this function unzips those files if necessary, creates a new file 
#  entry in the database, and returns the file ids of the new file entry
def unzip_files( user_id = None, file_ids = [], destination_directory = '~', logger = celery_logger):

    if len(file_ids) == 0:
        return ReturnValue('No files to unzip.', file_ids = file_ids)

    logger.info('Checking for files to unzip...')

    output_file_ids = []
    number_files_to_unzip = 0

    print 'File IDs: {}'.format(file_ids)

    ##### Begin Session #####
    with session_scope() as session:

        files = session.query(File).filter(File.id.in_(file_ids)).all()
        files_to_unzip = []

        for file in files:

            if file.file_type == 'GZIPPED_FASTQ': 

                number_files_to_unzip += 1

                new_file = File()
                new_file.user_id = user_id
                new_file.parent_id = file.id 
                new_file.path = destination_directory.rstrip('/') + '/' + file.name.replace('.gz','')
                new_file.file_type = 'FASTQ'
                new_file.available = False
                new_file.name =  file.name.replace('.gz', '')
                new_file.command = 'gunzip -c {} > {}'.format(file.path, new_file.path)
                analysis.status = 'GUNZIPPING' 
                session.add(new_file)
                session.commit()
                session.refresh( new_file )
                files_to_unzip.append( new_file )

            else: 
                # file does not need to be unzipped, so add it to the list as-is
                output_file_ids.append(file.id)

        # print 'Here'

        session_objects = expunge_session_objects(session)
    ##### End Session #####

    number_files_unzipped = 0

    if files_to_unzip != []:

        for file in files_to_unzip:

            logger.info( 'Unzipping file id {}:{}'.format(file.id, file.command ) )

            error = False
            return_code = None

            try:
                command_line_process = subprocess.check_output(
                    file.command,
                    stderr=subprocess.STDOUT,
                    shell=True
                )
            except subprocess.CalledProcessError, return_error: 
                logger.error( 'Error: process exited with return code {}: {}'.format( return_error.returncode, return_error.output ) )
                error = True


            if error == False: 
                file.available = True 
                output_file_ids.append(file.id)
                number_files_unzipped += 1

    # Save all of the changes
    logger.info('Saving changes.')
    with session_scope() as session:
        add_session_objects(session, session_objects)
        session.commit()

    if number_files_to_unzip == 0:
        return ReturnValue('No file to unzip.'.format( str( number_files_unzipped ) ), file_ids = output_file_ids )
    else:
        return ReturnValue('{} files unzipped.'.format( str( number_files_unzipped ) ), file_ids = output_file_ids )

def run_igrep_annotation_on_dataset_files(dataset_id, file_ids, user_id, analysis_id = None, overlap=False, paired=False, cluster=False, cluster_setting=[0.85,0.9,.01], species = None, logger = celery_logger, parent_task = None):
    task = parent_task

    # Want to run IGREP without putting out EVERY line of output (~100s)
    # So create a list of status outputs and dictionary of counts (repeated status)
    igrep_states = ['Calcuating number of sequences', 'Running IgFFT', 'Evaluating Parameters', 
                    'Parsing and summarizing alignment file', 'Germline Alignment', 
                    'Performing isotyping on sequences', 
                    'annotation complete, merging files...', 'files merged.', 'Performing isotyping', 
                    'Processing raw fastq files', 'IgFFT run started']
    igrep_counts = {}
    for state in igrep_states:
        igrep_counts[state] = 0


    ##### Open database session #####
    
    # We want to execute the commands outside of the session scope, so store them in a list
    commands = []

    with session_scope() as session:

        # load database objects
        dataset = session.query(Dataset).get(dataset_id)
        files = session.query(File).filter(File.id.in_(file_ids)).all()

        logger.info( 'Running IGREP IGFFT on Dataset {}.'.format( dataset.id ) )
        igrep_script_path = app.config['IGREP_PIPELINES']

        if species == None:
            if dataset.species == 'Human': species = 'homosapiens' 
            elif dataset.species == 'Mouse': species = 'musmusculus' 
            else: species = 'homosapiens'
        elif species == 'M. musculus':
            species = 'musmusculus'
        elif species == 'H. sapiens':
            species = 'homosapiens'
        else:
            species = 'homosapiens'

        annotated_file_ids = []
        for file in files: 
            loci = ''
            if file.chain == 'HEAVY': loci = 'igh'
            if file.chain == 'LIGHT': loci = 'igk,igl'
            if file.chain == 'HEAVY/LIGHT': loci = 'igh,igk,igl'

            # Set default loci here
            if loci == '': loci = 'igh,igk,igl'

            # annotated_f = igfft.igfft_multiprocess(f.path, file_type='FASTQ', species=species, locus=loci, parsing_settings={'isotype': isotyping_barcodes, 'remove_insertions': remove_insertions}, num_processes=number_threads, delete_alignment_file=True)           
            # annotated_files.append(annotated_f[0])
            script_command = 'python {}/gglab_igfft_single.py -species {} -locus {} {}'.format(igrep_script_path, species, loci, file.path)
            commands.append(script_command)

        session_objects = expunge_session_objects(session)

    ##### End database session #####

    for command in commands:

        logger.info( 'executing script: {}'.format(script_command) )
        
        error = None
        try:
            command_line_process = subprocess.Popen( shlex.split(command) , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize = 1 )

            # keep track of the last two states
            # that way we can tell the user what finished happening
            last_state = ''
            counting = False
            start = dt.datetime.now()

            pid_pattern = re.compile('\((.*?)\)')

            for line in iter(command_line_process.stdout.readline, b''):
                line = line.strip()
                print line
                if 'Error'  in line or 'error' in line or 'ERROR' in line:
                    logger.error(line)

                pid = None

                pid_match =  pid_pattern.match(line)
                if pid_match:
                    pid = pid_match.group(1)
                    line = line.replace( pid_match.group(0), '' )
                    line = line.strip()

                for state in igrep_states:
                    if state in line:
                        # if we were counting, let the user know it's done
                        # sys.stdout = open(str(os.getpid()) + ".out", "w")
                        igrep_counts[state] += 1

                        if pid:
                            current_status_number = pid
                        else:
                            current_status_number = igrep_counts[state]

                        if counting:
                            logger.info('{}({}) complete.'.format( last_state, current_status_number ) )
                            counting = False
                        last_state = state
                        current = dt.datetime.now()
                        elapsed = (current - start).seconds

                        #status = 'Time Elapsed: {} - Number of Reads: {}'.format(elapsed, reads)
                        #parent_task.update_state(state='STATUS', meta={'status': status })

                        status = 'Time Elapsed: {} - {}({})'.format(elapsed, line, current_status_number)
                        task.update_state(state='STATUS', meta={'status': status })

                    elif ('% percent done' in line):

                        if pid:
                            current_status_number = pid
                            pid_str = 'PID: {} '.format(pid)
                        else:
                            current_status_number = ''
                            pid_str = ''


                        counting = True
                        try:
                            line_parts = line.split( '%', 1)
                            percent = line_parts[0].strip()
                            percent = float(percent)
                        except:
                            logger.debug( 'Couldn\'t convert {} to float'.format(percent) )
                            percent = 0

                        current = dt.datetime.now()
                        elapsed = (current - start).seconds

                        task.update_state(state='PROGRESS',
                            meta={'status': '{} ({}Time Elapsed: {})'.format( last_state , pid_str, elapsed ) , 'current' : percent, 'total' : 100, 'units' : '%' })

            if counting:
                task.update_state(state='ANALYZING')
                counting = False

            response, error = command_line_process.communicate()
            command_line_process.stdout.close()
            command_line_process.wait()
        except subprocess.CalledProcessError as error:
            error = error.output
            logger.error('Error executing command.')
            logger.error(error)

    ##### Open a new session #####

    with session_scope() as session:

        add_session_objects(session, session_objects)

        all_files_created = True
        total_files = 0
        number_files_created = 0
        files_not_created = []

        files = session.query(File).filter(File.id.in_(file_ids)).all()
        for file in files: 
            total_files += 1
            new_file_path = file.path.replace('fastq','igfft.annotation')

            if os.path.isfile( new_file_path ):
                number_files_created += 1

                new_file = File()
                new_file.user_id = user_id
                new_file.parent_id = file.id 
                new_file.dataset_id = dataset.id

                if analysis_id:
                    new_file.analysis_id = analysis_id

                new_file.name = file.name.replace('fastq','igfft.annotation')
                new_file.name = file.name.replace('fq','igfft.annotation')
                new_file.path = file.path.replace('fastq','igfft.annotation')
                new_file.path = file.path.replace('fq','igfft.annotation')
                new_file.file_type = 'IGFFT_ANNOTATION'
                new_file.created='now'
                new_file.available=True 
                session.add(new_file)
                session.commit()
                session.refresh(new_file)
                annotated_file_ids.append(new_file.id)

            else:
                all_files_created = False
                files_not_created.append( new_file_path )
                logger.error ('IGREP failed to create new file: {}'.format( new_file_path ) )

    if not all_files_created:
        raise Exception( 'IGREP/IGFFT failed to create all files ({}/{}). The following files were not created: {}'.format( number_files_created, total_files, ' '.join(files_not_created) ) )

    ##### End of session #####

    return ReturnValue( 'IGREP analysis complete.', file_ids = annotated_file_ids )


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

@celery.task(base= LogTask, bind = True)
def parse_gsaf_response_into_datasets(self, url, user_id=2, celery_queue='default'):
    if self.parent_task:
        task = self.parent_task
    else:
        task = self
    logger = self.logger
    logger.info('Beginning import of files from GSAF URL.')

    request = urllib2.Request(url)
    logger.info('Retrieving HTML from URL {}'.format(url))
    response = urllib2.urlopen(request)

    file_arrays = [l.rstrip().split('\t') for l in response.readlines() if '<!--gsafdata' in l]
    file_arrays_by_sample_name = itertools.groupby(file_arrays, lambda x: x[1].split('_')[0])
    with session_scope() as session:
        user=session.query(User).filter(User.id==user_id).all()[0]
        new_file_ids=[]
        for sample_name, file_arrays in file_arrays_by_sample_name:
            logger.info('Collecting Info On Sample {}'.format(sample_name))
            dataset = Dataset()
            dataset.user_id = user_id
            dataset.name = sample_name
            session.add(dataset)
            session.flush()
            session.refresh(dataset)
            dataset.directory = "{}/Dataset_{}_{}".format(user.path.rstrip('/') , dataset.name, dataset.id)
            if not os.path.isdir(dataset.directory):
                os.mkdir(dataset.directory)
            for file_array in file_arrays: 
                            # first create a new db file to place the download in
                file_name = file_array[1]
                file_url = file_array[-1].replace('-->','')
                file_checksum = file_array[4]
                try:
                    response = urllib2.urlopen(file_url)
                except urllib2.HTTPError as err:
                    logger.error(err)
                    logger.error('The GSAF URLs may be stale. Try to download one file directly...')
                else: 
                    new_file = File()
                    new_file.url = file_url
                    new_file.name = file_name
                    new_file.file_type = parse_file_ext(new_file.name)
                    new_file.dataset_id = dataset.id
                    new_file.path = '{}/{}'.format(dataset.directory.rstrip('/'), new_file.name)
                    new_file.user_id = user_id
                    new_file.available = False 
                    new_file.status = ''

                    # if 'gz' in new_file.file_type.lower():
                    #     new_file.file_type = 'GZIPPED_FASTQ'

                    session.add(new_file)
                    session.commit()
                    session.refresh( new_file )
                    new_file_ids.append( new_file.id )

                    # add the new file to the dataset
                    dataset.files.append(new_file)

                    download_file( url = new_file.url, checksum=file_checksum, path = new_file.path, file_id = new_file.id, user_id = user_id, parent_task = task)

    # call create_datasets_from_JSON_string(json_string, project)
    return ReturnValue('import finished', file_ids=new_file_ids)

# @Dave - function to create datasets from a JSON file
# If the project is give, the datasets are added to the project
def create_datasets_from_JSON_string(json_string, project_id = None, dataset_id = None):

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
    new_datasets = [] 
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
        new_dataset.user_id = 2
        # new_dataset.user_id = current_user.id
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
        new_datasets.append(new_dataset)

        if project_id:
            project = db.session.query(Project).filter(id==project_id).first()
            new_relationship = ProjectDatasets(new_dataset, project)
            db.session.add(new_relationship)
            db.session.flush()
        else:
            print "Warning: new dataset {} not added to any project".format(new_dataset.id)

        if current_user:
            current_user.datasets.append(new_dataset)
            db.session.flush()
            db.session.refresh(current_user)

    db.session.commit() 
    if new_datasets == []: 
        return None
    else: 
        return new_datasets

@celery.task(base= LogTask, bind = True)
def test_function(self, analysis_id = None, user_id = None):

    logger = self.logger

    logger.info('Beginning test of logger stuff.')

    saved_stdout = sys.stdout
    sys.stdout = LoggerWriter( logger )

    test_print()

    sys.stdout = saved_stdout

    logger.info("Finished test of logger stuff.")



    return ReturnValue('Test completed successfully.')

def test_print():
    print "This is just a test."


# Adds all files in a directory (not already in database) to database
# Returns a list of file ids
# Automatically renames files and determines file type using a dictionary of regular expressions
def add_directory_files_to_database(directory = None, description = None, dataset_id = None, analysis_id = None, user_id = None, file_names = None, prefix = None, logger = celery_logger):

    # most file typing can be accomplished through this dictionary
    file_type_dict = {
        'gz' : 'GZIPPED_FASTQ' ,
        'cdr3_clonotype' : 'CDR3_CLONOTYPE' ,
        'cdr3list' : 'CDR3_LIST' ,
        'Gucken' : 'MSDB_TXT' ,
        'msDB' : 'MSDB_FASTA' ,
        'parsed_summary' : 'MSDB_SUMMARY' 
    }

    # Not implemented yet
    file_type_regex_dict = {
    }

    file_rename_regex_dict = {
        r'MASSSPECDB(\d+)msDB.fasta' : r'PREFIX_MSDB.fasta',
        r'cdr3_clonotype_list.txt' : r'PREFIX_cdr3_clonotype_list.txt',
        r'MASSSPECDB(\d+)malGucken.txt' : r'PREFIX_MSDB.txt',
        r'cdr3list.txt' : r'PREFIX_cdr3list.txt',
        r'MASSSPECDB(\d+)parsed_summary.txt' : r'PREFIX_parsed_summary.txt'
    }

    if file_names == None:
        file_names = next(os.walk(directory))[2]

    number_added_files = 0
    added_file_ids = []

    with session_scope() as session:

        # Get destination dataset and analysis, if provided
        if dataset_id: dataset = session.query(Dataset).get(dataset_id)
        if analysis_id: analysis = session.query(Analysis).get(analysis_id)

        for file_name in file_names:
            path = '{}/{}'.format(directory.rstrip('/'), file_name)

            if session.query(File).filter_by(path=path).count() > 0:
                # logger.info( 'File already in database: {}'.format(path) )
                pass
            else:
                # logger.info( 'Adding file to database: {}'.format(path) )

                # Step 1. Make sure the file exists on disk
                if os.path.isfile(path):

                    # Step 2. If the file exists on disk, rename the file if we have a rule for doing so
                    for find, replace in file_rename_regex_dict.iteritems():

                        pattern = re.compile(find)
                        pattern_match =  pattern.match(file_name)

                        if pattern_match:
                            new_file_name = re.sub( find, replace, file_name)

                            if prefix:
                                new_file_name = new_file_name.replace('PREFIX', prefix)
                            else:
                                new_file_name = new_file_name.replace('PREFIX_', '')

                            new_path = '{}/{}'.format(directory.rstrip('/'), new_file_name)

                            os.rename( path, new_path )

                            if os.path.isfile( new_path ):
                                logger.debug('Renamed file {} to {}'.format(path, new_path) )

                                path = new_path
                                file_name = new_file_name
                            else:
                                logger.warning('WARNING: failed to rename file {} to {}'.format(path, new_path) )


                    # Step 3. Add the file to the database

                    new_file = File()
                    new_file.name = file_name
                    new_file.description = description
                    new_file.dataset_id = dataset_id
                    new_file.user_id = user_id
                    new_file.analysis_id = analysis_id
                    new_file.path = path
                    new_file.available = True 
                    new_file.s3_status = ''
                    new_file.status = ''

                    # Use the default extension, unless we know better
                    new_file.file_type = parse_file_ext(new_file.name)
                    for search_str, file_type in file_type_dict.iteritems():
                        if search_str in file_name:
                            new_file.file_type = file_type

                    session.add(new_file)
                    session.commit()
                    session.refresh( new_file )
                    added_file_ids.append( new_file.id )
                    number_added_files += 1
                else:
                    logger.warning( 'WARNING: file not found: {}'.format(path) ) 
    return ReturnValue('{} files added to database.'.format(number_added_files), file_ids = added_file_ids )

@celery.task(base = LogTask, bind = True)
def create_analysis_zip_file(self, analysis_id, user_id):
    logger = self.logger

    # Do not set an analysis id for this task - it will overwrite the existing analysis log
    # self.task.analysis_id = analysis_id


    with session_scope() as session:
        analysis = session.query(Analysis).get(analysis_id)
        if not analysis:
            raise Exception('Error: Analysis {} not found.'.format( analysis_id ) )

        if analysis.zip_file_id != None:
            raise Exception('Error: Analysis {} already has a zip file.'.format( analysis_id ) )


        if analysis.files.count() == 0:
            return 'Analysis {} contains no files to zip.'.format( analysis_id )

        files_to_zip = []
        for file in analysis.files:
            if os.path.isfile(file.path):
                files_to_zip.append( file.path )

        if files_to_zip == []:
            return 'No files were found in the analysis directory {}'.format( analysis.directory )
        else:
            analysis_tarfile_name_prefix = analysis.name.replace(' ', '_')
            analysis_tarfile_path = '{}/{}.tar.gz'.format( analysis.directory.rstrip('/'), analysis_tarfile_name_prefix )

        analysis.zip_file = File(path = analysis_tarfile_path, file_type = 'TAR.GZ', dataset_id = analysis.dataset_id, analysis_id = analysis.id, user_id = user_id )
        analysis.zip_file.status = 'COMPRESSING'
        session.commit()

    logger.info('Creating tar.gz file for Analysis {}'.format(analysis_id) )

    analysis_tar = tarfile.open(analysis_tarfile_path, "w:gz")
    for file_path in files_to_zip:
        logger.info('Adding {} to tar.gz file...'.format( os.path.basename(file_path) ) )
        analysis_tar.add(file_path)
    analysis_tar.close()

    if not os.path.isfile(analysis_tarfile_path):
        logger.info( 'Finished compression for Analysis {}'.format(analysis_id) )

        return 'Failed to create {}'.format( analysis_tarfile_path )
    else:
        with session_scope() as session:
            analysis = session.query(Analysis).get(analysis_id)
            analysis.zip_file.validate()
            analysis.zip_file.status = 'AVAILABLE'
            session.commit()
            zip_file_id = analysis.zip_file.id

            logger.info( 'Finished compression for Analysis {}'.format(analysis_id) )

    return 'Completed compression of {} analysis files. Saved result as {} in file {}'.format( len(files_to_zip), analysis_tarfile_path, zip_file_id )

@celery.task(base = LogTask, bind = True)
def run_analysis_pipeline(self, *args,  **kwargs):

    if self.parent_task:
        task = self.parent_task
    else:
        task = self

    logger = self.logger

    user_id = kwargs['user_id']
    file_source = kwargs['file_source']
    dataset = kwargs['dataset']
    if dataset and dataset != []: dataset = dataset[0]
    dataset_files = kwargs['dataset_files']

    name = kwargs['name']
    description = kwargs['description']
    output_dataset = kwargs['output_dataset']
    output_project = kwargs['output_project']
    ncbi_accession = kwargs['ncbi_accession']
    ncbi_chain = kwargs['ncbi_chain']
    download_url = kwargs['download_url']
    download_chain = kwargs['download_chain']
    gsaf_url = kwargs['gsaf_url']
    gsaf_chain = kwargs['gsaf_chain']
    trim = kwargs['trim']
    trim_slidingwindow = kwargs['trim_slidingwindow']
    trim_slidingwindow_size = kwargs['trim_slidingwindow_size']
    trim_slidingwindow_quality = kwargs['trim_slidingwindow_quality']
    trim_illumina_adapters = kwargs['trim_illumina_adapters']
    filter = kwargs['filter']
    filter_percentage = kwargs['filter_percentage']
    filter_quality = kwargs['filter_quality']
    pandaseq = kwargs['pandaseq']
    analysis_type = kwargs['analysis_type']
    description = kwargs['description']
    pandaseq_algorithm = kwargs['pandaseq_algorithm']
    cluster = kwargs['cluster']
    species = kwargs['species']
    loci = kwargs['loci']
    generate_msdb = kwargs['generate_msdb']
    pair_vhvl = kwargs['pair_vhvl']
    msdb_cluster_percent = float( kwargs['msdb_cluster_percent'] )
    require_cdr1 = kwargs['require_cdr1']
    require_cdr2 = kwargs['require_cdr2']
    require_cdr3 = kwargs['require_cdr3']
    vhvl_min = float( kwargs['vhvl_min'] )
    vhvl_max = float( kwargs['vhvl_max'] )
    vhvl_step = float( kwargs['vhvl_step'] )

    ##### Obtain Files for Analysis #####
    file_ids_to_analyze = []
    analysis_id = None

    with session_scope() as session:

        # get the current user
        current_user = session.query(User).get(user_id)
        if not current_user:
            raise Exception('User with id {} not found.'.format(user_id))

        # get the target dataset
        if output_dataset and output_dataset.isdigit():
            output_dataset = int(output_dataset)
        else:
            logger.info( str( type(output_dataset) ) )
            logger.info( output_dataset )
            raise Exception( 'Invalid format for output dataset: {}'.format(output_dataset) )

        dataset = session.query(Dataset).get(output_dataset)
        if not dataset:
            raise Exception( 'Could not find dataset {}.'.format(output_dataset) )
        # not going to check dataset permission, was checked in frontend after form submission

        if file_source =='file_dataset':
            if dataset_files and dataset_files != []:
                for file_id in dataset_files:
                    if type(file_id) == str and file_id.isdigit(): file_id = int(file_id)
                    file = session.query(File).get(file_id)
                    if not file:
                        raise Exception( 'File with id {} not found.'.format(file_id) )
                    else:
                        file_ids_to_analyze.append(file_id)

                    # add file to the output dataset if it's not in there already
                    if file not in dataset.files:
                        dataset.files.append(file)
            else:
                raise Exception('No files given for analysis.')

        elif file_source =='file_gsaf':
            raise Exception ('Upload from GSAF URL not currently supported.')
            pass # call GSAF script here
        elif file_source =='file_url':

            # first create a new db file to place the download in
            new_file = File()
            new_file.url = download_url.rstrip()
            new_file.name = new_file.url.split('/')[-1].split('?')[0]
            new_file.file_type = parse_file_ext(new_file.name)
            new_file.description = description
            new_file.chain = download_chain
            new_file.dataset_id = output_dataset
            new_file.path = '{}/{}'.format(current_user.path.rstrip('/'), new_file.name)
            new_file.user_id = user_id
            new_file.available = False 
            new_file.status = ''

            if 'gz' in new_file.file_type.lower():
                new_file.file_type = 'GZIPPED_FASTQ'

            session.add(new_file)
            session.commit()
            session.refresh( new_file )
            file_ids_to_analyze.append( new_file.id )

            # add the new file to the dataset
            dataset.files.append(new_file)

            download_file( url = new_file.url, path = new_file.path, file_id = new_file.id, user_id = user_id, parent_task = task)
        else: # file_source =='file_ncbi':
            return_value = import_from_sra(accession = ncbi_accession, name=ncbi_accession, user_id = user_id, chain = ncbi_chain, project_selection = str(output_project), dataset_selection = str(output_dataset), parent_task = task)
            file_ids_to_analyze = return_value.file_ids

        if file_ids_to_analyze == []:
            raise Exception('Unable to load files for analysis.')
        else:

            analysis = generate_new_analysis(
                user = current_user, 
                dataset = dataset, 
                directory = dataset.directory, 
                directory_prefix = 'Analysis_', 
                session = session,
                name = name,
                description = description,
                async_task_id = self.task.request_id)

            self.set_analysis_id(analysis_id)

            # Set other values
            if analysis.name == "" or analysis.name == None: 
                analysis.name = 'Analysis_{}'.format(analysis.id)
            analysis.program = analysis_type.upper()
            analysis.params = {}
            analysis.status = 'QUEUED'
            analysis.responses = []
            analysis.available = False
            session.commit()

            analysis_file_name_prefix = analysis.name.replace(' ', '_')
            analysis_json_path = '{}/{}_settings.json'.format( analysis.directory.rstrip('/'), analysis_file_name_prefix )

            with open(analysis_json_path, 'w') as json_file:
                json.dump( (args, kwargs) , json_file)

            if os.path.isfile( analysis_json_path ):
                analysis.settings_file = File( path = analysis_json_path, file_type = 'JSON', dataset_id = analysis.dataset_id, analysis_id = analysis.id, user_id = analysis.user_id )

            # Persist values for outside db session
            analysis_id = analysis.id
            dataset_id = dataset.id
            analysis_name = analysis.name
            analysis_directory = analysis.directory

    ##### Perform Pre-processing #####
    if trim:

        if trim_slidingwindow_size == '': trim_slidingwindow_size = 4
        if trim_slidingwindow_quality == '': trim_slidingwindow_quality = 15

        return_value = run_trim_analysis_with_files(analysis_id = analysis_id, file_ids = file_ids_to_analyze, logger = logger, trim_illumina_adapters = trim_illumina_adapters, trim_slidingwindow = trim_slidingwindow, trim_slidingwindow_size = trim_slidingwindow_size, trim_slidingwindow_quality = trim_slidingwindow_quality)
        file_ids_to_analyze = return_value.file_ids
        logger.info (return_value)

    if pandaseq:
        return_value = run_pandaseq_with_dataset_id(dataset_id, analysis_id = analysis_id, file_ids = file_ids_to_analyze, algorithm = pandaseq_algorithm, parent_task = task)
        file_ids_to_analyze = return_value.file_ids
        logger.info (return_value)

    if filter: 
        return_value = run_quality_filtering_with_dataset_id(dataset_id, analysis_id=analysis_id, file_ids=file_ids_to_analyze, minimum_percentage=filter_percentage, minimum_quality=filter_quality, parent_task = task)
        file_ids_to_analyze = return_value.file_ids 
        logger.info (return_value)

    ##### Perform Analysis #####
    if analysis_type == 'igrep':

        return_value = unzip_files( user_id = user_id, file_ids = file_ids_to_analyze, destination_directory = analysis_directory, logger = logger)
        file_ids_to_analyze = return_value.file_ids
        logger.info (return_value)

        return_value = run_igrep_annotation_on_dataset_files(dataset_id = dataset_id, file_ids = file_ids_to_analyze, user_id = user_id, analysis_id = analysis_id, species = species, logger = logger, parent_task = task)
        file_ids_to_analyze = return_value.file_ids
        logger.info (return_value)

    elif analysis_type == 'mixcr':
        return_value = run_mixcr_analysis_id_with_files(analysis_id = analysis_id, file_ids = file_ids_to_analyze, species = species, loci=loci, parent_task = task)
        file_ids_to_analyze = return_value.file_ids

    elif analysis_type == 'abstar':
    
        # Abstar requires unzipped files
        return_value = unzip_files( user_id = user_id, file_ids = file_ids_to_analyze, destination_directory = analysis_directory, logger = logger)
        file_ids_to_analyze = return_value.file_ids
        logger.info (return_value)

        # Run Abstar function
        return_value = run_abstar_analysis_id_with_files(user_id = user_id, analysis_id = analysis_id, file_ids = file_ids_to_analyze, species = species, parent_task = task)
        file_ids_to_analyze = return_value.file_ids
        logger.info (return_value)

    else:
        raise Exception( 'Analysis type "{}" cannot be performed.'.format(analysis_type) )

    ##### Perform Post-Processing #####
    if analysis_type == 'igrep':
        if generate_msdb:
            return_value = run_msdb_with_analysis_id( analysis_id = analysis_id, file_ids = file_ids_to_analyze, user_id = user_id, cluster_percent = msdb_cluster_percent, parent_task = self)

        if pair_vhvl:
            #return_value = run_pair_vhvl_with_dataset_id( analysis_id = analysis_id, file_ids = file_ids_to_analyze, user_id = user_id, parent_task = self)
            return_value = run_pair_vhvl_with_dataset_id( user_id= user_id, dataset_id = output_dataset, analysis_id = analysis_id, file_ids = file_ids_to_analyze, vhvl_min = vhvl_min, vhvl_max = vhvl_max, vhvl_step = vhvl_step, parent_task = self)

    ##### Add files to Appropriate Dataset/Project #####

    return ReturnValue( 'All analyses and processing completed.', file_ids = file_ids_to_analyze)

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
    app.run(host='0.0.0.0', port=5000, debug=True, threaded = app.config['THREADED'])


