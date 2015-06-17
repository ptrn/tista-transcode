# Technical Documentation Tista Transcode #

## Server ##

The TTC Server consists of a thin web interface and a sql database. The server is accessed by user applications (CMS etc) and by the TTC Client through the web interface. Direct access to the database may be necessary at regular intervals to remove old entries.

### Interface ###

Remote procedure calls understood by the server.

#### Add one job ####

```
/ttc/jobs/add_one_job?srcuri=file://path/file&format=mp4&vcodec=h.264&acodec=aac&vbitrate=1024&abitrate=128&width=640&height=480
```

Requests ttc to transcode the item located at url [file://path/file](file://path/file) to containerformat mp4 with videoformat h.264, sound format aac etc. Source URL (srcuri) may be file: or http:.

  * srcuri : url to the video that should be transcoded
  * format : requested containerformat, ogg or mp4
  * vcodec : requested videoformat, theora or h.264
  * acodec : requested audioformat vorbis or aac

Note that in the existing implementation, format will overrule vcodec and acodec. format=ogg will always give vcodec =theora and acodec=vorbis. format=mp4 will return vcodec=h.264 and acodec=aac

  * vbitrate : requested videobitrate. If this is not supplied, the transcoder will try to keep the current bitrate from the source video or choose a functioning replacement value.
  * abitrate : requested audiobitrate. If this is not supplied, the transcoder will try to keep the current bitrate from the source video or choose a functioning replacement value.
  * width : requested width. If this is not supplied, the transcoder will try to keep the current width from the source video or choose a functioning replacement value.
  * height : requested height. If this is not supplied,the transcoder will try to keep the current height from the source video or choose a functioning replacement value.
  * imguri : URL, file or http, to a picture in png-format that will be added in front of and in the end of the video document.
  * imgduration : duration in whole seconds of the added image
  * separation = duration in whole seconds of the period of black between the image and the video.

Return: text in application/json-format:

```
{
"id" : "xxxxxx...",
"srcURI" : "file://path/file",
"dstURI" : "file://path/file2"
}
```

where id is a 32-byte code used to identify the transcoding job in further communication.

Used by CMS.

#### Download ####

```
/ttc/jobs/download/xxxxxx...
```

Downloads a not yet transcoded video document from ttc server.

Return: File content

Used by ttc client.

#### Upload ####

```
/ttc/jobs/upload/xxxxxx...
```

Uploads a transcoded video document to the ttc server. The server will recognize the document as the product of a transcoding job identified by the id.

Used by ttc client.

#### Get Job info ####

```
/ttc/jobs/get_job_info ? id=xxxxxx...
```

Asks for information on a particular transcoding job.

Return: application/json following the pattern:

```
{
"id" : "xxxxxx...", 
"state" : "w", 
"srcURI" : "file://path/file",
"dstURI" : "file://path/file2"
"progress" : "0"
}
```

where state (w|i|f|e) indicates wether the job Waits in queue, is In progress, is Finished or has Error status. Pogress is the number of bytes written to the result document.

Used by CMS

#### Jobs ####

```
/ttc/jobs/
```

Returns a html page informing about what the ttc is doing: All jobs and their state.

Used by system administrator.

#### Snapshot ####

```
/ttc/jobs/snapshot ? id=xxxxxx...
```

Deprecated.

#### Help ####

```
/ttc/help
```

A short version of this documentation in html.

#### get Job List ####

```
/ttc/jobs/get_job_list?format=mp4&vcodec=h.264&acodec=aac&vbitrate=1024&abitrate=128&width=640&height=480
```

A list of all jobs in the database that follows certain conditions.

Return: json

```
[
{"id": "xxxxxx...", "format": "mp4"}, 
{"id": "xxxxxx...", "format": "ogg"}
]
```

Used by: ttc client wanting to do a job

#### Update ####

```
/ttc/jobs/update ? id=xxxxxx...&b=nn
```

Informing the server about how many bytes has been transcoded for a paricular job.

Used by : ttc client.

#### Assign job ####

```
/ttc/jobs/assign_job ? id=xxxxxx...
```

Informing the server that a ttc client has grabbed a job from the Waiting list.

Return: json on the form

```
{
"srcURI" : "file://path/file",
"dstURI" : "file://path/file2"
}
```

where file and file2 are the locations where the client may fetch and store the video document.

Used by : ttc client.

#### Error ####

```
/ttc/jobs/error ? id=xxxxxx...
```

Informing ttc server that a transcoding job has failed

Used by : ttc client.


#### Error ####

```
/ttc/jobs/finish ? id=xxxxxx... 
```

Informing ttc server that a transcoding job has terminated without known errors.

Used by : ttc client.

### Implementation ###

The server is implemented as a mod\_python module and a postgress sql database.
Configuration

The following entries are necessary in the apache configuration:

```
  <Directory /usr/local/tista-transcode/python/mod_python/>
              AddHandler python-program .py
              PythonHandler handler
              PythonDebug On
              PythonPath "['/usr/local/tista-transcode/python'] + sys.path"
              PythonOption ttcConfigPath "/usr/local/tista-transcode/config/film.cfg"
  </Directory>
```

```
  RewriteEngine on
  RewriteRule ^/ttc/(.*) /usr/local/tista-transcode/python/mod_python/handler.py/$1 [L]
```

The configuration file at ttcConfigPath is a python script looking like this:

```
# Network settings
network["host"]       = "film"
network["domain"]     = "hiof.no"
network["smtp"]       = "mailserver.hiof.no"
network["userscheme"] = "file"
network["clientscheme"] = "file"
```

```
# Path settings
path["html"]          = "/usr/local/tista-transcode/data/html"
path["scripts"]       = "/usr/local/tista-transcode/python/scripts"
path["cache"]         = "/var/lib/tista-transcode/cache"
path["base"]          = "/var/lib/tista-transcode"
path["storage"]       = "store"
```

```
# Database settings
database["name"]      = "tista-transcode"
database["adminUser"] = "root"
database["webUser"]   = "www-data"
```

```
# Debugging
debug["debugMode"]    = True
```

host/domain identifies the server running ttc.

userscheme = file means that the user application/cms has access to the ttc servers file system (alternative is http)

clientscheme = file means that the ttc clients have access to the ttc servers file system (alternative is http or s3)

clientscheme = s3 means that results from transcoding will be stored at amazones s3 storage

base is the path to the directory serving ttc web content. (When using s3, base should be empty.)

store is a sub directory where transcoded files will be put

## Client ##

### Implementation ###

The ttc client is implemented as a python script and the source is located in tista-transcode/python/scripts/ttclient2.py. It transcodes to ogg/theora and mp4/h.264, but does not necessarily use the most efficent transcoder.

For transcoding to mp4 Handbrake is used, while ogg/theora is created by ffmpeg2theora

The source consists of a series of transcoders, all being the subclasses of the Transcoder class. Each transcoder makes use of an external transcoder tool, like VLC, ffmpeg2theora, Handbrake etc, being called as subprocesses with various arguments.

Most of these transcoders are defunct, but are kept in the code for possible future use. The method cando, witch takes a list of requested properties as argument, returns true if the transcoder can handle that request.

The client fetches a list of transcoding jobs from the server. It then checks if it has an available transcoder that can do any of the jobs. If so, it assigns that job to itself before calling the transcoders methods to download the jobs source video, transcode it and upload the result.

If the job requests a pretext image, the transcoder is asked to transcode the image to same output format and then glue it to the target video.

### Interface ###

The ttc client is started from the command line

```
 ./scripts/ttclient2.py http://dokfilm.l6.no/ttc/
```

with one single argument, identifying the ttc server.

The clients sets the following properties during transcoding format, vcodec, acodec, bredde, høyde, audiobitrate og videobitrate

These properties are fetched from the ttc servers database and are assumed to be delivered by the servers web interface. I f the properties are missing the following default values are used:

width: 480, height: 320, vbitrate: 256, abitrate: 96

If format is mp4: videocodec: h.264, audiocodec: aac

If format is ogg: videocodec: theora, audiocodec: vorbis

In addition samplerate is set fixed to 24000 and framerate to 25 fps.

If the property imguri is present in the servers job description, a static picture is glued to the beginning and end of the film. Between the picture and the film is a period where the screen goes black. The length of the time the picture and the black screen is shown is given by the properties imgDuration and separation. Of technical reasons the picture is followed by a soundtrack. This is copied from a file situated in the running directory with the name silence.mp3. This file does not have to contain any sound.

### Dependencies ###

  * ffmpeg2theora >= version 0.26
  * HandBrakeCLI
  * MP4Box
  * oggCat
  * ffmpeg >= version 0.6.1 . Installing instructions is found in [Ubuntu Forums](http://ubuntuforums.org/showthread.php?t=786095)