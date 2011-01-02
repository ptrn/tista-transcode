#! /usr/bin/python
# -*- coding: utf-8; -*-

"""

This module defines classes, functions and database tables for
manipulating users. Also includes authentication functions.

"""

import os, stat, tempfile, subprocess, shutil, urlparse

import psycopg2, PIL.Image, PIL.ImageOps
from psycopg2.extensions import adapt

from ttc.db import PsE

import ttc.model

# Placed outside Job class for re-use without object instantiation
def GetSnapshotPath(jobID, cachePath):
    c1 = jobID[0:1]
    c2 = jobID[0:2]
    c3 = jobID[0:3]
    c4 = jobID[0:4]
    c5 = "%s_full.jpg" % jobID
    
    return os.path.join(cachePath, "snapshots", c1, c2, c3, c4, c5)

class Job(object):
    """
    
    Represents a job

    """


    def TakeSnapshot(self, cachePath):
        """

        Stores a JPEG snapshot of the most interesting frame of
        source's first five seconds of video. Returns None if snapshot
        couldn't be made.
        
        Currently defunct
        """
        
        root = tempfile.mkdtemp(prefix = 'ttc-snapshot-')
        cmd = ('vlc', self.srcURI, '-vvv', '--no-audio', '-I', 'dummy', '-V', 'image', '--start-time=0', '--stop-time=5', '--snapshot-format=jpeg', '--snapshot-path=%s/' % root, 'vlc://quit')
        proc = subprocess.Popen(cmd)
        proc.wait()
        sizePaths = []
        for name in os.listdir(root):
            path = os.path.join(root, name)
            size = os.stat(path)[stat.ST_SIZE]
            sizePaths.append((size, path))
        if sizePaths:
            img = PIL.Image.open(sorted(sizePaths)[-1][1])
            img = PIL.ImageOps.fit(img, (128, 96), PIL.Image.ANTIALIAS, bleed = 0.02, centering = (0.5, 0.5))
            snapshotPath = GetSnapshotPath(self.id, cachePath)
            snapshotRoot = os.path.split(snapshotPath)[0]
            if not os.path.exists(snapshotRoot):
                os.makedirs(snapshotRoot)
                
            img.save(snapshotPath)

        shutil.rmtree(root)


    def __init__(self, jobID, srcURI, dstURI, imgURI, imgDur, sepDur, fDict, state = 'w', creationTime = None, workerAddress = None, workerStartTime = None, workerHeardFrom = None, workerRelativeProgress = None, priority = 128):
        self.id = jobID
        self.srcURI = srcURI
        self.dstURI = dstURI
        self.imgURI = imgURI
        self.imgDur = imgDur
        self.sepDur = sepDur
        self.fDict  = fDict
        self.state  = state
        self.priority = priority

        self.creationTime = creationTime

        self.workerAddress = workerAddress
        self.workerStartTime = workerStartTime
        self.workerHeardFrom = workerHeardFrom
        self.workerRelativeProgress = workerRelativeProgress

    def CalculateSourceSize(self):
        """
        Only call this when source is file 
        """
        return 0

    def GetType(self):
        """

        Returns a string describing the transcoding procedure
    
        """
        return "%s/%s" % (self.fDict.get("format","?"), self.fDict.get("vcodec","?"))

    def Insert(self, cursor, cachePath):
        """

        Insert job into the database. ID, dstPath, srcPaths, format arguments and srcSize will be stored.
        
        cursor    : database handle
        cachePath : direcory for placing snapshots during transcoding (currently not working)
        Returns   : nothing

        """

        self.id = ttc.model.RandomHexString(32)
        size = self.CalculateSourceSize()

        PsE(cursor, "insert into Jobs (id, srcURI, dstURI, imgURI, imgDuration, separation, priority, srcSize) values (%s, %s, %s, %s, %s, %s, %s, %s)", (self.id, str(self.srcURI), self.dstURI, str(self.imgURI), self.imgDur, self.sepDur, self.priority, size))
#        PsE(cursor, "insert into Jobs (id, srcURI, dstURI, imgURI, imgDuration, priority, srcSize) values (%s, %s, %s, %s, %s, %s, %s)", (self.id, str(self.srcURI), self.dstURI,str(self.imgURI), self.imgDur, self.priority, size))
        for key in self.fDict:
            PsE(cursor, "insert into Parameters (jobID, key, value) values (%s, %s, %s)", (self.id, str(key), str(self.fDict[key])))

    def UpdateProgress(self, cursor, numBytes):
        PsE(cursor, "update jobs set workerRelativeProgress=%s, workerHeardFrom=current_timestamp where id=%s", (numBytes, self.id))

    def SetInProgress(self, cursor, ip):
        PsE(cursor, "update jobs set state='i', workerAddress=%s, workerStartTime=current_timestamp where id=%s", (ip, self.id))

    def SetFinished(self, cursor):
        PsE(cursor, "update jobs set state='f' where id=%s", (self.id,))

    def SetError(self, cursor):
        PsE(cursor, "update jobs set state='e' where id=%s", (self.id,))

    def Assign(self, cursor, ip):
        """
        Marks job as active. Client will transcoding.
        """
        self.SetInProgress(cursor, ip)
        self.UpdateProgress(cursor, 0)

    def GetDownloadURI(self, cfg, outHost):
        """
        In (rare) cases when the source item is available as a file in the servers file storage,
        but not in the transclients, we construct a special http url for downloading  
        """
        clientSchm = cfg["network"]["clientscheme"]
        if self.srcURI.startswith("file") and clientSchm.startswith("http"):
            srcPath = os.path.join("/ttc/jobs/download", self.id)
            return urlparse.urlunparse(["http",outHost,srcPath,"","",""])
        return self.srcURI 

    def GetImageURI(self, cfg, outHost):
        """
        The URI of the encapsulating image is treated as the source uri
        """
        clientSchm = cfg["network"]["clientscheme"]
        if self.imgURI.startswith("file") and clientSchm.startswith("http"):
            imgPath = os.path.join("/ttc/jobs/imgload", self.id)
            return urlparse.urlunparse(["http",outHost,imgPath,"","",""])
        return self.imgURI 

    def GetUploadURI(self, cfg, outHost):
        """
        In cases when the destination item is available as a file in the servers file storage,
        but not in the transclients, we construct a special http url for uploading  
        """
        clientSchm = cfg["network"]["clientscheme"]
        outRoot  = cfg["path"]["base"]
        outStore = cfg["path"]["storage"]
        outBase  = os.path.join(outRoot,outStore)
        if self.dstURI.startswith("http") and clientSchm == "file":
            inParsed = urlparse.urlparse(self.dstURI)
            inPath   = inParsed.path
            basePart = os.path.basename(inPath)
            dstPath  = os.path.join(outBase, basePart)
            return urlparse.urlunparse(["file","",dstPath,"","",""])
        elif clientSchm == "http":
            dstPath = os.path.join("/ttc/jobs/upload", self.id)
            return urlparse.urlunparse(["http",outHost,dstPath,"","",""])
        return self.dstURI 

    def GetUploadPath(self, cfg):
        """
        Return path of the location were a file uploaded from a client will be stored

        Note that when using file or s3 as client scheme, this wil not be in use
        """
        dstPath =  urlparse.urlparse(self.dstURI).path
        if self.dstURI.startswith("file"): # Extract destination path from file URI
            dstDir = os.path.dirname(dstPath)
        elif self.dstURI.startswith("http"):  # Fetch path from http uri, append this to webserver root
            outRoot  = cfg["path"]["base"]
            outStore = cfg["path"]["storage"]
            outBase  = os.path.join(outRoot,outStore)
            basePart = os.path.basename(dstPath)
            dstPath  = os.path.join(outBase, basePart)
            dstDir   = outBase
        else:
            dstDir   = outBase
        if not os.path.exists(dstDir):
            os.makedirs(dstDir)
        return dstPath

    def GetBasics(self):
        return "{\n  \"id\" : \"%s\", \n  \"state\" : \"%s\", \n  \"srcURI\" : \"%s\", \n  \"dstURI\" : \"%s\", \n  \"progress\" : \"%s\"\n}\n" % (
                self.id,
                self.state,
                self.srcURI,
                self.dstURI,
                self.workerRelativeProgress)



def CreateDstURI(cfg, srcURI, myHost, args):
    """
    Create a destination uri, based on the source uri, the availabilty of the transcoders file storage, the transcoding host and
    the type of the transcoded item. 
    """
    w  = args.get('width','def')
    h  = args.get('height','def')
    vb = args.get('vbitrate','def')
    ab = args.get('abitrate','def')
    outExt = '_%s_%s_%s_%s_%s_%s_%s' % (args['format'],args['vcodec'],args['acodec'],vb,ab,w,h,)
    userSchm = cfg["network"]["userscheme"]
    inParsed = urlparse.urlparse(srcURI)
    inPath   = inParsed.path
    basePart = os.path.splitext(os.path.split(inPath)[1])[0]
    outStore = cfg["path"]["storage"]
    if userSchm == "file":
        outRoot  = cfg["path"]["base"]
        outHost  = ""
    elif userSchm == "s3":
        userSchm = "http"
        outHost  = cfg["network"]["s3host"]
        outRoot  = cfg["path"]["base"]
    else:
        outRoot  = ""
        outHost  = myHost
    dstPath  = os.path.join(outRoot, outStore, basePart + outExt)
    dstURI   = urlparse.urlunparse([userSchm,outHost,dstPath,"","",""])
    return dstURI
 
def AddOneJob(cursor, srcURI, dstURI, imgURI, imgDur, sepDur, cache, arguments):
    """

    Creates destination URI, adds job to the database

    cursor    : sql database handle 
    srcURI    : URI of item that should be transcoded
    dstURI    : URI of the location that should hold the transcoded item 
    arguments : dictionary containing key value pairs describing destination format and transcoding options

    Returns   : job 
    """
    
    job = Job(None, srcURI, dstURI, imgURI, imgDur, sepDur, arguments)
    if not job:
        return None
    try:
        job.Insert(cursor, cache)
    except psycopg2.IntegrityError:
        return None

    return job

def GetJobsByParams(cursor, state=None, arguments=dict([])):
    """

    Returns a list of jobs, optionally filtered by state and destination format
 
    cursor    : sql database handle 
    arguments : dictionary containing key value pairs describing possible destination formats

    Returns   : list of jobs 
    """
    
    keypart = " "
    valpart = []

    if state:
        statepart = " where state=%s"
        valpart.append(str(state))
    else:
        statepart = " where state=state"
    
    for key in arguments:
        keypart += " and exists (select jobID from parameters where jobs.id=parameters.jobID and key = %s and value = %s)"
        valpart.append(str(key))
        valpart.append(str(arguments[key]))
    
    jobs = []


    PsE(cursor, "select id, srcURI, dstURI, imgURI, imgDuration, separation, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs " + statepart + keypart + " order by priority asc",valpart)
    for jobID, srcURI, dstURI, imgURI, imgDur, sepDur, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority in cursor.fetchall():
            
        PsE(cursor, "select key, value from parameters where jobID=%s", (jobID,))
        fDict = dict([(p[0], p[1]) for p in cursor.fetchall()])

        jobs.append(Job(jobID, srcURI, dstURI, imgURI, imgDur, sepDur, fDict, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority))
    return jobs

def GetJobsByState(cursor, state = None):
    """

    Returns a list of jobs, optionally filtered by state
    
    state     : w/i/f/e, character indicating transcoding state
    Returns   : job list 

    """

    if state:
        statePart = " where state='%s'" % state
    else:
        statePart = []

    jobs = []

    PsE(cursor, "select id, srcURI, dstURI, imgURI, imgDuration, separation, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs%s" % statePart)
    for jobID, srcURI, dstURI, imgURI, imgDur, sepDur, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority in cursor.fetchall():
        PsE(cursor, "select key, value from parameters where jobID=%s", (jobID,))
        fDict = dict([(p[0], p[1]) for p in cursor.fetchall()])

        jobs.append(Job(jobID, srcURI, dstURI, imgURI, imgDur, sepDur, fDict, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority))

    return jobs


def GetJobByID(cursor, jobID):
    """
    
    Returns a job identified by the argument

    jobID   : 32 byte hexadecimal string 
    returns : job or None if no matching jobID was found
 
    """

    PsE(cursor, "select id, srcURI, dstURI, imgURI, imgDuration, separation, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs where id=%s", (jobID,))
    try:
        jobID, srcURI, dstURI, imgURI, imgDur, sepDur, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority = cursor.fetchone()
    except TypeError:
        # No jobs matching id
        return None
    PsE(cursor, "select key, value from parameters where jobID=%s", (jobID,))
    fDict = dict([(p[0], p[1]) for p in cursor.fetchall()])

    job = Job(jobID, srcURI, dstURI, imgURI, imgDur, sepDur, fDict, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority)
    if not job:
        return None

    return job




