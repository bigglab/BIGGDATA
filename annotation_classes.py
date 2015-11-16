#System Imports
import json
import static
import os
import time
import random
from celery import Celery
from collections import defaultdict
import collections
import random
import jinja2 
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Boolean, Integer, String, MetaData, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import TSRANGE, JSON, JSONB, ARRAY, BIT, VARCHAR, INTEGER, FLOAT, NUMERIC, OID, REAL, TEXT, TIME, TIMESTAMP, UUID, NUMRANGE, DATERANGE
from sqlalchemy.sql import select
from sqlalchemy.orm import sessionmaker, scoped_session
from pymongo import MongoClient
import pymongo
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()






class Sequence:  

	id = Column(Integer(), primary_key=True)
	dataset_id = Column(Integer(), ForeignKey('dataset.id'))
	file_id = Column(Integer(), ForeignKey('file.id'))
	header = Column(String(100))
	sequence = Column(String(500))
	quality = Column(String(500))

	annotations = db.relationship('Annotation', backref='sequence', lazy='dynamic')





class Annotation:  

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
	cdr3_aa = Column(String(100))
	cdr3_nt = Column(String(100))
	fr1_nt = Column(String(200))
	fr1_aa = Column(String(100))
	fr2_nt = Column(String(100))
	fr2_aa = Column(String(100))
	fr3_nt = Column(String(100))
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





class Analysis:  

	id = Column(Integer(), primary_key=True)
	user_id = Column(Integer(), ForeignKey('user.id'))
	dataset_id = Column(Integer(), ForeignKey('dataset.id'))
	name = Column(String())
	description = Column(String(256))
	program = Column(String())
	started = Column(TIMESTAMP)
	finished = Column(TIMESTAMP)
	duration = Column(TSRANGE)
	params = Column(JSON)
	vdj_count = Column(Integer)
	vj_count = Column(Integer)
	tcra_count = Column(Integer)
	tcrb_count = Column(Integer)
	total_count = Column(Integer)
	passed_filter = Column(Integer)
	command = Column(String(256))
	notes = Column(String(1000))

	annotations = db.relationship('Annotation', backref='analysis', lazy='dynamic')






sequences = db.relationship('Sequence', backref='dataset', lazy='dynamic')
analyses = db.relationship('Analysis', backref='dataset', lazy='dynamic')
annotations = db.relationship('Annotation', backref='dataset', lazy='dynamic')
analyses = db.relationship('Analysis', backref='user', lazy='dynamic')
sequences = db.relationship('Sequence', backref='file', lazy='dynamic')

