#! /usr/bin/python

import sys, urllib, urllib2, time, tempfile, os, httplib, stat, shutil, socket, subprocess

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

    def UpdateProgress(self, jobID, numBytes):
        url = "%sjobs/update?%s" % (self.baseURL, urllib.urlencode((("id", jobID), ("b", numBytes))))
    
    def Transcode(self, root, jobID):
        inPath  = os.path.join(root, "original")
        outPath = os.path.join(root, "transcoded")

        proc = subprocess.Popen(self.GetCMD(inPath, outPath))

        lastUpdate = time.time()

        while True:
            retCode = proc.poll()
            if retCode != None:
                break

            now = time.time()
            if now - lastUpdate >= 60:
                if os.path.exists(outPath):
                    self.UpdateProgress(jobID, os.stat(outPath)[stat.ST_SIZE])
                lastUpdate = now
            
            time.sleep(1)

        if retCode != 0:
            raise TTTranscodingError, "VLC returned error code %i" % retCode

    def Download(self, root, baseURL, jobID, numFiles):
        fOut = open(os.path.join(root, "original"), "wb")

        url = os.path.join(baseURL, "jobs/download/")

        for i in xrange(0, numFiles):
            fIn = urllib2.urlopen("%s/%s/%i" % (url, jobID, i))

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

    def Upload(self, root, baseURL, jobID):
        url = os.path.join(baseURL, "jobs/upload/")
        
        # We need to do this ourselves, since we post raw, binary data
        hostAndPort = url.split("/")[2]
        try:
            host, port = hostAndPort.split(":")
        except ValueError:
            host = hostAndPort
            port = 80
        else:
            port = int(port)

        inPath = os.path.join(root, "transcoded")
        fSize = os.stat(inPath)[stat.ST_SIZE]

        conn = httplib.HTTPConnection(host, port)
        conn.connect()
        conn.putrequest('POST', '/ttc/jobs/upload/%s' % jobID)
        conn.putheader('content-type', 'application/octet-stream')
        conn.putheader('content-length', str(fSize))
        conn.endheaders()

        inFile = open(inPath, "rb")
        while True:
            s = inFile.read(1024 * 128)
            if not s:
                break
            conn.send(s)

        resp = conn.getresponse().status
        if resp != 200:
            raise TTUploadError, "HTTP error %i during upload" % resp

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

    def GetCMD(self, inPath, outPath):
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

    def GetCMD(self, inPath, outPath):
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
            
    def GetCMD(self, inPath, outPath):
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

    def GetCMD(self, inPath, outPath):
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
            
    def GetCMD(self, inPath, outPath):
        return (self.execPath, '--width', '384', '--height', '224', '--sync', '-o', outPath, inPath)

def ProcessOneJob(baseURL, transcoderMapping):
    root = tempfile.mkdtemp(prefix = 'ttc-')

    arguments = "%s" % urllib.urlencode([("r", r) for r in transcoderMapping.keys()])
    assignURL = os.path.join(baseURL, "jobs/assign_next_job?", arguments)
    if arguments == "":
        sys.stderr.write('Transcoding error: No transcoders available\n')
        sys.exit(1)


    jobDesc = urllib2.urlopen(assignURL).read().strip()

    if not jobDesc:
        raise TTNoJobsAvailableError

    jobID, recipe, numSrcPaths = jobDesc.split()
    numSrcPaths = int(numSrcPaths)

    transcoder = transcoderMapping[recipe]
    
    try:
        transcoder.Download(root, baseURL, jobID, numSrcPaths)
        transcoder.Transcode(root, jobID)
    except TTTranscodingError:
        sys.stderr.write('Transcoding error: Job was not submitted\n')
    else:
        try:
            transcoder.Upload(root, baseURL, jobID)
        except socket.error:
            sys.stderr.write('Upload error: Job was not submitted\n')

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

def Main():
    try:
        baseURL = sys.argv[1]
    except IndexError:
        sys.stderr.write('Usage: %s <base url>\n' % sys.argv[0])
        sys.exit(1)

    if not baseURL.endswith("/"):
        baseURL += "/"

    transcoderMapping = GetTranscoderMapping(baseURL)

    while True:
        try:
            ProcessOneJob(baseURL, transcoderMapping)
        except TTNoJobsAvailableError:
            sys.stderr.write("No jobs available\n")
            time.sleep(300)
        except TTDownloadError:
            sys.stderr.write("Download error\n")
            time.sleep(300)
        else:
            time.sleep(10)

if __name__ == "__main__":
    Main()
