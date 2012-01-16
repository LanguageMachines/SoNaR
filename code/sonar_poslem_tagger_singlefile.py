#!/usr/bin/env python
#-*- coding:utf-8 -*-

from pynlpl.formats.sonar import CorpusDocumentX, ns
from pynlpl.clients.frogclient import FrogClient
import sys
import datetime


if len(sys.argv) == 3 and sys.argv[2].isdigit():
    docname = sys.argv[1]
    port = int(sys.argv[2])
else:
    print >>sys.stderr,"Usage: ./sonar_poslem_tagger_singlefile.py [filename] [frog-port]"
    print >>sys.stderr, "Please first start a Frog server with: frog --skip=tmp -S 12345 (or some other port number)"
    print >>sys.stderr,"Reads and writes D-Coi XML"    
    
    
#Make sure Tadpole/Frog server runs with tokeniser and MWU *DISABLED* !
frogclient = FrogClient('localhost',port) 

print >>sys.stderr, "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] PROCESSING " + docname  + " (port " + str(port) + ")"
doc = CorpusDocumentX(docname)

processed_doc = False
for sentence in doc.sentences():
        words = " ".join([ x.text for x in sentence ])

        process_sentence = False
        for x in sentence:
            if not (ns('dcoi') + 'pos' in x.attrib or ns('dcoi') + 'lemma' in x.attrib or 'pos' in x.attrib or 'lemma' in x.attrib):
                process_sentence = True
        if process_sentence:
            processed_doc = True
            for i, (word, lemma, morph, pos) in enumerate(frogclient.process_aligned(words,'iso-8859-15')):
                if word:
                    try:
                        word_id = sentence[i].attrib[ns('xml') + 'id']
                    except KeyError: 
                        print >>sys.stderr, "ERROR: Unable to extract ID attribute!"  
                        break
                    except IndexError: 
                        print >>sys.stderr, "ERROR: words out of sync in " + sentence.attrib[ns('xml') + 'id'] + ': Unable to resolve word ' + str(i+1) + ': ' + word.encode('utf-8') + '. Source has '  + str(len(sentence)) + ' words.' 
                        break
                    if pos:
                        doc[word_id].attrib['pos'] = pos
                    if lemma:
                        doc[word_id].attrib['lemma'] = lemma
if processed_doc:
    try:
        doc.save(doc.filename+'.pos') #write .tok.pos files
    except IOError:
        print >>sys.stderr, "ERROR: UNABLE TO SAVE FILE " + doc.filename+'.pos'


