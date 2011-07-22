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
        return None

    try:
        foliadoc = folia.Document(tree=parsedfolia)
    except Exception as e:
        errout("\t\tERROR loading FoLiA document after conversion from D-Coi: " + filename + ":" + str(e))
        return None
        
        
    print "\t\tConverted"   
    
    #find filename base, strip extensions and path (only .xml stays)
    filename = getfilename(filename)
        
        
    #Load document prior to tokenisation
    try:
        pretokdoc = folia.Document(file=sonardir + '/' + filename)
        print "\t\tPre-tokenised version included: yes"
    except Exception, e:        
        errout("\t\tWARNING: Unable to load pretokdoc " + filename + ": " + str(e))
        print "\t\tPre-tokenised version included: no"
        pretokdoc = None
        
    if pretokdoc:
        for p2 in pretokdoc.paragraphs():
            try:
                p = foliadoc[p2.id]        
            except:
                errout("\t\tERROR: Paragraph " + p2.id + " not found in converted document. Tokenised and pre-tokenised versions out of sync!")
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
                content = gap.annotator
                content = content.replace('\\n','\n')
                gap.replace(folia.Content, value=content)
                gap.annotator = None                
    
    print "\t\tDone"    
    return foliadoc
    
    
class dcoi:    
    Word = re.compile('<w[^>]*>')
    Sentence = re.compile('<s[^>]*>')
    Paragraph = re.compile('<p[^>]*>')
    Division =  re.compile('<div[0-9]?[^>]*>')
    Head =  re.compile('<head[^>]*>')
    Gap =  re.compile('<gap[^>]*>')



xmlextract = re.compile('<([A-Za-z0-9:]+)[^>]*>')
checkelements = [
    ('w', folia.Word),
    ('s', folia.Sentence),
    ('p', folia.Paragraph), 
    ('div', folia.Division), 
    ('div0', folia.Division), 
    ('div1', folia.Division), 
    ('div2', folia.Division), 
    ('div3', folia.Division), 
    ('div4', folia.Division), 
    ('div5', folia.Division), 
    ('div6', folia.Division), 
    ('div7', folia.Division), 
    ('div8', folia.Division), 
    ('div9', folia.Division), 
    ('head', folia.Head), 
    ('figure', folia.Figure), 
    ('list', folia.List), 
    ('item', folia.ListItem), 
    ('gap', folia.Gap),         
]  
    
def integritycheck(doc, filename, contents, parseddcoi):    
    global xmlextract, checkelements
    print "\tStructural integrity check:"

    dcoitags = [ tag for tag in xmlextract.findall(contents) if tag in [ x[0] for x in checkelements ] ]
    foliaitems = [ item for item in [ x.__class__ for x in doc.items() ] if item in [ x[1] for x in checkelements ] ]
    
    if len(dcoitags) == 0:
        errout("\t\t\tWARNING: DCOI DOCUMENT HAS NO SENSIBLE ELEMENTS!")
    elif len(foliaitems) == 0:
        errout("\t\t\tWARNING: FOLIA DOCUMENT HAS NO SENSIBLE ELEMENTS!")
    
    success = True
    if len(dcoitags) != len(foliaitems):
        errout("\t\t\tERROR: STRUCTURAL INTEGRITY CHECK FAILED, DCOI HAS " + str(len(dcoitags)) + " checkable items, FoLiA has " + str(len(foliaitems)))
        success = False    
    else:
        for i, (dcoitag, foliaitem) in enumerate(zip(dcoitags, foliaitems)):
            if not ((dcoitag, foliaitem) in checkelements):
                errout("\t\t\tERROR: STRUCTURAL INTEGRITY CHECK FAILED ON ITEM " + str(i) + " OF " + len(dcoitags) + ": " + dcoitag + " != " + str(foliaitem))
                success = False        
                break
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
        errout("ERROR saving " + dcoidir + getfilename(filename))
        
    
def validate(filepath):
    global schema
    print "\tValidating"
    try:
        folia.validate(filepath, schema)
        print "\t\tSuccess"       
    except Exception,e :
        errout("\t\tERROR: DOCUMENT DOES NOT VALIDATE! ("  +filepath + "): " + str(e))


def splittags(doc):
    print "\tResolving PoS tags:"
    for word in doc.words():
        if word.hasannotation(folia.PosAnnotation):
            word.replace( cgn.parse_cgn_postag(word.pos()) )
        else:
            errout("\t\tWARNING: No PoS tag for " + word.id )
        if not word.hasannotation(folia.LemmaAnnotation):
            errout("\t\tWARNING: No Lemma for " + word.id )
    return doc
        
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
        foliadoc = dcoitofolia(filepath, parseddcoi)
        if not foliadoc:
            return False
        
        #Split CGN tags
        splittags(foliadoc)
        
        #FoLiA to plaintext
        foliatoplaintext(foliadoc, filepath)

        print "\tSaving:"
        #Save document
        try:        
            foliadoc.save(foliadir + getfilename(filepath))
            print "\t\t" + foliadir + getfilename(filepath)
        except Exception as e:
            errout("\t\tERROR saving " + foliadir + getfilename(filepath) + ": " + str(e))
            return False
        
        #Integrity Check
        succes = integritycheck(foliadoc, filepath, content, parseddcoi)
        
        validate(foliadir + getfilename(filepath))
        
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
    
    
    if foliadir[-1] != '/': foliadir += '/'
    try:
        os.mkdir(foliadir[:-1])
    except:
        pass
            
    print "Building index..."
    index = list(enumerate([ x for x in sonar.CorpusFiles(sonardir,'pos', "", lambda x: True, True) if not outputexists(x, sonardir, foliadir) ]))
    indexlength = len(index)

    
    print "Processing..."
    p = Pool(threads)
    p.map(process, index )

    print "All done."
