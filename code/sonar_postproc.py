#! /usr/bin/env python
# -*- coding: utf8 -*-

import sys
import os

if __name__ == "__main__":
    sys.path.append(sys.path[0] + '/../..')
    os.environ['PYTHONPATH'] = sys.path[0] + '/../..'

from pynlpl.formats import folia
from pynlpl.statistics import FrequencyList
import datetime
import codecs



def process(data):
    global foliadir, indexlength

    filepath, args, kwargs = data        
    s =  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' +  filepath     
    print >>sys.stderr, s


    #CURATION STEP
    replace = [
        ('<pos-annotation annotator="tadpole" annotatortype="auto" set="http://ilk.uvt.nl/folia/sets/cgn"/>', '<pos-annotation annotator="frog" annotatortype="auto" set="hdl:1839/00-SCHM-0000-0000-000B-9"/>'),
        ('<lemma-annotation annotator="tadpole" annotatortype="auto" set="http://ilk.uvt.nl/folia/sets/lemmas-nl"/>', '<lemma-annotation annotator="frog" annotatortype="auto" set="hdl:1839/00-SCHM-0000-0000-000E-3"/>'),        
    ]
    
    
    f = codecs.open(filepath,'r','utf-8')
    outputlines = []
    gapinsertpoint = 0
    hasgap = False
    metadata = 0
    for i, line in enumerate(i, f):
        if metadata == 0 and line.find('<?xml version') != -1:
            outputlines.append(line)
            outputlines.append('<?xml-stylesheet type="text/xsl" href="sonar-foliaviewer.xsl"?>')
            continue        
        if metadata == 0 and line.find('<metadata src=') != -1: 
            metadata = 1
        if metadata == 1:
            if line.find('</metadata>') != -1:
                gapinsertpoint = i -1
                metadata = 2
            else:
                for source,target in replace:                    
                    line = line.replace(source,target)
        if metadata == 2:      
            if not hasgap and line.find('<gap ') != -1: 
                hasgap = True


        outputlines.append(line)            
    f.close()
    
    if hasgap and gapinsertpoint > 0:        
        outputlines.insert(gapinsertpoint, '<gap-annotation />')
    
    f = codecs.open(filepath+'.tmp','w','utf-8')
    for line in outputlines:
        f.write(line)
    f.close()
    
    os.rename(filepath+'.tmp', filepath)
    
    #COUNT STEP
    
    freqlist_word = FrequencyList()
    freqlist_lemma = FrequencyList()
    freqlist_lemmapos = FrequencyList()
    
    for word in folia.Reader(filepath, folia.Word):
        try:
            freqlist_word.count(word.text())
        except folia.NoSuchText:
            print >>sys.stderr, "ERROR: Got NoSuchText error on " + word.id + " !!!"
            continue
        if word.lemma():
            freqlist_lemma.count(word.lemma())
            if word.pos():
                freqlist_lemmapos.count( (word.lemma(), word.pos()) )
    
    return freqlist_word, freqlist_lemma, freqlist_lemmapos
            
            
        
        
         
    
        

if __name__ == '__main__':    
    try:
        sonardir = sys.argv[1]        
        threads = int(sys.argv[2])
    except:
        print >>sys.stderr,"Syntax: sonar_postproc.py sonardir threads"
        sys.exit(2)
    
    
    cat_freqlist_word = {}
    cat_freqlist_lemma = {}
    cat_freqlist_lemmapos = {}


    maxtasksperchild = 10
    preindex = True
    processor = folia.CorpusProcessor(sonardir, process, threads, 'folia.xml',"",lambda x: True, maxtasksperchild,preindex)
    for i, data in enumerate(processor):
        category = 'blah' #TODO: extract category
        if not category in cat_freqlist_word: 
            cat_freqlist_word[category] = FrequencyList()
            cat_freqlist_lemma[category] = FrequencyList()
            cat_freqlist_lemmapos[category] = FrequencyList()
                        
        freqlist_word, freqlist_lemma, freqlist_lemmapos = data
        cat_freqlist_word[category] += freqlist_word
        cat_freqlist_lemma[category] += freqlist_lemma
        cat_freqlist_lemmapos[category] += freqlist_lemmapos

        progress = round((i+1) / float(len(processor.index)) * 100,1)    
        print "#" + str(i) + " - " + str(progress) + '%'
        
        
print "Saving frequency lists by category"
        
total_freqlist_word = FrequencyList()
total_freqlist_lemma = FrequencyList()
total_freqlist_lemmapos = FrequencyList()        
        
for cat in cat_freqlist_word:
    cat_freqlist_word[cat].save(cat+'.wordfreqlist.csv')
    cat_freqlist_lemma[cat].save(cat+'.lemmafreqlist.csv')
    cat_freqlist_lemmapos[cat].save(cat+'.lemmaposfreqlist.csv')
    total_freqlist_word += cat_freqlist_word[cat]
    del cat_freqlist_word[cat]
    total_freqlist_lemma += cat_freqlist_lemma[cat]
    del cat_freqlist_lemma[cat]
    total_freqlist_lemmapos += cat_freqlist_lemmapos[cat]
    del cat_freqlist_lemmapos[cat]
    
print "Saving global lists by category"    
    
total_freqlist_word[cat].save('wordfreqlist.csv')
total_freqlist_lemma[cat].save('lemmafreqlist.csv')
total_freqlist_lemmapos[cat].save('lemmaposfreqlist.csv')    
