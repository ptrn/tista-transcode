#! /usr/bin/python
# -*- coding: utf-8; -*-

"""

Adds files listed on command line

"""

import sys, os, re

import psycopg2

import urlparse

import ttc.config, ttc.model.jobs



def Main():  
    try:
        cfgPath, outExt, inPath = sys.argv[1:4]
        fArgs = sys.argv[4:]
    except ValueError:
        sys.stderr.write("Usage: %s <config> <out root> <out ext.> <in path> <format arg.> ... \n" % sys.argv[0])
        sys.exit(1)

    # Add . to extensions if necessary
    if not outExt.startswith("."):
        outExt = "." + outExt
    
    cfg = ttc.config.Load(cfgPath)

    dbName = cfg["database"]["name"]

    conn = psycopg2.connect("dbname=%s" % (dbName,))
    cursor = conn.cursor()

    srcURI = urlparse.urlunparse(["file","",inPath,"","",""])
    dstURI = ttc.model.jobs.CreateDstURI(cfg, srcURI, outExt)
    fDict  = dict([(arg.split("=") ) for arg in fArgs])
        
    print srcURI, "  ", dstURI
    job = ttc.model.jobs.Job2(None, srcURI, dstURI, fDict)
    try:
        job.Insert(cursor, cfg["path"]["cache"])
        conn.commit()
    except psycopg2.IntegrityError:
        sys.stderr.write('WARNING: Duplicate job: %s\n' % dstURI)
        conn.rollback()

    print "will be uploaded to %s" % job.GetUploadPath(cfg) 

if __name__ == "__main__":
    Main()
