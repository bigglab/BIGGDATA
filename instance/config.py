import os 
import sys 

DEBUG = True

if DEBUG:
	THREADED = True
else:
	THREADED = False

# SQLALCHEMY_DATABASE_URI = "postgresql://localhost/biggig"
SQLALCHEMY_DATABASE_URI = "postgres://uf8vm9gg6isrbk:p6iot5ksr6i60ff173l8f4v1ig@ec2-107-20-136-206.compute-1.amazonaws.com:6712/d30h3s4gmpmcuo"
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_POOL_TIMEOUT = None
QUOTAGUARD_URL = 'http://quotaguard4189:013877db0c3e@proxy.quotaguard.com:9292'

# Local Development-specific vars, override below if in production
HOME='/Users/red/Desktop/GeorgiouProjects/BIGGDATA'

TRIMMAMATIC = 'java -jar /home/russ/software/Trimmomatic-0.35/trimmomatic-0.35.jar'
TRIMMAMATIC_ADAPTERS = '/home/russ/software/Trimmomatic-0.35/adapters'
MIGMAP = 'java -Xmx2g -jar /home/russ/software/migmap-0.9.8/migmap-0.9.8.jar'

# File System configurations - this is where all user data is stored! Need a more universal way.... 
# Dropboxes and Data kept separate to efficiently use 2x local SSD on AWS c3.xlarge node 
DROPBOX_ROOT='/data/dropboxes'
SCRATCH_ROOT='/data/scratch'
SHARE_ROOT = '/data/dropboxes/shared'
#SCRATCH_ROOT='/data/<username>/scratch'
USER_ROOT='/data/<username>/'

# Heroku-specific vars 
if 'DATABASE_URL' in os.environ.keys():  # HACK TO CHECK IF WE'RE IN PRODUCTION ON HEROKU: 
	SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
	HOME = os.environ['HOME']

# AWS-specifc vars 
if 'LESSOPEN' in os.environ.keys():  # HACK TO CHECK IF WE'RE ON AWS INSTANCE: 
	SQLALCHEMY_DATABASE_URI = "postgres://uf8vm9gg6isrbk:p6iot5ksr6i60ff173l8f4v1ig@ec2-107-20-136-206.compute-1.amazonaws.com:6712/d30h3s4gmpmcuo"
	# Local instance stores, for speed 
	HOME = '/home/ubuntu/BIGGDATA'
	TRIMMAMATIC = 'java -jar /home/ubuntu/install/Trimmomatic-0.35/trimmomatic-0.35.jar'
	TRIMMAMATIC_ADAPTERS = '/home/ubuntu/install/Trimmomatic-0.35/adapters'


S3_BUCKET = 'biggdata'

# @Dave - temporary for local environment
AWSACCESSKEYID = os.environ['AWSACCESSKEYID'] 
AWSSECRETKEY = os.environ['AWSSECRETKEY']

SECRET_KEY = '\x95\x90+\x1c\xd36\xa3\x94\x99\xaeA\xac\xd3M5\x0b\xc7\xefF\xf3\x08\x05t\xd9'

# Target static dir
COLLECT_STATIC_ROOT = '{}/static'.format(HOME) 
COLLECT_STORAGE = 'flask_collect.storage.file'

# MONGO SETUP ON BIOTSEQ 
MONGO_DATABASE_URI = "biotseq.icmb.utexas.edu"
MONGO_USER = 'reader'
MONGO_PASSWORD = 'cdrom'
mongo_config = {"reader":"cdrom","writer":"rag1rag2","dbpath":"biotseq.icmb.utexas.edu"}

IGREP_COMMON_TOOLS = '/home/russ/IGREP/common_tools'
IGREP_PIPELINES = '/home/russ/IGREP/pipelines'

# Set config based on computer name
# Development only
import subprocess
import shlex

daves_machine = False

try:
	command_line_args = shlex.split('scutil --get LocalHostName')
	command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	response, error = command_line_process.communicate()
	if 'Davids-MacBook-Air' in response:
		daves_machine = True
except subprocess.CalledProcessError as error:
    error = error.output

if daves_machine:
	IGREP_COMMON_TOOLS = '/Users/davidmagness/IGREP/common_tools'
	IGREP_PIPELINES = '/Users/davidmagness/IGREP/pipelines'




# OPTIONS AVAILABLE ACCORDING TO app.config.__dict__  AFTER COMPILATION 

 # 'BOOTSTRAP_LOCAL_SUBDOMAIN': None, 
 # 'BOOTSTRAP_USE_MINIFIED': True, 
 # 'SESSION_COOKIE_PATH': None, 
 # 'SQLALCHEMY_RECORD_QUERIES': None, 
 # 'SESSION_COOKIE_DOMAIN': None, 
 # 'SESSION_COOKIE_NAME': 'session', 
 # 'BOOTSTRAP_SERVE_LOCAL': False, 
 # 'SQLALCHEMY_BINDS': None, 
 # 'SQLALCHEMY_POOL_RECYCLE': None, 
 # 'BOOTSTRAP_CDN_FORCE_SSL': False, 
 # 'LOGGER_NAME': 'app', 'DEBUG': True, 
 # 'SQLALCHEMY_COMMIT_ON_TEARDOWN': False, 
 # 'SECRET_KEY': '\x95\x90+\x1c\xd36\xa3\x94\x99\xaeA\xac\xd3M5\x0b\xc7\xefF\xf3\x08\x05t\xd9', 
 # 'SQLALCHEMY_NATIVE_UNICODE': None, 
 # 'MAX_CONTENT_LENGTH': None, 
 # 'SQLALCHEMY_POOL_SIZE': None, 
 # 'SQLALCHEMY_ECHO': False, 
 # 'APPLICATION_ROOT': None, 
 # 'SERVER_NAME': None, 
 # 'PREFERRED_URL_SCHEME': 'http', 
 # 'JSONIFY_PRETTYPRINT_REGULAR': True, 
 # 'TESTING': False, 
 # 'PERMANENT_SESSION_LIFETIME': datetime.timedelta(31), 
 # 'PROPAGATE_EXCEPTIONS': None, 
 # 'TRAP_BAD_REQUEST_ERRORS': False, 
 # 'JSON_SORT_KEYS': True, 
 # 'SQLALCHEMY_MAX_OVERFLOW': None, 
 # 'SESSION_COOKIE_HTTPONLY': True, 
 # 'SEND_FILE_MAX_AGE_DEFAULT': 43200, 
 # 'PRESERVE_CONTEXT_ON_EXCEPTION': None, 
 # 'S3_BUCKET': 's3://BIGGDATA',
 #  'SESSION_COOKIE_SECURE': False, 
 #  'TRAP_HTTP_EXCEPTIONS': False










