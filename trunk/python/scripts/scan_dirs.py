#! /usr/bin/python
# -*- coding: utf-8; -*-

"""

Scans two directory trees. Files in tree 1 that haven't got
counterparts in tree 2 will be transcoded.

File names ending in _ddd before extension will be assumed to be part
of a set.

"""

import sys, os, re

import psycopg2

import ttc.config, ttc.model.jobs

D = re.compile(r'(.*)_(\d\d\d)$')

def BuildPathLists(inRoot, inExt, outRoot, outExt):
    groups = {}

    for curRoot, dNames, fNames in os.walk(inRoot):
        branchPart = curRoot[len(inRoot) + 1:]
                
        for fName in sorted(fNames):
            base, ext = os.path.splitext(fName)
            if ext == inExt:
                m = D.search(base)
                if m:
                    base = m.group(1)

                srcPath = os.path.join(curRoot, fName)
                dstPath = os.path.join(outRoot, branchPart, base + outExt)

                if not os.path.exists(dstPath):
                    sys.stderr.write('NEW:      %s\n' % srcPath)
                    
                    basePath = os.path.join(curRoot, base)
                    try:
                        groups[basePath][0].append(srcPath)
                    except KeyError:
                        groups[basePath] = ([srcPath], dstPath)
                else:
                    sys.stderr.write('EXISTING: %s\n' % srcPath)

    return groups.values()
                        
def Main():  
    try:
        cfgPath, recipe, inRoot, inExt, outRoot, outExt = sys.argv[1:]
    except ValueError:
        sys.stderr.write("Usage: %s <config> <recipe> <in root> <in ext.> <out root> <out ext.>\n" % sys.argv[0])
        sys.exit(1)

    # Add . to extensions if necessary
    if not inExt.startswith("."):
        inExt = "." + inExt
    if not outExt.startswith("."):
        outExt = "." + outExt
    
    cfg = ttc.config.Load(cfgPath)

    dbName = cfg["database"]["name"]

    conn = psycopg2.connect("dbname=%s" % (dbName,))
    cursor = conn.cursor()

    pathLists = BuildPathLists(inRoot, inExt, outRoot, outExt)

    for srcPaths, dstPath in pathLists:
        job = ttc.model.jobs.Job(None, srcPaths, dstPath, recipe)
        try:
            job.Insert(cursor, cfg["path"]["cache"])
            conn.commit()
        except psycopg2.IntegrityError:
            sys.stderr.write('WARNING: Duplicate job: %s\n' % dstPath)
            conn.rollback()

if __name__ == "__main__":
    Main()
