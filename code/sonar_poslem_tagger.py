#!/usr/bin/env python
#-*- coding:utf-8 -*-

from pynlpl.formats.sonar import CorpusFiles
from pynlpl.evaluation import ExperimentPool, AbstractExperiment
import sys
import os.path
import datetime

class TagDoc(AbstractExperiment):
    def __init__(self, data, **parameters):
        super(TagDoc,self).__init__(data, **parameters)
    
    def start(self):
        sonardoc, tadpoleport, count = self.inputdata
        print '#' +str(count) + ')\tSTARTING\t' + sonardoc + '\t@ '+ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.startcommand('./sonar_poslem_tagger_singlefile.py', False,sys.stdout,sys.stderr, sonardoc, tadpoleport)
        sys.stdout.flush()

if len(sys.argv) >= 3 and os.path.isdir(sys.argv[1]) and sys.argv[2].isdigit():
    sonardir = sys.argv[1]
    poolsize = int(sys.argv[2])
    ports = [ int(x) for x in sys.argv[3:] ]
    pool = ExperimentPool(poolsize)
else:
    print >>sys.stderr,"Usage: ./sonar_poslem_tagger.py [sonardir] [#processes] [frog-port] [[frog-port2]] etc.."
    print >>sys.stderr,"Please first start a Frog server with: frog --skip=tmp -S 12345 (or some other port number)"    
    print >>sys.stderr,"Multiple Frog servers may be used (specify multiple ports), the script will attempt to balance the load (not optimally though)"    
    print >>sys.stderr,"Reads and writes D-Coi XML"    
    sys.exit(2)

#start five tadpoles with tokeniser and MWU *DISABLED*, ports 12350 onward
#print "SPAWNING FROGS..."
#BEGINPORT = 12350

#ports = range(BEGINPORT, BEGINPORT+poolsize)
#if len(ports) >= 7:
#    raise Exception("Don't start too many frogs!")
#for port in ports:
#    os.system('Frog --skip=tmp -S ' + str(port) + ' &')

print "POPULATING POOL.."

portindex = -1
for i, doc in enumerate(CorpusFiles(sonardir,'tok',"", lambda f: not os.path.exists(f + '.pos') )): #read the *.tok files, on condition there are no *.pos equivalents
    portindex += 1
    if portindex == len(ports):
       portindex = 0
    print '#' + str(i+1) + ')\tQUEING\t' + doc + ' [' + str(ports[portindex]) + ']'
    pool.append( TagDoc((doc, port, i+1)) )
    sys.stdout.flush()

print "RUNNING POOL..."
for experiment in pool.run():
    sonardoc, tadpoleport, count = experiment.inputdata
    print '#' +str(count) + ')\tDONE\t' + sonardoc + '\t@ '+ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


