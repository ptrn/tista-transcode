#! /usr/bin/python
# -*- coding: utf-8; -*-

"""

Adds files listed on command line

"""

import sys, os, re

import psycopg2

import ttc.config, ttc.model.jobs

def Main():  
    try:
        cfgPath, recipe, outRoot, outExt = sys.argv[1:5]
        inPaths = sys.argv[5:]
    except ValueError:
        sys.stderr.write("Usage: %s <config> <recipe> <out root> <out ext.> <in paths...>\n" % sys.argv[0])
        sys.exit(1)

    # Add . to extensions if necessary
    if not outExt.startswith("."):
        outExt = "." + outExt
    
    cfg = ttc.config.Load(cfgPath)

    dbName = cfg["database"]["name"]

    conn = psycopg2.connect("dbname=%s" % (dbName,))
    cursor = conn.cursor()

    for inPath in inPaths:
        basePart = os.path.splitext(os.path.split(inPath)[1])[0]
        dstPath = os.path.join(outRoot, basePart + outExt)
        
        job = ttc.model.jobs.Job(None, [inPath], dstPath, recipe)
        try:
            job.Insert(cursor, cfg["path"]["cache"])
            conn.commit()
        except psycopg2.IntegrityError:
            sys.stderr.write('WARNING: Duplicate job: %s\n' % dstPath)
            conn.rollback()

if __name__ == "__main__":
    Main()
