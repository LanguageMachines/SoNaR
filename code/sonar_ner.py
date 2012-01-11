#!/usr/bin/env python2.7
#-*- coding:utf-8 -*-

from pynlpl.formats import folia
import sys
import random
import os
import datetime
import codecs
import subprocess

random.seed()

TMPDIR = '/tmp/'
NERDDIR = '/exp2/NERD/nerd_voor_sonar/'

try:
    sonardir = sys.argv[1]    
except:
    print >>sys.stderr, "Usage: sonar_ner.py sonardir-or-single-document-file [#processes] [output-dir]"
    print >>sys.stderr, "Reads FoLiA XML, runs NERD for each document, and integrates the results. If output-dir is not specified, files will be edited in place"
    sys.exit(2)
        
    
try:
    threads = int(sys.argv[2])    
except:
    threads = 1


try:
    outputdir = sys.argv[3]    
except:
    outputdir = None
    
if outputdir and not os.path.isdir(outputdir):
    print sys.stderr,"ERROR: Output directory " + outputdir + " does not exist"
    sys.exit(1)

def process(data):
    global foliadir, indexlength, TMPDIR, outputdir
    filepath, args, kwargs = data
    s =  "[" +  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] Processing ' + filepath
    print >>sys.stderr, s        
    
    #Load FoLiA document
    try:
        doc = folia.Document(file=filepath)
        if doc.declared(folia.AnnotationType.ENTITY, 'sonar-ner'):
            print >>sys.stderr, "WARNING: Document " + filepath +  " is already NER tagged, skipping"
            return 2 
    except:
        print >>sys.stderr, "ERROR: Error whilst reading FoLiA Document " + filepath
        return 1  
        
    
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
    r = subprocess.call(NERDDIR + 'nerd_for_sonar.py -i ' + tmpfile + ' -e utf-8', shell=True,stdout=subprocess.STDOUT,stderr=subprocess.STDERR)
    if r != 0:
        print >>sys.stderr, "ERROR: NERD failed with exit code " + str(r) + " (" + filepath + ")"
        return 1
            
    #Read NER Output and integrate in FoLiA        
    doc.declare(folia.AnnotationType.ENTITY,'sonar-ner')
    
    
    if not os.path.exists(tmpfile):
        print >>sys.stderr, "ERROR: Expected output file " + tmpfile + ".ner not found! Error in NERD system? (" + filepath + ")"
        return 1
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
                            print >>sys.stderr,"WARNING: No class found for B tag! Falling back to 'unknown' (" + filepath + ")"
                        tokens = []
                        try: 
                            tokens.append(doc[id])
                        except KeyError:
                            print >>sys.stderr, "ERROR: Unable to resolve ID " + id + "!!!"
                    elif iobtag == 'I':
                        if not iobclass:
                            print >>sys.stderr,"NOTICE: I tag without B tag: " + id
                            try:                        
                                iobclass = fields[2][2:]
                            except:
                                iobclass = 'unknown'
                                print >>sys.stderr,"WARNING: No class found for I tag! Falling back to 'unknown' (" + filepath + ")"
                            tokens = []							
                        try:
                            tokens.append(doc[id])
                        except KeyError:
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
        
        if outputdir:
            doc.save(outputdir + '/' + os.path.basename(doc.filename))
        else:
            doc.save()

        try:
            os.unlink(tmpfile)
            os.unlink(tmpfile + '.ner')
            os.unlink(tmpfile + '.crf_in')
        except:
            print >>sys.stderr, "Warning: cleanup failed (" + filepath + ")"
            
        s =  "[" +  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] Saved ' + filepath
        print >>sys.stderr, s
        return 0

if os.path.isfile(sonardir):
    process( (sonardir,[],{}) )
elif os.path.isdir(sonardir):
    maxtasksperchild = 25
    preindex = True

    success = errors = skipped = 0

    processor = folia.CorpusProcessor(sonardir, process, threads, 'folia.xml', "",lambda x: True, maxtasksperchild,preindex)
    for output in processor.run():
        if output == 0: 
            success += 1
        elif output == 1:
            errors += 1
        elif output == 2:
            skipped += 1

    print >>sys.stderr,"All done..."
    print >>sys.stderr,"Succesfully processed files:    " + str(success)
    print >>sys.stderr,"Unprocessed due to errors:      " + str(errors)
    print >>sys.stderr,"Skipped files (already tagged): " + str(skipped)

else:
    print >>sys.stderr, "Invalid SoNaR directory"


