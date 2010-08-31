# -*- coding: utf-8; -*-

"""

Job handling (user interface and RPC)

"""

import time, urllib, urllib2, os, stat, urlparse, json

import mod_python.util

from mod_python import apache

import ttc.model.jobs

import ttc.view.web

from ttc.view.web import Page, EH


class Help(Page):
    """

    Deliever a human-readable help-page.
    HTTP-query arguments:
    Used by  : CMS (Content Manager System)

    """
    
    path = "/ttc/help"

    showDebug = False

    def Main(self):
        pathMapping = dict([(c.path, c) for c in globals().values() if type(c) is type(Page) and issubclass(c, Page) and c is not Page and isinstance(c.path, str)])
        s = "<h2>Usage:</h2><ol>"
        for c in pathMapping:
            s = s + "<li>" + c
            if isinstance(pathMapping[c].args, str):
              s += " ? " + pathMapping[c].args
            s += "</li>"
        s += "</ol>" 
        html = "<html><head><title>Tista Transcoding</title></head><body><h1>Tista Transcoding Job Management</h1>%s</body></html>" % s
        self.SendHeader("text/html")
        self.Write(html)

        return apache.OK

class AddOneJob(Page):
    """

    HTTP-handler requesting a transcoding job.
    HTTP-query arguments:
      src:
        srcuri   : URI, file or http, of an item that should be transcoded
        imguri   : URI, file or http, of an image that should be added at the front and back of the resulting item
        imgduration : length in seconds (with decimals) of the added image
        separation  = length in seconds (with decimals) of the periode between the image and the video
      destination format:
        format      
        vcodec     
        acodec     
        vbitrate   
        abitrate   
        width      
        height     
      video options
        aspectratio
        interlace 
        fieldorder 
    Returns:
        jobid
        srcuri
        dsturi
    Used by  : CMS (Content Manager System)

    """

    
    path = "/ttc/jobs/add_one_job"
    args = 'srcuri=file://path/file&format=mp4&vcodec=h.264&acodec=aac&vbitrate=1024&abitrate=128&width=640&height=480'

    showDebug = False

    def Main(self):
        self.SendHeader("application/json")
        try:
            form = dict(mod_python.util.FieldStorage(self.req))
            srcURI = form.pop("srcuri") # should uridecode this
            imgURI = form.pop("imguri") # should uridecode this
            imgDur = float(form.pop("imgduration","1.0"))
            sepDur = float(form.pop("separation","1.0"))
            outExt = form.get("format","ogg")
        except:
            self.req.status = apache.HTTP_BAD_REQUEST 
            self.Write("{\n  \"Error\" : \"Parameter error\",\n  \"Suggestion\" : \"Missing srcuri\"\n}\n\n")
            return apache.OK
   
        cfg      = self.req.config
        cache    = cfg["path"]["cache"]
        try: 
            dstURI   = ttc.model.jobs.CreateDstURI(cfg, srcURI, self.req.hostname, outExt)
        except:
            self.req.status = apache.HTTP_CONFLICT  # Must set status before calling write !
            self.Write("{\n  \"Error\" : \"Job not created\",\n  \"Suggestion\" : \"Transcoder cannot read user files\",\n  \"srcURI\" : \"%s\"\n}\n" % (srcURI, ))
            return apache.OK

        job = ttc.model.jobs.AddOneJob(self.req.cursor, srcURI, dstURI, imgURI, imgDur, sepDur, cache, form)
        if job:
            self.Write("{\n  \"id\" : \"%s\",\n  \"srcURI\" : \"%s\",\n  \"dstURI\" : \"%s\"\n}\n" % (job.id,job.srcURI,job.dstURI))
            self.req.conn.commit()
            return apache.OK
        else:
            self.req.status = apache.HTTP_CONFLICT  # Must set status before calling write !
            self.Write("{\n  \"Error\" : \"Job not created\",\n  \"Suggestion\" : \"Maybe duplicate\",\n  \"srcURI\" : \"%s\",\n  \"dstURI\" : \"%s\"\n}\n" % (srcURI, dstURI))
            self.req.conn.rollback()
            return apache.OK

class GetJobList(Page):
    """

    HTTP-handler providing a list of waiting transcoding jobs.
    HTTP-query arguments:
      destination format: used for filtering available jobs
        format      
        vcodec     
        acodec     
        vbitrate   
        abitrate   
        width      
        height     
    Returns:
      If jobs are waiting: Job list in JSON
      If job not available: Status code / JSON-description
    Used by  : Transcoding client

    """

    
    path = "/ttc/jobs/get_job_list"
    args = 'format=mp4&vcodec=h.264&acodec=aac&vbitrate=1024&abitrate=128&width=640&height=480'

    showDebug = False

    def Main(self):
        form = dict(mod_python.util.FieldStorage(self.req))
        state = form.pop("state",None)

        cfg      = self.req.config

        jobs = ttc.model.jobs.GetJobsByParams(self.req.cursor, state, form )
        self.SendHeader("application/json")
        if jobs:
            jsonList = []
            for j in jobs:
                jsonDict = dict(j.fDict)
                jsonDict["id"] = j.id
                jsonList.append(jsonDict) 
            self.Write(json.dumps(jsonList))
            """
            self.Write("[")
            d = ",".join(["\n {%s\n  %s\n }" % (
                    "\n  \"id\" : \"%s\"," % (j.id),
                    ",\n  ".join(["\"%s\" : \"%s\"" % (k,v) for k,v in j.fDict.iteritems()])) for j in jobs]) 
            self.Write("%s" % d) 
            self.Write("\n]\n")
            """
            return apache.OK
        else:
            self.req.status = apache.HTTP_NOT_FOUND # Must set status before calling write !
            self.Write("{ \"Error\" : \"Jobs not found\"  }\n\n\n")
            return apache.OK
#            raise apache.SERVER_RETURN(apache.HTTP_NOT_FOUND)
#            return apache.HTTP_NOT_FOUND

class AssignJob(Page):
    """

    HTTP-handler assigning a transcoding job to a client.
    HTTP-query arguments:
      id: identifier from the previously transmitted list of available jobs. 32 hexadecimal digits
    Returns:
      If job is available: Source and destination uri in JSON
      If job not available: Status code / JSON-description
    Used by  : Transcoding client

    """
   
    path = "/ttc/jobs/assign_job"
    args = 'id=xxxxxx...'

    showDebug = False

    def Main(self):
        form  = mod_python.util.FieldStorage(self.req)
        jobID = form["id"].value
 
        cfg   = self.req.config
        myHost = self.req.hostname
        self.SendHeader("application/json")
        job   = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)
        if job is None:
            return ReturnError(self, apache.HTTP_NOT_FOUND, "Job not found", "Job ID not in database")
        elif job.state == 'w' or job.state == 'e': # assign waiting jobs and allow retry on failed jobs
            job.Assign(self.req.cursor, self.req.get_remote_host(apache.REMOTE_NOLOOKUP))
            self.Write("{\n  \"srcURI\" : \"%s\",\n  \"dstURI\" : \"%s\",\n  \"imgURI\" : \"%s\",\n  \"imgDuration\" : \"%s\",\n  \"separation\" : \"%s\"\n}\n" % (job.GetDownloadURI(cfg,myHost),job.GetUploadURI(cfg,myHost),job.GetImageURI(cfg,myHost), job.imgDur, job.sepDur))
        elif job.state is 'i':
            return ReturnError(self, apache.HTTP_CONFLICT, "Cannot assign job", "Job busy")
        elif job.state is 'f':
            return ReturnError(self, apache.HTTP_CONFLICT, "Cannot assign job", "Job finished")
        else:
            return ReturnError(self, apache.HTTP_INTERNAL_SERVER_ERROR, "Database error", "Unknown job state %s" % job.state)
	return apache.OK

class GetJobInfo(Page):
    """

    Get info from the job database.
    HTTP-query arguments:
      id: identifier from the previously transmitted list of available jobs. 32 hexadecimal digits
    Returns:
      If job is available: Job properties and state in JSON format
        id
        state
        srcURI
        dstURI
      If job not available: Status code / JSON-description
    Used by  : Transcoding client

    """
   
    path = "/ttc/jobs/get_job_info"
    args = 'id=xxxxxx...'

    showDebug = False

    def Main(self):
        form  = mod_python.util.FieldStorage(self.req)
        jobID = form["id"].value
 
        cfg   = self.req.config
        myHost = self.req.hostname
        job   = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)
        if job is None:
            return self.ReturnError(apache.HTTP_NOT_FOUND, "Job not found", "Job ID not in database")
        else:
            self.SendHeader("application/json")
            self.Write(job.GetBasics())
            return apache.OK
 
class DownloadJob(Page):
    """

    Used by clients to download the source item of a job
    
    """

    path = "/ttc/jobs/download"

    showDebug = False

    def Main(self):
        (jobID,) = self.req.uri.split("/")[-1:]
        job = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)
        f = urllib2.urlopen(job.srcURI)
        l = f.info().getheader("content-length")
        self.req.headers_out["Content-Length"] = l
        self.SendHeader("application/octet-stream")

        while True:
            s = f.read(128 * 1024)
            if not s:
                break
            self.Write(s)
        return apache.OK

class ImageloadJob(Page):
    """

    Used by clients to download the encapsulating image of a job
    
    """

    path = "/ttc/jobs/imgload"

    showDebug = False

    def Main(self):
        (jobID,) = self.req.uri.split("/")[-1:]
        job = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)
        f = urllib2.urlopen(job.imgURI)
        l = f.info().getheader("content-length")
        self.req.headers_out["Content-Length"] = l
        self.SendHeader("image/png")

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

    path = "/ttc/jobs/upload"

    showDebug = False

    def Main(self):
        jobID = self.req.uri.split("/")[-1]

        if jobID == 0:
          return ReturnError(self, apache.HTTP_NOT_FOUND, "Job not found", "Missing job id")
        job = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)
        if not job:
          return ReturnError(self, apache.HTTP_NOT_FOUND, "Job not found", "Job deleted from transcoder database")
        
        if 'content-length' in self.req.headers_in: 
          fSize = int(self.req.headers_in['content-length'])
        else:
          return ReturnError(self, apache.HTTP_LENGTH_REQUIRED, "Cannot receive data", "No content-length header")
        try:
          dstPath  = job.GetUploadPath(self.req.config)
        except:
          return ReturnError(self, apache.HTTP_CONFLICT, "Error retrieving directory", "No permission")
        try:
          f = open(dstPath + ".ttc", "wb")
        except:
          return ReturnError(self, apache.HTTP_NOT_FOUND, "Error writing result file", "No permission")

        bytesReceived = 0
        while bytesReceived < fSize:
            s = self.req.read(min(1024 * 128, fSize - bytesReceived))
            f.write(s)
            bytesReceived += len(s)

        f.close()

        os.rename(dstPath + ".ttc", dstPath)

        job.SetFinished(self.req.cursor)

        return apache.OK
    
class FinishJob(Page):
    """

    Used by clients to inform server that a job is finished, when no upload is needed
    
    """

    path = "/ttc/jobs/finish"
    args = 'id=xxxxxx...'

    showDebug = False

    def Main(self):
        form = mod_python.util.FieldStorage(self.req)
        jobID = form["id"].value
        if jobID == 0:
          return ReturnError(self, apache.HTTP_NOT_FOUND, "Job not found", "Missing job id")
        job = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)
        if not job:
          return self.ReturnError(apache.HTTP_NOT_FOUND, "Job not found", "Job deleted from transcoder database")
        job.SetFinished(self.req.cursor)
        return apache.OK

class ErrorJob(Page):
    """

    Used by clients to inform server that a job has terminated irregularly
    
    """

    path = "/ttc/jobs/error"
    args = 'id=xxxxxx...'

    showDebug = False

    def Main(self):
        form = mod_python.util.FieldStorage(self.req)
        jobID = form["id"].value
        if jobID == 0:
          return ReturnError(self, apache.HTTP_NOT_FOUND, "Job not found", "Missing job id")
        job = ttc.model.jobs.GetJobByID(self.req.cursor, jobID)
        if not job:
          return self.ReturnError(apache.HTTP_NOT_FOUND, "Job not found", "Job deleted from transcoder database")
        job.SetError(self.req.cursor)
        return apache.OK

class UpdateProgress(Page):
    """

    Used by clients to upload a job
    
    """

    path = "/ttc/jobs/update"
    args = 'id=xxxxxx...&b=nn'

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
    args = 'id=xxxxxx...'

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
            sizeS = " %i bytes" % job.workerRelativeProgress
        else:
            sizeS = ""

        return '<div class="job"><img src="snapshot?id=%s" alt="" /><strong>%s</strong> %s%s</div>\n' % (job.id, job.GetType(), os.path.split(job.dstURI)[-1], sizeS)

    def JobsToHTML(self, jobs):
        html  = '<div class="group">\n'
        html += '\n'.join([self.JobToHTML(j) for j in jobs])
        html += '</div>\n'

        return html

    def Main(self):
        waiting    = ttc.model.jobs.GetJobsByState(self.req.cursor, 'w')
        inProgress = ttc.model.jobs.GetJobsByState(self.req.cursor, 'i')
        finished   = ttc.model.jobs.GetJobsByState(self.req.cursor, 'f')
        failed     = ttc.model.jobs.GetJobsByState(self.req.cursor, 'e')

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

    <h2>Waiting</h2>

    %s

    <h2>In progress</h2>

    %s

    <h2>Finished</h2>

    %s

    <h2>Erroneous</h2>

    %s

  </body>
</html>
""" % (self.JobsToHTML(waiting), self.JobsToHTML(inProgress), self.JobsToHTML(finished), self.JobsToHTML(failed))

        self.SendHeader()
        self.Write(html)

        return apache.OK
