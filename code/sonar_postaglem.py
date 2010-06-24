#!/usr/bin/env python
#-*- coding:utf-8 -*-

from pynlpl.formats.sonar import CorpusX, CorpusDocumentX, ns
from pynlpl.clients.tadpoleclient import TadpoleClient
import sys
import os.path



#Make sure Tadpole/Frog server runs with tokeniser *DISABLED* !
tadpoleclient = TadpoleClient('localhost',12345) 

if len(sys.argv) == 2 and os.path.isdir(sys.argv[1]):
    sonardir = sys.argv[1]
else:
    print >>sys.stderr,"Usage: ./sonar_postaglem.py [sonar-root-directory]"

for doc in CorpusX(sonardir,'tok'): #read the *.tok files
    processed_doc = False
    if not os.path.exists(doc.filename+'.pos'):
        print doc.filename + '\tPROCESSING'
        for sentence in doc.sentences():
                words = " ".join([ x.text for x in sentence ])
		print words

                process_sentence = False
                for x in sentence:
                    if not ns('dcoi') + 'pos' in x.attrib or not ns('dcoi') + 'lemma' in x.attrib:
                        process_sentence = True
                if process_sentence:
                    processed_doc = True
                    for i, (word, pos,lemma, morph) in enumerate(tadpoleclient.process(words)):
                        word_id = sentence[i].attrib[ns('xml') + 'id']
                        if pos:
                            doc[word_id].attrib[ns('dcoi') + 'pos'] = pos
                        if lemma:
                            doc[word_id].attrib[ns('dcoi') + 'lemma'] = lemma
        if processed_doc:
            doc.save(doc.filename+'.pos') #write .tok.pos files
    else:
        print doc.filename + '\tSKIPPING'


