#!/usr/bin/env python
#-*- coding:utf-8 -*-

from pynlpl.formats.sonar import CorpusX
from pynlpl.evaluation import ExperimentPool, AbstractExperiment
import sys
import os.path
import datetime

class TagDoc(AbstractExperiment):
    def __init__(self, data, **parameters):
        super(TagDoc,self).__init__(data, **parameters)
    
    def start(self):
        sonardoc, tadpoleport, count = self.data
        print '#' +str(count) + ')\tPROCESSING\t' + sonardoc + '\t@ '+ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.startcommand('sonar_postaglem_1.py', False,sys.stdout,sys.stderr, sonardoc.filename, tadpoleport)


if len(sys.argv) == 2 and os.path.isdir(sys.argv[1]) and sys.argv[2].isdigit():
    sonardir = sys.argv[1]
    poolsize = int(sys.argv[2])
    pool = ExperimentPool(poolsize)
else:
    print >>sys.stderr,"Usage: ./sonar_postaglem_master.py [sonardir] [#processes] "

#start five tadpoles with tokeniser and MWU *DISABLED*, ports 12350 onward

print "SPAWNING TADPOLES..."

for port in range(12350, 123450+poolsize):
    os.system('Tadpole --skip=tmp -S ' + str(port) + ' &')

print "POPULATING POOL.."

tadpoleport = 12349
for i, doc in enumerate(CorpusX(sonardir,'tok',"", lambda f: not os.path.exists(f + '.pos') )): #read the *.tok files, on condition there are no *.pos equivalents
    tadpoleport += 1
    if tadpoleport == 12350 + poolsize: 
        tadpoleport = 12350
    print '#' + str(i+1), + ')\tQUEING\t' + doc.filename + ' [' + str(tadpoleport) + ']'
    pool.append( TagDoc((doc.filename, tadpoleport, i+1)) )




pool.run()

