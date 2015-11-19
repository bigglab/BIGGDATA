import os 
import sys 

DEBUG = True



# Local Development-specific vars, override below if in production

SQLALCHEMY_DATABASE_URI = "postgresql://localhost/biggig"
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_POOL_TIMEOUT = None

HOME = '/Users/red/Desktop/GeorgiouProjects/BIGGDATA'
DROPBOX_ROOT='{}/data/dropbox_root'.format(HOME)
SCRATCH_ROOT='{}/data/scratch_root'.format(HOME)
SHARE_ROOT = '/dropboxes/shared'





# Heroku-specific vars 
if 'DATABASE_URL' in os.environ.keys():  # HACK TO CHECK IF WE'RE IN PRODUCTION ON HEROKU: 
	SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
	# HOME = os.environ['HOME']
	# DROPBOX_ROOT='{}/data/dropbox_root'.format(HOME)
	# SCRATCH_ROOT='{}/data/scratch_root'.format(HOME)
	DROPBOX_ROOT='/dropboxes'
	SCRATCH_ROOT='/data'
	SHARE_ROOT = '/dropboxes/shared'
# Heroku postgres:   postgres://uf8vm9gg6isrbk:p6iot5ksr6i60ff173l8f4v1ig@ec2-107-20-136-206.compute-1.amazonaws.com:6712/d30h3s4gmpmcuo 



# AWS-specifc vars 
if 'LESSOPEN' in os.environ.keys():  # HACK TO CHECK IF WE'RE ON AWS INSTANCE: 
	SQLALCHEMY_DATABASE_URI = "postgres://uf8vm9gg6isrbk:p6iot5ksr6i60ff173l8f4v1ig@ec2-107-20-136-206.compute-1.amazonaws.com:6712/d30h3s4gmpmcuo"
	# Local instance stores, for speed 
	DROPBOX_ROOT='/dropboxes'
	SCRATCH_ROOT='/data'
	SHARE_ROOT = '/dropboxes/shared'



S3_BUCKET = 's3://biggdata'

SECRET_KEY = '\x95\x90+\x1c\xd36\xa3\x94\x99\xaeA\xac\xd3M5\x0b\xc7\xefF\xf3\x08\x05t\xd9'


MONGO_DATABASE_URI = "biotseq.icmb.utexas.edu"
MONGO_USER = 'reader'
MONGO_PASSWORD = 'cdrom'
mongo_config = {"reader":"cdrom","writer":"rag1rag2","dbpath":"biotseq.icmb.utexas.edu"}





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










