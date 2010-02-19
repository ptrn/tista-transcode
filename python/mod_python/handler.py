#! /usr/bin/python
# -*- coding: utf-8; -*-


import time, sys

import psycopg2

import mod_python.Cookie

from mod_python import apache

import ttc.config
import ttc.view.web

from ttc.view.web.jobs import *

# cfg depends on the configuration path, which won't be known before
# we receive our first request.
cfg = None

dbConnection = None

def handler(req):
    remoteHost = req.get_remote_host(apache.REMOTE_NOLOOKUP)
    #if remoteHost not in ("158.39.165.66", "81.175.13.7", "158.39.165.133"):
    #    return 403
    
    global cfg, dbConnection
    
    req.debugThen = time.time()

    if cfg == None:
        cfgPath = req.get_options()["ttcConfigPath"]
        if cfgPath:
          cfg = ttc.config.Load(cfgPath)
    if cfg == None:
        return apache.HTTP_NOT_FOUND

    dbName = cfg["database"]["name"]
    dbUser = cfg["database"]["webUser"]
 
    hostName = cfg["network"]["host"]
    if hostName != 'localhost':
        hostName = "%s.%s" % (cfg["network"]["host"], cfg["network"]["domain"])
    if req.hostname != hostName:
        # *** Todo: Handle other protocols (e.g. HTTPS) and ports
        target = "http://%s%s" % (hostName, req.uri)
        mod_python.util.redirect(req, target)
        return

    if not dbConnection:
        dbConnection = psycopg2.connect("dbname=%s user=%s" % (dbName, dbUser))

    req.config = cfg
    req.conn = dbConnection
    req.cursor = dbConnection.cursor()

    if pathMapping.has_key(req.uri):
        method = pathMapping[req.uri]
    elif req.uri.startswith("/ttc/jobs/upload/"):
        method = UploadJob
    elif req.uri.startswith("/ttc/jobs/download/"):
        method = DownloadJob
    else: 
        return apache.HTTP_NOT_FOUND

    try:
        res = method(req)()
    except:
        req.conn.rollback()
        raise
    else:
        req.conn.commit()
        return res
 
pathMapping = dict([(c.path, c) for c in globals().values() if type(c) is type(Page) and issubclass(c, Page) and c is not Page and isinstance(c.path, str)])

