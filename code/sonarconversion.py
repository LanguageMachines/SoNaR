#!/usr/bin/env python
#-*- coding:utf-8 -*-

#---------------------------------------------------------------
# PyNLPl - Conversion script for converting SoNaR/D-Coi from D-Coi XML to FoLiA XML, including full retagging
#   by Maarten van Gompel, ILK, Tilburg University
#   http://ilk.uvt.nl/~mvgompel
#   proycon AT anaproy DOT nl
#
#   Licensed under GPLv3
#
#----------------------------------------------------------------

# Usage: sonarconversion.py sonar-input-dir output-dir nr-of-threads

import sys
import os
import traceback
import re
import time

if __name__ == "__main__":
    sys.path.append(sys.path[0] + '/../..')
    os.environ['PYTHONPATH'] = sys.path[0] + '/../..'

from pynlpl.formats import folia
from pynlpl.formats import sonar
from pynlpl.formats import cgn
from pynlpl.clients.frogclient import FrogClient
from multiprocessing import Pool, Process
import datetime
import codecs

def errout(error):
    print error
    print >>sys.stderr, error

def dcoitofolia(filename, content):
    global foliadir
    print "\tConversion to FoLiA:"
    try:
        doc = folia.Document(string=content)
    except Exception as e:
        print >> sys.stderr,"\t\tERROR loading " + filename + ":" + str(e)
        return False
    filename = filename.replace(sonardir,'')
    if filename[0] == '/':
        filename = filename[1:]
    if filename[-4:] == '.pos':
        filename = filename[:-4]
    if filename[-4:] == '.tok':
        filename = filename[:-4]    
    if filename[-4:] == '.ilk':
        filename = filename[:-4]    
    #Load document prior to tokenisation
    try:
        pretokdoc = folia.Document(file=sonardir + '/' + filename)
        print "\t\tPre-tokenised version included: yes"
    except:        
        errout("\t\tWARNING: Unable to load pretokdoc " + filename)
        print "\t\tPre-tokenised version included: no"
        pretokdoc = None
        
    if pretokdoc:
        for p2 in pretokdoc.paragraphs():
            try:
                p = doc[p2.id]        
            except:
                errout("\t\tERROR: Paragraph " + p2.id + " not found. Tokenised and pre-tokenised versions out of sync?")
                continue
            p.append(p2.text(folia.TextCorrectionLevel.UNCORRECTED), corrected=folia.TextCorrectionLevel.UNCORRECTED)
    try:
        os.mkdir(foliadir + os.path.dirname(filename))
    except:
        pass
        
    doc.declare( folia.AnnotationType.POS, set='http://ilk.uvt.nl/folia/sets/cgn', annotator='frog', annotatortype=folia.AnnotatorType.AUTO)
    doc.declare( folia.AnnotationType.LEMMA, set='http://ilk.uvt.nl/folia/sets/lemmas-nl', annotator='frog', annotatortype=folia.AnnotatorType.AUTO)
    doc.declare( folia.AnnotationType.MORPHEME, set='http://ilk.uvt.nl/folia/sets/mbma-nl', annotator='frog', annotatortype=folia.AnnotatorType.AUTO)

    return doc
    
def integritycheck(doc, filename):
    print "\tIntegrity check:"
    success = True
    r = re.compile('<p.*xml:id="([^"]*)"(.*)>(.*)</p>')
    origpcount = r.findall(contents)
    r = re.compile('<s.*xml:id="([^"]*)"(.*)>(.*)</s>')
    origscount = r.findall(contents)
    r = re.compile('<w.*xml:id="([^"]*)"(.*)>(.*)</w>')
    origwcount = r.findall(contents)

    pcount = len(doc.paragraphs())
    scount = len(doc.sentences())
    wcount = len(doc.words())
    print "\t\tParagraphs:\t" + str(pcount)
    if pcount != origpcount:
        errout("ERROR: INTEGRITY CHECK FAILED ON PARAGRAPH COUNT (" + str(origpcount)+"): " + filename)
        success = False
    print "\t\tSentences:\t" + str(scount)
    if scount != origscount:
        errout("ERROR: INTEGRITY CHECK FAILED ON SENTENCE COUNT (" + str(origscount)+"): " + filename)
        success = False
    print "\t\tWords:\t" + str(wcount)
    if wcount != origwcount:
        errout("ERROR: INTEGRITY CHECK FAILED ON WORD COUNT (" + str(origwcount)+"): " + filename)
        success = False
    return success
    
    
def foliatoplaintext(doc, filename):
    global foliadir
    print "\tConversion to plaintext:"
    try:
        f = codecs.open(foliadir + filename.replace('.xml','.tok.txt'),'w','utf-8')
        f.write(unicode(doc))    
        f.close()        
    except:
        errout("ERROR saving " + foliadir + filename.replace('.xml','.tok.txt'))

def foliatodcoi(doc, filename):
    global dcoidir
    print "\tConversion back to D-Coi XML:"
    try:
        #doc.savedcoi(dcoidir + filename)
        pass
    except:
        errout(sys.stderr,"ERROR saving " + dcoidir + filename)
        
    

        
def retag(doc, i):
    global threads
    print "\tRetagging:"
    r = re.compile('\[(.*)\]')
    frogclient = FrogClient('localhost',9000 + (i % threads) )
    
    for sentence in doc.sentences():
        words = " ".join([ w.text() for w in sentence.words() ])
        for j, (word, lemma, morph, pos) in enumerate(frogclient.process(words)):
            wordelement = sentence.words(j)
            wordelement.replace( cgn.parse_cgn_postag(pos) )
            wordelement.replace( folia.LemmaAnnotation, cls=lemma )
            
            #parse mbma
            morphemes = r.findall(morph)
            if morphemes:
                layer = wordelement.append( folia.MorphologyLayer )
                for morpheme in morphemes:
                    layer.append( folia.Morpheme, cls=morpheme )            
    

def process(data):
    global foliadir, indexlength
    try:
        i, filename = data
        category = os.path.basename(os.path.dirname(filename))
        progress = round((i+1) / float(indexlength) * 100,1)    
        s =  "#" + str(i+1) + " " + filename + ' ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' +  str(progress) + '%'    
        print s
        print >>sys.stderr, s

        #Load file (raw)
        f = codecs.open(filename,'r','iso-8859-15')
        content = "\n".join(f.readlines())
        f.close()
        
        #Convert to FoLiA
        doc = dcoitofolia(filename, content)
        
        #FoLiA to plaintext
        foliatoplaintext(doc, filename)
        
        #Retag
        retag(doc,i)    

        print "\tSaving:"
        #Save document
        try:        
            doc.save(foliadir + filename)
        except Exception as e:
            errout("\t\tERROR saving " + foliadir + filename + ": " + str(e))
            return None
        
        #Integrity Check
        succes = integritycheck(doc, content)
        
        #FoLiA to D-Coi
        foliatodcoi(doc, filename)
                
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception as e:
        print >> sys.stderr, e
        traceback.print_exc(file=sys.stderr)
        return False
    return True
    
def outputexists(filename, sonardir, foliadir):
    filename = filename.replace(sonardir,'')
    if filename[0] == '/':
        filename = filename[1:]
    if filename[-4:] == '.pos':
        filename = filename[:-4]
    if filename[-4:] == '.tok':
        filename = filename[:-4]    
    if filename[-4:] == '.ilk':
        filename = filename[:-4]     
    return os.path.exists(foliadir + filename)


if __name__ == '__main__':    
    sonardir = sys.argv[1]
    foliadir = sys.argv[2]
    threads = int(sys.argv[3])
    
    #Starting temporary Frog servers
    print "Starting Frog server..."
    for i in range(0,threads):
        port = 9000 + i
        os.system("frog --skip=tmp -S " + str(port) + " >/dev/null &")
    
    if foliadir[-1] != '/': foliadir += '/'
    try:
        os.mkdir(foliadir[:-1])
    except:
        pass
            
    print "Building index..."
    index = list(enumerate([ x for x in sonar.CorpusFiles(sonardir,'tok', "", lambda x: True, True) if not outputexists(x, sonardir, foliadir) ]))
    indexlength = len(index)

    
    print "Processing..."
    p = Pool(threads)
    p.map(process, index )

    print "All done."
