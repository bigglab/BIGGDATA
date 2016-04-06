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

# 
# Dataset notes: only support human and mouse
# Add parameters for PANDASEQ and MIXCR to datasets
# Figure out how to cascade changes to User/Project/UserProject tables
# Read up on SQLAlchemy sessions
#
# Add public user functionality --> See and example project, etc
# Add tabs for yours, shared, and read-only 
# 

projects_blueprint = Blueprint('projects', __name__)

@projects_blueprint.route('/manage_projects', methods=['GET', 'POST'])
@login_required
def manage_projects():
    edit_project_form = CreateProjectForm()

    # lists of projects (data stored as tuples) where current user is owner, editor, or has read-only access
    own_projects = []
    edit_projects = []
    read_projects = []
    projects = []
    
    user_projects = db.session.query(Project).filter(Project.project_users.any(read_only = 'FALSE')). \
                                                     filter(Project.users.contains(current_user))

    if user_projects and user_projects.count() > 0:

        read_only = False

        for project in user_projects:

            if project.user_id == current_user.id:
                role = 'Owner'
            else:
                role = 'User'

            projects.append((
                project.project_name,
                project.id, 
                project.description, 
                project.species, 
                project.cell_types_sequenced, 
                project.date_string(),
                role, 
                read_only ))
    
    user_projects =  db.session.query(Project).filter(Project.project_users.any(read_only = 'TRUE')). \
                                                     filter(Project.users.contains(current_user))

    if user_projects and user_projects.count() > 0:

        read_only = True
        role = 'Read Only'

        for project in user_projects:
            projects.append((
                project.project_name,
                project.id, 
                project.description, 
                project.species, 
                project.cell_types_sequenced, 
                project.date_string(),
                role,  
                read_only ))

    if len(projects) == 0:
        projects = None

    return render_template("manage_projects.html", projects = projects, edit_project_form = edit_project_form)

@projects_blueprint.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    create_project_form = CreateProjectForm()

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

        new_project.users.append(current_user)

        db.session.add(new_project)
        db.session.commit()

        flash('Success!!! Your new project has been created.', 'success')
        return redirect( url_for('projects.manage_projects') )

    else:
        flash_errors(create_project_form)
    return render_template("create_project.html", create_project_form = create_project_form)

    #return render_template("create_project.html", create_project_form = create_project_form, get_flashed_messages=get_flashed_messages)

@projects_blueprint.route('/edit_project', methods=['POST'])
@login_required
def edit_project():
    edit_project_form = CreateProjectForm()

    try:
        project_id = request.form['id']

        # first, determine if the project exists, and if the user has permission to edit it
        project_query = db.session.query(Project).filter(Project.project_users.any(read_only = 'FALSE')). \
                                                     filter(Project.users.contains(current_user)). \
                                                     filter(Project.id==project_id)
    except:
        flash('Error: there was an error attempting to edit that project.', 'warning')
        return redirect( url_for('projects.manage_projects') )


    if project_query and project_query.count() > 0:
        project = project_query[0]
    else:
        project = None

    choices = []
    editor_defaults = []
    viewer_defaults = []

    users = db.session.query(User).filter(User.id != current_user.id)

    user_choices = [(str(user.id), user.first_name + " " + user.last_name) for user in users]
    edit_project_form.editors.choices = user_choices # choices should be a tuple (id, username)
    edit_project_form.viewers.choices = user_choices # choices should be a tuple (id, username)

    if project:
        if request.form['submit'] == 'Edit':

            for user in users:
                if user not in project.users:
                    editor_defaults.append(str(user.id))
                if user not in project.read_only_users:
                    viewer_defaults.append(str(user.id))

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
            return render_template("edit_project.html", edit_project_form = edit_project_form, project_id = project_id)

        else:
            if edit_project_form.validate_on_submit():

                # Get a list of users who can edit
                user_access_list = []
                user_read_list = []

                for user in users:
                    if str(user.id) not in edit_project_form.editors.data:
                        user_access_list.append(user)
                    else:
                        if str(user.id) not in edit_project_form.viewers.data:
                            user_access_list.append(user)
                            user_read_list.append(user)


                # user editor list is now a list of editors and viewers, so set the association proxy accordingly, not forgetting current user!
                user_access_list.append(current_user)
                project.users = user_access_list

                print "Access List:"
                print user_access_list
                print "Read List:"
                print user_read_list

                for user in user_read_list:
                    try: 
                        read_only_user_project = db.session.query(UserProjects). \
                            filter(UserProjects.user_id == user.id). \
                            filter(UserProjects.project_id == project.id)
                        read_only_user_project[0].read_only = True
                    except:
                        print "Error setting read_only attribute for {}".format(user)


                # Still need to test for duplicate names
                # update the database with the data, then redirect
                project.project_name = edit_project_form.project_name.data
                project.description = edit_project_form.description.data
                project.cell_types_sequenced = edit_project_form.cell_types_sequenced.data
                project.publications = edit_project_form.publications.data
                project.species = edit_project_form.species.data
                project.lab = edit_project_form.lab.data
                
                db.session.commit()

                flash('Success!!! Your new project has been updated.', 'success')
                #return redirect( url_for('projects.manage_projects') )

                # painfully redundant, but this will clean up and form issues where there is a double viewer/editor selection:
                for user in users:
                    if user not in project.read_only_users:
                        viewer_defaults.append(str(user.id))

                # populate select fields with user names
                edit_project_form.viewers.data = viewer_defaults # default should be a list of ids NOT SELECTED

            else:
                flash_errors(edit_project_form)

            return render_template("edit_project.html", edit_project_form = edit_project_form, project_id = project_id)
    else:
        flash('Error: the project was not found or you do not have permission to edit the project.', 'warning')
        return redirect( url_for('projects.manage_projects') )

    return render_template("edit_project.html", edit_project_form = edit_project_form, project_id = project_id)

@projects_blueprint.route('/view_project', methods=['POST'])
@login_required
def view_project():

    view_project_form = CreateProjectForm()

    # first, make sure the user has access to the project
    try:
        project_id = request.form['id']
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

    if current_user in project.read_only_users:
        read_only = True
    else:
        read_only = False

    view_project_form.project_name.data = project.project_name
    view_project_form.description.data = project.description
    view_project_form.cell_types_sequenced.data = project.cell_types_sequenced
    view_project_form.publications.data = project.publications
    view_project_form.species.data = project.species
    view_project_form.lab.data = project.lab
    creation_date = project.date_string()

    return render_template("view_project.html", 
        view_project_form = view_project_form, 
        project_id = project_id, 
        read_only = read_only, 
        creation_date = creation_date)


