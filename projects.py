# -*- coding: utf-8 -*-

#System Imports
import json
import static
import sys
import os
import time
from datetime import datetime
import random
from shutil import copyfile
import operator
from sets import Set
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

from app import *

# Local Imports 
from forms import *
from functions import * 
from models import * 

# Add species to analysis form -- then use in Abstar
# Autopopulate species in UI dataset_selection, then dataset_default, then human
# Hide L/R button in carousel at ends
# CHeck that user directories are made if server is down

# Check file names and escape any undesired characters
# Check file names and prevent overwriting of other files

# Add all analysis files to analysis view/db
# clustering is in MSDB call
# Add Mass spec for Igrep, then Abstar, then Mixcr

# Questions for Russ:
# Pairing in the database - always refers to forward/reverse read pairing? VH/VL
# Switch all file uploads to direct uploads?
# Pair uploads?
# Abstar uses pandaseq - skip that and just use our PANDAseq?
# USSEARCH - 
# Output all formats in TSV
# Add link to analysis from Console

# Build pandas dataframe
# Take out CDR3 sequences - provided in header
# Separate text file with CDR3 sequences CDR3.AA
#   Now use clonotype - in IGREP binary
# Not USSEARCH

# 2. Add direct file upload
# 3. Add pairing functionality throughout - pair children output as well
# 5. # Hold off --- Add clustering algorithm
# 6. Check for number of files submitted for analysis
# 7. X Automatically check for R1/R2 etc
# 8. Require two files for PANDAseq
# 9. Check new trim analysis (passing analysis, files by ID)
# 10. /data/resources : all software
# 11. /data/resources/germlines : files reffed by system
# 12. Make sure that analyses can only be run on the correct files and cannot be run on empty filesets
# 13. Auto populate file name on upload page
# 14. Add dataset table to project page
# 15. Add Analysis Type and Cluster setting - min, max, and step
# 16. Add Dataset Defaults:
#      Human
#      SP: Mi-Seq 2x300
# 17. Check trimming filename failure

# OLDER:
# 4. Don't allow users to run analyses on empty datasets
# 5. TEST Prepopulate new datasets with default settings: d.populate_with_defaults(current_user)
# 6. TEST When creating a project for a dataset, get the project species/etc from the dataset
# 7. TEST vice versa vis a vis #6
# 8. TEST Update arrays on import from JSON
# 13. TEST No analysis on defaults
# 17. Start using new directory structure with dataset_#
#       File from URL: DONE
# 18. STARTED Add dashboard page
# 21. Clean up files listing
# 23. Add single page for running an analysis on a file/dataset
# 24. Add one-time welcome notice to dashboard page. 
# 25. Add page describing project/dataset/file concept

# Issues:
# Check for duplicate directories and files in datastore
# Add default dataset for each user
# Automatically link files into a dataset and a project for user 
#
# main goal is clustering and outputting mass spec database
# this code is currently in IGREP
# clean up UI while doing walkthrough
# 
# IGREP - biggigrep - public repo on github
# 
# Add parameters for PANDASEQ and MIXCR to datasets
# Figure out how to cascade changes to User/Project/UserProject tables
#
# Add public user functionality --> See and example project, etc
#
# get a list of projects based on a dataset query
# dataset.project
# 
# NavBar: 
# Files / Projects / Analyses
#
# igfft : can run through celery
# looks different from mixcr output
# parse and compare both outputs in a PANDAS panel
#
# Native file output
# TSV
# Common table
# Cluster and generate mass spec database
# 11 clones, 90 reads
# Need a new clustering software (USEARCH) - FASTA
# sorted by sequence length
# name each sequence
# queue - development
#
# Walk throughs - two files, run mixcr
# 
# 
# Make these celery tasks
# 
#
# Check duplicate dataset names in database
# add dashboard to dashboard route
# Add glyphicon for adding files
#
# Walk-through
#
# Dataset 158 10K reads good for analysis
# in Project 
#
# Add link to projects on dataset view. 
#
# Add dataset using urls
# Run an analysis
#
# check to make sure all datasets are viewed
#
# user can edit any dataset where they can edit the project
# user can view any dataset where they are a reader of the project
# 
# Should only create
# Walk through analyses
# /dataset/analysis/files
# Create analysis - work on the UI 

# Prevent users from running analyses 

projects_blueprint = Blueprint('projects', __name__)

@projects_blueprint.route('/manage_projects', methods=['GET', 'POST'])
@login_required
def manage_projects():
    edit_project_form = CreateProjectForm()

    projects = []
    read_only_projects = []
    editor_projects = []
    owner_projects = []

    user_projects = db.session.query(Project).filter(Project.users.contains(current_user)).order_by(Project.id)

    if user_projects and user_projects.count() > 0:

        for project in user_projects:
            role = project.role(current_user)

            if role == "Owner":
                read_only = False
                owner_projects.append((project.project_name, project.id, project.description, project.species, 
                        project.cell_types_sequenced, project.date_string(), role, read_only ))
            elif role == "Editor":
                read_only = False
                editor_projects.append((project.project_name, project.id, project.description, project.species, 
                        project.cell_types_sequenced, project.date_string(), role, read_only ))
            else:
                read_only = True
                read_only_projects.append((project.project_name, project.id, project.description, project.species, 
                        project.cell_types_sequenced, project.date_string(), role, read_only ))

    projects = owner_projects + editor_projects + read_only_projects
    
    if len(projects) == 0:
        projects = None

    return render_template("manage_projects.html", projects = projects, edit_project_form = edit_project_form, current_user=current_user)

@projects_blueprint.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    create_project_form = CreateProjectForm()

    # also need to wrap this with some exception handling in case this query fails
    users = Set(db.session.query(User).filter(User.id != current_user.id))
    users.discard(None)
    users = sorted(users, key=lambda x: x.last_name, reverse=False)
    user_choices = [(str(user.id), user.name) for user in users]
    create_project_form.editors.choices = user_choices # choices should be a tuple (str(id), username)
    create_project_form.viewers.choices = user_choices 

    datasets = Set(current_user.datasets)
    datasets.discard(None)
    datasets.discard(current_user.default_dataset)
    datasets = sorted(datasets, key=lambda x: x.id, reverse=False)
    dataset_choices = [(str(dataset.id), dataset.name + ' (' + str(dataset.id) + ')' ) for dataset in datasets]
    create_project_form.datasets.choices = dataset_choices # choices should be a tuple (id, username)

    if create_project_form.validate_on_submit():

        # Still need to test for duplicate names
        new_project = Project(
                            user_id = current_user.id,
                            project_name = create_project_form.project_name.data,
                            description = create_project_form.description.data,
                            cell_types_sequenced = create_project_form.cell_types_sequenced.data,
                            publications = create_project_form.publications.data,
                            species = create_project_form.species.data,
                            lab = create_project_form.lab.data
                        )

        # Get a list of users who can edit
        user_access_list = []
        user_read_list = []

        # The current user can of course access their own file
        user_access_list.append(current_user)

        # Add a list of users who can access the project
        for user in users:
            if str(user.id) not in create_project_form.editors.data:
                user_access_list.append(user)
            else:
                if str(user.id) not in create_project_form.viewers.data:
                    user_access_list.append(user)
                    user_read_list.append(user)

        # user editor list is now a list of editors and viewers, so set the association proxy accordingly
        new_project.users = user_access_list

        # add selected datasets to the project
        dataset_selection = []
        for dataset in datasets:
            if str(dataset.id) not in create_project_form.datasets.data:
                dataset_selection.append(dataset)

        if current_user.default_dataset:
            dataset_selection.append(current_user.default_dataset) 

        new_project.datasets = dataset_selection

        db.session.add(new_project)
        db.session.flush()
        
        # if the owner set read-only access for users, then we have to update the read-only setting in the association table manually
        if len(user_read_list) > 0:
            db.session.refresh(new_project)
            for user in user_read_list:
                try: 
                    read_only_user_project = db.session.query(UserProjects). \
                        filter(UserProjects.user_id == user.id). \
                        filter(UserProjects.project_id == new_project.id)
                    read_only_user_project[0].read_only = True
                except:
                    print "Error setting read_only attribute for {}".format(user)

        # determine if a JSON was submitted to be added to the project
        try:
            if request.files['file'].filename != '':
                db.session.refresh(new_project)

                request_file = request.files['file']
                json_string = request_file.read()

                # if this function returns a string, it describes the error
                error = create_datasets_from_JSON_string(json_string, new_project)
                if error:
                    flash(error, 'warning')            
        except:
            flash('There was an error in uploading your JSON file.','warning')

        db.session.commit()

        flash('Your new project has been created.', 'success')
        return redirect( url_for('projects.manage_projects') )

    else:
        flash_errors(create_project_form)

    defaults = [(str(user.id)) for user in users]
    create_project_form.editors.data = defaults # defaults should be a list [str(id)]
    create_project_form.viewers.data = defaults 
    dataset_defaults = [(str(dataset.id)) for dataset in datasets]
    create_project_form.datasets.data = dataset_defaults 

    return render_template("create_project.html", create_project_form = create_project_form, current_user=current_user)

@projects_blueprint.route('/edit_project/<project_id>', methods=['GET','POST'])
@login_required
def edit_project(project_id):
    edit_project_form = CreateProjectForm()

    try:
        # first, determine if the project exists, and if the user has permission to edit it
        project_query = db.session.query(Project).filter(Project.id==project_id)
        
        if project_query and project_query.count() > 0:
            project = project_query[0]
        else:
            flash('Error: there was an error attempting to edit that project.', 'warning')
            return redirect( url_for('projects.manage_projects') )
    except:
        flash('Error: there was an error attempting to edit that project.', 'warning')
        return redirect( url_for('projects.manage_projects') )        

    if not project or current_user in project.readers or (current_user != project.owner and current_user not in project.editors):
        flash('Error: you do not have permission to edit that project.', 'warning')
        return redirect( url_for('projects.manage_projects') )        

    editor_defaults = []
    viewer_defaults = []

    # Set of users, not including current user or project owner
    users = Set(db.session.query(User). \
            filter(User.id != current_user.id). \
            filter(User.id != project.user_id))
    users.discard(None)
    users = sorted(users, key=lambda x: x.last_name, reverse=False)

    user_choices = [(str(user.id), user.name) for user in users]
    edit_project_form.editors.choices = user_choices # choices should be a tuple (id, username)
    edit_project_form.viewers.choices = user_choices # choices should be a tuple (id, username)

    datasets = Set(current_user.datasets)
    datasets.discard(None)
    datasets.discard(current_user.default_dataset)
    datasets = sorted(datasets, key=lambda x: x.id, reverse=False)

    dataset_choices = [(str(dataset.id), dataset.name + ' (' + str(dataset.id) + ')' ) for dataset in datasets]
    edit_project_form.datasets.choices = dataset_choices # choices should be a tuple (id, username)

    owner = None

    if project:
        owner = project.owner.name
        
        if request.method == 'GET':
            for user in users:
                if user not in project.read_only_users:
                    viewer_defaults.append(str(user.id))
                else: # the user is in the read_only list, so they have to be taken off the editor list
                    editor_defaults.append(str(user.id))

                if user not in project.users:
                    editor_defaults.append(str(user.id))
            
            # this places datasets not attached to the current project on the right side of the multiselect
            edit_project_form.datasets.data = []
            for dataset in datasets:
                if dataset not in project.datasets:
                    edit_project_form.datasets.data.append(str(dataset.id))

            # populate select fields with user names
            edit_project_form.editors.data = editor_defaults # default should be a list of ids NOT SELECTED
            edit_project_form.viewers.data = viewer_defaults # default should be a list of ids NOT SELECTED

            # prepopulate the form with data from the database                
            edit_project_form.project_name.data = project.project_name
            edit_project_form.description.data = project.description
            edit_project_form.cell_types_sequenced.data = project.cell_types_sequenced
            edit_project_form.publications.data = project.publications
            edit_project_form.species.data = project.species
            edit_project_form.lab.data = project.lab 
            return render_template("edit_project.html", edit_project_form = edit_project_form, project_id = project_id, owner = owner, current_user=current_user)

        else:
            if edit_project_form.validate_on_submit():

                # Get a list of users who can edit
                user_access_list = []
                user_read_list = []

                # determine which users are selected as editors or readers (editor selection trumps reader selection)
                for user in users:
                    if str(user.id) not in edit_project_form.editors.data:
                        user_access_list.append(user)
                    else:
                        if str(user.id) not in edit_project_form.viewers.data:
                            user_access_list.append(user)
                            user_read_list.append(user)

                # user editor list is now a list of editors and viewers, so set the association proxy accordingly, not forgetting current user!
                user_access_list.append(current_user)
                if current_user.id != project.user_id:
                    for user in project.users:
                        if user.id == project.user_id:
                            user_access_list.append(user)

                project.users = user_access_list

                # Change the read only setting for selected read only users
                for user in user_read_list:
                    try: 
                        read_only_user_project = db.session.query(UserProjects). \
                            filter(UserProjects.user_id == user.id). \
                            filter(UserProjects.project_id == project.id)
                        read_only_user_project[0].read_only = True
                    except:
                        print "Error setting read_only attribute for {}".format(user)

                # Detmine which datasets are selected and add them to the databse
                dataset_selection = []

                # first, if another user has their datasets in the project, keep them there!
                project_datasets = Set(project.datasets)
                project_datasets.discard(None)
                for dataset in project_datasets:
                    if dataset.user_id != current_user.id:
                        dataset_selection.append(dataset)

                # now, add the datasets selected by the user
                for dataset in datasets:
                    if str(dataset.id) not in edit_project_form.datasets.data:
                        dataset_selection.append(dataset)
                project.datasets = dataset_selection

                # Still need to test for duplicate names
                # update the database with the data, then redirect
                project.project_name = edit_project_form.project_name.data
                project.description = edit_project_form.description.data
                project.cell_types_sequenced = edit_project_form.cell_types_sequenced.data
                project.publications = edit_project_form.publications.data
                project.species = edit_project_form.species.data
                project.lab = edit_project_form.lab.data

                db.session.commit()

                # determine if a JSON was submitted to be added to the project
                try:
                    if request.files['file'].filename != '':

                        request_file = request.files['file']
                        json_string = request_file.read()

                        # if this function returns a string, it describes the error
                        error = create_datasets_from_JSON_string(json_string, project)
                        if error:
                            flash(error, 'warning')    
                        else:
                            # now, we need to update the list of datasets in the project
                            db.session.commit()
                            flash('Success!!! Your new project has been updated.', 'success')
                            return redirect( url_for('projects.edit_project', project_id = project.id) )
                except:
                    flash('There was an error in uploading your JSON file.','warning')
                
                flash('Success!!! Your new project has been updated.', 'success')

                # painfully redundant, but this will clean up and form issues where there is a double viewer/editor selection:
                for user in users:
                    if user not in project.read_only_users:
                        viewer_defaults.append(str(user.id))

                # populate select fields with user names
                edit_project_form.viewers.data = viewer_defaults # default should be a list of ids NOT SELECTED

            else:
                flash_errors(edit_project_form)

            return render_template("edit_project.html", edit_project_form = edit_project_form, project_id = project_id, owner = owner, current_user=current_user)
    else:
        flash('Error: the project was not found or you do not have permission to edit the project.', 'warning')
        return redirect( url_for('projects.manage_projects') )

    return render_template("edit_project.html", edit_project_form = edit_project_form, project_id = project_id, current_user=current_user)

@projects_blueprint.route('/view_project/<project_id>', methods=['GET', 'POST'])
@login_required
def view_project(project_id):

    view_project_form = CreateProjectForm()

    # first, make sure the user has access to the project
    try:
        project_query = db.session.query(Project). \
                            filter(Project.id == project_id). \
                            filter(Project.users.contains(current_user))
    except:
        flash('Error: there was an error attempting to view that project.','warning')
        return redirect( url_for('projects.manage_projects') )

    if project_query and project_query.count() > 0:
        project = project_query[0]
    else:
        flash('Error: there was an error attempting to view that project.','warning')
        return redirect( url_for('projects.manage_projects') )

    read_only = current_user in project.read_only_users

    view_project_form.project_name.data = project.project_name
    view_project_form.description.data = project.description
    view_project_form.cell_types_sequenced.data = project.cell_types_sequenced
    view_project_form.publications.data = project.publications
    view_project_form.species.data = project.species
    view_project_form.lab.data = project.lab
    creation_date = project.date_string()

    owner = project.owner.name
    write_user_list = [user.name for user in sorted(project.editors, key=lambda x: x.last_name, reverse=False)]
    read_only_list = [user.name for user in sorted(project.readers, key=lambda x: x.last_name, reverse=False)]

    datasets = Set(project.datasets)
    datasets.discard(None)
    datasets = sorted(datasets, key=lambda x: x.id, reverse=False)

    dataset_list = [(dataset.name + ' (' + str(dataset.id) + ')', dataset.owner.name, dataset.id) for dataset in datasets]

    return render_template("view_project.html", 
        view_project_form = view_project_form, 
        project_id = project_id, 
        read_only = read_only, 
        creation_date = creation_date,
        owner = owner,
        read_only_list = read_only_list,
        write_user_list = write_user_list,
        dataset_list = dataset_list, 
        current_user=current_user)


