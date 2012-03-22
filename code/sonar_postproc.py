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
    global foliadir, indexlength, inputdir, outputdir

    filepath, args, kwargs = data
    outputfile = filepath.replace(inputdir, outputdir)
    if os.path.exists(outputfile):
        print >>sys.stderr, "Skipping " + filepath + " (output file already exists)"
        return None,None,None,None
            
    s =  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' +  filepath     
    print >>sys.stderr, s


    #CURATION STEP
    replace = [
        ('<pos-annotation annotator="tadpole" annotatortype="auto" set="http://ilk.uvt.nl/folia/sets/cgn"/>', '<pos-annotation annotator="frog" annotatortype="auto" set="hdl:1839/00-SCHM-0000-0000-000B-9"/>'),
        ('<lemma-annotation annotator="tadpole" annotatortype="auto" set="http://ilk.uvt.nl/folia/sets/lemmas-nl"/>', '<lemma-annotation annotator="frog" annotatortype="auto" set="hdl:1839/00-SCHM-0000-0000-000E-3"/>'),        
        ('<entity-annotation set="sonar-ner"/>','<entity-annotation annotator="NERD" annotatortype="auto" set="hdl:1839/00-SCHM-0000-0000-000D-5"/>')
    ]
    

    
    
    f = codecs.open(filepath,'r','utf-8')
    outputlines = []
    gapinsertpoint = 0
    hasgap = False
    metadata = 0
    for i, line in enumerate(f):
        if metadata == 0 and line.find('<?xml version') != -1:
            outputlines.append(line)
            outputlines.append('<?xml-stylesheet type="text/xsl" href="sonar-foliaviewer.xsl"?>\n')
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
        outputlines.insert(gapinsertpoint, '<gap-annotation />\n')

    
    dir = os.path.dirname(outputfile)
    if not os.path.isdir(dir):
        os.mkdir( os.path.dirname(outputfile))
    
    tmpfile = filepath.replace(inputdir, outputdir) + '.tmp'
    f = codecs.open(tmpfile,'w','utf-8')
    for line in outputlines:
        f.write(line)
    f.close()
    
    

        

    try:
        os.rename(tmpfile, outputfile )
    except:
        print >>sys.stderr,"Unable to write file " + outputfile 
    
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
    
    return filepath, freqlist_word, freqlist_lemma, freqlist_lemmapos
            
            
        
        
         
    
        

if __name__ == '__main__':    
    try:
        inputdir = sys.argv[1]        
        outputdir = sys.argv[2]
        threads = int(sys.argv[3])
    except:
        print >>sys.stderr,"Syntax: sonar_postproc.py inputdir outputdir threads"
        sys.exit(2)
    
    
    cat_freqlist_word = {}
    cat_freqlist_lemma = {}
    cat_freqlist_lemmapos = {}


    maxtasksperchild = 10
    preindex = True
    print >>sys.stderr,"Initialising (indexing)..."
    processor = folia.CorpusProcessor(inputdir, process, threads, 'folia.xml',"",lambda x: True, maxtasksperchild,preindex)
    print >>sys.stderr,"Processing..."
    for i, data in enumerate(processor):
        filepath, freqlist_word, freqlist_lemma, freqlist_lemmapos = data
        if filepath:
            category = None
            for e in filepath.split('/'):
                if e[-4:] != '.xml' and e[:3] == 'WR-' or e[:3] == 'WS-':
                    category = e
            if not category:
                print >>sys.stderr, "No category found for: " + filepath
                sys.exit(2)
            
            if not category in cat_freqlist_word: 
                cat_freqlist_word[category] = FrequencyList()
                cat_freqlist_lemma[category] = FrequencyList()
                cat_freqlist_lemmapos[category] = FrequencyList()
                            
            
            cat_freqlist_word[category] += freqlist_word
            cat_freqlist_lemma[category] += freqlist_lemma
            cat_freqlist_lemmapos[category] += freqlist_lemmapos

            progress = round((i+1) / float(len(processor.index)) * 100,1)    
            print "#" + str(i) + " - " + str(progress) + '%'
        else:
            print "#" + str(i) + " - " + str(progress) + '% (skipped)'
                
        
        
print "Saving frequency lists by category"
        
total_freqlist_word = FrequencyList()
total_freqlist_lemma = FrequencyList()
total_freqlist_lemmapos = FrequencyList()        
        
for cat in cat_freqlist_word:
    cat_freqlist_word[cat].save(outputdir + '/' + cat+'.wordfreqlist.csv',True)
    cat_freqlist_lemma[cat].save(outputdir + '/' + cat+'.lemmafreqlist.csv',True)
    cat_freqlist_lemmapos[cat].save(outputdir + '/' + cat+'.lemmaposfreqlist.csv',True)
    total_freqlist_word += cat_freqlist_word[cat]
    total_freqlist_lemma += cat_freqlist_lemma[cat]
    total_freqlist_lemmapos += cat_freqlist_lemmapos[cat]
    
print "Saving global lists by category"    
    
total_freqlist_word.save(outputdir + '/' + 'wordfreqlist.csv',True)
total_freqlist_lemma.save(outputdir + '/' + 'lemmafreqlist.csv',True)
total_freqlist_lemmapos.save(outputdir + '/' + 'lemmaposfreqlist.csv',True)    
