# System Imports
import ast
import errno
import json
import logging
import os
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

os.environ['http_proxy'] = ''
import urllib2
import itertools
import subprocess
import math
from celery import Celery, Task, states
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger, ColorFormatter

from collections import defaultdict, OrderedDict

# Flask Imports
from werkzeug import secure_filename
from flask import Blueprint, render_template, flash, redirect, url_for, g
from flask import Flask, Blueprint, make_response, render_template, render_template_string, request, session, flash, \
    redirect, url_for, jsonify, get_flashed_messages, send_from_directory
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask.ext.mail import Mail, Message
from flask_bootstrap import Bootstrap
import random
import jinja2

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


# Local Imports - local imports go here to prevent circular imports 
from forms import *
from functions import *
from models import *

from utils.standardization import *
from utils.clustering import *
from utils.pairing import *


# Initialize Application
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
# Initialize extensions
bcrypt = Bcrypt(app)
Bootstrap(app)

db.init_app(app)
db.app = app
engine = db.engine
Session = sessionmaker(bind=engine)

mail = Mail(app)


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
templateLoader = jinja2.FileSystemLoader(searchpath="{}/templates".format(app.config['HOME']))
templateEnv = jinja2.Environment(loader=templateLoader, extensions=['jinja2.ext.with_'])

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


def format_datetime(value, format='just_day'):
    d = datetime.datetime(value)  # .fromordinal(730920) # 730920th day after 1. 1. 0001
    if format == 'just_day':
        out = d.strftime("%d/%m/%y")
    else:
        out = d.strftime("%d/%m/%y %H:%M")
    return out


app.jinja_env.filters['datetime'] = format_datetime

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


### Time responses

# @app.before_request
# def before_request():
#     g.request_response_start = time.time()


# @app.teardown_request
# def teardown_request(exception=None):
#     diff = time.time() - g.request_response_start
#     print '{} seconds to resolve request: '.format(str(diff))


# Flask-Login use this to reload the user object from the user ID stored in the session
@login_manager.user_loader
def load_user(email):
    user = db.session.query(User).filter_by(email=email).first()
    if user:
        return user
    else:
        return None



@login_manager.unauthorized_handler

def unauthorized():
    flash('You must login or register to view that page.', 'success')
    return redirect(url_for('frontend.login'))


def initiate_celery_task_logger(logger_id, logfile):
    logger = get_task_logger(logger_id)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    logger.handlers = []
    handler = logging.FileHandler(logfile)
    handler.setLevel(logging.INFO)

    formatter = ColorFormatter
    format = '[%(asctime)s: %(levelname)s %(funcName)s] %(message)s'
    handler.setFormatter(formatter(format, use_color=False))
    logger.addHandler(handler)

    stdout_handler = logging.StreamHandler(sys.stdout)
    format = '%(message)s'
    stdout_handler.setFormatter(formatter(format, use_color=True))
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
    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message != '\n':
            self.logger.log(self.level, message)


# Used to redirect stdout to the logger
class LoggerWriterRedirect(LoggerWriter):
    def __init__(self, logger, level=logging.INFO, task=None):
        self.logger = logger
        self.level = level
        self.task = task
        self.tracking_status = False

    def write(self, message):
        if self.task:
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
                    celery_logger.debug('User Id: {}'.format(user_id))

                    try:
                        user = session.query(User).get(user_id)
                    except:
                        time.sleep(1)
                        user = session.query(User).get(user_id)
                    if user:
                        self.user_found = True
                        logfile = '{}/{}.log'.format(user.log_path.rstrip('/'), logger_id)
                        celery_logger.debug('Starting log file at {}'.format(logfile))
                    else:
                        user_found = False
                        celery_logger.warning(
                            'Warning({}): User ID ({}) not found. The decorator "log_celery_task" cannot log information without a user_id passed parametrically to the function decorated.'.format(
                                f.func_name, kw['user_id']))

                        if not os.path.isdir('/data/logs/'):
                            os.makedirs('/data/logs/')

                        logfile = '/data/logs/{}.log'.format(request_id)
                else:
                    celery_logger.warning(
                        'Warning({}): The decorator "log_celery_task" cannot log information without a user_id passed parametrically to the function decorated.'.format(
                            self.__class__.__name__))

                    if not os.path.isdir('/data/logs/'):
                        os.makedirs('/data/logs/')

                    logfile = '/data/logs/{}.log'.format(self.request_id)

                logger = initiate_celery_task_logger(logger_id=logger_id, logfile=logfile)
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

                self.update_state(state='STARTED', meta={'status': 'Task Started'})

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
                    self.celery_task.result = '{}: {}'.format(exception_type_name, exc)
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
                                analysis_logfile_path = '{}/{}.log'.format(analysis.directory.rstrip('/'),
                                                                           analysis_file_name_prefix)
                                copyfile(self.logfile, analysis_logfile_path)
                            if os.path.isfile(analysis_logfile_path):
                                analysis.log_file = File(path=analysis_logfile_path, file_type='LOG',
                                                         dataset_id=analysis.dataset_id, analysis_id=analysis.id,
                                                         user_id=self.user_id)

                            # Save the trackback
                            if einfo and einfo.traceback:
                                analysis_traceback_path = '{}/{}_traceback.txt'.format(analysis.directory.rstrip('/'),
                                                                                       analysis_file_name_prefix)

                                with open(analysis_traceback_path, "w") as traceback_file:
                                    traceback_file.write(einfo.traceback)

                                if os.path.isfile(analysis_traceback_path):
                                    analysis.traceback_file = File(path=analysis_traceback_path, file_type='TRACEBACK',
                                                                   dataset_id=analysis.dataset_id,
                                                                   analysis_id=analysis.id, user_id=self.user_id)

                    session.commit()

    def on_success(self, retval, task_id, args, kwargs):
        if self.maintain_log:

            with session_scope() as session:

                # Close Database Record
                if self.user_found:
                    result = celery.AsyncResult(task_id)
                    print 'On Success Result Status: {}'.format(result.status)

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
                                analysis_logfile_path = '{}/{}.log'.format(analysis.directory.rstrip('/'),
                                                                           analysis_file_name_prefix)
                                copyfile(self.logfile, analysis_logfile_path)
                            if os.path.isfile(analysis_logfile_path):
                                analysis.log_file = File(path=analysis_logfile_path, file_type='LOG',
                                                         analysis_id=analysis.id, user_id=self.user_id)
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


def link_file_to_user(path, user_id, name, dataset_id=None):
    file = File()
    file.name = name
    file.path = path
    file.user_id = user_id
    file.description = ''
    file.file_type = parse_file_ext(file.path)
    file.available = True
    file.chain = parse_name_for_chain_type(name)
    file.dataset_id = dataset_id
    db.session.add(file)
    db.session.commit()
    return True


# returns a string if unable to create the user directories
# returns false otherwise. 
@celery.task
def instantiate_user_with_directories(new_user_id):
    new_user = db.session.query(User).filter(User.id == new_user_id).first()

    for path in new_user.all_paths:
        try:
            if not os.path.isdir(path):
                os.makedirs(path)
                print 'Created new directory at {}'.format(path)
        except ValueError, error:
            return 'Failed to create directory {}: {}'.format(path, error)


def get_user_dataset_dict(user):
    datadict = OrderedDict()
    for dataset in sorted(user.get_ordered_datasets(), key=lambda x: x.id, reverse=True):
        if dataset.name != '__default__':
            datadict[dataset] = sorted(dataset.files.all(), key=lambda x: x.file_type)
    return datadict


@celery.task(base=LogTask, bind=True)
def import_from_sra(self, accession=None, name=None, user_id=57, chain=None, project_selection=None, project_name=None,
                    project_description=None, dataset_selection=None):
    logger = self.logger
    user = db.session.query(User).filter(User.id == user_id).first()

    if not user:
        raise Exception("Unable to find user with id {}.".format(user_id))

    file_dataset = None
    if dataset_selection == 'new' or dataset_selection == None or dataset_selection == 'None':
        dataset = generate_new_dataset(user=user, session=db.session, name=accession,
                                       description="NCBI SRA Accession {}".format(accession))
        file_dataset = dataset
        logger.info('SRA Downloads will be added to dataset "{}".'.format(dataset.name))
    else:  # check if the user has selected a dataset which they have access to
        dataset = db.session.query(Dataset).get(int(dataset_selection))
        if dataset.user_has_write_access(user):
            file_dataset = dataset
        else:
            logger.error('You do not have permission to add a file to dataset ({}).'.format(dataset_selection))

    # now do the same with projects, with the qualification that we add the dataset to the project if it's not there already
    # check if the user has selected the default project (i.e., the user has no projects)
    if file_dataset:
        if project_selection == 'new' or project_selection == None or project_selection == 'None':
            output_project = generate_new_project(user=user, datasets=dataset, name=project_name,
                                                  description=project_description, session=db.session)
        else:
            output_project = db.session.query(Project).get(int(project_selection))
            if output_project.user_has_write_access(user):
                if file_dataset not in output_project.datasets:
                    output_project.datasets.append(file_dataset)
                    db.session.commit()
            else:
                logger.error('Error: you do not have permission to add a dataset to that project ({}).'.format(
                    project_selection))

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
        logger.info('Creating directory {}'.format(directory))
        os.makedirs(directory)

    if os.path.isfile(path):
        path = os.path.splitext(path)[0] + '_1' + os.path.splitext(path)[1]

    logger.info('Fetching SRA data from NCBI {}'.format(accession))
    command = "/data/resources/software/sratoolkit.2.8.1-2/bin/fastq-dump -I --gzip --defline-qual '+' --split-files -T --outdir {} {}".format(
        directory, accession)

    logger.info(command)

    # response = os.system(command)
    command_line_args = shlex.split(command)
    command_line_process = subprocess.Popen(command_line_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            bufsize=1)
    for line in iter(command_line_process.stdout.readline, b''):
        line = line.strip()
        logger.info(line.strip())
    response, error = command_line_process.communicate()
    command_line_process.stdout.close()
    command_line_process.wait()

    if error == None:
        file_paths = []
        dirs = os.listdir('{}/{}'.format(directory, accession))
        if dirs == ['1']:
            # flatten and clean up the directory tree:
            source = '{}/{}/1/fastq.gz'.format(directory, accession)
            destination = '{}/{}_1.fastq.gz'.format(directory, accession)
            os.rename(source, destination)

            file_paths = [destination]
            # filename_array = ['{}_1.fastq.gz'.format(accession)]

            os.rmdir('{}/{}/1/'.format(directory, accession))
            os.rmdir('{}/{}/'.format(directory, accession))

        if dirs == ['1', '2'] or dirs == ['2', '1']:

            file_paths = []
            filename_array = []

            for directory_number in dirs:
                # flatten and clean up the directory tree:
                source = '{}/{}/{}/fastq.gz'.format(directory, accession, directory_number)
                destination = '{}/{}_{}.fastq.gz'.format(directory, accession, directory_number)
                os.rename(source, destination)

                file_paths.append(destination)
                # filename_array.append('{}_{}.fastq.gz'.format(accession, directory_number))

                os.rmdir('{}/{}/{}/'.format(directory, accession, directory_number))

            os.rmdir('{}/{}/'.format(directory, accession))


        else:
            raise Exception('Number of files from SRA export not one or two...')
        logger.info('Writing sra output files to {}'.format(directory))
        return_value = import_files_as_dataset(filepath_array=file_paths, user_id=user_id, name=name,
                                               chain=chain, dataset=file_dataset, parent_task=self)
        logger.info('SRA import complete.')

        print return_value.__dict__

        file_ids = return_value.file_ids

        return ReturnValue('Dataset from SRA Accession {} created for user {}'.format(accession, user.username),
                           file_ids=file_ids)
    else:
        raise Exception('fastq-dump command failed:'.format(error))


@celery.task(base=LogTask, bind=True)
def import_files_as_dataset(self, filepath_array=[], user_id=2, chain=None, name=None, dataset=None,
                            remove_original=False, project=False, paired=False):
    logger = self.logger


    current_user = db.session.query(User).filter(User.id == user_id).first()

    if not current_user:
        raise Exception("Error: user with id {} not found.".format(user_id))

    if filepath_array == []:
        raise Exception("Filepath array to ingest was empty [].")

    if not dataset:
        d = generate_new_dataset(user=current_user, name=name, description='Dataset Imported From Server Files')
    elif type(dataset)==int:
        d = Dataset.query.get(d)
    else:
        d = dataset

    logger.info("Working with dataset {}".format(d.__dict__))

    if paired: d.paired=True

    if project:
        if type(project)==int:
            p = Project.query.get(project)
        else:
            p = project
        pd = ProjectDatasets(dataset=d, project=p)
        db.session.add(pd)

    # if not os.path.exists(d.directory):
    #     logger.info('Making directory {}'.format(d.directory))
    #     os.makedirs(d.directory)
    # db.session.commit()

    new_file_ids = []
    for index, path in enumerate(filepath_array):
        if os.path.isfile(path):
            logger.info('Importing file {} and linking to dataset {}'.format(path, d.name))
            file_name = path.split('/')[-1]
            new_path = d.directory + '/' + file_name
            file = File(name=file_name, path=new_path, user_id=current_user.id, dataset_id=d.id, check_name=False)
            logger.info(file.__dict__)
            file.validate()
            db.session.add(file)
            logger.info('Copying file {} to new dataset path: {}'.format(file.name, file.path))
            from shutil import copyfile
            copyfile(path, new_path)
            # os.rename(path, new_path) # would move file, removing old path
            file.validate()
            db.session.commit()
            new_file_ids.append(file.id)
    d.primary_data_files_ids = new_file_ids
    db.session.commit()
    return ReturnValue('Files copied and added to Dataset {} ({}): {}'.format(d.id, d.directory, new_file_ids), file_ids=new_file_ids)



def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


@celery.task(base=LogTask, bind=True)
def download_file(self, url, path, file_id, checksum=None, user_id=None):
    logger = self.logger

    logger.info('Downloading file from: {}'.format(url))

    # check if the directory for the file exists. If not, make the directory path with makedirs
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        logger.info('Creating directory: {}'.format(directory))
        os.makedirs(directory)

    logger.info('Downloading file to directory: {}'.format(directory))

    # you can try the following large files
    # ftp://ftp.ddbj.nig.ac.jp/ddbj_database/dra/fastq/SRA143/SRA143000/SRX478835/SRR1179882_2.fastq.bz2
    # http://hgdownload.cse.ucsc.edu/goldenPath/hg38/bigZips/refMrna.fa.gz
    response = urllib2.urlopen(url)
    total_size = response.info().getheader('Content-Length').strip()
    total_size = int(total_size)
    bytes_so_far = 0
    logger.info('Target file size: {}'.format(total_size))

    # Initiate the download bar
    # self.update_state(state='PROGRESS', meta={'status': 'Downloading', 'current' : str(0), 'total' : str(1), 'units' : 'bytes' })

    CHUNK = 16 * 1024
    with open(path, 'wb') as outfile:
        while True:
            chunk = response.read(CHUNK)
            if not chunk: break
            outfile.write(chunk)
            bytes_so_far += len(chunk)

            # Send a progress message with the number of bytes downloaded.
            self.update_state(state='PROGRESS',
                              meta={'status': 'Downloading', 'current': str(bytes_so_far), 'total': str(total_size),
                                    'units': 'bytes'})

    # This status will take down the progress bar and show that the download is complete.
    self.update_state(state='SUCCESS', meta={'status': 'Download complete.'})

    f = db.session.query(File).filter(File.id == file_id).first()

    if os.path.isfile(f.path):
        if checksum:
            if md5(f.path) == checksum:
                logger.info('File {} Checksums Agree {}'.format(f.path, checksum))
                f.available = True
            else:
                logger.warning('File {} Checksums Disagree!'.format(f.path))
                f.available = False
        f.file_size = os.path.getsize(f.path)
        logger.info('Download finished.')
    else:
        # Alternatively, delete file here
        f.available = False
        f.file_size = 0
        logger.error('Failed to download file {}: file not found.'.format(f.path))

    db.session.commit()
    return 'File download complete.'



@celery.task(base=LogTask, bind=True)
def run_mixcr_analysis_id_with_files(self, analysis_id, file_ids, species=None, loci=None):
    logger = self.logger
    self.set_analysis_id(analysis_id)

    analysis = db.session.query(Analysis).filter(Analysis.id == analysis_id).first()
    files = [db.session.query(File).get(file_id) for file_id in file_ids]
    dataset = analysis.dataset

    if species == None:
        if dataset.species == 'Human':
            species = 'hsa'
        elif dataset.species == 'Mouse':
            species = 'mmu'
        else:
            species = 'hsa'
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
        loci = loci.replace('TCR', 'TR', 99)

    if not analysis:
        raise Exception('MixCR Exception: Analysis with ID {} cannot be found.'.format(analysis_id))
    analysis_name = 'Analysis_{}'.format(analysis_id)

    files_to_execute = []
    logger.info('Running MiXCR on these files: {}'.format(files))

    for i, file in enumerate(files):
        # if multiple files names  XXXX.R1.fastq and XXXX.R2.fastq are given, this will fail: 
        basename = file.path.split('/')[-1].split('.')[0]
        basepath = '{0}/{1}'.format(analysis.directory.rstrip('/'), basename)
        logger.info('Writing output files to base name: {}'.format(basepath))
        print 'Base Path: {}'.format(basepath)
        print 'Base Name: {}'.format(basename)

        # Instantiate Produt Files
        output_files = []
        alignment_file = File()
        alignment_file.user_id = dataset.user_id
        alignment_file.path = '{}.mixcr'.format(basepath)
        alignment_file.name = "{}.mixcr".format(basename)
        # MIGHT NEED TO ADD THIS ARGUMENT to align (from costas)   -OjParameters.parameters.mapperMaxSeedsDistance=5 
        alignment_file.command = '{} align -t 6 -OjParameters.parameters.mapperMaxSeedsDistance=5 --chains {} --species {} --save-description -f {} {}'.format(
            app.config['MIXCR'], loci, species, file.path, alignment_file.path)
        alignment_file.file_type = 'MIXCR_ALIGNMENTS'
        output_files.append(alignment_file)
        # clone_index_file = File()
        # clone_index_file.user_id = dataset.user_id
        # clone_index_file.file_type = 'MIXCR_CLONE_INDEX'
        # clone_index_file.path = '{}.aln.clns.index'.format(basepath)
        # clone_index_file.name = '{}.aln.clns.index'.format(basename)
        # clone_index_file.command = 'echo "Indexing Done On Clone Assemble Step"'
        # clone_file = File()
        # clone_file.user_id = dataset.user_id
        # clone_file.file_type = 'MIXCR_CLONES'
        # clone_file.path = '{}.clns.mixcr'.format(basepath)
        # clone_file.name = '{}.clns.mixcr'.format(basename)
        # clone_file.command = '{} assemble  -OassemblingFeatures=VDJRegion -f {} {}'.format(app.config['MIXCR'],
        #                                                                                    alignment_file.path,
        #                                                                                    clone_file.path)
        # output_files.append(clone_file)
        # output_files.append(clone_index_file)
        db.session.add(alignment_file)
        # db.session.add(clone_file)
        db.session.commit()
        # Commit To Get Parent IDs
        # clone_output_file = File()
        # clone_output_file.user_id = dataset.user_id
        # clone_output_file.parent_id = clone_file.id
        # clone_output_file.path = '{}.txt'.format(clone_file.path)
        # clone_output_file.file_type = 'MIXCR_CLONES_TEXT'
        # clone_output_file.name = '{}.txt'.format(clone_file.name)
        # clone_output_file.command = '{} exportClones -sequence -quality -s --preset full {} {}'.format(
        #     app.config['MIXCR'], clone_file.path, clone_output_file.path)
        # output_files.append(clone_output_file)
        alignment_output_file = File()
        alignment_output_file.user_id = dataset.user_id
        alignment_output_file.parent_id = alignment_file.id
        alignment_output_file.path = '{}.txt'.format(alignment_file.path)
        alignment_output_file.file_type = 'MIXCR_ALIGNMENT_TEXT'
        alignment_output_file.name = '{}.txt'.format(alignment_file.name)
        alignment_output_file.command = '{} exportAlignments  -s --preset-file /data/resources/software/BIGGDATA/utils/mixcr_output_presets.txt {} {}'.format(
            app.config['MIXCR'], alignment_file.path, alignment_output_file.path)
        output_files.append(alignment_output_file)
        # pretty_alignment_file = File()
        # pretty_alignment_file.user_id = dataset.user_id    
        # pretty_alignment_file.parent_id = alignment_file.id 
        # pretty_alignment_file.path = '{}.pretty.txt'.format(alignment_file.path)
        # pretty_alignment_file.file_type = 'MIXCR_PRETTY_ALIGNMENT_TEXT'
        # pretty_alignment_file.name =  '{}.pretty.txt'.format(alignment_file.name)
        # pretty_alignment_file.command = 'mixcr exportAlignmentsPretty {} {}'.format(alignment_file.path, pretty_alignment_file.path)
        # output_files.append(pretty_alignment_file)

        for f in output_files:
            f.dataset_id = file.dataset_id
            f.analysis_id = analysis.id
            f.chain = file.chain
            files_to_execute.append(f)

    # make sure we dont overwrite similarly named files (those with .R1. and .R2. instead of _R1 _R2)
    duplicate_paths = set([path for path in map(lambda f: f.path, files_to_execute) if
                           map(lambda f: f.path, files_to_execute).count(path) > 1])
    if len(duplicate_paths) > 0:
        new_files = []
        duplicate_files = []
        for file in files_to_execute:
            if file.path in duplicate_paths:
                duplicate_files.append(file)
            else:
                new_files.append(file)
        for i, file in enumerate(duplicate_files):
            file.path = "{}.mixcr".format(i).join(file.path.split('mixcr'))
            file.name = "{}.mixcr".format(i).join(file.name.split('mixcr'))
            new_files.append(file)
        files_to_execute = new_files

    analysis.status = 'EXECUTING'
    db.session.commit()

    output_file_ids = []
    execution_error = False

    for f in files_to_execute:
        f.command = f.command.encode('ascii')

        logger.info('Executing: {}'.format(f.command))
        analysis.active_command = f.command
        f.in_use = True
        db.session.add(f)
        db.session.commit()

        # MAKE THE CALL *****
        # response = os.system(f.command)
        error = None
        try:
            command_line_args = shlex.split(f.command)
            command_line_process = subprocess.Popen(command_line_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                    bufsize=1)

            for line in iter(command_line_process.stdout.readline, b''):
                line = line.strip()

                tracking_percent = False
                tracking = True
                if 'Exception' in line:
                    logger.error(line)
                    execution_error = True
                elif 'Error' in line:
                    logger.error(line)
                    execution_error = True
                elif ('Alignment:' in line or 'Exporting alignments:' in line or 'Assembling initial clonotypes:' in line or 'Exporting clones:' in line) & ('%' in line):
                    tracking_percent = True
                    tracking_status, line = line.split(':', 1)
                    if line.endswith('%'):
                        percent = line.replace('%', '')
                        eta = ''
                    else:
                        percent, eta = line.split('%', 1)
                        eta = ' ({})'.format(eta.strip())
                    self.update_state(state='PROGRESS',
                                      meta={'status': '{}{}'.format(tracking_status, eta), 'current': float(percent),
                                            'total': 100, 'units': '%'})
                    print '{} ({}): {}/{}'.format(tracking_status, eta, percent, 100)
                else:
                    tracking_percent = False
                    self.update_state(state='RUNNING',
                                      meta={'status': 'Executing MiXCR'})
                    logger.info(line)

            response, error = command_line_process.communicate()
            command_line_process.stdout.close()
            command_line_process.wait()
        except subprocess.CalledProcessError as error:
            error = error.output
            logger.error(error)

        if tracking_percent:
            tracking_percent = False
            self.update_state(state='RUNNING',
                              meta={'status': 'Executing MiXCR'})
            logger.info('{} complete.'.format(tracking_status))

        if error == None and os.path.isfile(f.path):
            f.available = True
            f.file_size = os.path.getsize(f.path)
            db.session.commit()
            db.session.refresh(f)
            if f.file_type == 'MIXCR_ALIGNMENT_TEXT':
                output_file_ids.append(f.id)
        else:
            if error != None:
                logger.error(error)
            elif os.path.isfile(f.path):
                logger.error('Error: Unable to find output file {}'.format(f.path))
            f.available = False
            analysis.status = 'FAILED'
            db.session.commit()
    logger.info('All commands in analysis {} have been executed.'.format(analysis))
    if set(map(lambda f: f.available, files_to_execute)) == set([True]) :
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
        return ReturnValue('MiXCR encountered errors while processing.', file_ids=output_file_ids)
    else:
        return ReturnValue('MiXCR analysis completed successfully.', file_ids=output_file_ids)


# While Abstar has pairing ability (it uses PANDAseq), this function presumes that all files have already
# been preprocessed (e.g., all pairing has already been performed by PANDAseq)
@celery.task(base=LogTask, bind=True)
def run_abstar_analysis_id_with_files(self, user_id=None, analysis_id=None, file_ids=[], species=None):
    logger = self.logger

    with session_scope() as session:
        analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
        files = [session.query(File).get(file_id) for file_id in file_ids]
        dataset = analysis.dataset

        if species == None:
            if dataset.species == 'Human':
                species = 'human'
            elif dataset.species == 'Mouse':
                species = 'mouse'
            else:
                species = 'human'
        elif species == 'M. musculus':
            species = 'mouse'
        elif species == 'H. sapiens':
            species = 'human'
        else:
            species = 'human'

        if not analysis:
            raise Exception('Abstar Exception: analysis with ID {} not found.'.format(analysis_id))
        analysis_name = 'Analysis_{}'.format(analysis_id)

        files_to_execute = []
        logger.debug('Running Abstar on these files: {}'.format(files))

        path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
        path = path.replace('///', '/')
        path = path.replace('//', '/')

        basename = analysis_name
        basepath = analysis.directory
        logger.debug('Writing output files to base name: {}'.format(basepath))
        files_to_execute = []

        for file in files:
            if file.file_type == 'GZIPPED_FASTQ':
                logger.warning('Cannot run Abstar analysis with zipped files, skipping file {}'.format(file.path))
            else:
                new_file = File()
                new_file.user_id = dataset.user_id

                new_file.path = '{}/{}'.format(basepath.rstrip('/'), os.path.splitext(file.name)[0] + ".json")
                new_file.name = "{}".format(os.path.splitext(file.name)[0] + ".json")
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
        logger.info('Executing: {}'.format(file.command))

        # MAKE THE CALL *****
        # response = os.system(f.command)
        error = None
        try:
            command_line_args = shlex.split(file.command)
            command_line_process = subprocess.Popen(command_line_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                    bufsize=1)

            line = ''
            vdj_started = False
            vdj_finished = False

            vdj_progress_pattern = re.compile('\(([0-9]*)/([0-9]*)\)([^0-9]+)([0-9]+%)')

            process_executing = True

            while process_executing:

                # nextline = command_line_process.stdout.readline()
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
                        self.update_state(state='RUNNING')
                        logger.info(line.rstrip())
                        line = ''

                    elif char == '%':
                        line = line.strip()
                        progress_match = vdj_progress_pattern.match(line)

                        if progress_match:
                            current_job = progress_match.group(1)
                            total_jobs = progress_match.group(2)
                            current_percent = progress_match.group(4).rstrip('%')

                            self.update_state(state='PROGRESS',
                                              meta={'status': '{}/{} jobs '.format(current_job, total_jobs),
                                                    'current': int(current_percent), 'total': 100, 'units': '%'})

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
                logger.error('Abstar Error: failed to create output file {}'.format(file.path))

        else:
            file.available = False
            analysis.status = 'FAILED'
    logger.info('All commands in analysis {} have been executed.'.format(analysis))
    if set(map(lambda file: file.available, files_to_execute)) == set([True]) :
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
    return ReturnValue('Abstar analysis completed successfully.', file_ids=output_file_ids)


@celery.task(base=LogTask, bind=True)
def standardize_output_files(self, user_id=None, analysis_id=None, file_ids=None, append_ms_peptides=False,
                             rmindels=True, require_annotations=['aaSeqCDR3'], *args, **kwargs):
    if self.parent_task:
        task = self.parent_task
    else:
        task = self
    logger = self.logger

    ##### Obtain Files for Analysis #####
    if not file_ids:
        logger.warning('No File Ids To Standardize?')

    with session_scope() as session:

        files_to_standardize = []
        for file_id in file_ids:
            files_to_standardize.append(session.query(File).get(file_id))
        logger.info('Standardizing {} files: {}'.format(str(len(files_to_standardize)),
                                                        ','.join(map(lambda f: f.name, files_to_standardize))))
        standardized_file_ids = []
        for file in files_to_standardize:
            logger.info('Standardizing file {} and adding to Dataset id {}, Analysis {}'.format(str(file.name),
                                                                                                str(file.dataset_id),
                                                                                                str(file.analysis_id)))
            if 'IGFFT' in file.file_type:
                df = build_annotation_dataframe_from_igfft_file(file.path, rmindels=rmindels,
                                                                append_ms_peptides=append_ms_peptides,
                                                                require_annotations=require_annotations)
            if 'MIXCR' in file.file_type:
                df = build_annotation_dataframe_from_mixcr_file(file.path, rmindels=rmindels,
                                                                append_ms_peptides=append_ms_peptides,
                                                                require_annotations=require_annotations)

            def add_bigg_txt(string):
                return string.replace('.txt', '', 99) + '.bigg.txt'

            new_file = File(name=add_bigg_txt(file.name), directory=file.directory, path=add_bigg_txt(file.path),
                            file_type='BIGG_ANNOTATION', dataset_id=file.dataset_id, analysis_id=file.analysis_id,
                            user_id=user_id, parent_id=file.id, check_name=False)
            logger.info('Writing standardized file to path: {}'.format(new_file.path))
            df.to_csv(new_file.path, sep='\t', index=False)
            session.add(new_file)
            session.commit()
            standardized_file_ids.append(new_file.id)
        return_value = ReturnValue('{} Files Standardized.'.format(len(standardized_file_ids)),
                                   file_ids=standardized_file_ids)

    return return_value


@celery.task(base=LogTask, bind=True)
def pair_annotation_files_with_analysis_id(self, user_id=None, analysis_id=None, file_ids=None, *args, **kwargs):
    if self.parent_task:
        task = self.parent_task
    else:
        task = self
    logger = self.logger

    ##### Obtain Files for Analysis #####
    if not file_ids:
        logger.warning('No File Ids To Pair?')
    if len(file_ids) != 2:
        logger.warning('Something other than two files supplied. Can only pair 2 files...')
        return ReturnValue("Must supply two annotation files for pairing", file_ids=None)

    with session_scope() as session:

        files_to_pair = []
        for file_id in file_ids:
            files_to_pair.append(session.query(File).get(file_id))
        file = files_to_pair[0]
        logger.info('Pairing these {} files for Dataset {} and Analysis {}: {}'.format(str(len(files_to_pair)),
                                                                                       str(files_to_pair[0].dataset_id),
                                                                                       str(analysis_id), ','.join(
                map(lambda f: f.name, files_to_pair))))
        # Briefly redirect stdout to logger to capture function output
        saved_stdout = sys.stdout
        sys.stdout = LoggerWriterRedirect(logger, task=self)
        paired_df = pair_annotation_files(files_to_pair[0].path, files_to_pair[1].path)
        # Restore STDOUT to the console
        sys.stdout = saved_stdout

        def add_paired_txt(string): return string.replace('_R1', '').replace('_R2', '').replace('R1', '').replace('R2',
                                                                                                                  '').replace(
            '.R1.', '.').replace('.R2.', '.').replace('.txt', '', 99) + '.paired.txt'

        new_file = File(name=add_paired_txt(file.name), directory=file.directory, path=add_paired_txt(file.path),
                        file_type='BIGG_ANNOTATION', dataset_id=file.dataset_id, analysis_id=file.analysis_id,
                        user_id=user_id, parent_id=file.id, check_name=False)
        logger.info('Writing paired file to path: {}'.format(new_file.path))
        paired_df.to_csv(new_file.path, sep='\t', index=False)
        session.add(new_file)
        session.commit()
        return_value = ReturnValue('Paired Annotation File Produced: {}'.format(new_file.path), file_ids=[new_file.id])

    return return_value


@celery.task(base=LogTask, bind=True)
def parse_and_insert_mixcr_annotations_from_file_path(self, file_path, dataset_id=None, analysis_id=None):
    logger = self.logger

    print 'Building annotations from MiXCR output at {}, then inserting into postgres in batches'.format(file_path)
    if analysis_id:
        analysis = db.session.query(Analysis).filter(Analysis.id == analysis_id).first()
    else:
        analysis = None
    if analysis: analysis.db_status = 'BUILDING ANNOTATIONS'
    if analysis: analysis.status = 'INSERTING TO DB'
    db.session.commit()
    annotations = build_annotations_from_mixcr_file(file_path, dataset_id=dataset_id, analysis_id=analysis_id)
    total_count = len(annotations)
    if analysis: analysis.total_count = total_count
    db.session.commit()
    for i, a in enumerate(annotations):
        db.session.add(a)
        if i % 1000 == 0:
            print "Inserting # {} and the previous 1000 annotations to postgres. Here's what it looks like: {}".format(
                i, a.__dict__)
            percent_done = float(i) / float(total_count)
            if analysis: analysis.db_status = '{} Annotations Inserted in DB,  {} Percent Done'.format(i, int(
                percent_done * 100))
            db.session.commit()
    if analysis:
        analysis.db_status = 'Finished. {} Annotations Inserted'.format(len(annotations))
        analysis.status = 'COMPLETE'
    db.session.commit()
    result = annotate_analysis_from_db.apply_async((analysis.id,), queue=celery_queue)
    return len(annotations)


@celery.task(base=LogTask, bind=True)
def parse_and_insert_mixcr_annotation_dataframe_from_file_path(self, file_path, dataset_id=None, analysis_id=None):
    logger = self.logger

    print 'Building annotation dataframe from MiXCR output at {}, then inserting into postgres'.format(file_path)
    if analysis_id:
        analysis = db.session.query(Analysis).filter(Analysis.id == analysis_id).first()
    else:
        analysis = None
    if analysis: analysis.db_status = 'BUILDING ANNOTATIONS'
    if analysis: analysis.status = 'BUILDING DATABASE'
    db.session.commit()
    annotation_df = build_annotation_dataframe_from_mixcr_file(file_path, dataset_id=dataset_id,
                                                               analysis_id=analysis_id)
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
    result = annotate_analysis_from_db.apply_async((analysis.id,), queue=celery_queue)
    return True


@celery.task
def annotate_analysis_from_db(analysis_id):
    analysis = db.session.query(Analysis).filter(Analysis.id == analysis_id).first()
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


@celery.task(base=LogTask, bind=True)
def run_pandaseq_with_dataset_id(self, dataset_id, analysis_id=None, analysis_name='',
                                 analysis_description='Pandaseq Alignment Consensus', file_ids=[], user_id=2,
                                 minimum_length=100, maximum_length=500, minimum_overlap=10, algorithm='pear'):
    logger = self.logger
    dataset = db.session.query(Dataset).filter(Dataset.id == dataset_id).first()
    files = [db.session.query(File).get(file_id) for file_id in file_ids]
    logger.info('Running PANDAseq on Dataset {}.'.format(dataset_id))

    if analysis_id:
        analysis = db.session.query(Analysis).filter(Analysis.id == analysis_id).first()
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
        analysis.directory = '{}/Analysis_{}/'.format(dataset.directory.rstrip('/'), analysis.id)
        if not os.path.isdir(analysis.directory):
            os.mkdir(analysis.directory)

    if len(files) != 2:
        logger.error('Bad request for pandaseq alignment of only {} files'.format(len(files)))

    else:
        logger.info('Running PANDAseq concatenation on these {} files: {}'.format(len(files), ', '.join(
            [file.name for file in files])))

        files_to_execute = []
        path = '/{}'.format('/'.join(files[0].path.split('/')[:-1]))
        path = path.replace('//', '/')

        basename = parse_basename(map(lambda file: file.path, files))
        # files[0].path.split('/')[-1].split('.')[0]
        # basename = analysis_name
        if basename == '' or basename == None:
            basename = 'Analysis_{}'.format(analysis.id)
        basepath = '{0}/{1}'.format(analysis.directory.rstrip('/'), basename)
        logger.info('Writing output files to base name: {}'.format(basepath))

        # Instantiate Output Files
        alignment_file = File()
        alignment_file.user_id = dataset.user_id
        alignment_file.path = '{}.pandaseq_{}.fastq'.format(basepath, algorithm)
        alignment_file.name = "{}.pandaseq_{}.fastq".format(basename, algorithm)
        alignment_file.command = 'pandaseq -f {} -r {} -F -T 4 -A {} -w {} -l {} -L {} -o {} 2> {}.log'.format(files[0].path,
                                                                                                         files[1].path,
                                                                                                         algorithm,
                                                                                                         alignment_file.path,
                                                                                                         minimum_length,
                                                                                                         maximum_length,
                                                                                                         minimum_overlap,
                                                                                                         alignment_file.path)
        alignment_file.file_type = 'PANDASEQ_ALIGNED_FASTQ'
        files_to_execute.append(alignment_file)
        analysis.status = 'EXECUTING'
        db.session.commit()

        for f in files_to_execute:
            f.command = f.command.encode('ascii')
            f.dataset_id = analysis.dataset_id
            f.analysis_id = analysis.id
            f.chain = files[0].chain
            logger.info('Executing: {}'.format(f.command))
            analysis.active_command = f.command
            f.in_use = True
            db.session.add(f)
            db.session.commit()
            # MAKE THE CALL
            # response = os.system(f.command)
            # print 'Response: {}'.format(response)

            error = None
            lowq_errors = 0
            try:
                command_line_args = shlex.split(f.command)
                command_line_process = subprocess.Popen(command_line_args, stdout=subprocess.PIPE,
                                                        stderr=subprocess.STDOUT, bufsize=1)

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
                                self.update_state(state='RUNNING', meta={'status': status})
                        except:
                            pass

                self.update_state(state='RUNNING',
                                  meta={'status': 'PANDAseq complete.'})

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
                    logger.error('PANDAseq Error: unable to create file {}'.format(f.path))

            else:
                f.available = False
                analysis.status = 'FAILED'
                db.session.commit()
                logger.error(error)

                ##### ***** Need to Check Output Files Here ***** #####

    logger.info('All commands in analysis {} have been executed.'.format(analysis))
    if set(map(lambda f: f.available, files_to_execute)) == set([True]) :
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'
    db.session.commit()

    return ReturnValue('PANDAseq analysis complete.', file_ids=output_file_ids)


def run_trim_analysis_with_files(analysis_id=None, file_ids=None, logger=celery_logger, trim_illumina_adapters=True,
                                 trim_slidingwindow=True, trim_slidingwindow_size=4, trim_slidingwindow_quality=15):
    analysis = db.session.query(Analysis).get(analysis_id)

    files = map(lambda x: db.session.query(File).filter(File.id == x).first(), file_ids)

    if not analysis:
        raise Exception('Analysis with ID {} not found.'.format(analysis_id))
    analysis_name = 'Analysis_{}'.format(analysis.id)

    logger.info('Running Trimmomatic on files {}.'.format(', '.join([str(file.id) for file in files])))

    illumina_command = ''
    if trim_illumina_adapters:
        illumina_command = 'ILLUMINACLIP:{}/TruSeq3-SE.fa:2:30:10 '.format(app.config['TRIMMOMATIC_ADAPTERS'])

    sliding_window_command = ''
    if trim_slidingwindow:
        sliding_window_command = 'SLIDINGWINDOW:{}:{} '.format(trim_slidingwindow_size, trim_slidingwindow_quality)

    # if len(files) == 0 or len(files) > 2:
    #     raise Exception('Can only run Trimmomatic on 1 or 2 files, not on {} files.'.format( str(len(files) ) ) )

    files_to_execute = []

    for file in files:
        # path = '/{}'.format('/'.join(file.path.split('/')[:-1])).replace('//', '/')
        basename = file.path.split('/')[-1].split('.')[0]
        basepath = '{0}/{1}'.format(analysis.directory, basename)
        logger.info('Writing trimmed file to: {}'.format(basepath))

        output_file = File()
        output_file.path = '{}.trimmed.fastq'.format(basepath)
        output_file.name = "{}.trimmed.fastq".format(basename)
        output_file.dataset_id = analysis.dataset_id
        output_file.user_id = analysis.user_id
        output_file.analysis_id = analysis.id
        output_file.chain = file.chain

        output_file.command = '{0} SE -phred33 -threads 4 {1} {2} {3} LEADING:3 TRAILING:3 {4}MINLEN:50'.format(
            app.config['TRIMMOMATIC'], file.path, output_file.path, illumina_command, sliding_window_command)
        output_file.file_type = 'TRIMMED_FASTQ'
        files_to_execute.append(output_file)

    analysis.status = 'EXECUTING TRIM'
    db.session.commit()

    output_file_ids = []
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        logger.info('Executing: {}'.format(f.command))
        analysis.active_command = f.command
        f.in_use = True
        db.session.add(f)
        db.session.commit()

        # MAKE THE CALL
        if f.command != '':
            logger.info(f.command)

            error = None
            try:
                command_line_process = subprocess.Popen(shlex.split(f.command), stdout=subprocess.PIPE,
                                                        stderr=subprocess.STDOUT, bufsize=1)

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
                logger.error('Error writing trimmed file {}: {}'.format(f.path, error))

        db.session.refresh(f)
        output_file_ids.append(f.id)

    logger.info('Trim job for analysis {} has been executed.'.format(analysis))
    return ReturnValue('Success', file_ids=output_file_ids)


# Quality filtering with fastx_toolkit on  % of read above certain PHRED threshold
@celery.task(base=LogTask, bind=True)
def run_quality_filtering_with_analysis_id(self, analysis_id=None, analysis_name='',
                                           analysis_description='Fastq Quality Filter', file_ids=[],
                                           minimum_percentage=50, minimum_quality=20):
    logger = self.logger
    files = [db.session.query(File).get(file_id) for file_id in file_ids]
    logger.info('Running Quality Filtering on Files {}.'.format(",".join(map(lambda f: f.path, files))))

    if analysis_id:
        analysis = db.session.query(Analysis).filter(Analysis.id == analysis_id).first()
    else:
        analysis = Analysis()
        if analysis_name == '':
            analysis_name = 'Analysis_{}'.format(analysis.id)
        analysis.async_task_id = self.task.request_id
        analysis.name = analysis_name
        analysis.description = analysis_description
        analysis.user_id = user_id
        analysis.dataset_id = files[0].id
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
        analysis.directory = '{}/Analysis_{}/'.format(files[0].dataset.directory.rstrip('/'), analysis.id)
        if not os.path.isdir(analysis.directory):
            os.mkdir(analysis.directory)

    logger.info('Running Quality Filtering with {}% bases above PHRED {} on these files: {}'.format(minimum_percentage,
                                                                                                    minimum_quality,
                                                                                                    ', '.join(
                                                                                                        [file.name for
                                                                                                         file in
                                                                                                         files])))

    # make sure we dont overwrite similarly named files
    if len(files) > 1 and len(set(map(lambda f: f.path.split('/')[-1].split('.')[0], files))) == 1:
        ii = True
    else:
        ii = False

    files_to_execute = []
    for i, file in enumerate(files):
        basename = file.path.split('/')[-1].split('.')[0]
        basepath = '{0}/{1}'.format(analysis.directory.rstrip('/'), basename)
        logger.info('Writing filtered output file to base: {}'.format(basepath))

        # Instantiate Output Files
        filtered_file = File()
        filtered_file.user_id = analysis.user_id
        filtered_file.path = '{}{}.filtered_q{}p{}.fastq'.format(basepath, '_R{}'.format(i + 1) if ii else '',
                                                                 minimum_quality, minimum_percentage)
        filtered_file.name = '{}{}.filtered_q{}p{}.fastq'.format(basename, '_R{}'.format(i + 1) if ii else '',
                                                                 minimum_quality, minimum_percentage)
        if 'GZIPPED' in file.file_type:
            filtered_file.command = ' gunzip -c {} | fastq_quality_filter -q {} -p {} -i - -o {} -Q 33 '.format(
                file.path, minimum_quality, minimum_percentage,
                filtered_file.path)  # -Q 33 for more recent Illumina quality outputs
        else:  # file.file_type == 'FASTQ' or 'PANDASEQ_ALIGNED_FASTQ'
            filtered_file.command = 'fastq_quality_filter -q {} -p {} -i {} -o {} -Q 33 '.format(minimum_quality,
                                                                                                 minimum_percentage,
                                                                                                 file.path,
                                                                                                 filtered_file.path)  # -Q 33 for more recent Illumina quality outputs
        filtered_file.file_type = 'FASTQ'
        filtered_file.dataset_id = file.dataset_id
        filtered_file.analysis_id = analysis.id
        filtered_file.chain = file.chain
        files_to_execute.append(filtered_file)

    analysis.status = 'EXECUTING'
    db.session.commit()

    output_file_ids = []
    for f in files_to_execute:
        f.command = f.command.encode('ascii')
        logger.info('Executing: {}'.format(f.command))
        analysis.active_command = f.command
        f.in_use = True
        db.session.add(f)
        db.session.commit()
        # MAKE THE CALL
        # response = os.system(f.command)
        # print 'Response: {}'.format(response)

        error = None
        try:
            command_line_args = shlex.split(f.command)
            if '|' in command_line_args:
                pipe_index = command_line_args.index('|')
                gunzip_args = command_line_args[:pipe_index]
                command_line_args = command_line_args[(pipe_index + 1):]
                gunzip_process = subprocess.Popen(gunzip_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                  bufsize=1)
                command_line_process = subprocess.Popen(command_line_args, stdin=gunzip_process.stdout,
                                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
                gunzip_process.stdout.close()
            else:
                command_line_process = subprocess.Popen(command_line_args, stdout=subprocess.PIPE,
                                                        stderr=subprocess.STDOUT, bufsize=1)

            start = dt.datetime.now()

            for line in iter(command_line_process.stdout.readline, b''):
                line = line.strip()
                logger.info(line)

            response, error = command_line_process.communicate()
            command_line_process.stdout.close()
            command_line_process.wait()
        except subprocess.CalledProcessError as error:
            error = error.output
            logger.error(error)
        if error == None:
            time.sleep(1)
            if os.path.isfile(f.path):
                f.available = True
                f.file_size = os.path.getsize(f.path)
                db.session.commit()
                db.session.refresh(f)
                output_file_ids.append(f.id)
            else:
                f.available = False
                f.in_use = False
                analysis.status = 'FAILED'
                db.session.commit()
                logger.error('Quality Filtering Error: unable to create file {}'.format(f.path))

        else:
            f.available = False
            analysis.status = 'FAILED'
            db.session.commit()
            logger.error(error)

    ##### ***** Need to Check Output Files Here ***** #####

    logger.info('Filtering steps for analysis {} have been executed.'.format(analysis))
    if set(map(lambda f: f.available, files_to_execute)) == set([True]):
        analysis.status = 'SUCCESS'
        analysis.available = True
    if not analysis.status == 'FAILED': analysis.status = 'SUCCESS'
    analysis.active_command = ''
    analysis.finished = 'now'
    db.session.commit()

    return ReturnValue('Quality Filtering complete.', file_ids=output_file_ids)


# Returns a ReturnValue with field file_ids which reflects only the new files added during the analysis
@celery.task(base=LogTask, bind=True)
def run_msdb(self, file_ids=[], user_id=None, dataset_id=None, analysis_id=None, analysis_name=None,
                 analysis_description=None, append_cterm_peptides=False, cluster_percent=0.9,
                 cluster_algorithm='greedy', cluster_on='aaSeqCDR3', read_cutoff=1, require_annotations=['aaSeqCDR3'],
                 cluster_linkage='min', max_sequences_per_cluster_to_report=1, generate_fasta_file=False):

    logger = self.logger


    with session_scope() as session:

        # Get the DB objects
        user = session.query(User).get(user_id)
        files = [db.session.query(File).get(id) for id in file_ids]
        logger.info('Preparing new clustering analysis with these annotations: {}'.format(','.join([f.path for f in files])))

        # Determine if a new analysis is needed
        if analysis_id != None:
            analysis = session.query(Analysis).get(analysis_id)
        else:  # no analysis provided, so we have to create a new analysis
            analysis = generate_new_analysis(user=user, directory=None, directory_prefix='Post-annotation_Analysis_',
                                             name=analysis_name, description=analysis_description, program='MSDB',
                                             session=session)

        self.set_analysis_id(analysis.id)

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

        runtime_parameters = {'file_ids':file_ids, 'user_id':user_id, 'dataset_id':dataset_id, 'analysis_id':analysis.id, 'analysis_name':analysis_name,
                     'append_cterm_peptides':append_cterm_peptides, 'cluster_percent':cluster_percent,
                     'cluster_algorithm':cluster_algorithm, 'cluster_on':cluster_on, 'read_cutoff':read_cutoff,
                     'require_annotations':require_annotations,
                     'cluster_linkage':cluster_linkage, 'max_sequences_per_cluster_to_report':max_sequences_per_cluster_to_report, 'generate_fasta_file':generate_fasta_file}


        analysis_file_name_prefix = analysis.name.replace(' ', '_')
        analysis_json_path = '{}/{}_settings.json'.format(analysis.directory.rstrip('/'), analysis_file_name_prefix)

        logger.info("Saving Execution Settings to {}".format(analysis_json_path))
        with open(analysis_json_path, 'w') as json_file:
            # json.dump( (args, kwargs) , json_file)
            json.dump(runtime_parameters, json_file, indent=4, sort_keys=True)

        if os.path.isfile(analysis_json_path):
            analysis.settings_file = File(path=analysis_json_path, file_type='JSON', dataset_id=analysis.dataset_id,
                                          analysis_id=analysis.id, user_id=analysis.user_id)

        session.add(analysis.settings_file)
        session.commit()
        dfs = []
        for file in files:
            logger.info('Parsing {} and adding to dataframe'.format(file.name))
            df = read_annotation_file(file.path)
            df['group'] = file.dataset.name
            dfs.append(df)
        df = pd.concat(dfs)
        del(dfs) # garbage collection - clear up some RAM cause we gunna need it
        logger.info("{} Total Annotations Grouped From Input Files".format(len(df)))
        df = df.dropna(subset=require_annotations, how='any')
        logger.info("{} Total Annotations With {} Annotated Being Clustered".format(len(df), ','.join(require_annotations)))
        logger.info(
            'Clustering at {}%  on {} with the {} method, requiring at least {} reads per cluster and all of these annotated: {}'.format(
                cluster_percent, cluster_on, cluster_algorithm, read_cutoff, ','.join(require_annotations)))
        if len(df) == 0:
            logger.error("No annotations contained all required CDR/FR sequences")
            self.update_state(state='FAILED',
                              meta={'status': 'No Annotations Resulted After Filtering On Required CDR/FR Sequences'})
            return ReturnValue("Post-analysis Clustering Failed - No Sequences Remaining After Filtering", file_ids=[])
        # redirect logger to capture function output
        saved_stdout = sys.stdout
        sys.stdout = LoggerWriterRedirect(logger, task=self)
        df = cluster_dataframe(df, identity=cluster_percent, on=cluster_on, how=cluster_algorithm,
                               linkage=cluster_linkage, read_cutoff=read_cutoff, group_tag='group', max_sequences_per_cluster_to_report=max_sequences_per_cluster_to_report)
        # Restore STDOUT to the console
        sys.stdout = saved_stdout
        logger.info("{} Clusters Generated".format(len(df)))

        if append_cterm_peptides:
            logger.info('Appending C-terminal constant region peptides to end of sequences')
            df = append_cterm_peptides_for_mass_spec(df)

        # write output files
        if generate_fasta_file:
            new_file = File(name="{}_Clustered_MSDB.fasta".format(analysis.name).replace(' ', '_'), directory=analysis.directory,
                            path="{}/{}_Clustered_MSDB.fasta".format(analysis.directory, analysis.name).replace(' ', '_'),
                            file_type='MSDB_FASTA', analysis_id=analysis.id, user_id=user_id, check_name=False)
            logger.info('Writing MSDB Fasta file to path: {}'.format(new_file.path))
            with open(new_file.path, 'w') as file:
                for i, row in df.iterrows():
                    file.write('>{}_{}_{}_{}\n'.format(i, row['aaSeqCDR3'], row['clusterSize'], row['collapsedCount']))
                    file.write(row['aaFullSeq'])
                    file.write('\n')
            session.add(new_file)


        new_file = File(name="{}_Clustered.txt".format(analysis.name).replace(' ', '_'), directory=analysis.directory,
                        path="{}/{}_Clustered.txt".format(analysis.directory, analysis.name).replace(' ', '_'),
                        file_type='CLUSTERED_TXT', analysis_id=analysis.id, user_id=user_id, check_name=False)
        logger.info('Writing Clustered Tabbed file to path: {}'.format(new_file.path))
        df.to_csv(new_file.path, sep='\t', index=False)
        session.add(new_file)

        logger.info('Post-annotation analysis complete. {} sequences were written.'.format(len(df)))
        return ReturnValue('Post-annotation analysis complete for analysis {}.'.format(analysis.id), file_ids=[])



# Provided with a list of file ids, this function unzips those files if necessary, creates a new file
#  entry in the database, and returns the file ids of the new file entry
def unzip_files(user_id=None, file_ids=[], destination_directory='~', logger=celery_logger):
    if len(file_ids) == 0:
        return ReturnValue('No files to unzip.', file_ids=file_ids)

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
                new_file.path = destination_directory.rstrip('/') + '/' + file.name.replace('.gz', '')
                new_file.file_type = 'FASTQ'
                new_file.available = False
                new_file.name = file.name.replace('.gz', '')
                new_file.command = 'gunzip -c {} > {}'.format(file.path, new_file.path)
                analysis.status = 'GUNZIPPING'
                session.add(new_file)
                session.commit()
                session.refresh(new_file)
                files_to_unzip.append(new_file)

            else:
                # file does not need to be unzipped, so add it to the list as-is
                output_file_ids.append(file.id)

        # print 'Here'

        session_objects = expunge_session_objects(session)
    ##### End Session #####

    number_files_unzipped = 0

    if files_to_unzip != []:

        for file in files_to_unzip:

            logger.info('Unzipping file id {}:{}'.format(file.id, file.command))

            error = False
            return_code = None

            try:
                command_line_process = subprocess.check_output(
                    file.command,
                    stderr=subprocess.STDOUT,
                    shell=True
                )
            except subprocess.CalledProcessError, return_error:
                logger.error('Error: process exited with return code {}: {}'.format(return_error.returncode,
                                                                                    return_error.output))
                error = True

            if error == False:
                file.available = True
                output_file_ids.append(file.id)
                number_files_unzipped += 1

    # Save all of the changes
    # logger.info('Saving changes.')
    with session_scope() as session:
        add_session_objects(session, session_objects)
        session.commit()

    if number_files_to_unzip == 0:
        return ReturnValue(
            'No file to unzip, moving forward with file ids {}'.format(str(','.join([str(id) for id in file_ids]))),
            file_ids=output_file_ids)
    else:
        return ReturnValue('{} files unzipped.'.format(str(number_files_unzipped)), file_ids=output_file_ids)


def run_igrep_annotation_on_dataset_files(dataset_id, file_ids, user_id, analysis_id=None, overlap=False, paired=False,
                                          cluster=False, cluster_setting=[0.85, 0.9, .01], species=None, loci=None,
                                          logger=celery_logger, parent_task=None):
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

        logger.info('Running IGREP IGFFT on Dataset {}.'.format(dataset.id))
        igrep_script_path = app.config['IGREP_PIPELINES']

        if species == None:
            if dataset.species == 'Human':
                species = 'homosapiens'
            elif dataset.species == 'Mouse':
                species = 'musmusculus'
            else:
                species = 'homosapiens'
        elif species == 'M. musculus':
            species = 'musmusculus'
        elif species == 'H. sapiens':
            species = 'homosapiens'
        else:
            species = 'homosapiens'

        annotated_file_ids = []
        for file in files:
            if not loci:
                loci = ''
                if file.chain == 'HEAVY': loci = 'igh'
                if file.chain == 'LIGHT': loci = 'igk,igl'
                if file.chain == 'HEAVY/LIGHT': loci = 'igh,igk,igl'

                # Set default loci here
                if loci == '': loci = 'igh,igk,igl'

            else:
                loci = ','.join(loci)
                loci = loci.lower()

                # annotated_f = igfft.igfft_multiprocess(f.path, file_type='FASTQ', species=species, locus=loci, parsing_settings={'isotype': isotyping_barcodes, 'remove_insertions': remove_insertions}, num_processes=number_threads, delete_alignment_file=True)
            # annotated_files.append(annotated_f[0])
            script_command = 'python {}/gglab_igfft_single.py -species {} -locus {} {}'.format(igrep_script_path,
                                                                                               species, loci, file.path)
            commands.append(script_command)

        session_objects = expunge_session_objects(session)

    ##### End database session #####

    for command in commands:

        logger.info('executing script: {}'.format(script_command))

        error = None
        try:
            command_line_process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT, bufsize=1)

            # keep track of the last two states
            # that way we can tell the user what finished happening
            last_state = ''
            counting = False
            start = dt.datetime.now()

            pid_pattern = re.compile('\((.*?)\)')

            for line in iter(command_line_process.stdout.readline, b''):
                line = line.strip()
                print line
                if 'Error' in line or 'error' in line or 'ERROR' in line:
                    logger.error(line)

                pid = None

                pid_match = pid_pattern.match(line)
                if pid_match:
                    pid = pid_match.group(1)
                    line = line.replace(pid_match.group(0), '')
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
                            logger.info('{}({}) complete.'.format(last_state, current_status_number))
                            counting = False
                        last_state = state
                        current = dt.datetime.now()
                        elapsed = (current - start).seconds

                        # status = 'Time Elapsed: {} - Number of Reads: {}'.format(elapsed, reads)
                        # parent_task.update_state(state='STATUS', meta={'status': status })

                        status = 'Time Elapsed: {} - {}({})'.format(elapsed, line, current_status_number)
                        task.update_state(state='RUNNING', meta={'status': status})

                    elif ('% percent done' in line):

                        if pid:
                            current_status_number = pid
                            pid_str = 'PID: {} '.format(pid)
                        else:
                            current_status_number = ''
                            pid_str = ''

                        counting = True
                        try:
                            line_parts = line.split('%', 1)
                            percent = line_parts[0].strip()
                            percent = float(percent)
                        except:
                            logger.debug('Couldn\'t convert {} to float'.format(percent))
                            percent = 0

                        current = dt.datetime.now()
                        elapsed = (current - start).seconds

                        task.update_state(state='PROGRESS',
                                          meta={
                                              'status': '{} ({}Time Elapsed: {})'.format(last_state, pid_str, elapsed),
                                              'current': percent, 'total': 100, 'units': '%'})

            if counting:
                task.update_state(state='RUNNING')
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
            new_file_path = file.path.replace('fastq', 'igfft.annotation')

            if os.path.isfile(new_file_path):
                number_files_created += 1

                new_file = File()
                new_file.user_id = user_id
                new_file.parent_id = file.id
                new_file.dataset_id = dataset.id

                if analysis_id:
                    new_file.analysis_id = analysis_id

                new_file.name = file.name.replace('fastq', 'igfft.annotation')
                new_file.name = new_file.name.replace('fq', 'igfft.annotation')
                new_file.path = file.path.replace('fastq', 'igfft.annotation')
                new_file.path = new_file.path.replace('fq', 'igfft.annotation')
                new_file.file_type = 'IGFFT_ANNOTATION'
                new_file.created = 'now'
                new_file.available = True
                session.add(new_file)
                session.commit()
                session.refresh(new_file)
                logger.info('Created New {} File #{} {}  at  {}'.format(new_file.file_type, new_file.id, new_file.name,
                                                                        new_file.path))
                annotated_file_ids.append(new_file.id)

            else:
                all_files_created = False
                files_not_created.append(new_file_path)
                logger.error('IGREP failed to create new file: {}'.format(new_file_path))

    if not all_files_created:
        raise Exception(
            'IGREP/IGFFT failed to create all files ({}/{}). The following files were not created: {}'.format(
                number_files_created, total_files, ' '.join(files_not_created)))

    ##### End of session #####

    return ReturnValue('IGREP analysis complete.', file_ids=annotated_file_ids)


@celery.task
def send_async_email(msg):
    """Background task to send an email with Flask-Mail."""
    with app.app_context():
        mail.send(msg)


# function to flash error messages from forms automatically
def flash_errors(form, category="warning"):
    '''Flash all errors for a form.'''
    for field, errors in form.errors.items():
        for error in errors:
            flash("{0} - {1}".format(getattr(form, field).label.text, error), category)


@celery.task(base=LogTask, bind=True)
def parse_gsaf_response_into_datasets(self, url, user_id=2, project_id=None, celery_queue='default'):
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
        user = session.query(User).filter(User.id == user_id).all()[0]
        if project_id:
            project = session.query(Project).get(project_id)
        new_file_ids = []
        for sample_name, file_arrays in file_arrays_by_sample_name:
            logger.info('Collecting Info On Sample {}'.format(sample_name))
            dataset = Dataset()
            dataset.user_id = user_id
            dataset.name = sample_name
            dataset.directory = "{}/Dataset_{}_{}".format(user.path.rstrip('/'), dataset.name, dataset.id)
            if not os.path.isdir(dataset.directory):
                os.mkdir(dataset.directory)
            if project_id:
                pd = ProjectDatasets(dataset=dataset, project=project)
                session.add(pd)
                session.commit()
            session.add(dataset)
            session.flush()
            session.refresh(dataset)
            for file_array in file_arrays:
                file_name = file_array[1]
                file_url = file_array[-1].replace('-->', '')
                file_checksum = file_array[4]
                try:
                    response = urllib2.urlopen(file_url)
                except urllib2.HTTPError as err:
                    logger.error(err)
                    logger.error('The GSAF URLs may be stale. Try to download one file directly...')
                    self.update_state(state='FAILED', meta={'status': 'Failed import - GSAF link likely forbidden'})
                    logger.error('The GSAF URLs may be stale. Try to download one file directly...')
                    return ReturnValue('GSAF import finished: {} files ingested.'.format(len(new_file_ids)),
                                       file_ids=new_file_ids)
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
                    session.add(new_file)
                    dataset.files.append(new_file)
                    session.commit()
                    session.refresh(new_file)
                    new_file_ids.append(new_file.id)
                    download_file(url=new_file.url, checksum=file_checksum, path=new_file.path, file_id=new_file.id,
                                  user_id=user_id, parent_task=task)

    # call create_datasets_from_JSON_string(json_string, project)
    return ReturnValue('GSAF import finished: {} files ingested.'.format(len(new_file_ids)), file_ids=new_file_ids)


# @Dave - function to create datasets from a JSON file
# If the project is give, the datasets are added to the project
def create_datasets_from_JSON_string(json_string, project_id=None, dataset_id=None):
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
    json_flatten_fields = ["SEQUENCING_SUBMISSION_NUMBER", "MID_TAG", "DESCRIPTION", "PRIMER_SET_NAME", "LAB",
                           "PERSON_WHO_PREPARED_LIBRARY"]
    json_comma_fields = ["CHAIN_TYPES_SEQUENCED", "LIST_OF_POLYMERASES_USED", "CELL_MARKERS_USED",
                         "CELL_TYPES_SEQUENCED", "PUBLICATIONS", "ISOTYPES_SEQUENCED"]
    json_psp_fields = ["POST_SEQUENCING_PROCESSING:PHI_X_FILTER", "POST_SEQUENCING_PROCESSING:PROCESS_R1_R2_FILE",
                       "POST_SEQUENCING_PROCESSING:QUALITY_FILTER"]

    try:
        json_data = json.loads(json_string)
    except ValueError, error:
        return "Error loading JSON: {}".format(error)

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
            if field in json_flatten_fields and type(json_dataset[field]) == list:  # flatten lists here
                json_dataset[field] = " ".join(json_dataset[field])
            if field in json_comma_fields and type(json_dataset[field]) == list:  # flatten comma lists here
                json_dataset[field] = ", ".join(json_dataset[field])
            if field in json_psp_fields and field in json_dataset:  # flatten special fields here
                post_sequencing_processing[field] = json_dataset[field]

        post_sequencing_processing = str(post_sequencing_processing)

        contains_rna_seq_data = False
        if json_dataset["CONTAINS_RNA_SEQ_DATA"] == "True":
            contains_rna_seq_data = True

        new_dataset = Dataset()
        new_dataset.user_id = 2
        # new_dataset.user_id = current_user.id
        new_dataset.name = dataset_name
        new_dataset.description = json_dataset["DESCRIPTION"]
        new_dataset.ig_type = ""

        # special treatment for arrays
        try:
            new_dataset.cell_types_sequenced = ast.literal_eval(str(json_dataset["CELL_TYPES_SEQUENCED"]))
        except:
            new_dataset.cell_types_sequenced = [str(json_dataset["CELL_TYPES_SEQUENCED"])]

        try:
            new_dataset.chain_types_sequenced = ast.literal_eval(str(json_dataset["CHAIN_TYPES_SEQUENCED"]))
        except:
            new_dataset.chain_types_sequenced = [str(json_dataset["CHAIN_TYPES_SEQUENCED"])]

        try:
            new_dataset.primary_data_files_ids = ast.literal_eval(str(dataset.primary_data_files_ids))
        except:
            if str(json_dataset["LAB_NOTEBOOK_SOURCE"]).isdigit():
                new_dataset.primary_data_files_ids = [int(json_dataset["LAB_NOTEBOOK_SOURCE"])]
            else:
                new_dataset.lab_notebook_source = json_dataset["LAB_NOTEBOOK_SOURCE"]

        new_dataset.sequencing_submission_number = json_dataset["SEQUENCING_SUBMISSION_NUMBER"]
        new_dataset.contains_rna_seq_data = contains_rna_seq_data
        new_dataset.reverse_primer_used_in_rt_step = json_dataset["REVERSE_PRIMER_USED_IN_RT_STEP"]
        new_dataset.list_of_polymerases_used = json_dataset["LIST_OF_POLYMERASES_USED"]
        new_dataset.sequencing_platform = json_dataset["SEQUENCING_PLATFORM"]
        new_dataset.target_reads = json_dataset["TARGET_READS"]
        new_dataset.cell_markers_used = json_dataset["CELL_MARKERS_USED"]
        new_dataset.adjuvant = json_dataset["ADJUVANT"]
        new_dataset.species = json_dataset["SPECIES"]
        new_dataset.cell_selection_kit_name = json_dataset["CELL_SELECTION_KIT_NAME"]
        new_dataset.isotypes_sequenced = json_dataset["ISOTYPES_SEQUENCED"]
        new_dataset.sample_preparation_date = json_dataset["SAMPLE_PREPARATION_DATE"]
        new_dataset.gsaf_barcode = json_dataset["GSAF_BARCODE"]
        new_dataset.mid_tag = json_dataset["MID_TAG"]
        new_dataset.cell_number = json_dataset["CELL_NUMBER"]
        new_dataset.primer_set_name = json_dataset["PRIMER_SET_NAME"]
        new_dataset.template_type = json_dataset["TEMPLATE_TYPE"]
        new_dataset.experiment_name = json_dataset["EXPERIMENT_NAME"]
        new_dataset.person_who_prepared_library = json_dataset["PERSON_WHO_PREPARED_LIBRARY"]
        new_dataset.pairing_technique = json_dataset["PAIRING_TECHNIQUE"]
        new_dataset.json_id = json_dataset["_id"]
        new_dataset.paired = json_dataset["VH:VL_PAIRED"]
        new_dataset.read_access = str(json_dataset["READ_ACCESS"])
        new_dataset.owners_of_experiment = str(json_dataset["OWNERS_OF_EXPERIMENT"])

        db.session.add(new_dataset)
        db.session.flush()
        db.session.refresh(new_dataset)
        new_datasets.append(new_dataset)

        if project_id:
            project = db.session.query(Project).filter(id == project_id).first()
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


@celery.task(base=LogTask, bind=True)
def test_function(self, analysis_id=None, user_id=None):
    logger = self.logger

    logger.info('Beginning test of logger stuff.')

    saved_stdout = sys.stdout
    sys.stdout = LoggerWriter(logger)

    test_print()

    sys.stdout = saved_stdout

    logger.info("Finished test of logger stuff.")

    return ReturnValue('Test completed successfully.')


def test_print():
    print "This is just a test."


# Adds all files in a directory (not already in database) to database
# Returns a list of file ids
# Automatically renames files and determines file type using a dictionary of regular expressions
def add_directory_files_to_database(directory=None, description=None, dataset_id=None, analysis_id=None, user_id=None,
                                    file_names=None, prefix=None, logger=celery_logger):
    # most file typing can be accomplished through this dictionary
    file_type_dict = {
        'gz': 'GZIPPED_FASTQ',
        'cdr3_clonotype': 'CDR3_CLONOTYPE',
        'cdr3list': 'CDR3_LIST',
        'Gucken': 'MSDB_TXT',
        'msDB': 'MSDB_FASTA',
        'parsed_summary': 'MSDB_SUMMARY'
    }

    # Not implemented yet
    file_type_regex_dict = {
    }

    file_rename_regex_dict = {
        r'MASSSPECDB(\d+)msDB.fasta': r'PREFIX_MSDB.fasta',
        r'cdr3_clonotype_list.txt': r'PREFIX_cdr3_clonotype_list.txt',
        r'MASSSPECDB(\d+)malGucken.txt': r'PREFIX_MSDB.txt',
        r'cdr3list.txt': r'PREFIX_cdr3list.txt',
        r'MASSSPECDB(\d+)parsed_summary.txt': r'PREFIX_parsed_summary.txt'
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
                        pattern_match = pattern.match(file_name)

                        if pattern_match:
                            new_file_name = re.sub(find, replace, file_name)

                            if prefix:
                                new_file_name = new_file_name.replace('PREFIX', prefix)
                            else:
                                new_file_name = new_file_name.replace('PREFIX_', '')

                            new_path = '{}/{}'.format(directory.rstrip('/'), new_file_name)

                            os.rename(path, new_path)

                            if os.path.isfile(new_path):
                                logger.debug('Renamed file {} to {}'.format(path, new_path))

                                path = new_path
                                file_name = new_file_name
                            else:
                                logger.warning('WARNING: failed to rename file {} to {}'.format(path, new_path))

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
                    session.refresh(new_file)
                    added_file_ids.append(new_file.id)
                    number_added_files += 1
                else:
                    logger.warning('WARNING: file not found: {}'.format(path))
    return ReturnValue('{} files added to database.'.format(number_added_files), file_ids=added_file_ids)


@celery.task(base=LogTask, bind=True)
def create_analysis_zip_file(self, analysis_id, user_id):
    logger = self.logger

    # Do not set an analysis id for this task - it will overwrite the existing analysis log
    # self.task.analysis_id = analysis_id


    with session_scope() as session:
        analysis = session.query(Analysis).get(analysis_id)
        if not analysis:
            raise Exception('Error: Analysis {} not found.'.format(analysis_id))

        if analysis.zip_file_id != None:
            raise Exception('Error: Analysis {} already has a zip file.'.format(analysis_id))

        if analysis.files.count() == 0:
            return 'Analysis {} contains no files to zip.'.format(analysis_id)

        files_to_zip = []
        for file in analysis.files:
            if os.path.isfile(file.path):
                files_to_zip.append(file.path)

        if files_to_zip == []:
            return 'No files were found in the analysis directory {}'.format(analysis.directory)
        else:
            analysis_tarfile_name_prefix = analysis.name.replace(' ', '_')
            analysis_tarfile_path = '{}/{}.tar.gz'.format(analysis.directory.rstrip('/'), analysis_tarfile_name_prefix)

        analysis.zip_file = File(path=analysis_tarfile_path, file_type='TAR.GZ', dataset_id=analysis.dataset_id,
                                 analysis_id=analysis.id, user_id=user_id)
        analysis.zip_file.status = 'COMPRESSING'
        session.commit()

    logger.info('Creating tar.gz file for Analysis {}'.format(analysis_id))

    analysis_tar = tarfile.open(analysis_tarfile_path, "w:gz")
    for file_path in files_to_zip:
        logger.info('Adding {} to tar.gz file...'.format(os.path.basename(file_path)))
        analysis_tar.add(file_path)
    analysis_tar.close()

    if not os.path.isfile(analysis_tarfile_path):
        logger.info('Finished compression for Analysis {}'.format(analysis_id))

        return 'Failed to create {}'.format(analysis_tarfile_path)
    else:
        with session_scope() as session:
            analysis = session.query(Analysis).get(analysis_id)
            analysis.zip_file.validate()
            analysis.zip_file.status = 'AVAILABLE'
            session.commit()
            zip_file_id = analysis.zip_file.id

            logger.info('Finished compression for Analysis {}'.format(analysis_id))

    return 'Completed compression of {} analysis files. Saved result as {} in file {}'.format(len(files_to_zip),
                                                                                              analysis_tarfile_path,
                                                                                              zip_file_id)


@celery.task(base=LogTask, bind=True)
def run_analysis_pipeline(self, *args, **kwargs):
    if self.parent_task:
        task = self.parent_task
    else:
        task = self

    logger = self.logger

    print 'args: {}'.format(args)
    print 'kwargs: {}'.format(kwargs)

    user_id = kwargs['user_id']
    if 'dataset' in kwargs.keys(): dataset = kwargs['dataset']
    if 'dataset_files' in kwargs.keys():
        dataset_files = kwargs['dataset_files']
    if 'dataset_files' not in locals():
        dataset_files = kwargs['file_ids']
    name = kwargs['name']
    description = kwargs['description']
    trim = kwargs['trim']
    trim_slidingwindow = kwargs['trim_slidingwindow']
    trim_slidingwindow_size = kwargs['trim_slidingwindow_size']
    trim_slidingwindow_quality = kwargs['trim_slidingwindow_quality']
    trim_illumina_adapters = kwargs['trim_illumina_adapters']
    filter = kwargs['filter']
    filter_percentage = kwargs['filter_percentage']
    filter_quality = kwargs['filter_quality']
    pandaseq = kwargs['pandaseq']
    pandaseq_algorithm = kwargs['pandaseq_algorithm']
    pandaseq_minimum_overlap = kwargs['pandaseq_minimum_overlap']
    pandaseq_minimum_length = kwargs['pandaseq_minimum_length']
    analysis_type = kwargs['analysis_type']
    species = kwargs['species']
    loci = kwargs['loci']
    standardize_outputs = kwargs['standardize_outputs']
    require_annotations = kwargs['require_annotations']
    append_cterm_peptides = kwargs['append_cterm_peptides']
    remove_seqs_with_indels = kwargs['remove_seqs_with_indels']
    pair_vhvl = kwargs['pair_vhvl']
    cluster = kwargs['cluster']
    cluster_algorithm = kwargs['cluster_algorithm']
    cluster_linkage = kwargs['cluster_linkage']
    cluster_percent = float(kwargs['cluster_percent'])

    ##### Obtain Files for Analysis #####
    file_ids_to_analyze = []
    analysis_id = None

    with session_scope() as session:

        # get the current user
        current_user = session.query(User).get(user_id)
        if not current_user:
            raise Exception('User with id {} not found.'.format(user_id))

        dataset = None # dont actually rely on dataset argument
        if dataset_files and len(dataset_files)!=0:
            for file_id in dataset_files:
                file = session.query(File).get(file_id)
                if not File == type(file):
                    raise Exception('File with id {} not found.'.format(file_id))
                else:
                    dataset = file.dataset
                    file_ids_to_analyze.append(file_id)
        else:
            raise Exception('No files given for analysis.')

        if file_ids_to_analyze == []:
            raise Exception('Unable to load files for analysis.')
        else:

            analysis = generate_new_analysis(
                user=current_user,
                dataset=dataset,
                directory=dataset.directory,
                directory_prefix='Analysis_',
                session=session,
                name=name,
                description=description,
                async_task_id=self.task.request_id,
            )

            self.set_analysis_id(analysis_id)

            # Set other values
            if analysis.name == "" or analysis.name == None:
                analysis.name = 'Analysis_{}'.format(analysis.id)
            analysis.program = analysis_type.upper()
            analysis.params = {}
            analysis.status = 'RUNNING'
            analysis.responses = []
            analysis.available = False
            session.commit()

            analysis_file_name_prefix = analysis.name.replace(' ', '_')
            analysis_json_path = '{}/{}_settings.json'.format(analysis.directory.rstrip('/'), analysis_file_name_prefix)

            with open(analysis_json_path, 'w') as json_file:
                # json.dump( (args, kwargs) , json_file)
                json.dump(kwargs, json_file, indent=4, sort_keys=True)
            analysis.settings = json.dumps(kwargs)
            if os.path.isfile(analysis_json_path):
                analysis.settings_file = File(path=analysis_json_path, file_type='JSON', dataset_id=analysis.dataset_id,
                                              analysis_id=analysis.id, user_id=analysis.user_id)

            # Persist values for outside db session
            analysis_id = analysis.id
            dataset_id = dataset.id
            analysis_name = analysis.name
            analysis_directory = analysis.directory

    ##### Perform Pre-processing #####
    self.update_state(state='RUNNING', meta={'status': 'Pre-processing reads'})
    if trim:

        if trim_slidingwindow_size == '': trim_slidingwindow_size = 4
        if trim_slidingwindow_quality == '': trim_slidingwindow_quality = 15

        return_value = run_trim_analysis_with_files(analysis_id=analysis_id, file_ids=file_ids_to_analyze,
                                                    logger=logger, trim_illumina_adapters=trim_illumina_adapters,
                                                    trim_slidingwindow=trim_slidingwindow,
                                                    trim_slidingwindow_size=trim_slidingwindow_size,
                                                    trim_slidingwindow_quality=trim_slidingwindow_quality)
        file_ids_to_analyze = return_value.file_ids
        logger.info(return_value)

    if pandaseq:
        return_value = run_pandaseq_with_dataset_id(dataset_id, analysis_id=analysis_id, file_ids=file_ids_to_analyze,
                                                    algorithm=pandaseq_algorithm,
                                                    minimum_overlap=pandaseq_minimum_overlap,
                                                    minimum_length=pandaseq_minimum_length, parent_task=task)
        file_ids_to_analyze = return_value.file_ids
        logger.info(return_value)

    if filter:
        return_value = run_quality_filtering_with_analysis_id(analysis_id=analysis_id, file_ids=file_ids_to_analyze,
                                                              minimum_percentage=filter_percentage,
                                                              minimum_quality=filter_quality, parent_task=task)
        file_ids_to_analyze = return_value.file_ids
        logger.info(return_value)

    ##### Perform Annotation Generation #####
    self.update_state(state='RUNNING', meta={'status': 'Running VDJ-Annotation'})

    if analysis_type == 'igrep':

        return_value = unzip_files(user_id=user_id, file_ids=file_ids_to_analyze,
                                   destination_directory=analysis_directory, logger=logger)
        file_ids_to_analyze = return_value.file_ids
        logger.info(return_value)

        return_value = annotated_file_return_value = run_igrep_annotation_on_dataset_files(dataset_id=dataset_id,
                                                                                           file_ids=file_ids_to_analyze,
                                                                                           user_id=user_id,
                                                                                           analysis_id=analysis_id,
                                                                                           species=species, loci=loci,
                                                                                           logger=logger,
                                                                                           parent_task=task)
        file_ids_to_analyze = return_value.file_ids
        logger.info(return_value)


    elif analysis_type == 'mixcr':
        return_value = run_mixcr_analysis_id_with_files(analysis_id=analysis_id, file_ids=file_ids_to_analyze,
                                                        species=species, loci=loci, parent_task=task)
        file_ids_to_analyze = return_value.file_ids

    elif analysis_type == 'abstar':

        # Abstar requires unzipped files
        return_value = unzip_files(user_id=user_id, file_ids=file_ids_to_analyze,
                                   destination_directory=analysis_directory, logger=logger)
        file_ids_to_analyze = return_value.file_ids
        logger.info(return_value)

        # Run Abstar function
        return_value = annotated_file_return_value = run_abstar_analysis_id_with_files(user_id=user_id,
                                                                                       analysis_id=analysis_id,
                                                                                       file_ids=file_ids_to_analyze,
                                                                                       species=species,
                                                                                       parent_task=task)
        file_ids_to_analyze = return_value.file_ids
        logger.info(return_value)

    else:
        raise Exception('Analysis type "{}" cannot be performed.'.format(analysis_type))

    # Coerce Annotations into Standard Format:
    if standardize_outputs:
        self.update_state(state='RUNNING', meta={'status': 'Standardizing VDJ-Annotations To Our Format'})

        annotation_files = return_value.file_ids
        if remove_seqs_with_indels == True:
            rmindels = True
            print 'Removing indels'
        else:
            rmindels = False
            print 'Leaving indels'
        if append_cterm_peptides == True:
            append_ms_peptides = True
            print 'Appending MS Peptides'
        else:
            append_ms_peptides = False
            print 'Not Appending MS Peptides'
        return_value = standardize_output_files(user_id=user_id, analysis_id=analysis_id, file_ids=annotation_files,
                                                append_ms_peptides=append_ms_peptides, rmindels=rmindels,
                                                require_annotations=require_annotations, parent_task=task)
        logger.info(return_value)
        file_ids_to_analyze = return_value.file_ids

    if pair_vhvl == True:
        self.update_state(state='RUNNING', meta={'status': 'Pairing VH/VL Annotations'})
        return_value = pair_annotation_files_with_analysis_id(user_id=user_id, analysis_id=analysis_id,
                                                              file_ids=file_ids_to_analyze, parent_task=task)
        logger.info(return_value)
        file_ids_to_analyze = return_value.file_ids

    analysis.status = 'COMPLETE'
    session.commit()

    logger.info(
        '<a href="/analysis/{}" >Analysis pipeline {}</a> finished successfully.'.format(analysis_id, analysis_id))
    return ReturnValue('All analyses and processing completed.', file_ids=file_ids_to_analyze)


######
#
# Imports @ End - to prevent circular imports
#
######

# import blueprint routes here
from frontend import *

app.register_blueprint(frontend)

nav.init_app(app)

if __name__ == '__main__':
    print 'Running application on port 5000......'
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=app.config['THREADED'])
