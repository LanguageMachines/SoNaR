#!/usr/bin/env python
#-*- coding:utf-8 -*-
from pynlpl.formats.sonar import CorpusX, CorpusDocumentX
import sys
import os.path


if len(sys.argv) == 2 and os.path.isdir(sys.argv[1]):
    sonardir = sys.argv[1]
else:
    print >>sys.stderr,"Usage: ./sonar_toutf8.py [sonar-root-directory]"

iterator = CorpusX(sonardir,'pos',"",lambda x: True, True) #ignoreerrors=True
for doc in iterator:
    try:
        doc.save(doc.filename, 'utf-8')
        print "     Processed: " + doc.filename
    except Exception, e:
        print "**** ERROR whilst processing " + doc.filename + ": " + str(e)

