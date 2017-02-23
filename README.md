# BIGGDATA 

BIGGDATA is a web portal for analyzing IG and TCR repertoire data, originally built for the Brent Iverson George Georgiou (BIGG) Laboratory. 

The goal of this system is twofold: to curate and provide a central repository for sequencing data collected by the lab, and to standardize analysis of IG and TCR repertoire data. 

Users are able to import data from local files, server files, NCBI SRA, web URLs or UT Austin GSAF sequencing core directories, preprocess sequencing data (quality & illumina adapter trimming, quality filtering, paired-end overlap consensus) and run a variety of analysis programs (MixCR, IGFFT, Abstar, etc) to annotate reads from IMGT and native databases. Paired VH::VL (or TRB::TRA) sequencing analysis is now supported as well. 

All annotation results are standardized to facilitate downstrem analysis and generate useful insights into repertoire distribution, polarization, and loci & gene usage. Comparative analysis of results between sample datasets includes a variety of repertoire similarity metrics and co-clustering to determine clonal overlap.  

####

## Installation 

#### Dependencies: 

  python2.7 w/ Flask
  
  rabbitmq-server 
  
  PostgreSQL Database 
  
  Celery task executor 
  
  Other python modules listed in requirements.txt 
  
  
  
#### Programs utilized: 

  Trimmomatic 
  
  fastx_toolkit 
  
  Pandaseq 
  
  MiXCR
  
  IGFFT 
  
  AbSTAR



#### Custom installation options can be made by modifying the instance/config.py file


## Execution 


### Start Broker 
rabbitmq-server

### Start Celery
testing: 
celery -A app.celery worker --loglevel=debug

production: 
celery multi restart node1 --verbose -A app.celery --loglevel=info

### Start Celery Admin (if you want to monitor task progression) 
flower --port=8001

### Start Web Service 
python manage.py runserver -p 8000 -h 0.0.0.0

#### Check It Out At http://0.0.0.0:8000


--------


### Installation Instructions To Come
