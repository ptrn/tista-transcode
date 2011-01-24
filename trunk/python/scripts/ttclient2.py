#! /usr/bin/python

import math, sys, urllib, urllib2, time, tempfile, os, httplib, stat, shutil, socket, subprocess, json, urlparse, datetime, mimetypes
import ttc.pretext

def prepare_field(key, value, B):
    L = []
    L.append('--' + B)
    L.append('Content-Disposition: form-data; name="%s"' % key)
    L.append('')
    L.append(value)  
    return L  

def prepare_file(key, filename, B):
    L = []
    L.append('--' + B)
    L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
    L.append('Content-Type: %s' % (mimetypes.guess_type(filename)[0] or 'video/mp4'))
    L.append('')
    L.append('')
    return L  

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
        self.baseURL  = baseURL
        self.recipe   = None
        self.execPath = None
        self.cmd      = None

    def GetRecipe(self):
        return self.recipe

    def CanDo(self, option):
        return False
      
    def UpdateProgress(self, jobID, numBytes):
        url = "%sjobs/update?%s" % (self.baseURL, urllib.urlencode((("id", jobID), ("b", numBytes))))
        urllib2.urlopen(url)

    def Transcode(self, root, jobID, inPath, outPath, options={}, defaults={}):
        cmd = self.GetCMD(inPath, outPath, options, defaults)
        sys.stderr.write("> %s \n" % " ".join(cmd))
        proc = subprocess.Popen(self.GetCMD(inPath, outPath, options, defaults))

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
            raise TTTranscodingError, "Transcoder returned error code %i" % retCode

    def Download(self, root, srcURI):
        if srcURI.startswith("file"):
            return urlparse.urlparse(srcURI).path

        outPath = os.path.join(root, "original")
        fOut = open(outPath, "wb")
        fIn = urllib2.urlopen(srcURI)

        fSize  = int(fIn.headers['Content-Length'])

        sys.stderr.write(datetime.datetime.now().strftime("[%d %b %H:%M] ttclient ") + "Downloading ")

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

    def Upload(self, root, inPath, dstURI, jobID, format):
        """
        Extract scheme, host, port, path etc from dstURI 
        If scheme is file, just copy or move the file locally
        Else use extracted parts to do the connection
        """
        parsedURI = urlparse.urlparse(dstURI)
        outPath   = parsedURI.path
        sys.stderr.write(datetime.datetime.now().strftime("[%d %b %H:%M] ttclient ") + "Upload from %s to %s\n" % (inPath, outPath))
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

        if parsedURI.hostname.startswith("s3.amazonaws"):
            basename = os.path.dirname(outPath)
            filename = os.path.basename(outPath)

            BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
            CRLF = '\r\n'
            L = []
            L.extend(prepare_field("key", "${filename}", BOUNDARY))
            L.extend(prepare_field("acl", "public-read", BOUNDARY))
            L.extend(prepare_field("content-type", (mimetypes.guess_type(filename)[0] or format), BOUNDARY))
            L.extend(prepare_field("AWSAccessKeyId", "AKIAI37KHFCWAVFHJQKQ", BOUNDARY))
            L.extend(prepare_field("policy", "ewogICJleHBpcmF0aW9uIjogIjIwMzAtMDEtMDFUMTI6MDA6MDAuMDAwWiIsCiAgImNvbmRpdGlvbnMiOiBbCiAgICB7ImJ1Y2tldCI6ICJkb2tmaWxtLXJhd191cCIgfSwKICAgIHsiYWNsIjogInB1YmxpYy1yZWFkIiB9LAogICAgWyJzdGFydHMtd2l0aCIsICIka2V5IiwgIiJdLAogICAgWyJzdGFydHMtd2l0aCIsICIkQ29udGVudC1UeXBlIiwgIiJdLAogIF0KfQo=",
                                   BOUNDARY))
            L.extend(prepare_field("signature", "48WiDbaPCX8qWKMonL3nhM3XcPg=", BOUNDARY))
            L.extend(prepare_file("file", filename, BOUNDARY))
 
            LT = []
            LT.append('')
            LT.append('--' + BOUNDARY + '--')
            LT.append('')

            body = CRLF.join(L)
            tail = CRLF.join(LT) 

            content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
            conn.putrequest('POST', basename)
            conn.putheader('content-type', content_type)
            conn.putheader('content-length', str(len(body) + fSize + len(tail)))
            conn.endheaders()

            """
            send fields
            """
            conn.send(body)

            """
            send file content
            """
            inFile = open(inPath, "rb")
            sys.stderr.write(datetime.datetime.now().strftime("[%d %b %H:%M] ttclient ") + "Uploading ")

            prevTick = -100
            bytesWritten = 0
            while True:
                s = inFile.read(1024 * 128)
                if not s:
                    break
                conn.send(s)
                bytesWritten += len(s)

                percent = ((bytesWritten * 100.0) / fSize)
                if percent - prevTick >= 2.5:
                    sys.stderr.write("=")
                    prevTick = percent
            sys.stderr.write("\n")

            """
            send terminating boundary
            """
            conn.send(tail)

            resp = conn.getresponse()

            if (resp.status / 100) != 2:
                raise TTUploadError, "HTTP error %i during s3 upload." % (resp.status)
            arg = "%s" % urllib.urlencode([("id",jobID)])
            urllib2.urlopen("%sjobs/finish?%s" % (self.baseURL,arg))
            return


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

class VLC(Transcoder):
    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)

        if os.path.exists(self.linuxVLC):
            self.execPath = self.linuxVLC
            self.recipe = "linux VLC"
        elif os.path.exists(self.macVLC):
            self.execPath = self.macVLC
            self.recipe = "mac VLC"

    def CanDo(self, options):
        if self.execPath == None: return False
        return False


    def GetCMD(self, inPath, outPath, options={}, defaults={}):
        # downURL = os.path.join(self.baseURL, "jobs", "download", self.jobID, "0")
        return (self.execPath,"-v",
          "--sout", 
          "#transcode{vcodec=ogg,vb=1920,deinterlace,width=640,height=480,vcodec=theora,acodec=vorbis,ab=128,aenc=vorbis}:standard{access=file:,mux=ogg,dst=%s}" % outPath,
          inPath,
          "vlc://quit")

    def Glue(self, root,sources,target): 
        ttc.pretext.glueOGGPretext(root,sources, target)

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
        if self.execPath == None: return False
        if options.get('format','ogg') == 'ogg': return True   # If no other format is given, default to ogg
        return False
          
    def GetCMD(self, inPath, outPath, options={}, defaults={}):
        return (self.execPath, '-o', outPath, 
            '-x', options.get('width',defaults.get('width','480')),
            '-y', options.get('height',defaults.get('height','320')),
            '--two-pass', 
            '-V', options.get('vbitrate',defaults.get('vbitrate','1024')),  
            '-A', options.get('abitrate','64'), 
            '-c', '2', 
#            '-H', '44100', 
            '-F', '25', 
            inPath)

    def Glue(self, root,sources,target): 
        ttc.pretext.glueOGGPretext(root,sources, target)


class Handbrake(Transcoder):
    correct = {'h.264':'x264', 'aac':'faac'}

    def __init__(self, baseURL):
        Transcoder.__init__(self, baseURL)
        self.execPath ="HandBrakeCLI"
        self.recipe = "Handbrake"

    def CanDo(self, options):
        if self.execPath == None: return False
#        if options.get('format','') == 'ogg': return True 
        if options.get('format','') == 'mp4': return True 
        if options.get('format','') == 'mkv': return True 
        return False
          
    def GetCMD(self, inPath, outPath, options={}, defaults={}):
        return (self.execPath, '-i', inPath,'-o', outPath, 
            '-f',  options.get('format','mp4'), 
            '-e',  self.correct.get(options.get('vcodec','h.264'),options.get('vcodec','x264')),
            '-E',  self.correct.get(options.get('acodec','aac')),
            '-w',  options.get('width',defaults.get('width','480')),
            '-l',  options.get('height',defaults.get('height','320')),
            '--vb', options.get('vbitrate','1024'), 
            '--ab', options.get('abitrate','64'), 
#            '-R', '44100',  # samplerate
            '-r', '25')

    def Glue(self,root,sources,target): 
        ttc.pretext.glueMP4Pretext(root,sources, target)

def GetTranscoderJob(transcoderList, jobs):
    for d in jobs:
        for t in transcoderList:
            if t.CanDo(d):
                return(t,d)
    raise TTNoJobsAvailableError

def GetInfo(path):
    command = ["ffmpeg2theora", "--info", path]
    proc    = proc = subprocess.Popen(command,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret     = proc.communicate()[0]
    finfo   = json.loads(ret)
    if len(finfo[u"video"]) < 1: finfo[u"video"] = [{}]
    if u"bitrate" not in finfo[u"video"][0]: finfo[u"video"][0][u"bitrate"] = finfo[u"bitrate"]
    if len(finfo[u"audio"]) < 1: finfo[u"audio"] = [{}]
    return finfo


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
    imgURI = ad[u"imgURI"]
    imgDur = ad[u"imgDuration"]
    sepDur = ad[u"separation"]

    format = d[u"format"]

    sys.stderr.write(datetime.datetime.now().strftime("[%d %b %H:%M] ttclient ") + "%s will transcode from %s to %s\n" % (recipe,srcURI,dstURI))

    da = {};
    try:
        inPath = transcoder.Download(root, srcURI)

# Get properties of src 
        info = GetInfo(inPath)
        print info
        defWidth = info[u"video"][0][u"width"]
        defHeight = info[u"video"][0][u"height"]
        defVBitrate = info[u"video"][0][u"bitrate"]
        defABitrate = info[u"audio"][0][u"bitrate"]
# Get wanted properties
        width  = d.get("width","%d" % defWidth)
        height = d.get("height","%d" % defHeight)
        vbitrate  = d.get("vbitrate", "%f" % defVBitrate)
        abitrate  = d.get("abitrate", "%f" % defABitrate)

        da["width"] = width;
        da["height"] = height;
        da["vbitrate"] =vbitrate;
        da["abitrate"] = abitrate;

        if imgURI != "None":
          print imgURI
          imgPath = transcoder.Download(root, imgURI)
        else:
          imgPath = False
    except Exception as e:
        arg = "%s" % urllib.urlencode([("id",jobID)])
        urllib2.urlopen("%sjobs/error?%s" % (baseURL,arg))
        raise TTDownloadError, e
    else:
      try:
        outPath      = os.path.join(root, "transcoded")
        transcoder.Transcode(root, jobID, inPath, outPath, d, da)
        if imgPath:
          soundPath    = "silence.mp3"
          textPath     = os.path.join(root, "pretext")
          blankPath    = os.path.join(root, "blank")
          outTextPath  = os.path.join(root, "pretext2")
          outBlankPath = os.path.join(root, "blank2")
          resPath      = os.path.join(root, "encapsulated")
          ttc.pretext.makeMP4Pretext(root, float(imgDur), imgPath, soundPath, textPath, vbitrate, abitrate, width, height)
          ttc.pretext.makeMP4Pretext(root, float(sepDur), False, soundPath, blankPath, vbitrate, abitrate, width, height)
          transcoder.Transcode(root, jobID, textPath, outTextPath, d, da)
          transcoder.Transcode(root, jobID, blankPath, outBlankPath, d, da)
          transcoder.Glue(root,[outTextPath, outBlankPath, outPath, outBlankPath, outTextPath], resPath)
        else:
          resPath = outPath 
      except Exception as e:
        arg = "%s" % urllib.urlencode([("id",jobID)])
        urllib2.urlopen("%sjobs/error?%s" % (baseURL,arg))
        raise TTTranscodingError, e
      else:
        try:
            transcoder.Upload(root, resPath, dstURI, jobID, "video/%s" % (format,))
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
    print transcoderList[0].GetRecipe()
    print transcoderList[1].GetRecipe()

    while True:
        try:
            ProcessOneJob(baseURL, transcoderList)
        except TTNoJobsAvailableError:
            sys.stderr.write(datetime.datetime.now().strftime("[%d %b %H:%M] ttclient ") + "No jobs available\n")
            time.sleep(300)
        except TTDownloadError, why:
            sys.stderr.write(datetime.datetime.now().strftime("[%d %b %H:%M] ttclient ") + "Download error. %s\n" % why)
            time.sleep(10)
        except TTUploadError, why:
            sys.stderr.write(datetime.datetime.now().strftime("[%d %b %H:%M] ttclient ") + "Upload error. %s \n" % why)
            time.sleep(10)
        except TTTranscodingError, why:
            sys.stderr.write(datetime.datetime.now().strftime("[%d %b %H:%M] ttclient ") + "Transcoding error: Job did not finish. %s\n" % why)
        else:
            time.sleep(10)

if __name__ == "__main__":
    Main()
