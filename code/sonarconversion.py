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
import lxml.etree
from StringIO import StringIO


def errout(error):
    print error
    print >>sys.stderr, error

def dcoitofolia(filename, parseddcoi):        
    global foliadir, dcoitofoliatransformer
    print "\tConversion to FoLiA:"    

    try:
        parsedfolia = dcoitofoliatransformer(parseddcoi)
    except Exception as e:
        errout("\t\tERROR transforming D-Coi document to FoLiA: " + filename + ":" + str(e))
        return None, None
        
    try:
        foliadoc = folia.Document(tree=parsedfolia)
    except Exception as e:
        errout("\t\tERROR loading FoLiA document after conversion from D-Coi: " + filename + ":" + str(e))
        return None, None
        
        
    print "\t\tConverted"   
    
    #find filename base, strip extensions and path (only .xml stays)
    filename = getfilename(filename)
        
        
    #Load document prior to tokenisation
    try:
        pretokdoc = folia.Document(file=sonardir + '/' + filename)
        errout("\t\tPre-tokenised version included: yes")
    except:        
        errout("\t\tWARNING: Unable to load pretokdoc " + filename)
        errout("\t\tPre-tokenised version included: no")
        pretokdoc = None
        
    if pretokdoc:
        for p2 in pretokdoc.paragraphs():
            try:
                p = foliadoc[p2.id]        
            except:
                errout("\t\tERROR: Paragraph " + p2.id + " not found in converted document. Tokenised and pre-tokenised versions out of sync?")
                continue
            p.append(p2.text(folia.TextCorrectionLevel.UNCORRECTED), corrected=folia.TextCorrectionLevel.UNCORRECTED)
    try:
        os.mkdir(foliadir + os.path.dirname(filename))
    except:
        pass
        
        
    #Fix Gap problem (widely spread invalid D-Coi XML in SoNaR)       
    for text in foliadoc:
        for gap in text.select(folia.Gap):
            if gap.annotator and not gap.content():                
                print "\t\tCorrecting malformed gap"
                gap.replace(folia.Content, value=gap.annotator)
                gap.annotator = None                
    
    print "\t\tDone"    
    return foliadoc, parsedfolia
    
def integritycheck(doc, filename, contents):
    print "\tIntegrity check:"
    success = True
    r = re.compile('<p.*xml:id="([^"]*)"(.*)>')
    origpcount = len(r.findall(contents))
    r = re.compile('<s.*xml:id="([^"]*)"(.*)>')
    origscount = len(r.findall(contents))
    r = re.compile('<w.*xml:id="([^"]*)"(.*)>(.*)</w>')
    origwcount = len(r.findall(contents))

    pcount = len(doc.paragraphs())
    scount = len(doc.sentences())
    wcount = len(doc.words())
    print "\t\tParagraphs:\t" + str(pcount)
    if pcount != origpcount:
        errout("\t\t\tERROR: INTEGRITY CHECK FAILED ON PARAGRAPH COUNT (" + str(origpcount)+"!=" + str(pcount)+"): " + filename)
        success = False
    print "\t\tSentences:\t" + str(scount)
    if scount != origscount:
        errout("\t\t\tERROR: INTEGRITY CHECK FAILED ON SENTENCE COUNT (" + str(origscount)+"!=" + str(scount)+"): " + filename)
        success = False
    print "\t\tWords:\t" + str(wcount)
    if wcount != origwcount:
        errout("\t\t\tERROR: INTEGRITY CHECK FAILED ON WORD COUNT (" + str(origwcount)+"!=" + str(wcount)+"): " + filename)
        success = False
    
    if success:
        print "\t\tSuccess"            
    return success
    
    
def foliatoplaintext(doc, filename):
    global foliadir
    print "\tConversion to plaintext:"
    try:
        f = codecs.open(foliadir + getfilename(filename).replace('.xml','.tok.txt'),'w','utf-8')
        f.write(unicode(doc))    
        f.close()        
        print "\t\tDone"    
    except Exception as e:
        errout("\t\tERROR saving " + foliadir + getfilename(filename).replace('.xml','.tok.txt') + ": " + str(e))

def foliatodcoi(doc, filename):
    global dcoidir
    print "\tConversion back to D-Coi XML:"
    try:
        #doc.savedcoi(dcoidir + getfilename(filename))
        pass
    except:
        errout(sys.stderr,"ERROR saving " + dcoidir + getfilename(filename))
        
    

        
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
        i, filepath = data
        category = os.path.basename(os.path.dirname(filepath))
        progress = round((i+1) / float(indexlength) * 100,1)    
        s =  "#" + str(i+1) + " " + filepath + ' ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' +  str(progress) + '%'    
        print s
        print >>sys.stderr, s

        #Load file (raw)
        f = codecs.open(filepath,'r','iso-8859-15')
        content = "\n".join(f.readlines())
        f.close()
        
        try:
            parseddcoi = lxml.etree.parse(StringIO(content.encode('iso-8859-15')))
        except Exception, e:
            errout("\t\tERROR: D-COI DOCUMENT " + filepath + " IS MALFORMED XML! " +  str(e))
            return False
            
        #Convert to FoLiA
        foliadoc, parsedfolia = dcoitofolia(filepath, parseddcoi)
        if not foliadoc:
            return False
        
        #FoLiA to plaintext
        foliatoplaintext(foliadoc, filepath)

        print "\tSaving:"
        #Save document
        try:        
            foliadoc.save(foliadir + getfilename(filepath))
        except Exception as e:
            errout("\t\tERROR saving " + foliadir + getfilename(filepath) + ": " + str(e))
            return False
        
        #Integrity Check
        succes = integritycheck(foliadoc, filepath, content)
        
        #FoLiA to D-Coi
        #foliatodcoi(foliadoc, filepath)
            
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception as e:
        print >> sys.stderr, e
        traceback.print_exc(file=sys.stderr)
        return False
    return True

def getfilename(filename):
    #find filename base, strip extensions and path (only .xml stays)
    global sonardir
    filename = filename.replace(sonardir,'')
    if filename[-4:] == '.pos':
        filename = filename[:-4]
    if filename[-4:] == '.tok':
        filename = filename[:-4]    
    if filename[-4:] == '.ilk':
        filename = filename[:-4]     
    return filename
                
def outputexists(filename, sonardir, foliadir):   
    return os.path.exists(foliadir + getfilename(filename))


if __name__ == '__main__':    
    try:
        sonardir = sys.argv[1]
        foliadir = sys.argv[2]
        xsltfile = sys.argv[3]
        threads = int(sys.argv[4])
    except:
        print >>sys.stderr,"Syntax: sonarconversion.py sonardir foliadir dcoi2folia.xsl threads"
        sys.exit(2)
    
    #Let XSLT do the basic conversion to HTML
    xslt = lxml.etree.parse(xsltfile)
    dcoitofoliatransformer = lxml.etree.XSLT(xslt)
    #html = transform(xmldoc)    
    
    schema = lxml.etree.RelaxNG(folia.relaxng())
    #schema.assertValid(doc)
    
    time.sleep(3)
    
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
