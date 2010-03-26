#! /usr/bin/python

import sys, urllib, urllib2, time, tempfile, os, httplib, stat, shutil, socket, subprocess, json, urlparse

# *** Should be imported from tt.py
class TTError(Exception):
    pass

# *** Should be imported from tt.py
class TTNoJobsAvailableError(TTError):
    pass

# *** Should be imported from tt.py
class TTTranscodingError(TTError):
    pass

# *** Should be imported from tt.py
class TTDownloadError(TTError):
    pass

# *** Should be imported from tt.py
class TTUploadError(TTError):
    pass

class Transcoder(object):
    linuxVLC      = "/usr/bin/vlc"
    macVLC        = "/Applications/VLC.app/Contents/MacOS/VLC"
    ffmpeg2theora = "ffmpeg2theora"
    
    def __init__(self, baseURL):
        self.baseURL = baseURL
        self.recipe = None
        self.execPath = None
        self.cmd = None

    def GetRecipe(self):
        return self.recipe

    def CanDo(self, option):
        return False
      
    def UpdateProgress(self, jobID, numBytes):
        url = "%sjobs/update?%s" % (self.baseURL, urllib.urlencode((("id", jobID), ("b", numBytes))))
        urllib2.urlopen(url)
        print url

    def Transcode(self, root, jobID, inPath, options={}):
        outPath = os.path.join(root, "transcoded")

        proc = subprocess.Popen(self.GetCMD(inPath, outPath, options))

        lastUpdate = time.time()

        while True:
            retCode = proc.poll()
            if retCode != None:
                break
            now = time.time()
            if now - lastUpdate >= 60:
                if os.path.exists(outPath):
                    part = os.stat(outPath)[stat.ST_SIZE]
                    self.UpdateProgress(jobID, part)
                lastUpdate = now
            
            time.sleep(1)

        if retCode != 0:
            raise TTTranscodingError, "VLC returned error code %i" % retCode

    def Download(self, root, srcURI):
        if srcURI.startswith("file"):
            return urlparse.urlparse(srcURI).path

        outPath = os.path.join(root, "original")
        fOut = open(outPath, "wb")

        fIn = urllib2.urlopen(srcURI)

        fSize  = int(fIn.headers['Content-Length'])

        sys.stderr.write("Downloading ")

        prevTick = -100
        bytesWritten = 0
        while True:
            s = fIn.read(1024 * 128)
            if not s:
                break
            fOut.write(s)
            bytesWritten += len(s)

            percent = ((bytesWritten * 100.0) / fSize)
            if percent - prevTick >= 2.5:
                sys.stderr.write("=")
                prevTick = percent
            
        fIn.close()

        sys.stderr.write(" 100%\n")
        
        if fSize != bytesWritten:
            raise TTDownloadError
        fOut.close()
        return outPath 

    def Upload(self, root, dstURI, jobID):
        """
        Extract scheme, host, port, path etc from dstURI 
        If scheme is file, just copy or move the file locally
        Else use extracted parts to do the connection
        """
        parsedURI = urlparse.urlparse(dstURI)
        inPath    = os.path.join(root, "transcoded")
        outPath   = parsedURI.path
        if parsedURI.scheme.startswith("file"):
            try:
                shutil.copy(inPath,outPath)
            except Exception as why :
                raise TTUploadError, "Error while copying to destination file: %s " % why
            arg = "%s" % urllib.urlencode([("id",jobID)])
            urllib2.urlopen("%sjobs/finish?%s" % (self.baseURL,arg))
            return

        host = parsedURI.hostname
        port = parsedURI.port
        if port is None:
            port = 80

        fSize = os.stat(inPath)[stat.ST_SIZE]

        conn = httplib.HTTPConnection(host, port)
        conn.connect()
#        conn.putrequest('POST', '/ttc/jobs/upload/%s' % jobID) # let server generate dstURI instead
        conn.putrequest('POST', outPath)
        conn.putheader('content-type', 'application/octet-stream')
        conn.putheader('content-length', str(fSize))
        conn.endheaders()

        inFile = open(inPath, "rb")
        while True:
            s = inFile.read(1024 * 128)
            if not s:
                break
            conn.send(s)

        resp = conn.getresponse()
        if resp.status != 200:
            s = resp.read().strip()
#            sys.stderr.write(s)
            pd = json.loads(s)
            raise TTUploadError, "HTTP error %i during upload. %s" % (resp.status, pd["Error"])

class StreamingTranscoder(Transcoder):
    """
    Base class for transcoders that don't need to perform separate
    download step
    """

    def Download(self, root, baseURL, jobID, numFiles):
        self.jobID = jobID

class iPhoneTranscoder(Transcoder):
    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)

        if os.path.exists(self.macVLC):
            self.execPath = self.macVLC
            self.recipe = "iPhone"

    def GetCMD(self, inPath, outPath):
        return (self.execPath, inPath, "-I", "dummy", "--sout", "#transcode{vcodec=mp4v,vb=1024,fps=25,deinterlace,width=480,height=320,acodec=mp4a,ab=128}:standard{access=file,mux=mp4,dst=%s}" % outPath, "vlc:quit")

class FMAASTranscoderHigh(StreamingTranscoder):
    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)

        if os.path.exists(self.linuxVLC):
            self.execPath = self.linuxVLC
            self.recipe = "FMAAS_high"
        elif os.path.exists(self.macVLC):
            self.execPath = self.macVLC
            self.recipe = "FMAAS_high"

    def GetCMD(self, inPath, outPath, options={}):
        downURL = os.path.join(self.baseURL, "jobs", "download", self.jobID, "0")
        return (self.execPath, downURL, "-I", "dummy", "--sout", "#transcode{vcodec=h264,vb=1920,deinterlace,width=640,height=480,acodec=mp4a,ab=128}:standard{access=file,mux=mp4,dst=%s}" % outPath, "vlc:quit")

class FMAASTranscoderLow(StreamingTranscoder):
    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)

        if os.path.exists(self.linuxVLC):
            self.execPath = self.linuxVLC
            self.recipe = "FMAAS_low"
        elif os.path.exists(self.macVLC):
            self.execPath = self.macVLC
            self.recipe = "FMAAS_low"

    def GetCMD(self, inPath, outPath):
        downURL = os.path.join(self.baseURL, "jobs", "download", self.jobID, "0")
        return (self.execPath, downURL, "-I", "dummy", "--sout", "#transcode{vcodec=h264,vb=896,deinterlace,width=640,height=480,acodec=mp4a,ab=128}:standard{access=file,mux=mp4,dst=%s}" % outPath, "vlc:quit")

class FMAASTranscoderAVIHigh(Transcoder):
    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)

        if os.path.exists(self.linuxVLC):
            self.execPath = self.linuxVLC
            self.recipe = "FMAAS_AVI_high"
        elif os.path.exists(self.macVLC):
            self.execPath = self.macVLC
            self.recipe = "FMAAS_AVI_high"

    def GetCMD(self, inPath, outPath):
        return (self.execPath, inPath, "-I", "dummy", "--sout", "#transcode{vcodec=h264,vb=1920,deinterlace,width=640,height=480,acodec=mp4a,ab=128}:standard{access=file,mux=mp4,dst=%s}" % outPath, "vlc:quit")

class FMAASTranscoderAVILow(Transcoder):
    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)

        if os.path.exists(self.linuxVLC):
            self.execPath = self.linuxVLC
            self.recipe = "FMAAS_AVI_low"
        elif os.path.exists(self.macVLC):
            self.execPath = self.macVLC
            self.recipe = "FMAAS_AVI_low"

    def GetCMD(self, inPath, outPath, options={}):
        return (self.execPath, inPath, "-I", "dummy", "--sout", "#transcode{vcodec=h264,vb=896,deinterlace,width=640,height=480,acodec=mp4a,ab=128}:standard{access=file,mux=mp4,dst=%s}" % outPath, "vlc:quit")

class TheoraTranscoder(Transcoder):
    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)

        try:
            proc = subprocess.Popen("ffmpeg2theora", stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        except OSError:
            pass
        else:
            if proc.wait() == 0:
                self.execPath ="ffmpeg2theora"
                self.recipe = "Theora"

    def CanDo(self, options):
        if options.get('format','') == 'ogg': return True 
        return False
          
    def GetCMD(self, inPath, outPath, options={}):
        return (self.execPath, '--sync', '-o', outPath, inPath)

class SNDPTheoraFromWMV(Transcoder):
    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)

        try:
            subprocess.Popen("ffmpeg2theora", stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        except OSError:
            pass
        else:
            self.execPath = self.ffmpeg2theora
            self.recipe = "SNDPTheoraFromWMV"

    def GetCMD(self, inPath, outPath, options={}):
        #downURL = os.path.join(self.baseURL, "jobs", "download", self.jobID, "0")
        #return (self.execPath, downURL, "-I", "dummy", "--sout", "#transcode{vcodec=h264,vb=1920,deinterlace,width=640,height=480,acodec=mp4a,ab=128}:standard{access=file,mux=mp4,dst=%s}" % outPath, "vlc:quit")
        return (self.execPath, '--sync', '--width', '384', '-o', outPath, inPath)

class SNDPTheoraTranscoder(Transcoder):
    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)

        try:
            proc = subprocess.Popen("ffmpeg2theora", stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        except OSError:
            pass
        else:
            if proc.wait() == 0:
                self.execPath ="ffmpeg2theora"
                self.recipe = "SNDPTheora"
            
    def GetCMD(self, inPath, outPath, options={}):
        return (self.execPath, '--width', '384', '--height', '224', '--sync', '-o', outPath, inPath)

class Handbrake(Transcoder):
    correct = {'h.264':'x264'}

    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)
        self.execPath ="HandBrakeCLI"
        self.recipe = "handbrake"

    def CanDo(self, options):
        if options.get('format','') == 'mp4': return True 
        if options.get('format','') == 'mkv': return True 
        return False
          
    def GetCMD(self, inPath, outPath, options={}):
        return (self.execPath, '-i', inPath,'-o', outPath, 
            '-f', self.correct.get(options.get('format','mp4'),options.get('format','mp4')), 
            '-e', self.correct.get(options.get('vcodec','h.264'),options.get('vcodec','h.264')))

def GetTranscoderJob(transcoderList, jobs):
    for d in jobs:
        for t in transcoderList:
            if t.CanDo(d):
                return(t,d)
    raise TTNoJobsAvailableError

def ProcessOneJob(baseURL, transcoderList):
    root = tempfile.mkdtemp(prefix = 'ttc-')

#    arguments = "%s" % urllib.urlencode([("format", f) for f in transcoderMapping.keys()])
    
    getjobURL = os.path.join(baseURL, "jobs/get_job_list?state=w")
    try:
        handle  = urllib2.urlopen(getjobURL)
        jobDesc = handle.read().strip()
    except urllib2.HTTPError, e:
        if e.code == 404:
            raise TTNoJobsAvailableError
        raise TTError

    l    = json.loads(jobDesc)
    while(True):
        if not l:
            raise TTNoJobsAvailableError
        transcoder,d  = GetTranscoderJob(transcoderList,l)
        l.remove(d)
        arg = "%s" % urllib.urlencode([("id",d[u"id"])])
        assignURL = os.path.join(baseURL, "jobs/assign_job?%s" % arg)
        print assignURL
        try:
            handle  = urllib2.urlopen(assignURL)
            jobDesc = handle.read().strip()
            break
        except urllib2.HTTPError, e: # job is probably busy
            continue
   
    jobID  = d[u"id"]
    recipe = transcoder.GetRecipe()

    ad     = json.loads(jobDesc)
    srcURI = ad[u"srcURI"]
    dstURI = ad[u"dstURI"]

    print "%s will transcode from %s to %s" % (recipe,srcURI,dstURI)
    

    try:
        inPath = transcoder.Download(root, srcURI)
        print inPath
    except Exception as e:
        arg = "%s" % urllib.urlencode([("id",jobID)])
        urllib2.urlopen("%sjobs/error?%s" % (baseURL,arg))
        raise TTDownloadError, e
    else:
      try:
        transcoder.Transcode(root, jobID, inPath, d)
      except Exception as e:
        arg = "%s" % urllib.urlencode([("id",jobID)])
        urllib2.urlopen("%sjobs/error?%s" % (baseURL,arg))
        raise TTTranscodingError, e
      else:
        try:
            transcoder.Upload(root, dstURI, jobID)
        except Exception as e:
            arg = "%s" % urllib.urlencode([("id",jobID)])
            urllib2.urlopen("%sjobs/error?%s" % (baseURL,arg))
            raise TTUploadError, e
 
    shutil.rmtree(root)
    

def GetTranscoderMapping(baseURL):
    d = {}
    ttype = type(Transcoder)

    #return dict([(c.path, c) for c in globals().values() if type(c) is type and issubclass(c, Page) and c is not Page and isinstance(c.path, str)])
    for c in globals().values():
        if type(c) is ttype and issubclass(c, Transcoder) and c is not Transcoder:
            transcoder = c(baseURL)
            recipe = transcoder.GetRecipe()

            if recipe:
                d[recipe] = transcoder

    return d

def GetTranscoderList(baseURL):
    l = []
    ttype = type(Transcoder)

    for c in globals().values():
        if type(c) is ttype and issubclass(c, Transcoder) and c is not Transcoder:
            transcoder = c(baseURL)
            l.append(transcoder)

    return l

def Main():
    try:
        baseURL = sys.argv[1]
    except IndexError:
        sys.stderr.write('Usage: %s <base url>\n' % sys.argv[0])
        sys.exit(1)

    if not baseURL.endswith("/"):
        baseURL += "/"

#    transcoderMapping = GetTranscoderMapping(baseURL)
    transcoderList = GetTranscoderList(baseURL)

    while True:
        try:
            ProcessOneJob(baseURL, transcoderList)
        except TTNoJobsAvailableError:
            sys.stderr.write("No jobs available\n")
            time.sleep(300)
        except TTDownloadError, why:
            sys.stderr.write("Download error. %s\n" % why)
            time.sleep(10)
        except TTUploadError, why:
            sys.stderr.write("Upload error. %s \n" % why)
            time.sleep(10)
        except TTTranscodingError, why:
            sys.stderr.write("Transcoding error: Job did not finish. %s\n" % why)
        else:
            time.sleep(10)

if __name__ == "__main__":
    Main()
