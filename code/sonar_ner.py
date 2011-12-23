#!/usr/bin/env python2.7
#-*- coding:utf-8 -*-

from pynlpl.formats import folia
import sys
import random
import os
import datetime
import codecs

random.seed()

TMPDIR = '/tmp/'
NERDDIR = '/exp2/NERD/nerd_voor_sonar/'

try:
    sonardir = sys.argv[1]    
except:
    print >>sys.stderr, "Usage: sonar_ner.py sonardir-or-single-document-file [#processes]"
    print >>sys.stderr, "Reads FoLiA XML, runs NERD for each document, and integrates the results"
    sys.exit(2)
    
try:
    threads = int(sys.argv[2])    
except:
    threads = 1

def process(data):
    global foliadir, indexlength, TMPDIR
    filepath, args, kwargs = data
    s =  "[" +  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] Processing ' + filepath
    print >>sys.stderr, s        
    
    #Load FoLiA document
    try:
        doc = folia.Document(file=filepath)
        if doc.declared(folia.AnnotationType.ENTITY, 'sonar-ner'):
            print >>sys.stderr, "WARNING: Document is already NER tagged, skipping"
            return
    except:
        print >>sys.stderr, "ERROR: Error whilst reading FoLiA Document " + filepath
        return        
        
    
    #Prepare NER input
    tmpfile = TMPDIR + str(random.randint(1000,1000000))
    f = codecs.open(tmpfile, 'w','utf-8')                
    
    for sentence in doc.sentences():
        words = sentence.words()
        for i, word in enumerate(words):
            try:
                f.write(word.id + '\t' + word.text() + '\t' + word.pos() + '\t' + word.lemma() + '\n')
            except:
                print >>sys.stderr, "WARNING: insufficient data for " + word.id + ": skipping"
            if i == len(words) - 1:
                f.write('\n') #empty line between sentences        
    f.close()
    
    #Run NERD
    r = os.system(NERDDIR + 'nerd_for_sonar.py -i ' + tmpfile + ' -e utf-8')
    if r != 0:
        print >>sys.stderr, "ERROR: NERD failed with exit code " + str(r)
        return
            
    #Read NER Output and integrate in FoLiA        
    doc.declare(folia.AnnotationType.ENTITY,'sonar-ner')
    
    
    if not os.path.exists(tmpfile):
        print >>sys.stderr, "ERROR: Expected output file " + tmpfile + ".ner not found! Error in NERD system?"
        return
    else:
        iobclass = None
        f = codecs.open(tmpfile + '.ner', 'r','utf-8')                
        for line in f:
            if line.strip():
                fields = line.strip().split('\t')                
                if len(fields) == 3:
                    id = fields[0]
                    iobtag = fields[2][0]
                    if iobtag == 'B':
                        try:                        
                            iobclass = fields[2][2:]
                        except:
                            iobclass = 'unknown'
                            print >>sys.stderr,"WARNING: No class found for B tag! Falling back to 'unknown'"
                        tokens = []
                        try: 
                            tokens.append(doc[id])
                        except:
                            print >>sys.stderr, "ERROR: Unable to resolve ID " + id + "!!!"
                    elif iobtag == 'I':
                        try:
                            tokens.append(doc[id])
                        except:
                            print >>sys.stderr, "ERROR: Unable to resolve ID " + id + "!!!"
                    if iobclass and (iobtag == 'O' or doc[id] == doc[id].sentence().words(-1)):  #O tag or last word of sentence
                        
                        annotationlayers = doc[id].sentence().select(folia.EntitiesLayer)
                        if annotationlayers:
                            annotationlayer = annotationlayers[0]
                        else:
                            annotationlayer = doc[id].sentence().append(folia.EntitiesLayer)
                        
                        annotationlayer.append(folia.Entity, *tokens, set='sonar-ner', cls=iobclass)
                        
                        iobclass = None
                    
        f.close()
        
        doc.save()

        try:
            os.unlink(tmpfile)
            os.unlink(tmpfile + '.ner')
            os.unlink(tmpfile + '.crf_in')
        except:
            print >>sys.stderr, "Warning: cleanup failed"
            
        s =  "[" +  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] Saved ' + filepath

if os.path.isfile(sonardir):
    process( (sonardir,[],{}) )
elif os.path.isdir(sonardir):
    maxtasksperchild = 25
    preindex = True

    processor = folia.CorpusProcessor(sonardir, process, threads, 'folia.xml', "",lambda x: True, maxtasksperchild,preindex)
    for output in processor.run():
        if output: 
            print output

else:
    print >>sys.stderr, "Invalid SoNaR directory"

