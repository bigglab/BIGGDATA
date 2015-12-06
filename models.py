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
 
#Local Imports 
from forms import *
from functions import * 


bcrypt = Bcrypt()
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
        user_type = db.Column(db.String(128))
        dropbox_path = db.Column(db.String(256))
        scratch_path = db.Column(db.String(256))
        files = db.relationship('File', backref='user', lazy='dynamic')
        datasets = db.relationship('Dataset', backref='user', lazy='dynamic')
        analyses = db.relationship('Analysis', backref='user', lazy='dynamic')
        
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
            return "<  User {}: {}  {}  {}  >".format(self.username, self.first_name, self.last_name, self.email)



        def __init__(self): 
            self.user_type = 'researcher'






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
        file_size = db.Column(db.Integer)
        s3_available = db.Column(db.Boolean)
        s3_status = db.Column(db.String(50))
        s3_path = db.Column(db.String(256))
        chain = db.Column(db.String(128))
        url = db.Column(db.String(256))
        command = db.Column(db.String(1024))
        created = db.Column(db.DateTime, default=db.func.now())
        paired_partner = db.Column(db.Integer, db.ForeignKey('file.id'))
        parent_id = db.Column(db.Integer, db.ForeignKey('file.id'))
        analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'))

        sequences = db.relationship('Sequence', backref='file', lazy='dynamic')

        def __repr__(self): 
            if self.paired_partner: 
                p = 'Paired To: {}'.format(str(self.paired_partner))
            else: 
                p = ''
            return "<File {}: _{}_  {}  {}>".format(self.id, self.file_type, self.name, p)

        def __init_(self): 
            self.s3_status = ''
            self.status = '' 
            self.available = False 
            self.created = 'now'

        def pair(self, f): 
            if self.file_type == f.file_type: 
                self.paired_partner = f.id 
                f.paired_partner = self.id 
                if self.dataset_id: 
                    d = self.dataset 
                    d.paired = True 
                return True 
            else: 
                return False


class Dataset(db.Model):
        __tablename__ = 'dataset'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
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


        def __repr__(self): 
            return "<Dataset {} : {} : {}>".format(self.id, self.name, self.description)

        def __init__(self):
            self.primary_data_files_ids = []



        def primary_data_files(self):
            all_files = self.files.all()
            if all_files == None: return []
            dataset = self 
            if len(self.primary_data_files_ids) == 0:
                print 'No Data Files Associated with Dataset {}'.format(dataset.id)
                gzipped_fastqs = dataset.files_by_type('GZIPPED_FASTQ')
                fastqs = dataset.files_by_type('FASTQ')
                print 'FOUND THESE DATA FILES: GZIPPED_FASTQ: {} {}  FASTQ: {} {}'.format(len(gzipped_fastqs), gzipped_fastqs, len(fastqs), fastqs)
                if len(fastqs) == 0 and len(gzipped_fastqs) == 0:
                    print 'NO FASTQ DATA ASSOCIATED WITH DATASET'
                    files = [] 
                if len(fastqs) == 0 and len(gzipped_fastqs) != 0:
                    files = gzipped_fastqs
                if len(fastqs) != 0: 
                    files = fastqs 
            else: 
                files = [f for f in all_files if f.id in self.primary_data_files_ids]
            return files 


        def files_by_type(self, type_string):
            all_files = self.files.all()
            if all_files == None: return []
            files =  [f for f in self.files.all() if f.file_type==type_string]
            return files 
        # primary_data_files = db.relationship('File', primaryjoin="File.dataset_id == Dataset.id")




class Experiment(db.Model):
        __tablename__ = 'experiment'
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        project_name = db.Column(db.String(128))
        description = db.Column(db.String(256))
        _id = db.Column(JSON())
        paired = db.Column(db.Boolean, default=False)
        chain_types_sequenced = db.Column(postgresql.ARRAY(db.String(20)))
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

        def __repr__(self): 
            return "<  Experiment {}:  {}   :   {}   :   {} >".format(self.id, self.project_name, self.experiment_name, self.seq_count)





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

        def __repr__(self): 
            return "< Annotation {} on Sequence {} : {} >".format(self.id, self.sequence_id, self.analysis_name)

        def __init__(self):
            self.v_hits = OrderedDict()
            self.d_hits = OrderedDict()
            self.j_hits = OrderedDict()
            self.c_hits = OrderedDict()







class Analysis(db.Model):  

        id = Column(Integer(), primary_key=True)
        user_id = Column(Integer(), ForeignKey('user.id'))
        dataset_id = Column(Integer(), ForeignKey('dataset.id'))
        name = Column(String())
        description = Column(String(256))
        program = Column(String())
        started = Column(TIMESTAMP)
        finished = Column(TIMESTAMP)
        params = Column(JSON)
        commands = Column(postgresql.ARRAY(String(1024)))
        responses = Column(postgresql.ARRAY(Integer))
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

        annotations = db.relationship('Annotation', backref='analysis', lazy='dynamic')
        files = db.relationship('File', backref='analysis', lazy='dynamic')

        def __repr__(self): 
            return "< Analysis {}: {} : {} : {}>".format(self.id, self.program, self.name, self.started)

        def __init__(self):
            self.available = False




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


def trim_ig_allele_name(long_name): 
    if long_name == None: return ''
    if '*' in long_name: long_name = [l for l in long_name.split('*') if 'IG' in l or 'TR' in l][0]
    return long_name

def trim_ig_locus_name(long_name): 
    # print 'trimming long name: {}'.format(long_name)
    if long_name == None: return ''
    if long_name == '*': return ''
    if long_name == '.': return ''
    if long_name == 'P': return ''
    if long_name == '-': return ''
    if long_name == ' ': return ''
    if '-' in long_name: long_name = [l for l in long_name.split('-') if 'IG' in l or 'TR' in l][0]
    if '*' in long_name: long_name = [l for l in long_name.split('*') if 'IG' in l or 'TR' in l][0]
    if '.' in long_name: long_name = [l for l in long_name.split('.') if 'IG' in l or 'TR' in l][0]
    if 'P' in long_name: long_name = [l for l in long_name.split('P') if 'IG' in l or 'TR' in l][0]
    if ' ' in long_name: long_name = [l for l in long_name.split(' ') if 'IG' in l or 'TR' in l][0]
    return long_name



def parse_alignments_from_mixcr_hits(hits): 
    score_dict = OrderedDict()
    hs = hits.split(',')
    if len(hs) == 0: 
        return score_dict
    for h in hs: 
        if len(h.split('(')) != 2: 
            # print '!!!!!!! Empty h?:  {}'.format(h)
            continue
        gene,score = h.split('(')
        # short_gene = trim_ig_locus_name(gene)
        score = int(score.replace(')',''))
        score_dict[gene] = score 
    return score_dict 



def build_annotations_from_mixcr_file(file_path, dataset_id=None, analysis_id=None): 
    f = open(file_path)
    headers = f.readline().split('\t')
    annotations = []
    for line in f.readlines():
        fields = line.split('\t')
        ann = Annotation() 
        ann.analysis_name = 'MIXCR'
        if dataset_id: ann.dataset_id = dataset_id 
        if analysis_id: ann.analysis_id = analysis_id
        for i,k in enumerate(headers): 

            # COULD USE THIS TO BUILD SEQUENCE DOCUMENTS
            # if "Read(s) sequence" == k: ann.   = fields[i]
            # if "Read(s) sequence qualities" == k: ann.   = fields[i]
            if "All V hits" == k: ann.v_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if "All D hits" == k: ann.d_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if "All J hits" == k: ann.j_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if "All C hits" == k: ann.c_hits  = parse_alignments_from_mixcr_hits(fields[i])
            if len(ann.v_hits): ann.v_top_hit = trim_ig_allele_name(sorted(ann.v_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.v_hits): ann.v_top_hit_locus = trim_ig_locus_name(ann.v_top_hit)
            if len(ann.d_hits): ann.d_top_hit = trim_ig_allele_name(sorted(ann.d_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.d_hits): ann.d_top_hit_locus = trim_ig_locus_name(ann.d_top_hit)
            if len(ann.j_hits): ann.j_top_hit = trim_ig_allele_name(sorted(ann.j_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.j_hits): ann.j_top_hit_locus = trim_ig_locus_name(ann.j_top_hit)
            if len(ann.c_hits): ann.c_top_hit = trim_ig_allele_name(sorted(ann.c_hits.items(), key=lambda x: x[1], reverse=True)[0][0])
            if len(ann.c_hits): ann.c_top_hit_locus = trim_ig_locus_name(ann.c_top_hit)
            # if "All V alignments" == k: ann.   = fields[i]
            # if "All D alignments" == k: ann.   = fields[i]
            # if "All J alignments" == k: ann.   = fields[i]
            # if "All C alignments" == k: ann.   = fields[i]
            if "N. Seq. FR1" == k: ann.fr1_nt   = fields[i]
            # if "Min. qual. FR1" == k: ann.   = fields[i]
            if "N. Seq. CDR1" == k: ann.cdr1_nt   = fields[i]
            # if "Min. qual. CDR1" == k: ann.   = fields[i]
            if "N. Seq. FR2" == k: ann.fr2_nt   = fields[i]
            # if "Min. qual. FR2" == k: ann.   = fields[i]
            if "N. Seq. CDR2" == k: ann.cdr2_nt   = fields[i]
            # if "Min. qual. CDR2" == k: ann.   = fields[i]
            if "N. Seq. FR3" == k: ann.fr3_nt   = fields[i]
            # if "Min. qual. FR3" == k: ann.   = fields[i]
            if "N. Seq. CDR3" == k: ann.cdr3_nt   = fields[i]
            # if "Min. qual. CDR3" == k: ann.   = fields[i]
            if "N. Seq. FR4" == k: ann.fr4_nt   = fields[i]
            # if "Min. qual. FR4" == k: ann.   = fields[i]
            if "AA. Seq. FR1" == k: ann.fr1_aa   = fields[i]
            if "AA. Seq. CDR1" == k: ann.cdr1_aa   = fields[i]
            if "AA. Seq. FR2" == k: ann.fr2_aa   = fields[i]
            if "AA. Seq. CDR2" == k: ann.cdr2_aa   = fields[i]
            if "AA. Seq. FR3" == k: ann.fr3_aa   = fields[i]
            if "AA. Seq. CDR3" == k: ann.cdr3_aa   = fields[i]
            if "AA. Seq. FR4" == k: ann.fr4_aa   = fields[i]
            # if "Ref. points" == k: ann.   = fields[i]


            # if "data.productive" == k: 
            #     if 'PRODUCTIVE' in v: 
            #         ann.productive = True
            #     else: 
            #         ann.productive = False 

        annotations.append(ann)
    return annotations




