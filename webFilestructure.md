This describes the file tree for the web prototype, and the purpose of each file.

# Tree #

**File structure:**
```
|-- LoremIpsum.class.php
|-- core.php
|-- events
|   |-- upload-subs-post.php
|   |-- upload-video-post.php
|   `-- upload-video-pre.php
|-- fetcher.php
|-- index.php
|-- img
|   |-- annot.png
|   |-- dot-red.png
|   `-- dot-yellow.png
|-- inc
|   |-- upload-video.php
|   |-- video-list.php
|-- js
|   |-- annotations.js
|   |-- core.js
|   |-- jquery-min.js
|   `-- upload.js
|-- policy.php
|-- sql.php
|-- style2.css
|-- subs.php
|-- tools.php
`-- video.php
```

## File description ##

  * **`.htaccess`**
    * Apache configuration settings. READ MORE SOMEWHERE
  * **`LoremIpsum.class.php`**
    * used for generating random sentences, used to generate fictive video desciptions
  * **`core.php`**
    * Used for initialization of global PHP variables and functions. Used by most PHP files
  * **`events/upload-subs-post.php`**
    * script that receives, processes and stores the annotations that get uploaded
  * **`events/upload-video-post.php`**
    * After upload to Amazon S3 storage is done, the user is redirected here with some information about the uploaded object. READ MORE SOMEWHERE
  * **`events/upload-video-pre.php`**
    * Generates policy and certificate to allow upload of object to Amazon. READ MORE SOMEWHERE
  * **`fetcher.php`**
    * various set functions to extract data from the database
  * **`index.php`**
    * TODO
  * **`import.php`**
    * parses SRT files
  * **`inc/upload-video.php`**
    * HTML for video upload form
  * **`inc/video-list.php`**
    * lists all uploaded videos in HTML
  * **`js/annotations.js`**
    * JavaScript for showing annotations while in video view
  * **`js/core.js`**
    * Used for initialization of global variables, functions and objects, used in all pages
  * **`js/genkey.php`**
    * TODO
  * **`js/jquery-min.js`**
    * jQuery library
  * **`js/upload.js`**
    * JavaScript used in upload form
  * **`policy.php`**
    * creates certificate and policy to allow upload of objects to Amazon S3
  * **`sql.php`**
    * handles database connections and queries
  * **`style2.css`**
    * stylesheet
  * **`subs.php`**
    * handles annotation objects
  * **`tools.php`**
    * common used functions
  * **`video.php`**
    * handles the video objects

### Notes ###

Some files that need some further explanation.

#### .htaccess ####
Used to rewrite URL's. Parameters are sent as `/par1/par2`. Eg.:
```
/view/4863
```
In this example, the site for viewing a video is requested, with video ID 4863. This makes the URI less confusing and more clean. The only case where query strings are used is post upload of an object to Amazon S3, but the user is immediately redirected to a new page.

The configuration settings specified in this file should be set in the webserver settings file instead of using a .htaccess file, as this will increase server performance.

#### core.php ####

This file defines all common PHP classes, variables and functions.

#### events/upload-subs-post.php ####

This script receives, processes and stores uploaded annotations. An SRT-formatted file is required. Read more about the syntax [here](webAnnotations#uploading.md).

#### events/upload-video-post.php ####

After the user has uploaded an object to Amazon S3, he gets redirected back to a callback URI. A query string follows the callback, giving information about the uploaded object:
  * a random generated ID used when generating the policy to allow upload
  * the original file name, extension removed
  * Amazon S3 bucket name
  * location in bucket of the uploaded object
  * ~~an Amazon S3 object reference (not used)~~

The following pseudocode will describe the flow of the code:

```

FOR all formats defined in $GLOBALS['ttc']['output']
  compose URI to request TTC server
  requesting TTC to add job to transcode to a given output format (footnote: see below code)
  IF job added successfully
    IF this is first job added so far in this instance
      add movie to database
      store ID for movie
    add movie format to database, using movie ID as part of primary key

redirect user to URI for viewing processed video
```

Footnote: for some reason, curl and other functions for doing a HTTP request fails and returns a HTTP 400 error code for ~1/5 of the requests, corrupting the database. As a preliminary fix, the HTTP request is done until the response code is not HTTP 400. This should most definitively be fixed.

#### events/upload-video-pre.php ####

Generates information needed to be allowed to upload to Amazon S3. Given a file name as input, the output is a set of JSON encoded data:

  * which Amazon S3 bucket to upload to
  * the specific URI of the bucket
  * name of file to be stored at Amazon S3
  * public permissions to file after upload
  * content type of data
  * AWS Access Key, public key used to validate certificate
  * a BASE64 coded policy
  * a signature of the policy, signed by private key on server
  * the URI the browser will be redirected to after upload
  * meta data about original file

Read more about Amazon S3 [S3 here](Amazon#Amazon.md).

#### fetcher.php ####

A set of functions for obtaining data from database.

#### index.php ####



#### inc/upload-video.php ####

This is the HTML code for the form to upload an object. Note that the actual submit button is outside the form.

The sequence is as following:
  * user selects a file to upload
  * user clicks on submit button, which triggers the JavaScript function `upload.click()`
    * JavaScript does GET request to `events/upload-video-pre.php`, giving name of file selected for upload
    * GET request returns dynamic variables required to upload to Amazon S3
    * JavaScript adds hidden inputs containing required variables
    * the uploading is triggered

#### js/annotations.js ####

JavaScript for handling annotation when viewing a video. The function `anno.updateTime()` gets more and more inefficient as the number of annotations for a video increases, as all annotations are iterated on update.

#### js/core.js ####

Defines common variables and initiates objects.

#### js/upload.js ####

Object containing functions that gets the variables required for Amazon S3 upload.

#### policy.php ####

Class that generates policies and other variables necessary to upload to Amazon S3.

#### subs.php ####

Script that receives the uploaded SRT files, parses them and adds it to the video and database.

#### video.php ####

Contains several classes for handling video, annotation and video format objects.