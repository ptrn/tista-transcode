#! /usr/bin/python
# -*- coding: utf-8; -*-

"""

This module defines classes, functions and database tables for
manipulating users. Also includes authentication functions.

"""

import os, stat, tempfile, subprocess, shutil

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

    def CalculateSourceSize(self):
        """
        Returns total size of all source files
        """
        return sum([os.stat(p)[stat.ST_SIZE] for p in self.srcPaths])

    def GetType(self):
        """

        Returns a string describing the transcoding procedure
    
        """
        return self.recipe   

    def __init__(self, jobID, srcPaths, dstPath, recipe, state = 'w', creationTime = None, workerAddress = None, workerStartTime = None, workerHeardFrom = None, workerRelativeProgress = None, priority = 128):
        self.id = jobID
        self.srcPaths = srcPaths
        self.dstPath = dstPath
        self.recipe = recipe
        self.state = state
        self.priority = priority

        self.creationTime = creationTime

        self.workerAddress = workerAddress
        self.workerStartTime = workerStartTime
        self.workerHeardFrom = workerHeardFrom
        self.workerRelativeProgress = workerRelativeProgress

    def TakeSnapshot(self, cachePath):
        """

        Stores a JPEG snapshot of the most interesting frame of
        source's first five seconds of video. Returns None if snapshot
        couldn't be made.
        
        """
        
        root = tempfile.mkdtemp(prefix = 'ttc-snapshot-')

        cmd = ('vlc', self.srcPaths[0], '-vvv', '--no-audio', '-I', 'dummy', '-V', 'image', '--start-time=0', '--stop-time=5', '--image-out-format=jpeg', '--image-out-ratio=1', '--image-out-prefix=%s/' % root, 'vlc:quit')
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

    def Insert(self, cursor, cachePath):
        """

        Insert a new job into the database. Note that only ID,
        dstPath, srcPaths, recipe and srcSize will be stored.
        
        """

        self.id = ttc.model.RandomHexString(32)

        #self.TakeSnapshot(cachePath)

        PsE(cursor, "insert into jobs (id, dstPath, recipe, priority, srcSize) values (%s, %s, %s, %s, %s)", (self.id, self.dstPath, self.recipe, self.priority, self.CalculateSourceSize()))

        for path in self.srcPaths:
            PsE(cursor, "insert into SourcePaths (jobID, path) values (%s, %s)", (self.id, path))

        #PsE(cursor, "update jobs set dstPath=%s, recipe=%s, state=%s, srcSize=%i, workerAddress=%s, workerStartTime=%s, workerHeardFrom=%s, workerAbsoluteProgress=%i", (self.dstPath, self.recipe, self.state, self.CalculateSourceSize(), self.workerAddress, self.workerStartTime, self.workerHeardFrom, workerAbsoluteProgress))

    def UpdateProgress(self, cursor, numBytes):
        PsE(cursor, "update jobs set workerRelativeProgress=%s, workerHeardFrom=current_timestamp where id=%s", (numBytes, self.id))

    def SetInProgress(self, cursor, ip):
        PsE(cursor, "update jobs set state='i', workerAddress=%s, workerStartTime=current_timestamp where id=%s", (ip, self.id))

    def SetFinished(self, cursor):
        PsE(cursor, "update jobs set state='f' where id=%s", (self.id,))

def GetJobByID(cursor, jobID):
    """

    Returns details of next job and marks it as active. If no jobs are
    available, None is returned.
    
    """

    PsE(cursor, "select id, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs where id=%s", (jobID,))

    try:
      jobID, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority = cursor.fetchone()
    except TypeError:
      # No jobs matching id
      return None

    PsE(cursor, "select path from SourcePaths where jobID=%s", (jobID,))
    srcPaths = [r[0] for r in cursor.fetchall()]

    job = Job(jobID, srcPaths, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority)

    return job

def GetJobs(cursor, state = None):
    """

    Returns a list of jobs, optionally filtered by state
    
    """

    if state:
        statePart = " where state='%s'" % state
    else:
        statePart = []

    jobs = []

    PsE(cursor, "select id, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs%s" % statePart)
    for jobID, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority in cursor.fetchall():
        PsE(cursor, "select path from SourcePaths where jobID=%s", (jobID,))
        srcPaths = [r[0] for r in cursor.fetchall()]

        jobs.append(Job(jobID, srcPaths, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority))

    return jobs

def AssignNextJob(cursor, workerIP, recipes):
    """

    Returns details of next job and marks it as active. If no jobs are
    available, None is returned.
    
    """

    rPart = " or ".join(["recipe='%s'" % r for r in recipes])

    PsE(cursor, "select id, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs where state='w' and (%s) order by priority asc" % rPart)
    try:
        jobID, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority = cursor.fetchone()
    except TypeError:
        # No more available jobs
        return None

    PsE(cursor, "select path from SourcePaths where jobID=%s", (jobID,))
    srcPaths = [r[0] for r in cursor.fetchall()]

    job = Job(jobID, srcPaths, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority)

    job.SetInProgress(cursor, workerAddress)
    job.UpdateProgress(cursor, 0)

    return job

"""

Version using new database structure

"""

class Job2(Job):
    """
    
    Represents a job

    """

    def __init__(self, jobID, srcURI, dstURI, fDict, state = 'w', creationTime = None, workerAddress = None, workerStartTime = None, workerHeardFrom = None, workerRelativeProgress = None, priority = 128):
        self.id = jobID
        self.srcURI = srcURI
        self.dstURI = dstURI
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
        Only call this when source file 
        """
        return 0

    def GetType(self):
        """

        Returns a string describing the transcoding procedure
    
        """
        return "%s/%s" % (self.fDict["format"], self.fDict.get("vcodec","?"))

    def Insert(self, cursor, cachePath):
        """

        Insert job into the database. ID, dstPath, srcPaths, format arguments and srcSize will be stored.
        
        cursor    : database handle
        cachePath : direcory for placing snapshots during transcoding (currently not working)
        Returns   : nothing

        """

        self.id = ttc.model.RandomHexString(32)
        size = self.CalculateSourceSize()

        PsE(cursor, "insert into Jobs2 (id, srcURI, dstURI, priority, srcSize) values (%s, %s, %s, %s, %s)", (self.id, str(self.srcURI), self.dstURI, self.priority, size))
        for key in self.fDict:
            PsE(cursor, "insert into Parameters (jobID, key, value) values (%s, %s, %s)", (self.id, str(key), str(self.fDict[key])))

    def UpdateProgress(self, cursor, numBytes):
        PsE(cursor, "update jobs2 set workerRelativeProgress=%s, workerHeardFrom=current_timestamp where id=%s", (numBytes, self.id))

    def SetInProgress(self, cursor, ip):
        PsE(cursor, "update jobs2 set state='i', workerAddress=%s, workerStartTime=current_timestamp where id=%s", (ip, self.id))

    def SetFinished(self, cursor):
        PsE(cursor, "update jobs2 set state='f' where id=%s", (self.id,))

    def Assign(self, cursor, ip):
        """
        Returns details of requested job and marks it as active. If job is not
        available, None is returned.
        """
        self.SetInProgress(cursor, ip)
        self.UpdateProgress(cursor, 0)


def GetJobs2(cursor, state = None):
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

    PsE(cursor, "select id, srcURI, dstURI, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs2%s" % statePart)
    for jobID, srcURI, dstURI, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority in cursor.fetchall():
        PsE(cursor, "select key, value from parameters where jobID=%s", (jobID,))
        fDict = dict([(p[0], p[1]) for p in cursor.fetchall()])

        jobs.append(Job2(jobID, srcURI, dstURI, fDict, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority))

    return jobs

def AddOneJob(cursor, srcURI, dstURI, cache, arguments):
    """

    Creates destination URI, adds job to the database

    cursor    : sql database handle 
    srcURI    : URI of item that should be transcoded
    dstURI    : URI of the location that should hold the transcoded item 
    arguments : dictionary containing key value pairs describing destination format and transcoding options

    Returns   : job 
    """
    
    job = Job2(None, srcURI, dstURI, arguments)
    if not job:
        return None
    try:
        job.Insert(cursor, cache)
    except psycopg2.IntegrityError:
        return None

    return job

def GetJobList(cursor, state=None, arguments=dict([])):
    """

    Returns a list of jobs, optionally filtered by state and destination format
 
    cursor    : sql database handle 
    arguments : dictionary containing key value pairs describing possible destination formats

    Returns   : list of jobs 
    """
    
    if state:
        statePart = " where state='%s'" % state
    else:
        statePart = []

    keypart = " "
    valpart = []
    valpart.append(state)
    
    for key in arguments:
        keypart += " and exists (select jobID from parameters where jobs2.id=parameters.jobID and key = %s and value = %s)"
        valpart.append(str(key))
        valpart.append(str(arguments[key]))
    
    jobs = []


    PsE(cursor, "select id, srcURI, dstURI, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs2 where jobs2.state=%s" + keypart + " order by priority asc",valpart)
    for jobID, srcURI, dstURI, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority in cursor.fetchall():
            
        PsE(cursor, "select key, value from parameters where jobID=%s", (jobID,))
        fDict = dict([(p[0], p[1]) for p in cursor.fetchall()])

        jobs.append(Job2(jobID, srcURI, dstURI, fDict, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority))
    return jobs

def GetJobByID2(cursor, jobID):
    """

    
    """

    PsE(cursor, "select id, srcURI, dstURI, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs2 where id=%s", (jobID,))
    try:
        jobID, srcURI, dstURI, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority = cursor.fetchone()
    except TypeError:
        # No jobs matching id
        return None
    PsE(cursor, "select key, value from parameters where jobID=%s", (jobID,))
    fDict = dict([(p[0], p[1]) for p in cursor.fetchall()])

    job = Job2(jobID, srcURI, dstURI, fDict, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority)
    if not job:
        return None

    return job



