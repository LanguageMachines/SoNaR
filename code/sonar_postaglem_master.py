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
        sys.stdout.flush()

if len(sys.argv) == 3 and os.path.isdir(sys.argv[1]) and sys.argv[2].isdigit():
    sonardir = sys.argv[1]
    poolsize = int(sys.argv[2])
    pool = ExperimentPool(poolsize)
else:
    print >>sys.stderr,"Usage: ./sonar_postaglem_master.py [sonardir] [#processes] "
    sys.exit(2)

#start five tadpoles with tokeniser and MWU *DISABLED*, ports 12350 onward

print "SPAWNING TADPOLES..."

ports = range(12350, 12350+poolsize)
if len(ports) >= 7:
    raise Exception("Don't start too many tadpoles!")
for port in ports:
    os.system('Tadpole --skip=tmp -S ' + str(port) + ' &')

print "POPULATING POOL.."

tadpoleport = 12349
for i, doc in enumerate(CorpusX(sonardir,'tok',"", lambda f: not os.path.exists(f + '.pos') )): #read the *.tok files, on condition there are no *.pos equivalents
    tadpoleport += 1
    if tadpoleport == 12350 + poolsize:
        tadpoleport = 12350
    print '#' + str(i+1) + ')\tQUEING\t' + doc.filename + ' [' + str(tadpoleport) + ']'
    pool.append( TagDoc((doc.filename, tadpoleport, i+1)) )
    sys.stdout.flush()

print "RUNNING POOL.."


pool.run()

