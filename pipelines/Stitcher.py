import sys
import os

#This is a wrapper for Pear
#Requires modification of PEAR address in line 17


def stitcher(files):
	length=len(files)
	
	for i in range(0,length,2):
		R1=files[i]
		R2=files[i+1]
		
		output=str(R1).split('_L001_')[0]

		os.system("/home/gg-jm76798/Desktop/Lesson/Tools/PEAR/bin/pear-0.9.6-bin-32 -f {0} -r {1} -o {2} -v 10 -m 500 -n 50 -u 1 -j 4".format(R1,R2,output))

#python Stitcher.py file1.R1 file1.R2 file2.R1 file2.R2	
if __name__ == "__main__":
	arguments = sys.argv[1:]
	argnum = 0
	fastq_files = []
	while True:
		if argnum >= len(arguments):
			break
		else:
			fastq_files.append(arguments[argnum])
			f = os.path.expanduser(fastq_files[-1])			
			if not os.path.isfile(f):
				raise Exception('The provided file {0} does not exist'.format(f))
			fastq_files[-1] = os.path.abspath(f)			
		argnum += 1	
	stitcher(fastq_files)
