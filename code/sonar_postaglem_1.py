#!/usr/bin/env python
#-*- coding:utf-8 -*-

from pynlpl.formats.sonar import CorpusDocumentX, ns
from pynlpl.clients.tadpoleclient import TadpoleClient
import sys
import os.path


if len(sys.argv) == 3 and sys.argv[2].isdigit():
    docname = sys.argv[1]
    port = sys.argv[2]
else:
    print >>sys.stderr,"Usage: ./sonar_postaglem.py [sonar-root-directory]"

#Make sure Tadpole/Frog server runs with tokeniser and MWU *DISABLED* !
tadpoleclient = TadpoleClient('localhost',port) 

doc = CorpusDocumentX(sys.argv[1])

processed_doc = False
for sentence in doc.sentences():
        words = " ".join([ x.text for x in sentence ])

        process_sentence = False
        for x in sentence:
            if not ns('dcoi') + 'pos' in x.attrib or not ns('dcoi') + 'lemma' in x.attrib:
                process_sentence = True
        if process_sentence:
            processed_doc = True
            for i, (word, lemma, morph, pos) in enumerate(tadpoleclient.process(words)):
                try:
                    word_id = sentence[i].attrib[ns('xml') + 'id']
                except: 
                    print >>sys.stderr, "ERROR: words out of sync in " + sentence.attrib[ns('xml') + 'id']
                    break
                if pos:
                    doc[word_id].attrib[ns('dcoi') + 'pos'] = pos
                if lemma:
                    doc[word_id].attrib[ns('dcoi') + 'lemma'] = lemma
if processed_doc:
    doc.save(doc.filename+'.pos') #write .tok.pos files


