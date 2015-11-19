from app import *
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)
session = db.session
user = session.query(User).filter(User.first_name=='Russell').first()
# f = db.session.query(File).all()[0]
q = db.session.query 
a = db.session.add 
c = db.session.commit 



# lns = open('data/appsoma-seqs.imgt').readlines()
# anns = []
# for l in lns: 
# 	d = json.loads(l) 
# 	b = build_annotation_from_mongo_dict(d)
# 	anns.append(b)


# d = q(Dataset).all()[-1]
# fs = [f for f in d.files if f.file_type =='FASTQ']






test_imgt_seq = {'ANALYSIS_NAME': 'IMGT',
 'DATA.CDR3.AA': 'ARVRVHFGRQANPRRNWFDP',
 'DATA.CDR3.AA_LENGTH': 20,
 'DATA.CDR3.NT': 'GCGAGAGTACGGGTACACTTCGGTCGACAAGCTAACCCACGTCGCAACTGGTTCGACCCC',
 'DATA.CDR3.NT_LENGTH': 60,
 'DATA.DREGION.DGENES': ['HOMSAP IGHD5-24*01 ORF'],
 'DATA.JREGION.FR4.AA': 'WGQGTLVTVSS',
 'DATA.JREGION.FR4.NT': 'TGGGGCCAGGGAACCCTGGTCACCGTCTCCTCAG',
 'DATA.JREGION.JGENES': ['HOMSAP IGHJ5*02 F'],
 'DATA.JREGION.JGENE_QUERY_END': 411,
 'DATA.JREGION.JGENE_QUERY_START': 362,
 'DATA.JREGION.JGENE_SCORES': [246.0],
 'DATA.NOTES': 'POTENTIALLY, BECAUSE OF DETECTED INSERTION/DELETION',
 'DATA.PREDICTED_AB_SEQ.AA': 'EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYEMNWVRQAPGKGLEWVSYISSSGSTIYYADSVKGRFAISRDNAKNSLYLQTNSPRAEDTAVYYCARVRVHFGRQANPRRNWFDPWGQGTLVTVSS',
 'DATA.PREDICTED_AB_SEQ.NT': 'GAGGTGCAGCTGGTGGAGTCTGGGGGAGGCTTGGTACAGCCTGGAGGGTCCCTGAGACTCTCCTGTGCAGCCTCTGGATTCACCTTCAGTAGTTATGAAATGAACTGGGTCCGCCAGGCTCCAGGGAAGGGGCTGGAGTGGGTTTCATACATTAGTAGTAGTGGTAGTACCATATACTACGCAGACTCTGTGAAGGGCCGATTCGCCATCTCCAGAGACAACGCCAAGAACTCACTGTATCTGCAAACGAACAGCCCGAGAGCCGAGGACACGGCTGTTTATTACTGTGCGAGAGTACGGGTACACTTCGGTCGACAAGCTAACCCACGTCGCAACTGGTTCGACCCCTGGGGCCAGGGAACCCTGGTCACCGTCTCCTCAG',
 'DATA.PRODUCTIVE': 'PRODUCTIVE (SEE COMMENT)',
 'DATA.STRAND': '+',
 'DATA.VREGION.CDR1.AA': 'GFTFSSYE',
 'DATA.VREGION.CDR1.AA_LENGTH': 8,
 'DATA.VREGION.CDR1.NT': 'GGATTCACCTTCAGTAGTTATGAA',
 'DATA.VREGION.CDR1.NT_LENGTH': 24,
 'DATA.VREGION.CDR2.AA': 'ISSSGSTI',
 'DATA.VREGION.CDR2.AA_LENGTH': 8,
 'DATA.VREGION.CDR2.NT': 'ATTAGTAGTAGTGGTAGTACCATA',
 'DATA.VREGION.CDR2.NT_LENGTH': 24,
 'DATA.VREGION.FR1.AA': 'EVQLVESGGGLVQPGGSLRLSCAAS',
 'DATA.VREGION.FR1.NT': 'GAGGTGCAGCTGGTGGAGTCTGGGGGAGGCTTGGTACAGCCTGGAGGGTCCCTGAGACTCTCCTGTGCAGCCTCT',
 'DATA.VREGION.FR2.AA': 'MNWVRQAPGKGLEWVSY',
 'DATA.VREGION.FR2.NT': 'ATGAACTGGGTCCGCCAGGCTCCAGGGAAGGGGCTGGAGTGGGTTTCATAC',
 'DATA.VREGION.FR3.AA': 'YYADSVKGRFAISRDNAKNSLYLQTNSPRAEDTAVYYC',
 'DATA.VREGION.FR3.NT': 'TACTACGCAGACTCTGTGAAGGGCCGATTCGCCATCTCCAGAGACAACGCCAAGAACTCACTGTATCTGCAAACGAACAGCCCGAGAGCCGAGGACACGGCTGTTTATTACTGT',
 'DATA.VREGION.SHM.AA': 3.0,
 'DATA.VREGION.SHM.NT': 4.0,
 'DATA.VREGION.VGENES': ['HOMSAP IGHV3-48*03 F'],
 'DATA.VREGION.VGENE_QUERY_END': 324,
 'DATA.VREGION.VGENE_QUERY_START': 30,
 'DATA.VREGION.VGENE_SCORES': [1408.0],
 'DATE_UPDATED': '05/06/15',
 'EXP_ID': '552c261c9eb6363a487b62cb',
 'QUERY_DATA.DREGION.DGENES': [{'PARSED_ALLELES': ['IGHD5-24',
    'ORF',
    'HOMSAP IGHD5-24*01 ORF',
    'IGHD5-24*01',
    'HOMSAP']}],
 'QUERY_DATA.JREGION.JGENES': [{'PARSED_ALLELES': ['IGHJ5*02',
    'HOMSAP IGHJ5*02 F',
    'IGHJ5',
    'HOMSAP',
    'F']}],
 'QUERY_DATA.VREGION.VGENES': [{'PARSED_ALLELES': ['IGHV3-48*03',
    'HOMSAP IGHV3-48*03 F',
    'IGHV3-48',
    'HOMSAP',
    'F']}],
 'RECOMBINATION_TYPE': 'VDJ',
 'SEQ_ID': '552c98689eb636214d227371',
 'SETTINGS': 1,
 '_id': '552c9cee904f3e9c087069d2'}

