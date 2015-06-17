This will go through the code in detail when a user uploads a video to the page.

User enters page and finds input form for file upload. The user selects a file and clicks on the submit button to upload the file. This triggers the following events:
  * the upload of the file is cancelled
  * a JavaScript event is triggered, function named _upload.click()_, located in file _/js/upload.js_
  * An AJAX request is given to the server, giving the name of the file that is to be uploaded. The AJAX request is handled by the file _/events/upload-video-pre.php_
  * The server takes this information and generates an Amazon S3 policy and signature that allows the user to upload the file to Amazon S. The server returns the following, requireed, information:
    * name of file to be uploaded
    * ACL - the access control level, set to public read
    * content-type
    * the public key for Amazon S3
    * the policy generated
    * the signature of the policy, signed with private key
    * redirect location
    * the required DOM elements are added to the HTML tree, ensuring that all required information is given when uploading the file
    * the JavaScript triggers the upload of the file, and the file gets uploaded to the Amazon S3 site
    * After successfully uploading the file to Amazon S3, the browser gets redirected back to the original domain, to a system that register the uploaded files. The file that does this is named _/events/upload-video-post.php_
      * the uploaded file gets queued in TTC, one for each predefined format (defined in _/core.php_)
      * the uploaded file gets stored in the systems own database, and all the predefined video formats gets an entry that refers to the masterfile
        * as each file is queued in TTC its corresponding job ID gets added to that entry
    * the server sends a redirect signal to the web browser, redirecting to the page where the video can be viewed

After this, the transcoding system will find the queued jobs and process each one of them.