# -*- coding: utf-8; -*-

"""

Job handling (user interface and RPC)

"""

import time, urllib, os, stat

import mod_python.util

from mod_python import apache

import ttc.model.jobs

import ttc.view.web

from ttc.view.web import Page, EH

class AssignNextJob(Page):
    """

    Used by clients to be assigned a new job
    
    """

    path = "/ttc/jobs/assign_next_job"

    showDebug = False

    def Main(self):
        form = mod_python.util.FieldStorage(self.req)

        if type(form["r"]) == list:
            recipes = [e.value for e in form["r"]]
        else:
            recipes = [form["r"].value]

        job = ttc.model.jobs.AssignNextJob(self.req.cursor, self.req.get_remote_host(apache.REMOTE_NOLOOKUP), recipes)

        self.SendHeader("text/plain")

        if job:
            self.Write("%s %s %i\n" % (job.id, job.recipe, len(job.srcPaths)))

        return apache.OK

class DownloadJob(Page):
    """

    Used by clients to download a job
    
    """

    path = None #"/ttc/jobs/download"

    showDebug = False

    def Main(self):
        jobID, part = self.req.uri.split("/")[-2:]
        part = int(part)

        job = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)

        srcPath = sorted(job.srcPaths)[part]

        self.req.headers_out["Content-Length"] = str(os.stat(srcPath)[stat.ST_SIZE])
        self.SendHeader("application/octet-stream")

        f = open(srcPath, "rb")
        while True:
            s = f.read(128 * 1024)
            if not s:
                break
            self.Write(s)

        return apache.OK

class UploadJob(Page):
    """

    Used by clients to upload a job
    
    """

    path = None #"/ttc/jobs/upload"

    showDebug = False

    def Main(self):
        jobID = self.req.uri.split("/")[-1]

        job = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)

        fSize = int(self.req.headers_in['content-length'])

        dirPart = os.path.split(job.dstPath)[0]
        if not os.path.exists(dirPart):
            os.makedirs(dirPart)
        f = open(job.dstPath + ".ttc", "wb")

        bytesReceived = 0
        while bytesReceived < fSize:
            s = self.req.read(min(1024 * 128, fSize - bytesReceived))
            f.write(s)
            bytesReceived += len(s)

        f.close()

        os.rename(job.dstPath + ".ttc", job.dstPath)

        job.SetFinished(self.req.cursor)

        return apache.OK
    
class UpdateProgress(Page):
    """

    Used by clients to upload a job
    
    """

    path = "/ttc/jobs/update"

    showDebug = False

    def Main(self):
        form = mod_python.util.FieldStorage(self.req)

        jobID = form["id"].value
        numBytes = int(form["b"].value)

        job = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)
        job.UpdateProgress(self.req.cursor, numBytes)

        return apache.OK

class JobsSnapshot(Page):
    path = "/ttc/jobs/snapshot"

    showDebug = False

    def Main(self):
        form = mod_python.util.FieldStorage(self.req)
        jobID = form["id"].value

        # Generating snapshots on demand is recipe for
        # disaster. Should be done in a cron script.
        path = ttc.model.jobs.GetSnapshotPath(jobID, self.req.config["path"]["cache"])
        if os.path.exists(path):
            snapshot = open(path).read()
        else:
            job = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)
            job.TakeSnapshot(self.req.config["path"]["cache"])
            path = ttc.model.jobs.GetSnapshotPath(jobID, self.req.config["path"]["cache"])
            snapshot = open(path).read()

        self.SendHeader("image/jpeg")
        self.Write(snapshot)

        return apache.OK

class JobsMain(Page):
    path = "/ttc/jobs/"

    showDebug = False

    def JobToHTML(self, job):
        if job.workerRelativeProgress != None:
            sizeS = " %i%%" % job.workerRelativeProgress
        else:
            sizeS = ""

        return '<div class="job"><img src="snapshot?id=%s" alt="" /><strong>%s</strong> %s%s</div>\n' % (job.id, job.recipe, os.path.split(job.dstPath)[-1], sizeS)

    def JobsToHTML(self, jobs):
        html  = '<div class="group">\n'
        html += '\n'.join([self.JobToHTML(j) for j in jobs])
        html += '</div>\n'

        return html

    def Main(self):
        waiting    = ttc.model.jobs.GetJobs(self.req.cursor, 'w')
        inProgress = ttc.model.jobs.GetJobs(self.req.cursor, 'i')
        finished   = ttc.model.jobs.GetJobs(self.req.cursor, 'f')

        html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Jobs</title>
    <style type="text/css">
      body {
        background-color: black;
        color: white;
        font-family: Helvetica, sans-serif;
      }
      div.job {
        width:  96px;
        height: 96px;

        background-color: rgb(64, 64, 64);
        font-size: 10px;
        float: left;
        margin: 4px;
        opacity: 0.5;
      }
      div.job:hover {
        opacity: 1.0;
      }
      td.num {
        text-align: right;
      }
      img {
        width: 96px;
        vertical-align: top;
        margin: 0px 2px 0px 0px;
      }
      h2 {
        clear: both;
        padding-top: 1em;
      }
    </style>
  </head>
  <body>
    <h1>Jobs</h1>

    <h2>In progress</h2>

    %s

    <h2>Waiting</h2>

    %s

    <h2>Finished</h2>

    %s
  </body>
</html>
""" % (self.JobsToHTML(inProgress), self.JobsToHTML(waiting), self.JobsToHTML(finished))

        self.SendHeader()
        self.Write(html)

        return apache.OK
