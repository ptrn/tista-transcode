#! /usr/bin/python
# -*- coding: utf-8; -*-

"""

This module defines classes, functions and database tables for
manipulating users. Also includes authentication functions.

"""

import os, stat, tempfile, subprocess, shutil

import psycopg2, PIL.Image, PIL.ImageOps

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

def GetJobByID(cursor, jobID):
    """

    Returns details of next job and marks it as active. If no jobs are
    available, None is returned.
    
    """

    PsE(cursor, "select id, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority from jobs where id=%s", (jobID,))
    jobID, dstPath, recipe, state, creationTime, workerAddress, workerStartTime, workerHeardFrom, workerRelativeProgress, priority = cursor.fetchone()

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
