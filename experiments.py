# #System Imports
# import json
# import static
# import sys
# import os
# import time
# import random
# from shutil import copyfile
# import operator
# # import urllib
# os.environ['http_proxy']=''
# import urllib2
# import itertools
# import subprocess
# import boto 
# import math 
# # from filechunkio import FileChunkIO 
# from celery import Celery
# from collections import defaultdict, OrderedDict
# import collections
# #Flask Imports
# from werkzeug import secure_filename
# from flask import Blueprint, render_template, flash, redirect, url_for
# from flask import Flask, Blueprint, make_response, render_template, render_template_string, request, session, flash, redirect, url_for, jsonify, get_flashed_messages, send_from_directory
# from flask.ext.bcrypt import Bcrypt
# from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
# from flask.ext.mail import Mail, Message
# from flask.ext.script import Manager
# from flask.ext.migrate import Migrate, MigrateCommand
# from flask_bootstrap import Bootstrap
# from flask_bootstrap import __version__ as FLASK_BOOTSTRAP_VERSION
# from flask_nav import Nav 
# from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
# from flask_sqlalchemy import SQLAlchemy
# from markupsafe import escape
# # from render_utils import make_context, smarty_filter, urlencode_filter
# import wtforms
# from flask_wtf import Form
# import random
# import jinja2 
# from sqlalchemy import create_engine
# from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean
# from sqlalchemy.dialects import postgresql
# from sqlalchemy.dialects.postgresql import JSON, JSONB, ARRAY, BIT, VARCHAR, INTEGER, FLOAT, NUMERIC, OID, REAL, TEXT, TIME, TIMESTAMP, TSRANGE, UUID, NUMRANGE, DATERANGE
# from sqlalchemy.sql import select
# from sqlalchemy.orm import sessionmaker, scoped_session
# from pymongo import MongoClient
# import pymongo

# from app import *

# # Local Imports 
# from forms import *
# from functions import * 
# from models import * 

# #
# # Dataset notes: only support human and mouse
# # Add parameters for PANDASEQ and MIXCR to datasets
# # 
# # 
# # 
# #
# #
# #
# #

# experiments_blueprint = Blueprint('experiments', __name__)

# @experiments_blueprint.route('/manage_experiments', methods=['GET', 'POST'])
# @login_required
# def manage_experiments():

#     return render_template("manage_experiments.html")

# @experiments_blueprint.route('/browse_experiments', methods=['GET', 'POST'])
# @login_required
# def browse_experiments():
#     # print request.__dict__
#     files = current_user.files.all()
#     datasets = current_user.datasets.all()
#     datadict = tree()
#     for dataset in datasets:
#         datadict[dataset] = dataset.files.all()
#     form = Form()
#     exps = db.session.query(Experiment).order_by(Experiment.curated.desc(), Experiment.experiment_creation_date.desc()).all()
#     species_data = sorted(db.engine.execute('select species, count(*) from experiment GROUP BY species;').fetchall(), key=lambda x: x[1], reverse=True)
#     chain_data = sorted(db.engine.execute('select chain_types_sequenced, count(*) from experiment GROUP BY chain_types_sequenced;').fetchall(), key=lambda x: x[1], reverse=True)
#     cell_data = sorted(db.engine.execute('select cell_types_sequenced, count(*) from experiment GROUP BY cell_types_sequenced;').fetchall(), key=lambda x: x[1], reverse=True)
#     primer_data = sorted(db.engine.execute('select primer_set_name, count(*) from experiment GROUP BY primer_set_name;').fetchall(), key=lambda x: x[1], reverse=True)
#     cell_marker_data = sorted(db.engine.execute('select cell_markers_used, count(*) from experiment GROUP BY cell_markers_used;').fetchall(), key=lambda x: x[1], reverse=True)
#     owner_query_data = sorted(db.engine.execute('select owners_of_experiment, count(*) from experiment GROUP BY owners_of_experiment;').fetchall(), key=lambda x: x[1], reverse=True)
#     owners = set(flatten_list([o[0] for o in owner_query_data]))
#     owner_data = {}
#     for o in owners: 
#         owner_data[o] = 0 
#     for os,c in owner_query_data: 
#         for o in os: 
#             owner_data[o] += c 
#     owner_data = sorted(owner_data.items(), key=operator.itemgetter(1), reverse=True)
#     isotype_query_data = sorted(db.engine.execute('select isotypes_sequenced, count(*) from experiment GROUP BY isotypes_sequenced;').fetchall(), key=lambda x: x[1], reverse=True)
#     isotype_data = demultiplex_tuple_counts(isotype_query_data)
#     # sorted(isotype_counts.items(), key=operator.itemgetter(0))
#     cell_marker_query_data = sorted(db.engine.execute('select cell_markers_used, count(*) from experiment GROUP BY cell_markers_used;').fetchall(), key=lambda x: x[1], reverse=True)
#     cell_marker_data=demultiplex_tuple_counts(cell_marker_query_data, index=1, reverse=True)
#     # print cell_marker_data 
#     golden = retrieve_golden()
#     err = False
#     return render_template("browse_experiments.html", datadict=datadict, form=form, exps=exps, err=err, gif_path=golden, species_data=species_data, chain_data=chain_data, cell_data=cell_data, cell_marker_data=cell_marker_data, primer_data=primer_data, isotype_data=isotype_data, owner_data=owner_data)

# @experiments_blueprint.route('/create_experiment', methods=['GET', 'POST'])
# @login_required
# def create_experiment():
#     create_experiment_form = CreateExperimentForm()
#     return render_template("create_experiment.html", create_experiment_form = create_experiment_form)



# @experiments_blueprint.route('/edit_experiment', methods=['GET', 'POST'])
# @login_required
# def edit_experiment():
#     return redirect( url_for('experiments.manage_experiments') )




