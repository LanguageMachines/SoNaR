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



def process(filepath):
            
    s =  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' +  filepath     
    print >>sys.stderr, s
    
    #COUNT STEP    
    freqlist_word = FrequencyList()
    freqlist_lemma = FrequencyList()
    freqlist_lemmapos = FrequencyList()
    
    try:
        for word in folia.Reader(filepath, folia.Word):
            try:
                freqlist_word.count(word.text())
            except folia.NoSuchText:
                print >>sys.stderr, "ERROR: Got NoSuchText error on " + word.id + " !!!"
                continue
            try:
                if word.lemma():
                    freqlist_lemma.count(word.lemma())
                    if word.pos():
                        freqlist_lemmapos.count( (word.lemma(), word.pos()) )
            except folia.NoSuchAnnotation:
                print >>sys.stderr, "ERROR: Got NoSuchAnnotation error on " + word.id + " !!!"
                continue
    except Exception as e:
        print >>sys.stderr,"ERROR: Got exception counting " + filepath + ": ", repr(e)        
    return filepath, freqlist_word, freqlist_lemma, freqlist_lemmapos
            
            
        
        
         
    
        

if __name__ == '__main__':    
    try:
        sonardir = sys.argv[1]        
        #threads = int(sys.argv[2])
    except:
        print >>sys.stderr,"Syntax: sonar_postproc.py sonardir"
        sys.exit(2)
    
    
    cat_freqlist_word = FrequencyList()
    cat_freqlist_lemma = FrequencyList()
    cat_freqlist_lemmapos = FrequencyList()

    maxtasksperchild = 10
    preindex = True
    prevcategory = None
    print >>sys.stderr,"Initialising (indexing)..."
    processor = list(folia.CorpusFiles(sonardir,'folia.xml',"",lambda x: True, preindex))
    l = len(processor)
    print >>sys.stderr,"Processing " + str(l) + " files"
    for i, filepath in enumerate(processor):        
        filepath, freqlist_word, freqlist_lemma, freqlist_lemmapos = process(filepath)
        if filepath:
            category = None
            for e in filepath.split('/'):
                if e[-4:] != '.xml' and e[:3] == 'WR-' or e[:3] == 'WS-':
                    category = e
            if not category:
                print >>sys.stderr, "No category found for: " + filepath
                sys.exit(2)
               
            if category != prevcategory:
                if prevcategory:
                    print >>sys.stderr,"Saving frequency lists for ", prevcategory
                    #save previous category
                    cat_freqlist_word.save(sonardir + '/' + prevcategory +'.wordfreqlist.csv',True)
                    cat_freqlist_lemma.save(sonardir + '/' +prevcategory+'.lemmafreqlist.csv',True)
                    cat_freqlist_lemmapos.save(sonardir + '/' + prevcategory+'.lemmaposfreqlist.csv',True)    

                print >>sys.stderr,"NEW CATEGORY: ", category

                
                cat_freqlist_word = FrequencyList()
                cat_freqlist_lemma = FrequencyList()
                cat_freqlist_lemmapos = FrequencyList()
                prevcategory = category
            
            
            cat_freqlist_word += freqlist_word
            cat_freqlist_lemma += freqlist_lemma
            cat_freqlist_lemmapos += freqlist_lemmapos

            progress = round((i+1) / float(l) * 100,1)    
            print "#" + str(i) + " - " + str(progress) + '%'
        else:
            print "#" + str(i) + " - " + str(progress) + '% (skipped)'
                
    if prevcategory:
        #save previous category
        cat_freqlist_word.save(sonardir + '/' + prevcategory +'.wordfreqlist.csv',True)
        cat_freqlist_lemma.save(sonardir + '/' +prevcategory+'.lemmafreqlist.csv',True)
        cat_freqlist_lemmapos.save(sonardir + '/' + prevcategory+'.lemmaposfreqlist.csv',True)        
        
#print "Saving frequency lists by category"
        
#total_freqlist_word = FrequencyList()
#total_freqlist_lemma = FrequencyList()
#total_freqlist_lemmapos = FrequencyList()        
        
#for cat in cat_freqlist_word:
#    cat_freqlist_word[cat].save(outputdir + '/' + cat+'.wordfreqlist.csv',True)
#    cat_freqlist_lemma[cat].save(outputdir + '/' + cat+'.lemmafreqlist.csv',True)
#    cat_freqlist_lemmapos[cat].save(outputdir + '/' + cat+'.lemmaposfreqlist.csv',True)
#    total_freqlist_word += cat_freqlist_word[cat]
#    total_freqlist_lemma += cat_freqlist_lemma[cat]
#    total_freqlist_lemmapos += cat_freqlist_lemmapos[cat]
    
#print "Saving global lists by category"    
    
#total_freqlist_word.save(outputdir + '/' + 'wordfreqlist.csv',True)
#total_freqlist_lemma.save(outputdir + '/' + 'lemmafreqlist.csv',True)
#total_freqlist_lemmapos.save(outputdir + '/' + 'lemmaposfreqlist.csv',True)    
