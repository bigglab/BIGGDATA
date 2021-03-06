#System Imports
import ast
import io        
import json
import mmap
import static
import sys
import os
import time
from datetime import datetime
import random
import pandas as pd 
import numpy as np
from shutil import copyfile
import operator
from sets import Set

try:
    from shlex import quote as cmd_quote
except ImportError:
    from pipes import quote as cmd_quote

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
from flask import Flask, Blueprint, Markup, make_response, render_template, render_template_string, request, session, flash, redirect, url_for, jsonify, get_flashed_messages, send_from_directory
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask.ext.mail import Mail, Message
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from flask_bootstrap import Bootstrap
from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
from flask_nav import Nav 
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from markupsafe import escape
# from render_utils import make_context, smarty_filter, urlencode_filter
import wtforms
from flask_wtf import Form
import random
import jinja2 
from sqlalchemy import create_engine, event
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import * 
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker, scoped_session, validates
from flask_sqlalchemy import SQLAlchemy

from pymongo import MongoClient
import pymongo
 
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.collections import attribute_mapped_collection

import jellyfish


#Local Imports
from forms import *
from functions import * 
from utils.standardization import * 

db = SQLAlchemy()

# os.environ['http_proxy'] = app.config['QUOTAGUARD_URL']
proxy = urllib2.ProxyHandler()
opener = urllib2.build_opener(proxy)

# MODELS. Not abstracted to make alembic migrations easier 

class User(db.Model):
        __tablename__ = 'user'
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(64))
        first_name = db.Column(db.String(128))
        last_name = db.Column(db.String(128))
        email = db.Column(db.String(128))
        password_hash = db.Column(db.String(128))
        data = db.Column(db.Text())
        authenticated = db.Column(db.Boolean, default=False)
        authorized = db.Column(db.Boolean, default=False)
        user_type = db.Column(db.String(128))

        # user paths
        root_path = db.Column(db.String(256))

        files = db.relationship('File', backref='user', lazy='dynamic')
        datasets = db.relationship('Dataset', backref='user', lazy='dynamic')
        analyses = db.relationship('Analysis', backref='user', lazy='dynamic')

        celery_tasks = db.relationship('CeleryTask', backref='user', lazy='dynamic', cascade="all, delete-orphan")

        projects = association_proxy('user_projects', 'project')
        shared_projects = association_proxy('user_projects', 'shared')


        def get_ordered_datasets(self):
            projects = self.get_ordered_projects()
            projects_datasets = db.session.query(Dataset).join(ProjectDatasets).filter(ProjectDatasets.project_id.in_(map(lambda p: p.id, projects))).all() 
            # projects_datasets = [dataset for dataset_list in map(lambda p: p.datasets, self.get_ordered_projects()) for dataset in dataset_list]
            owned_datasets = self.datasets.all()
            # datasets = Set(self.datasets) #only returns owned datasets - need to include shared datasets through user_projects table 
            datasets = Set(projects_datasets + owned_datasets) # THIS DOES ONE QUERY PER PROJECT - NOT EFFICIENT ENOUGH 
            datasets.discard(None)
            datasets.discard(self.default_dataset)
            datasets = sorted(datasets, key=lambda x: x.id, reverse=True)
            return datasets

        def get_ordered_projects(self):
            projects = Set(self.projects)
            projects.discard(None)
            projects = sorted(projects, key=lambda x: x.id, reverse=True)
            return projects


        def get_projects_datasets_files(self, file_types=['FASTQ', 'GZIPPED_FASTQ', 'FASTA', 'GZIPPED_FASTA']):
            #retrieve datasets grouped over projects - including shared
            projects = self.get_ordered_projects()
            project_datasets_files = []
            datasets_processed = []
            for project in projects:
                datasets = [d for d in project.datasets if d != None and d!= self.default_dataset]
                for d in datasets: datasets_processed.append(d)
                if len(datasets)>0:
                    project_dict = dict(
                        id= str(project.id),
                        title= project.name,
                        has_children= True,
                        type= 'project',
                        level=2,
                    )
                    datasets_files = []
                    for dataset in sorted(datasets, key=lambda d: d.name):
                        dataset_files = dataset.dataset_and_files_of_types(file_types=file_types)
                        if dataset_files != None and len([f for f in dataset_files.values() if f!=None and f != []])>0:
                            datasets_files.append(dataset_files)
                    project_dict['children'] = datasets_files
                    project_datasets_files.append(project_dict)

            #retrieve datasets orphaned without a project but with your user_id
            owned_datasets = self.datasets.all()
            orphan_datasets = [d for d in owned_datasets if d.name not in datasets_processed]
            if len(orphan_datasets) > 0:
                project_dict = dict(
                    id= '0',
                    title= 'orphaned datasets',
                    has_children= True,
                    # type= 'project',
                    level=2
                )
                datasets_files = []
                for dataset in sorted(orphan_datasets, key=lambda d: d.name):
                    dataset_files = dataset.dataset_and_files_of_types(file_types=file_types)
                    if dataset_files != None and len([f for f in dataset_files.values() if f != None and f != []]) > 0:
                        datasets_files.append(dataset_files)
                    project_dict['children'] = datasets_files
                project_datasets_files.append(project_dict)


            # check we're not returning empty entries
            # project_datasets_files =
            return project_datasets_files



        @hybrid_property
        def name(self):
            return self.first_name + ' ' + self.last_name

        def get_id(self):
            """Return the email address to satisfy Flask-Login's requirements."""
            return self.email

        def is_active(self):
            """True, as all users are active."""
            return True

        def is_authenticated(self):
            """Return True if the user is authenticated."""
            return self.authenticated

        def is_anonymous(self):
            """False, as anonymous users aren't supported."""
            return False

        def __repr__(self): 
            return "<  User {} {}: {}  {}  {}  >".format(self.id, self.username, self.first_name, self.last_name, self.email)

        def __init__(self): 
            self.user_type = 'researcher'

        @hybrid_property
        def scratch_path(self):
            return self.root_path

        @hybrid_property
        def dropbox_path(self):
            return self.root_path.rstrip('/') + '/dropbox'

        @hybrid_property
        def log_path(self):
            return self.root_path.rstrip('/') + '/logs'

        @hybrid_property
        def path(self):
            return self.root_path

        # returns all user paths, beginning with the user root path
        # intended for use in instantiating user directories
        @hybrid_property
        def all_paths(self):
            paths = [ self.root_path, self.dropbox_path, self.log_path ]
            return paths

        @hybrid_property
        def default_dataset(self):
            for dataset in self.datasets:
                if dataset.name == '__default__':
                    return dataset
            return None

        def change_dataset_defaults(self, dataset):
            default_dataset = self.default_dataset
            if not default_dataset:
                default_dataset = Dataset()
                default_dataset.name = '__default__'
                default_dataset.user_id = current_user.id
                db.session.add(default_dataset)
                db.session.commit()
                db.session.refresh(default_dataset)
                self.datasets.append(default_dataset)

            try:

                if default_dataset:
                    default_dataset.ig_type = dataset.ig_type
                    default_dataset.paired = dataset.paired

                    # special treatment for arrays
                    try:
                        default_dataset.cell_types_sequenced = ast.literal_eval(str(dataset.cell_types_sequenced))
                    except:
                        default_dataset.cell_types_sequenced = [str(dataset.cell_types_sequenced)] 

                    try: 
                        default_dataset.chain_types_sequenced = ast.literal_eval(str(dataset.chain_types_sequenced))
                    except: 
                        default_dataset.chain_types_sequenced = [str(dataset.chain_types_sequenced)]

                    try:
                        default_dataset.primary_data_files_ids = ast.literal_eval(str(dataset.primary_data_files_ids))
                    except:
                        if dataset.primary_data_files_ids.isdigit():
                            default_dataset.primary_data_files_ids = [int(dataset.primary_data_files_ids)]

                    default_dataset.lab_notebook_source = dataset.lab_notebook_source
                    default_dataset.sequencing_submission_number = dataset.sequencing_submission_number
                    default_dataset.contains_rna_seq_data = dataset.contains_rna_seq_data
                    default_dataset.reverse_primer_used_in_rt_step = dataset.reverse_primer_used_in_rt_step
                    default_dataset.list_of_polymerases_used = dataset.list_of_polymerases_used
                    default_dataset.sequencing_platform = dataset.sequencing_platform
                    default_dataset.target_reads = dataset.target_reads
                    default_dataset.cell_markers_used = dataset.cell_markers_used
                    default_dataset.adjuvant = dataset.adjuvant
                    default_dataset.species = dataset.species
                    default_dataset.cell_selection_kit_name = dataset.cell_selection_kit_name
                    default_dataset.isotypes_sequenced = dataset.isotypes_sequenced
                    default_dataset.post_sequencing_processing_dict = dataset.post_sequencing_processing_dict
                    default_dataset.mid_tag = dataset.mid_tag
                    default_dataset.cell_number = dataset.cell_number
                    default_dataset.primer_set_name = dataset.primer_set_name
                    default_dataset.template_type = dataset.template_type
                    default_dataset.experiment_name = dataset.experiment_name
                    default_dataset.person_who_prepared_library = dataset.person_who_prepared_library
                    default_dataset.pairing_technique = dataset.pairing_technique
                    
                    db.session.commit()
                    return False

            except:
                return "Error: no default dataset found."

class File(db.Model):
        __tablename__ = 'file'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))
        name = db.Column(db.String(256))
        description =db.Column(db.String(512))
        file_type = db.Column(db.String(128))
        available = db.Column(db.Boolean)
        in_use = db.Column(db.Boolean)
        status = db.Column(db.String(50))
        path = db.Column(db.String(256))
        file_size = db.Column(db.BigInteger)
        chain = db.Column(db.String(128))
        url = db.Column(db.String(256))
        command = db.Column(db.String(1024))
        created = db.Column(db.DateTime, default=db.func.now())

        line_count = db.Column(db.BigInteger)

        vhvl_paired = db.Boolean() # If paired_partner is not null, then vhvl = False implies forward/reverse read pairing
        paired_partner = db.Column(db.Integer, db.ForeignKey('file.id'))
        parent_id = db.Column(db.Integer, db.ForeignKey('file.id'))
        analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

        sequences = db.relationship('Sequence', backref='file', lazy='dynamic')

        @hybrid_property
        def directory(self):
            if self.path:
                return os.path.dirname(self.path) 
            else:
                return None

        @hybrid_property
        def line_count_string(self):
            if self.line_count:
                return number_format(self.line_count)
            else:
                return None

        @hybrid_property
        def cat(self, n=100):
            with open(self.path) as file:
                line_count = 0
                for line in file.readlines():
                    print line
                    line_count+=1
                    if line_count > int(n):
                        break


        def read(self):
            with open(self.path) as file:
                lines = file.read()
            return lines



        # This allows system operations on the file
        # e.g., if os.path.isfile()file
        def __repr__(self): 
            return "<File {}  {} >".format(self.id, self.name)
            # if self.paired_partner: 
            #     p = 'Paired To: {}'.format(str(self.paired_partner))
            # else: 
            #     p = ''
            # return "<File {}: _{}_  {}  {}>".format(self.id, self.file_type, self.name, p)

        def __str__(self):
            return self.path

        def __unicode__(self):
            return unicode(self.path) or u''


        # Important! If you initialize this function with a directory/filename
        # If directory does not exist, this function will create the directory
        # If directory/filename exists --> This will rename the file, so you have to check self.name to make sure it hasn't changed
        def __init__(self, name = None, directory = None, path = None, file_type = None, user_id = None,
                    dataset_id = None, analysis_id = None, parent_id=None, check_name = False): 
            # self.s3_status = ''
            self.status = '' 
            self.available = False 
            self.created = 'now'
            self.file_type = file_type
            self.dataset_id = dataset_id
            self.analysis_id = analysis_id
            self.user_id = user_id
            self.parent_id = parent_id

            # Clean up file names here:
            if name is not None:
                name = name.replace(' ', '_')

            # If given only a path, but no name or directory, use the path
            if name == None and directory == None and path != None:
                directory = os.path.dirname(path)
                name = os.path.basename(path)
                if name == '': name = None

            # If no path is given, but a name and directory are given, make the path
            if path == None and name != None and directory != None:
                path = '{}/{}'.format(directory, name)

            # If a person confused the file path with the directory:
            if path != None and directory == None:
                if os.path.isdir(path):
                    directory = path
                else:
                    directory = os.path.dirname(path)

            if name == None or path == None or directory == None:
                self.path = path
                self.name = name
                return

            # Check directory here
            if directory != None:
                directory = directory.rstrip('/')

                if not os.path.isdir(directory):
                    print 'Making directory: {}'.format(directory)
                    os.path.mkdirs(directory)

            # Make sure this is not a duplicate file name
            split_result = name.split(os.extsep, 1)
            if len(split_result) == 2:
                file_name = split_result[0]
                file_extension = split_result[1]
            else:
                file_name = name
                file_extension = ''

            if check_name:
                # Check filenames until we find one that works
                copy_number = 0
                while os.path.isfile(path):
                    copy_number += 1
                    name = '{}_{}.{}'.format(file_name, str(copy_number), file_extension)
                    path = '{}/{}'.format(directory, name)

            self.path = path
            self.name = name

            # Change file type if not given
            if not self.file_type or self.file_type == None or self.file_type =='':
                if self.path:
                    self.file_type = parse_file_ext(self.path)


            # Set the file size and count if the file exists
            if os.path.isfile(self.path):
                self.file_size = os.stat(self.path).st_size

                if self.file_size and not self.line_count:
                    self.line_count = map_line_count(self.path)

                if not self.available: 
                    self.available = True
            else:

                if self.available: 
                    self.available = False

            return

        # Pair files
        # If vhvl_paired is False, this implies the files are paired as forward/reverse reads
        def pair(self, f, vhvl_paired = False): 
            if self.file_type == f.file_type:

                self.vhvl_paired = vhvl_paired
                f.vhvl_paired = vhvl_paired

                self.paired_partner = f.id 
                f.paired_partner = self.id 
                if self.dataset_id: 
                    d = self.dataset 
                    d.paired = True 

                self.chain = 'IGH/IGL'
                f.chain = 'IGH/IGL'
                return True 
            else: 
                return False

        # This returns True if the move is successful and false if the move is not successful
        # If the destination directory does not exist, this creates the destination directory
        # If the destination file exists, this renames the file being moved to filename_int where int is not taken
        def move(self, destination_directory = None, destination_path = None, destination_name = None):
            name = destination_name
            path = destination_path
            directory = destination_directory

            if path == None and directory == None:
                return False # Nothing to move?

            if not self.exists():
                return False # Nothing to move

            # locally, use name, directory, and path to describe the destination
            # do not overwrite db values until the move is successful!


            # Clean up file names here:
            if name is not None:
                name = name.replace(' ', '_')
                name = name
            else:
                if path and not os.path.isdir(path) and os.path.basename(path) != '':
                    name = os.path.basename(path)
                else:
                    name = self.name
            
            if path == None:
                path = '{}/{}'.format(directory.rstrip('/'), name)

            if directory == None:
                directory = os.path.dirname(path) 

            # If given only a path, but no name or directory, use the path
            if name == None and directory == None and path != None:
                directory = os.path.dirname(path)
                name = os.path.basename(path)
                if name == '': name = None

            # If no path is given, but a name and directory are given, make the path
            if path == None and name != None and directory != None:
                path = '{}/{}'.format(directory, name)

            # If a person confused the file path with the directory:
            if path != None and directory == None:
                if os.path.isdir(path):
                    directory = path
                else:
                    directory = os.path.dirname(path)

            if name == None or path == None or directory == None:
                print 'Unable to move file ({}) to directory ({})'.format(name, directory)
                return False

            # Check directory here
            if directory != None:
                directory = directory.rstrip('/')

                if not os.path.isdir(directory):
                    print 'Making directory: {}'.format(directory)
                    os.path.mkdirs(directory)

            # Make sure this is not a duplicate file name
            split_result = name.split(os.extsep, 1)
            if len(split_result) == 2:
                file_name = split_result[0]
                file_extension = split_result[1]
            else:
                file_name = name
                file_extension = ''

            # Check filenames until we find one that works
            copy_number = 0
            while os.path.isfile(path):
                copy_number += 1
                name = '{}_{}.{}'.format(file_name, str(copy_number), file_extension)
                path = '{}/{}'.format(directory, name)

            # Move it!
            try:
                os.rename( self.path, path )
            except OSError, error:
                print 'Error moving/renaming file id {} from {} to {}: {}'.format(self.id, self.path, path, error)

            self.path = path
            self.name = name

            return True


        def exists(self):
            if os.path.isfile(self.path):
                return True
            else:
                return False


        # Determine if the file described in the database actually exists
        # If the file does not exist, change database setting appropriate
        def validate(self):
            if os.path.isfile(self.path):
                if not self.available: 
                    self.available = True
                    db.session.commit()

                if not self.file_type or self.file_type == None or self.file_type =='':
                    if self.path:
                        self.file_type = parse_file_ext(self.path)


                self.status == 'AVAILABLE'

                self.file_size = os.stat(self.path).st_size

                if self.file_size and not self.line_count:
                    self.line_count = map_line_count(self.path) 
                return True
            else:
                if self.available: 
                    self.available = False
                    db.session.commit()
                return False

        # Returns True/False depending on whether the underlyng file is found
        def exists(self):
            return os.path.isfile(self.path)

        # Calls __init__ with self variables
        def change_name_to_available(self):
            return self.__init__(name = self.name, path = self.path, file_type = self.file_type, dataset_id = self.dataset_id, analysis_id = self.analysis_id, user_id = self.user_id, check_name = True)


        # Calls __init__ with self variables
        def change_name_if_taken(self):
            if self.exists():
                return self.__init__(name = self.name, path = self.path, file_type = self.file_type, dataset_id = self.dataset_id, analysis_id = self.analysis_id, user_id = self.user_id, check_name = True)
            else:
               return self

        def get_file_as_html(self):
            file_html = ''
            if os.path.isfile(self.path):

                with open(self.path, 'r') as infile:
                    if self.file_type == 'JSON':
                        try:
                            json_string = json.load(infile)
                            json_string = json.dumps(json_string, indent=4, sort_keys=True)
                            # for line in json_string:
                            #     line = line.strip()
                            #     file_html = file_html + line + '<br>\n'
                            file_html = json_string
                        except:
                            file_html = 'Unable to view JSON.<br>\n'
                    else:
                        for line in infile:
                            line = line.strip()

                            if self.file_type == 'LOG':
                                color = 'black'
                                if 'WARNING' in line:
                                    color = 'orange'
                                elif 'ERROR' in line:
                                    color = 'red'

                                file_html = file_html + '<font color="{}">{}</font><br>\n'.format( color , line )
                            else:
                                file_html = file_html + line + '<br>\n'

            return Markup(file_html)

        def get_file_head(self, num_lines, line_length = 77):
            head = ''
            if os.path.isfile(self.path):
                with io.open( self.path, encoding='ISO-8859-1' ) as infile:
                    for x in xrange(num_lines):
                        line = infile.readline()
                        if not line: break
                        line = line.strip()
                        if len(line) > line_length:
                             line = unicode_truncate(line, 117) + '...'
                        #line = '{}<br>\n'.format(line)
                        line = line + '<br>\n'
                        head = head + line

            return head


def unicode_truncate(s, length, encoding='ISO-8859-1'):
    encoded = s.encode(encoding)[:length]
    return encoded.decode(encoding, 'ignore')

def map_line_count(filename):
    f = open(filename, "r+")
    buf = mmap.mmap(f.fileno(), 0)
    lines = 0
    readline = buf.readline
    while readline():
        lines += 1
    return lines

def number_format(number):
    magnitude = 0
    while abs(number) >= 1000:
        magnitude += 1
        number /= 1000.0
    if magnitude > 6:
        magnitude = 6
    # add more suffixes if you need them
    return '{}{}'.format(int(number), ['', 'K', 'M', 'G', 'T', 'P','HUGE'][magnitude])

#@event.listens_for(Session, "before_flush")
def validate_file_object(session, flush_context = None, instances = None):
    for obj in session:
        if isinstance(obj, File):
            file = obj

            if os.path.isfile(file.path):
                file.file_size = os.stat(file.path).st_size

                if not file.file_type or file.file_type == None or file.file_type =='':
                    file.file_type = parse_file_ext(file.path)

                if file.file_size and not file.line_count:
                    file.line_count = map_line_count(file.path)

                if not file.available: 
                    file.available = True
            else:
                if file.available: 
                    file.available = False

event.listen(db.Session, 'before_flush', validate_file_object)
event.listen(db.Session, 'before_commit', validate_file_object)

#abstracted to functions.py: 
def parse_file_ext(path):

    if path.split('.')[-1] == 'gz':
        gzipped = True
    else:
        gzipped = False
    if gzipped: 
        ext = path.split('.')[-2]
    else:
        ext = path.split('.')[-1]
    ext_dict = {}
    ext_dict['fastq'] = 'FASTQ'
    ext_dict['fq'] = 'FASTQ'
    ext_dict['fa'] = 'FASTA'
    ext_dict['fasta'] = 'FASTA'
    ext_dict['fna'] = 'FASTA'
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
    if ext in ext_dict:
        file_type = ext_dict[ext]
    else:
        file_type = ''
    if isinstance(file_type, defaultdict):
        return None
    else:
        if gzipped: 
            return 'GZIPPED_{}'.format(file_type)
        else: 
            return file_type

def parse_basename(file_names): 
    if type(file_names) == str: file_names = [file_names] 
    if len(file_names) == 2: 
        file_bases = map(lambda f: f.split('/')[-1].split('.')[0], file_names)
        file_base_arrays = map(lambda f: f.split('_'), file_bases) 
        basename_array = [] 
        for i, string in enumerate(file_base_arrays[0]):
            if string == '1' and file_base_arrays[1][i] == '2': 
                continue 
            elif string == 'R1' and file_base_arrays[1][i] == 'R2':  
                continue 
            else: 
                basename_array.append(string)
        basename = '_'.join(basename_array)
        if not basename == '': 
            return basename 
        else: 
            return 'Analyzed'
    else: 
        return file_names[0].split('/')[-1].split('.')[0]




class Dataset(db.Model):
        __tablename__ = 'dataset'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
        experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
        name = db.Column(db.String(256))
        description =db.Column(db.String(512))
        ig_type = db.Column(db.String(128))
        paired = db.Column(db.Boolean, default=False)
        files = db.relationship('File', backref='dataset', lazy='dynamic')
        sequences = db.relationship('Sequence', backref='dataset', lazy='dynamic')
        analyses = db.relationship('Analysis', backref='dataset', lazy='dynamic')
        annotations = db.relationship('Annotation', backref='dataset', lazy='dynamic')
        cell_types_sequenced = db.Column(postgresql.ARRAY(db.String(50)))
        chain_types_sequenced = db.Column(postgresql.ARRAY(db.String(20)))
        primary_data_files_ids = Column(postgresql.ARRAY(db.Integer))

        lab_notebook_source = db.Column(db.String(256))
        sequencing_submission_number = db.Column(db.String(256))
        contains_rna_seq_data = db.Column(db.String(256))
        reverse_primer_used_in_rt_step = db.Column(db.String(256))
        list_of_polymerases_used = db.Column(db.String(256))
        sequencing_platform = db.Column(db.String(256))
        target_reads = db.Column(db.String(256))
        cell_markers_used = db.Column(db.String(256))
        read_access = db.Column(db.String(256)) # maintain this to add read access for users later
        owners_of_experiment = db.Column(db.String(256)) # - will use this to add to a new or existing project
        adjuvant = db.Column(db.String(256))
        species = db.Column(db.String(256)) 
        cell_selection_kit_name = db.Column(db.String(256))
        isotypes_sequenced = db.Column(db.String(256))
        post_sequencing_processing_dict = db.Column(db.String(512))    
        sample_preparation_date = db.Column(db.String(256))
        gsaf_barcode = db.Column(db.String(256))
        mid_tag = db.Column(db.String(256))
        cell_number = db.Column(db.String(256))
        primer_set_name = db.Column(db.String(256))
        template_type = db.Column(db.String(256))
        experiment_name = db.Column(db.String(256))
        person_who_prepared_library = db.Column(db.String(256))
        pairing_technique = db.Column(db.String(256))
        json_id = db.Column(db.String(256))

        directory = db.Column(db.String(256))

        projects = association_proxy('dataset_projects', 'project')

        def __repr__(self): 
            return "<Dataset {} : {} : {}>".format(self.id, self.name, self.description)

        def __init__(self):
            self.primary_data_files_ids = []

        def primary_data_files(self):
            dataset = self 
            if len(self.primary_data_files_ids) == 0:
                print 'No Data Files Associated with Dataset {}'.format(dataset.id)
                gzipped_fastqs = dataset.files_by_type('GZIPPED_FASTQ')
                fastqs = dataset.files_by_type('FASTQ')
                print 'FOUND THESE DATA FILES: GZIPPED_FASTQ: {} {}  FASTQ: {} {}'.format(len(gzipped_fastqs), gzipped_fastqs, len(fastqs), fastqs)
                if len(fastqs) == 0 and len(gzipped_fastqs) == 0:
                    print 'NO FASTQ DATA ASSOCIATED WITH DATASET'
                    files = [] 
                elif len(gzipped_fastqs) != 0:
                    files = gzipped_fastqs
                elif len(fastqs) != 0: 
                    files = fastqs 
                file_names = map(lambda f: f.name, files)
                out_files = []
                for file in files:
                    if 'R1' in file.name and file.name.replace('R1', 'R2') in file_names: 
                        out_files.append(file)
                    if 'R2' in file.name and file.name.replace('R2', 'R1') in file_names: 
                        out_files.append(file)
                    if len(files)==1:
                        out_files.append(file)
                if len(out_files) > 2: 
                    print "too many predicted primary_data_files!"
                    return None 
            else: 
                out_files = []
                for file_id in self.primary_data_files_ids: 
                    out_files.append(File.query.get(file_id))
            return out_files 


        def role(self, user):
            dataset_role = None
            if self.user_id == user.id:
                return "Owner"
            for project in self.projects:
                project_role = project.role(user)
                if project_role == "Owner":
                    return "Owner"
                elif project_role == "Editor":
                    dataset_role = "Editor"
                elif project_role == "Read Only" and dataset_role != "Editor":
                    dataset_role = "Read Only"
            return dataset_role

        def user_has_write_access(self, user): 
            user_role = self.role(user)
            if user_role == 'Owner' or user_role == 'Editor':
                return True 
            else: 
                return False 


        def files_by_type(self, type_string):
            all_files = self.files.all()
            if all_files == None: return []
            files =  [f for f in self.files.all() if f.file_type==type_string]
            return files 


        @hybrid_property
        def owner(self):
            #user = 
            try:
                user_query = db.session.query(User).filter(self.user_id == User.id)
                user = user_query[0]                    
                return user
            except:
                pass
            return None

        def populate_with_defaults(self, user):
            if not user:
                return 'Error: no user passed.'
            try:
                default_dataset = user.default_dataset
                if default_dataset:
                    self.ig_type = default_dataset.ig_type
                    self.paired = default_dataset.paired

                    self.cell_types_sequenced = default_dataset.cell_types_sequenced
                    self.chain_types_sequenced = default_dataset.chain_types_sequenced
                    self.primary_data_files_ids = default_dataset.primary_data_files_ids

                    self.lab_notebook_source = default_dataset.lab_notebook_source
                    self.sequencing_submission_number = default_dataset.sequencing_submission_number
                    self.contains_rna_seq_data = default_dataset.contains_rna_seq_data
                    self.reverse_primer_used_in_rt_step = default_dataset.reverse_primer_used_in_rt_step
                    self.list_of_polymerases_used = default_dataset.list_of_polymerases_used
                    self.sequencing_platform = default_dataset.sequencing_platform
                    self.target_reads = default_dataset.target_reads
                    self.cell_markers_used = default_dataset.cell_markers_used
                    self.adjuvant = default_dataset.adjuvant
                    self.species = default_dataset.species
                    self.cell_selection_kit_name = default_dataset.cell_selection_kit_name
                    self.isotypes_sequenced = default_dataset.isotypes_sequenced
                    self.post_sequencing_processing_dict = default_dataset.post_sequencing_processing_dict
                    self.mid_tag = default_dataset.mid_tag
                    self.cell_number = default_dataset.cell_number
                    self.primer_set_name = default_dataset.primer_set_name
                    self.template_type = default_dataset.template_type
                    self.experiment_name = default_dataset.experiment_name
                    self.person_who_prepared_library = default_dataset.person_who_prepared_library
                    self.pairing_technique = default_dataset.pairing_technique
                    return False
                else:
                    # if there are any overall defaults, initialize them here
                    pass

            except:
                return "Error: no default dataset found."

        def dataset_and_files_of_types(self, file_types=['FASTQ', 'GZIPPED_FASTQ', 'FASTA', 'GZIPPED_FASTA']):
            files = [f for f in self.files.all() if f.file_type in file_types]
            if len(files) > 0:
                dataset_value = {
                    'id': str(self.id),
                    'title': self.name,
                    'has_children': True,
                    # 'type': 'dataset',
                    'level': 3
                }
                dataset_files = []
                for file in files:
                    file_value = {
                        'id': file.id,
                        'title': file.name,
                        # 'type': 'file',
                        # 'file_type': file.file_type,
                        'has_children': False,
                        'level': 4
                    }
                    dataset_files.append(file_value)
                dataset_value['children'] = dataset_files
                return dataset_value
            else:
                return None


        # aligner= mixcr or igrep    type= overlap or paired

        def run_analysis(self, file_ids=[], analysis_type='overlap', aligner='mixcr', user_id=2):
                from app import run_analysis_pipeline
                if type(file_ids) != type([]): 
                    files = [File.query.get(int(file_ids))]
                elif file_ids != []: 
                    files = [File.query.get(int(id)) for id in file_ids] 
                else:
                    files = self.primary_data_files()
                if len(files)==0:
                    print 'must supply or get from dataset.primary_data_files() one or two files. {}'.format("file ids given: {}".format(file_ids) if file_ids!=[] else "")
                    return None
                settings = dict(user_id=user_id, species='H. sapiens', loci=['IGH', 'IGL', 'IGK'],
                                append_cterm_peptides=False,
                                cluster=False, cluster_algorithm='None', cluster_linkage='None', cluster_percent='0.9',
                                name='automated {} {} run'.format(analysis_type, aligner), description=u'',
                                filter=True, filter_percentage=50, filter_quality=20,
                                pandaseq_algorithm='ea_util', pandaseq_minimum_length=100, pandaseq_minimum_overlap=33,
                                remove_seqs_with_indels=False, require_annotations=['aaSeqCDR3'],
                                trim=False, trim_illumina_adapters=True,
                                trim_slidingwindow=False, trim_slidingwindow_quality=15, trim_slidingwindow_size=4,
                                standardize_outputs=True, )
                settings['analysis_type'] = aligner
                if analysis_type=='overlap':
                    settings['pair_vhvl'] = False
                    settings['pandaseq'] = True
                elif analysis_type=='single': 
                    settings['pair_vhvl'] = False
                    settings['pandaseq'] = False 
                elif analysis_type=='paired':
                    settings['pair_vhvl'] = True
                    settings['pandaseq'] = False
                else:
                    print 'must give overlap or paired analysis type, you gave {}'.format(analysis_type)

                settings['file_ids'] = [file.id for file in files]
                print "running analysis with these settings: {}".format(settings)
                # kick it off
                task = run_analysis_pipeline.apply_async((), settings)
                settings['async task id']=task
                return settings



class Project(db.Model):
        __tablename__ = 'project'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(128))
        description = db.Column(db.String(256))
        cell_types_sequenced = db.Column(db.String(256))
        publications = db.Column(db.String(256)) 
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        creation_date = db.Column(db.DateTime(), default=datetime.utcnow())

        species = db.Column(db.String(128))
        lab = db.Column(db.String(128))

        # establish a list of datasets
        # datasets = db.relationship('Dataset', backref='project', lazy='dynamic')
        datasets = association_proxy('project_datasets', 'dataset')

        # establish a relationship to the association table
        users = association_proxy('project_users', 'user')
        read_only_users = association_proxy('project_users', '_read_only_users')
        shared_users = association_proxy('project_users', '_shared')
        _id = db.Column(JSON())

        def __repr__(self):
            return "{} ({})".format(self.name, self.id)

        def date_string(self):
            try:
                dt = datetime.strptime(str(self.creation_date), "%Y-%m-%d %H:%M:%S.%f")
                #dt = project.creation_date
                dt_str =  dt.strftime("%Y-%m-%d")
            except:
                dt_str = None
            return dt_str

        # this does not include the owner
        @hybrid_property
        def editors(self):
            owner_set = Set([self.owner])
            total_user_set = Set(self.users)
            read_user_set = Set(self.read_only_users)
            editors = total_user_set - read_user_set
            editors = editors - owner_set
            editors.discard(None)
            return list(editors)

        @hybrid_property
        def readers(self):
            read_user_set = Set(self.read_only_users)
            read_user_set.discard(None)
            return list(read_user_set)

        @hybrid_property
        def owner(self):
            try:
                for user in self.users:
                    if self.user_id == user.id:
                        return user
            except:
                pass
            return None

        def role(self, user):
            try:
                if user == self.owner:
                    return "Owner"
                elif user in self.editors:
                    return "Editor"
                elif user in self.read_only_users:
                    return "Read Only" 
                else:
                    return None
            except:
                pass
            return None


        def user_has_write_access(self, user): 
            user_role = self.role(user)
            if user_role == 'Owner' or user_role == 'Editor':
                return True 
            else: 
                return False 


class ProjectDatasets (db.Model):
    __tablename__ = 'project_dataset'

    __table_args__ = (
        db.PrimaryKeyConstraint('project_id', 'dataset_id'),
    )

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'))

    dataset = db.relationship(Dataset, backref = db.backref("dataset_projects", cascade='save-update, merge, delete, delete-orphan'))
    project = db.relationship(Project, backref = db.backref("project_datasets",  cascade="all, delete-orphan"))

    def __init__(self, dataset = None, project = None):
        self.project = project
        self.dataset = dataset


class UserProjects (db.Model):
    __tablename__ = 'user_project'

    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'project_id'),
    )

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    read_only = db.Column(db.Boolean, default = False)
    shared = db.Column(db.Boolean, default = False)

    # _shared = db.relationship(User, primaryjoin="and_(UserProjects.shared=='TRUE', UserProjects.user_id == User.id)")
    user = db.relationship(User, backref = db.backref("user_projects"))
    _read_only_users = db.relationship(User, primaryjoin="and_(UserProjects.read_only=='TRUE', UserProjects.user_id == User.id)")

    # Orphan projects (i.e., projects with no owner OR person with read-only access) are deleted
    project = db.relationship(Project, backref = db.backref("project_users", cascade="all, delete-orphan"))

    def __init__(self, user = None, project = None, read_only = False):
        self.user = user
        self.project = project
        self.read_only = read_only

class Sequence(db.Model):  

        id = Column(Integer(), primary_key=True)
        dataset_id = Column(Integer(), ForeignKey('dataset.id'))
        file_id = Column(Integer(), ForeignKey('file.id'))
        header = Column(String(100))
        sequence = Column(String(500))
        quality = Column(String(500))
        annotations = db.relationship('Annotation', backref='sequence', lazy='dynamic')

        def __repr__(self): 
            return "< Sequence {}: {} >".format(self.id, self.header)

class Annotation(db.Model):  

        id = Column(Integer(), primary_key=True)
        sequence_id = Column(Integer(), ForeignKey('sequence.id'))
        dataset_id = Column(Integer(), ForeignKey('dataset.id'))
        analysis_id = Column(Integer(), ForeignKey('analysis.id'))
        _id = Column(JSON())
        seq_id = Column(JSON())
        exp_id = Column(JSON())
        analysis_name = Column(String())
        recombination_type = Column(String())
        strand = Column(String(10))
        strand_corrected_sequence = Column(String())
        read_sequences = Column(String())
        read_qualities = Column(String())
        header = Column(String())
        productive = Column(db.Boolean)
        productive_comment = Column(String(256))
        recombination_type = Column(String(20))
        chain = Column(String(20))

        locus = Column(String)
        isotype = Column(String)
        isotype_mismatches = Column(Integer)
        isotype_percent_similarity = Column(FLOAT)
        isotype_barcode_direction = Column(String)

        nt = Column(String(600))
        aa = Column(String(200))

        cdr1_aa = Column(String(100))
        cdr1_nt = Column(String(100))
        cdr2_aa = Column(String(100))
        cdr2_nt = Column(String(100))
        cdr3_aa = Column(String(200))
        cdr3_nt = Column(String(400))
        fr1_nt = Column(String(200))
        fr1_aa = Column(String(100))
        fr2_nt = Column(String(100))
        fr2_aa = Column(String(100))
        fr3_nt = Column(String(200))
        fr3_aa = Column(String(200))
        fr4_nt  = Column(String(100))
        fr4_aa = Column(String(100))

        c_top_hit = Column(String) 
        c_top_hit_locus = Column(String)
        v_top_hit = Column(String) 
        v_top_hit_locus = Column(String) 
        d_top_hit = Column(String) 
        d_top_hit_locus = Column(String) 
        j_top_hit = Column(String) 
        j_top_hit_locus = Column(String) 
        
        c_hits = Column(JSON)
        j_hits = Column(JSON)
        d_hits = Column(JSON)
        v_hits = Column(JSON)

        shm_aa = Column(FLOAT())
        shm_nt = Column(FLOAT())
        shm_nt_percent = Column(FLOAT())
        shm_aa_percent = Column(FLOAT())
        v_shm_nt = Column(Integer)
        v_shm_percent = Column(FLOAT)
        j_shm_nt = Column(Integer)
        j_shm_percent = Column(FLOAT)

        full_length = Column(Boolean)
        cdr3_junction_in_frame = Column(Boolean)
        codon_frame = Column(Integer)
        start_codon = Column(Integer)
        stop_codon = Column(Integer)
        index = Column(Integer)

        def __repr__(self): 
            return "< Annotation {} on Sequence {} : {} >".format(self.id, self.sequence_id, self.analysis_name)

        def __init__(self):
            self.v_hits = OrderedDict()
            self.d_hits = OrderedDict()
            self.j_hits = OrderedDict()
            self.c_hits = OrderedDict()

# Used to determine if an analysis completed without a valid exit state
pending_analysis_states = ['QUEUED', 'EXECUTING', 'WAITING', 'GUNZIPPING', 'TRIMMING FILES', 'EXECUTING USEARCH', 'EXECUTING TRIM']

class Analysis(db.Model):  

        id = Column(Integer(), primary_key=True)
        user_id = Column(Integer(), ForeignKey('user.id'))

        zip_file_id = Column(Integer(), ForeignKey('file.id', use_alter=True, name='zip_file_id'))
        log_file_id = Column(Integer(), ForeignKey('file.id', use_alter=True, name='log_file_id'))
        traceback_file_id = Column(Integer(), ForeignKey('file.id', use_alter=True, name='traceback_file_id'))
        settings_file_id = Column(Integer(), ForeignKey('file.id', use_alter=True, name='traceback_file_id'))

        async_task_id = Column(String(128))

        dataset_id = Column(Integer(), ForeignKey('dataset.id'))
        name = Column(String())
        description = Column(String(256))
        program = Column(String())
        started = Column(TIMESTAMP)
        finished = Column(TIMESTAMP)
        params = Column(JSON)
        commands = Column(postgresql.ARRAY(String(1024)))
        responses = Column(postgresql.ARRAY(Integer))
        files_to_analyze = Column(postgresql.ARRAY(Integer))
        vdj_count = Column(Integer)
        vj_count = Column(Integer)
        tcra_count = Column(Integer)
        tcrb_count = Column(Integer)
        total_count = Column(Integer)
        active_command = Column(String(512))
        status = Column(String(256))
        db_status = Column(String(256))
        notes = Column(String(1000))
        available = Column(Boolean)
        inserted_into_db = Column(Boolean)
        directory = Column(String(256))
        error = Column(String(256))
        settings = db.Column(JSON())

        annotations = db.relationship('Annotation', backref='analysis', lazy='dynamic')
        files = db.relationship('File', backref='analysis', lazy='dynamic', foreign_keys='File.analysis_id' )
        zip_file = db.relationship('File', foreign_keys='Analysis.zip_file_id')
        log_file = db.relationship('File', foreign_keys='Analysis.log_file_id')
        traceback_file = db.relationship('File', foreign_keys='Analysis.traceback_file_id')
        settings_file = db.relationship('File', foreign_keys='Analysis.settings_file_id')

        _dataset = db.relationship('Dataset', foreign_keys='Analysis.dataset_id')
        _user = db.relationship('User', backref='user_analysis', foreign_keys=[user_id])


        def __repr__(self): 
            return "< Analysis {}: {} : {} : {}>".format(self.id, self.program, self.name, self.started)

        def __init__(self):
            self.available = False

        @hybrid_property
        def dataset(self):
            return self._dataset


        @hybrid_property
        def user(self):
            return self._user

        @validates('commands', 'active_command', 'error')
        def validate_result(self, key, value):
            max_len = getattr(self.__class__, key).prop.columns[0].type.length
            if value and len(value) > max_len:
                return value[:max_len]
            return value

        def create_analysis_directory(self, directory = None, directory_prefix = None):

            if self.directory and os.path.isdir( self.directory ) : return

            if directory_prefix == None: directory_prefix = 'Analysis_'

            if directory: pass
            elif self.dataset: directory = self.dataset.directory
            elif self.user: directory = self.user.path
            else: directory = '/data'

            if not self.id:
                db.session.add(self)
                db.session.commit()
                db.session.refresh(self)
            
            self.directory = directory.rstrip('/') + '/{}{}'.format( directory_prefix, self.id)

            if not os.path.isdir(self.directory):
                os.makedirs(self.directory)

            return self.directory

class Experiment(db.Model):
        __tablename__ = 'experiment'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        project_name = db.Column(db.String(128))
        description = db.Column(db.String(256))
        _id = db.Column(JSON())
        paired = db.Column(db.Boolean, default=False)
        chain_types_sequenced = db.Column(postgresql.ARRAY(db.String(20)))
        
        # we should leave this column in temporarily for compatibility
        # as soon as the association table is created we can remove this column
        # TO DO: create new user accounts for every user listed in this column
        owners_of_experiment = db.Column(postgresql.ARRAY(db.String(20)))

        read_access = db.Column(postgresql.ARRAY(db.String(50)))
        cell_types_sequenced = db.Column(postgresql.ARRAY(db.String(50)))
        isotypes_sequenced = db.Column(postgresql.ARRAY(db.String(10)))
        publications = db.Column(postgresql.ARRAY(db.String(256)))
        mid_tag = db.Column(postgresql.ARRAY(db.String(256)))
        filenames = db.Column(postgresql.ARRAY(db.String(256)))
        reverse_primer_used_in_rt_step = db.Column(db.String(128))
        sample_preparation_date = db.Column(db.String(128))
        uploaded_by = db.Column(db.String(128))
        sequencing_platform = db.Column(db.String(128))
        experiment_creation_date = db.Column(db.String(128))
        species = db.Column(db.String(128))
        seq_count = db.Column(db.Integer())
        cell_number = db.Column(db.Integer())
        target_reads = db.Column(db.Integer())
        template_type = db.Column(db.String(128))
        experiment_name = db.Column(db.String(256))
        work_order = db.Column(db.String(128))
        gsaf_sample_name = db.Column(db.String(128))
        lab = db.Column(db.String(128))
        cell_selection_kit_name = db.Column(db.String(128))
        contains_rna_seq_data = db.Column(db.Boolean, default=False)
        curated = db.Column(db.Boolean, default=False)
        gsaf_barcode = db.Column(db.String(20))
        analyses_settings = db.Column(JSON())
        lab_notebook_source = db.Column(db.String(128))
        pairing_technique = db.Column(db.String(128))
        analyses_count = db.Column(JSON())
        person_who_prepared_library = db.Column(db.String(128))
        cell_markers_used = db.Column(postgresql.ARRAY(db.String(100)))
        list_of_polymerases_used = db.Column(postgresql.ARRAY(db.String(100)))
        primer_set_name = db.Column(postgresql.ARRAY(db.String(100)))
        datasets = db.relationship('Dataset', backref='experiment', lazy='dynamic')

        # establish a relationship to the association table
        # users = db.relationship('User', secondary = user_experiments, back_populates = 'experiments' )

        def __repr__(self): 
            return "<  Experiment {}:  {}   :   {}   :   {} >".format(self.id, self.project_name, self.experiment_name, self.seq_count)

class CeleryTask(db.Model):  
        __tablename__ = 'celery_task'

        id = Column(Integer(), primary_key=True)
        user_id = Column(Integer(), ForeignKey('user.id'))
        analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

        analysis = db.relationship('Analysis', foreign_keys='CeleryTask.analysis_id')
        #user = db.relationship('User', foreign_keys='CeleryTask.user_id')

        async_task_id = Column(String(128))

        # Name of the function called
        name = Column(String(128))

        # The final result returned from a Celery Task
        result = Column(String(512))

        # Possible values for status include PENDING, STARTED, RETRY, FAILURE, SUCCESS
        status = Column(String(16))
        
        # Might just turn these into hybrid attributes
        is_complete = Column(Boolean, default=False)
        failed = Column(Boolean, default=False)

        user_alerted = Column(Boolean, default=False)
        user_dismissed = Column(Boolean, default=False)

        @validates('result')
        def validate_result(self, key, value):
            max_len = getattr(self.__class__, key).prop.columns[0].type.length
            if value and len(value) > max_len:
                return value[:max_len]
            return value





class Source(db.Model):  
        __tablename__ = 'source'
        id = Column(Integer(), primary_key=True)
        name = Column(VARCHAR())
        release_date = Column(DATE())
        version = Column(VARCHAR())
        type = Column(VARCHAR())
        sample_size = Column(Integer())
        alleles = db.relationship('Allele', backref='source', lazy='dynamic')
        allele_frequencies = db.relationship('AlleleFrequency', backref='source', lazy='dynamic')
        populations = db.relationship('Population', backref='source', lazy='dynamic')

        def __repr__(self): 
            return "< Source {}: {} >".format(self.id, self.name)




class Allele(db.Model):  
        __tablename__ = 'allele'
        id = Column(Integer(), primary_key=True)
        name = Column(TEXT())
        functionality = Column(TEXT())
        sequence = Column(TEXT())
        gapped_sequence = Column(TEXT())
        sequence_gene = Column(TEXT())
        sequence_nuc = Column(TEXT())
        sequence_prot = Column(TEXT())
        imgt_accession = Column(TEXT())
        labels = Column(TEXT())
        codon_start = Column(DOUBLE_PRECISION())
        nucleotide_length = Column(DOUBLE_PRECISION())
        partial = Column(TEXT())
        reverse_complementary = Column(TEXT())
        coords = Column(TEXT())
        locus_id = Column(Integer(), ForeignKey('locus.id'))
        gene_id = Column(Integer(), ForeignKey('gene.id'))
        source_id = Column(Integer(), ForeignKey('source.id'))
        species_id = Column(Integer(), ForeignKey('species.id'))
        strain_id = Column(Integer(), ForeignKey('strain.id')) # To simplify Mus musculus_BCL6 to Mus
        allele_frequencies = db.relationship('AlleleFrequency', backref='allele', lazy='dynamic')

        def __repr__(self):
            return "< Allele {}: {} : {}bp >".format(self.id, self.name, len(self.sequence))

        def kmer_counts(self, k, seq_type='nuc'):
            #Count kmer occurrences in a given allele.
              #Returns:  counts : dictionary, {'string': int}
            if seq_type=='nuc':
              seq = self.sequence_nuc
            elif seq_type=='gene':
              seq = self.sequence_gene
            elif seq_type=='prot':
              seq = self.sequence_prot

            if seq==None:
              seq = self.sequence

            if 'seq' not in locals() or seq==None or seq=='' or len(seq)==0:
              return None

            counts = {}
            num_kmers = len(seq) - int(k) + 1
            for i in range(num_kmers):
                kmer = seq[i:i+k]
                if kmer not in counts:
                    counts[kmer] = 0
                counts[kmer] += 1
            return counts

        import jellyfish
        def distance_to(self, target_allele, method='hamming', seq_type='nuc'):
            if type(target_allele)!=Allele:
                print 'error: target not an allele class: {}'.format(target_allele)
                return None
            if seq_type=='nuc':
              seq1 = self.sequence_nuc
              seq2 = target_allele.sequence_nuc
            elif seq_type=='gene':
              seq1 = self.sequence_gene
              seq2 = target_allele.sequence_gene
            elif seq_type=='prot':
              seq1 = self.sequence_prot
              seq2 = target_allele.sequence_gene
            if seq1==None:
              seq1 = self.sequence
              seq2 = target_allele.sequence

            if seq1==seq2: return 0
            seqs = [unicode(s) for s in seq1,seq2 if s and len(s)>0 ]

            import jellyfish
            import editdistance
            if type(method) == str:
                if method == 'hamming':
                    method = jellyfish.hamming_distance
                elif method == 'levenshtein':
                    # method = jellyfish.levenshtein_distance
                    method = editdistance.eval  # 4x faster
                elif method == 'damerau_levenshtein':
                    method = jellyfish.damerau_levenshtein_distance
                elif method == 'jaro':
                    method = jellyfish.jaro_distance
            else:
                method = method # best to submit an actual callable method
            assert method(unicode('AAAAAA'),
                          unicode('AAAAAB')), 'allele_similarity method does not support method(str1,str2) call'

            distance = method(*seqs)
            return distance



        @hybrid_property
        def sequence_safe(self):
            if self.sequence_nuc != None and len(self.sequence_nuc) > 1:
                return self.sequence_nuc
            elif self.sequence_gene != None and len(self.sequence_gene) > 1:
                return self.sequence_gene
            elif self.sequence != None and len(self.sequence) > 1:
                return self.sequence
            else:
                return None


        @hybrid_property
        def sequence_by_type(self, seq_type='nuc'):
            if self.sequence_nuc != None and seq_type=='nuc' or seq_type=='spliced nucleotide':
                return self.sequence_nuc
            elif self.sequence_gene != None and seq_type=='gene' or seq_type=='gene':
                return self.sequence_gene
            elif self.sequence_prot != None and seq_type == 'prot' or seq_type=='protein':
                return self.sequence_prot
            elif self.sequence_prot != None and seq_type == 'default':
                return self.sequence
            else:
                return None



        @hybrid_property
        def to_fasta(self, seq_type='nuc'):
            header = ">{}_{}_{}\n".format(self.name, self.functionality, self.species.name)
            if seq_type=='nuc':
                sequence = self.sequence_nuc
            elif seq_type=='gene':
                sequence = self.sequence_gene
            elif seq_type=='prot':
                sequence = self.sequene_prot
            else:
                return None
            lines = header + sequence + '\n'
            return lines



        @classmethod
        def combined_kmers(cls, alleles, k=25, seq_type='nuc'):
          ret = defaultdict(int)
          for allele in alleles:
              counts = allele.kmer_counts(k, seq_type=seq_type)
              if not counts==None:
                for km, v in counts.items():
                    ret[km] += v
          return dict(ret)



def sum_dicts(*dicts):
    ret = defaultdict(int)
    if type(dicts[0])==list:
        dicts = dicts[0]
    for d in dicts:
        for km, v in d.items():
            ret[km] += v
    return dict(ret)





from scipy.cluster.hierarchy import cophenet
from scipy.spatial.distance import pdist

def allele_dendrogram(allele_similarity, linkage_method='ward', title='Hierarchical Clustering Dendrogram'):
    X = allele_similarity
    Z = linkage(X, linkage_method)
    # test correlation between linkage and distance
    c, coph_dists = cophenet(Z, pdist(X))



    #
    # plt.title('Hierarchical Clustering Dendrogram (truncated)')
    # plt.xlabel('sample index or (cluster size)')
    # plt.ylabel('distance')
    # dendrogram(
    #     Z,
    #     truncate_mode='lastp',  # show only the last p merged clusters
    #     p=12,  # show only the last p merged clusters
    #     leaf_rotation=90.,
    #     leaf_font_size=12.,
    #     show_contracted=True,  # to get a distribution impression in truncated branches
    # )
    # plt.show()
    #


    def allele_dendrogram_call(*args, **kwargs):
        max_d = kwargs.pop('max_d', None)
        if max_d and 'color_threshold' not in kwargs:
            kwargs['color_threshold'] = max_d
        annotate_above = kwargs.pop('annotate_above', 0)

        ddata = dendrogram(*args, **kwargs)

        if not kwargs.get('no_plot', False):
            plt.title(title)
            plt.xlabel('distance')
            plt.ylabel('allele or (cluster size)')
            for i, d, c in zip(ddata['icoord'], ddata['dcoord'], ddata['color_list']):
                if not kwargs.get('orientation', 'left'):
                    x = 0.5 * sum(i[1:3])
                    y = d[1]
                    if y > annotate_above:
                        plt.plot(x, y, 'o', c=c)
                        plt.annotate("%.3g" % y, (x, y), xytext=(0, -5),
                                     textcoords='offset points',
                                     va='top', ha='center')
                    if max_d:
                        plt.axhline(y=max_d, c='k')
                else:
                    y = 0.5 * sum(i[1:3])
                    x = d[1]
                    if x > annotate_above:
                        plt.plot(x, y, 'o', c=c)
                        plt.annotate("%.3g" % x, (x, y), xytext=(0, -5),
                                     textcoords='offset points',
                                     va='top', ha='center')

                    if max_d:
                        plt.axvline(x=max_d, c='k')
        return ddata



    plt.figure(figsize=(10,10))
    allele_dendrogram_call(
        Z,
        truncate_mode='lastp',
        p=30,
        orientation='left',
        leaf_rotation=0.,
        leaf_font_size=12.,
        show_contracted=True,
        annotate_above=50,
        max_d=50,
        labels=X.index
    )
    plt.show()


    return True




class Gene(db.Model):  
        __tablename__ = 'gene'
        id = Column(Integer(), primary_key=True)
        name = Column(TEXT())
        locus_id = Column(Integer(), ForeignKey('locus.id'))
        alleles = db.relationship('Allele', backref='gene', lazy='dynamic')
        locus_name = Column(TEXT())
        allele_frequencies = db.relationship('AlleleFrequency', backref='gene', lazy='dynamic')

        def __repr__(self): 
            return "< Gene {}: {} >".format(self.id, self.name)

        def kmer_count_alleles(self, k=25, seq_type='nuc'):
            alleles = self.alleles.all()
            if len(alleles)==0 or alleles==False:
                return None
            else:
                return Allele.combined_kmers(alleles, k=k, seq_type=seq_type)


class Locus(db.Model):  
        __tablename__ = 'locus'
        id = Column(Integer(), primary_key=True)
        name = Column(TEXT())
        type = Column(TEXT())
        alleles = db.relationship('Allele', backref='locus', lazy='dynamic')
        genes = db.relationship('Gene', backref='locus', lazy='dynamic')
        allele_frequencies = db.relationship('AlleleFrequency', backref='locus', lazy='dynamic')

        def __repr__(self): 
            return "< {} Locus {}: {} >".format(self.type, self.id, self.name)

        def kmer_count_alleles(self, k=25, seq_type='nuc'):
            alleles = self.alleles.all()
            if len(alleles)==0 or alleles==False:
                return None
            else:
                return Allele.combined_kmers(alleles, k=k, seq_type=seq_type)





class Species(db.Model):
    __tablename__ = 'species'
    id = Column(Integer(), primary_key=True)
    name = Column(VARCHAR())
    populations = db.relationship('Population', backref='species', lazy='dynamic')
    strains = db.relationship('Strain', backref='species', lazy='dynamic')
    alleles = db.relationship('Allele', backref='species', lazy='dynamic')


    def __repr__(self):
        return "< Species {}: {} >".format(self.id, self.name)


class Strain(db.Model):
    __tablename__ = 'strain'
    id = Column(Integer(), primary_key=True)
    name = Column(VARCHAR())
    species_id = Column(Integer(), ForeignKey('species.id'))
    alleles = db.relationship('Allele', backref='strain', lazy='dynamic')

    def __repr__(self):
        return "< Strain {}: {} >".format(self.id, self.name)


class Population(db.Model):
    __tablename__ = 'population'
    id = Column(Integer(), primary_key=True)
    name = Column(VARCHAR())
    species_id = Column(Integer(), ForeignKey('species.id'))
    allele_frequencies = db.relationship('AlleleFrequency', backref='population', lazy='dynamic')
    source_id = Column(Integer, ForeignKey('source.id'))

    def __repr__(self):
        return "< Population {}: {} >".format(self.id, self.name)


class AlleleFrequency(db.Model):
    __tablename__ = 'allele_frequency'
    id = Column(Integer(), primary_key=True)
    allele_id = Column(Integer(), ForeignKey('allele.id'))
    gene_id = Column(Integer(), ForeignKey('gene.id'))
    locus_id = Column(Integer(), ForeignKey('locus.id'))
    population_id = Column(Integer(), ForeignKey('population.id'))
    value = Column(FLOAT)
    source_id = Column(Integer(), ForeignKey('source.id'))

    def __repr__(self):
        return "< AlleleFrequency {}: {} >".format(self.id)



class Distance(db.Model):
    __tablename__ = 'distance'
    id = Column(Integer, primary_key=True)
    allele_id_1 = Column(Integer)
    allele_id_2 = Column(Integer)
    type = Column(VARCHAR)
    value = Column(FLOAT)




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



def get_dataset_choices(user = current_user, new = False):
    '''
    Used to get tuples for the purpose of adding a list of choices to WTForms select field
    If new == True, add an option to create a new dataset
    '''
    # set the dataset options
    datasets = Set(user.datasets)
    datasets.discard(None)
    datasets.discard(user.default_dataset)

    datasets = sorted(datasets, key=lambda x: x.id, reverse=True)
    dataset_tuples = []

    # Create form choices for datasets and files
    if len(datasets) > 0:
        for dataset in datasets:
            dataset_tuples.append( (str(dataset.id), dataset.name))

        # This form does not need a new dataset option
        if new:
            dataset_tuples.insert(0,('new', 'New Dataset'))
    elif new:
        dataset_tuples = [ ('new', 'New Dataset') ]

    return dataset_tuples

def get_project_choices(user = None, new = False):
    '''
    Used to get tuples for the purpose of adding a list of choices to WTForms select field
    If new == True, add an option to create a new project
    '''

    # get a list of user projects for the form
    projects = Set(user.projects)
    projects.discard(None)
    projects = sorted(projects, key=lambda x: x.id, reverse=True)
    project_tuples = []

    # Create form choices for projects
    if len(projects) > 0:
        for project in projects:
            if project.role(user) == 'Owner' or project.role(user) == 'Editor':
                project_tuples.append( (str(project.id), project.name))
        if len(project_tuples) > 0 and new:
            project_tuples.insert(0, ('new', 'New Project'))
    elif new:
        project_tuples = [ ('new', 'New Project') ]

    return project_tuples

def generate_new_dataset(user = None, session = db.session, name='New Dataset', description=None):
    '''
    Generates a new, default dataset and returns the dataset object
    '''
    if not user:
        return None

    new_dataset = Dataset()
    new_dataset.user_id = user.id
    new_dataset.populate_with_defaults(user)
    new_dataset.name = 'New Dataset'
    new_dataset.description = description
    session.add(new_dataset)
    session.commit()

    if name or name!='': 
        if name == '__default__':
            return redirect(url_for('.datasets'))
        new_dataset.name = name.replace(' ', '_', 99)
        new_dataset.directory = "{}/Dataset_{}_{}".format(user.path.rstrip('/') , new_dataset.name, new_dataset.id)
        if not os.path.isdir(new_dataset.directory):
            os.makedirs(new_dataset.directory)
            print 'Created directory for dataset {} at {}'.format(new_dataset.name, new_dataset.directory)
    else: 
        new_dataset.name = 'Dataset_' + str(new_dataset.id)
        new_dataset.directory = "{}/Dataset_{}".format(user.path.rstrip('/') , new_dataset.id)
        if not os.path.isdir(new_dataset.directory):
            os.makedirs(new_dataset.directory)
            print 'Created new directory at {}'.format(new_dataset.directory)

    user.datasets.append(new_dataset)
    session.commit()
    return new_dataset


def generate_new_project(user = None, datasets = None, name=None, description=None, session = db.session):
    # create a new project here with the name default, add the user and dataset to the new project
    new_project = Project()
    new_project.user_id = user.id
    if name: 
        new_project.name = name
        new_project.description = description 
        session.add(new_project)
        session.flush()
    else: 
        new_project.name = 'Project'
        session.add(new_project)
        session.flush()
        new_project.name = 'Project ' + str(new_project.id)
    new_project.users = [user]
    if datasets:
        if type(datasets)==list: 
            new_project.datasets = datasets
        else: 
            new_project.datasets = [datasets]
    session.commit()
    return new_project

# Adds a new analysis with a path formatted as: /directory/directory_prefix# where number is analysis.id
def generate_new_analysis(user = None, dataset = None, directory = None, name = None, description = None, program=None, directory_prefix = None, session = db.session, async_task_id = None):
    analysis = Analysis()

    analysis.started = 'now'
    analysis.name = name
    analysis.description = description
    analysis.async_task_id = async_task_id
    analysis.program = program 
    
    if dataset: analysis.dataset_id = dataset.id
    if user: analysis.user_id = user.id

    if directory_prefix == None: directory_prefix = 'Analysis_'

    if directory: pass
    elif dataset and dataset.directory: directory = dataset.directory
    elif user: directory = user.path
    else: directory = '/data'

    session.add(analysis)
    session.commit()
    session.refresh(analysis)

    if not analysis.name:
        analysis.name = 'Analysis_{}'.format(analysis.id)
        
    if directory:
        analysis.directory = directory.rstrip('/') + '/{}{}'.format( directory_prefix, analysis.id)

    if not os.path.isdir(analysis.directory):
        os.makedirs(analysis.directory)

    session.commit()

    return analysis
                        
