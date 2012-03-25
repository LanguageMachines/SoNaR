#! /usr/bin/env python
# -*- coding: utf8 -*-

import sys
import os

if __name__ == "__main__":
    sys.path.append(sys.path[0] + '/../..')
    os.environ['PYTHONPATH'] = sys.path[0] + '/../..'

from pynlpl.formats import folia
#from pynlpl.statistics import FrequencyList
import datetime
import codecs



def process(data):
    global foliadir, indexlength, inputdir, outputdir
    curate = True
    filepath, args, kwargs = data
    outputfile = filepath.replace(inputdir, outputdir)
    #if os.path.exists(outputfile):
    #    print >>sys.stderr, "Skipping curation of " + filepath + " (output file already exists)"
    #    curate = False
            
    s =  datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' +  filepath     
    print >>sys.stderr, s



    if curate:
        #CURATION STEP
        replace = [
            ('<pos-annotation annotator="tadpole" annotatortype="auto" set="http://ilk.uvt.nl/folia/sets/cgn"/>', '<pos-annotation annotator="frog" annotatortype="auto" set="hdl:1839/00-SCHM-0000-0000-000B-9"/>'),
            ('<lemma-annotation annotator="tadpole" annotatortype="auto" set="http://ilk.uvt.nl/folia/sets/lemmas-nl"/>', '<lemma-annotation annotator="frog" annotatortype="auto" set="hdl:1839/00-SCHM-0000-0000-000E-3"/>'),        
            ('<entity-annotation set="sonar-ner"/>','<entity-annotation annotator="NERD" annotatortype="auto" set="hdl:1839/00-SCHM-0000-0000-000D-5"/>')
        ]
        
        
        try:
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

        except Exception as e:
            print >>sys.stderr,"ERROR: Got exception curating " + filepath + ": ", repr(e)

            
        
        
         
    
        

if __name__ == '__main__':    
    try:
        inputdir = sys.argv[1]        
        outputdir = sys.argv[2]
        threads = int(sys.argv[3])
    except:
        print >>sys.stderr,"Syntax: sonar_postproc.py inputdir outputdir threads"
        sys.exit(2)


    maxtasksperchild = 10
    preindex = True
    prevcategory = None
    print >>sys.stderr,"Initialising (indexing)..."
    processor = folia.CorpusProcessor(inputdir, process, threads, 'folia.xml',"",lambda x: not os.path.exists(x.replace(inputdir,outputdir)), maxtasksperchild,preindex)
    l = len(processor.index)
    print >>sys.stderr,"Indexed " + str(l) + " files for curation"
    print >>sys.stderr,"Processing..."
    for i ,_ in enumerate(processor.run()):
        progress = round((i+1) / float(l) * 100,1)    
        print "#" + str(i) + " - " + str(progress) + '%'
