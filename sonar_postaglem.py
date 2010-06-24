#!/usr/bin/env python
#-*- coding:utf-8 -*-

from pynlpl.input.sonar import CorpusX, CorpusDocumentX
from pynlpl.client import TadpoleClient
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
        for sentence_id, sentence in doc.sentences():
                words = " ".join([ x[0] for x in sentence ])
                process_sentence = False
                for x in sentence:
                    if not x[2] or x[3]:
                        process_sentence = True
                if process_sentence:
                    processed_doc = True
                    for i, (word, pos,lemma, morph) in enumerate(tadpoleclient.process(sentence)):
                        word_id = sentence[i][1]
                        if pos:
                            doc[word_id].attrib['pos'] = pos
                        if lemma:
                            doc[word_id].attrib['lemma'] = lemma
        if processed_doc:
            doc.save(doc.filename+'.pos') #write .tok.pos files
    else:
        print doc.filename + '\tSKIPPING'


