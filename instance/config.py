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


HOME='/data/resources/software/BIGGDATA'
TRIMMOMATIC = 'java -jar /data/resources/software/Trimmomatic-0.35/trimmomatic-0.35.jar'
TRIMMOMATIC_ADAPTERS = '/data/resources/software/Trimmomatic-0.35/adapters'
MIGMAP = 'java -Xmx2g -jar /data/resources/software/migmap-0.9.8/migmap-0.9.8.jar'

#SCRATCH_ROOT='/data/<username>/scratch'
USER_ROOT='/data/<username>/'


# Heroku-specific vars 
if 'DATABASE_URL' in os.environ.keys():  # HACK TO CHECK IF WE'RE IN PRODUCTION ON HEROKU: 
	SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
	HOME = os.environ['HOME']


S3_BUCKET = 'biggdata'

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

IGREP_COMMON_TOOLS = '/data/resources/software/IGREP/common_tools'
IGREP_PIPELINES = '/data/resources/software/IGREP/pipelines'









# Set config based on computer name
# Development only
# import subprocess
# import shlex

DAVES_MACHINE = False

# try:
# 	command_line_args = shlex.split('scutil --get LocalHostName')
# 	command_line_process = subprocess.Popen( command_line_args , stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
# 	response, error = command_line_process.communicate()
# 	if 'Davids-MacBook-Air' in response:
# 		DAVES_MACHINE = True
# except subprocess.CalledProcessError as error:
#     error = error.output

# if DAVES_MACHINE:
# 	IGREP_COMMON_TOOLS = '/Users/davidmagness/IGREP/common_tools'
# 	IGREP_PIPELINES = '/Users/davidmagness/IGREP/pipelines'

# 	SQLALCHEMY_DATABASE_URI = "postgresql://localhost:5432/biggdata"
# 	#SQLALCHEMY_DATABASE_URI = "postgres://biggdata:jkl@127.0.0.1:6712/biggdata"
# 	SQLALCHEMY_TRACK_MODIFICATIONS = True
# 	SQLALCHEMY_POOL_TIMEOUT = None

# 	TRIMMOMATIC = 'trimmomatic'
# 	TRIMMOMATIC_ADAPTERS = '/usr/local/share/trimmomatic/adapters'



