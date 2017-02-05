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
 
# Local Imports - local imports go here to prevent circular imports 
from forms import *
from functions import * 
from models import * 
from app import * 

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


# Mongo DB for Legacy Sequence Data
mongo_connection_uri = 'mongodb://reader:cdrom@geordbas01.ccbb.utexas.edu:27017/'
login_manager = LoginManager()
login_manager.init_app(app)


q = db.session.query 



def read_json_file(json_file): 
	with open(json_file) as data: 
		settings = json.load(data)
	return settings 




test_settings_local = {'analysis_type': 'mixcr',
 'append_cterm_peptides': False,
 'cluster': False,
 'dataset': ['187'],
 'dataset_files': ['1548'],
 'description': '',
 'download_chain': 'HEAVY',
 'download_url': '',
 'file_source': 'file_dataset',
 'filter': True,
 'filter_percentage': 50,
 'filter_quality': 20,
 'generate_msdb': False,
 'gsaf_chain': 'None',
 'gsaf_url': '',
 'loci': ['IGH', 'IGL', 'IGK'],
 'msdb_cluster_percent': '0.90',
 'name': '',
 'ncbi_accession': '',
 'ncbi_chain': 'HEAVY',
 'output_dataset': '187',
 'output_project': '39',
 'pair_vhvl': False,
 'pandaseq': False,
 'pandaseq_algorithm': 'ea_util',
 'pandaseq_minimum_length': 100,
 'pandaseq_minimum_overlap': 10,
 'remove_seqs_with_indels': True,
 'require_annotations': ['aaSeqCDR3'],
 'species': 'H. sapiens',
 'standardize_outputs': True,
 'trim': False,
 'trim_illumina_adapters': True,
 'trim_slidingwindow': False,
 'trim_slidingwindow_quality': 15,
 'trim_slidingwindow_size': 4,
 'user_id': 2,
 'vhvl_max': '0.96',
 'vhvl_min': '0.96',
 'vhvl_step': '0.0'}



