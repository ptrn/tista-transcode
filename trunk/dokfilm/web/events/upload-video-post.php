<?php
require_once('../core.php');

header('Content-type: text/plain; charset=utf-8');

$id = mysql_real_escape_string($_GET['id']);
$bucket = mysql_real_escape_string($_GET['bucket']);
$filename = mysql_real_escape_string($_GET['key']);
$filenameOriginal = mysql_real_escape_string($_GET['fname']);

if (false) {
  # file/URI already added
}
else {
  # assume that file exists in S3
  # add the following

  $formats = $GLOBALS['CONF']['ttc']['output'];
  $insid = null;

  for ($i=0; $i<count($formats); $i++) {
    # queue jobs in TTC
    $url = sprintf('%sjobs/add_one_job?srcuri=%s',
                   $GLOBALS['CONF']['ttc']['baseURI'],
                   $GLOBALS['CONF']['s3']['baseURI'].$bucket.'/'.$filename
                   );

    foreach ($formats[$i] as $key=>$val) $url .= sprintf('&%s=%s', $key, $val);

    /*
     * FIX BEGIN - of some reason, a significat amount of the requests
     * are returned with a 400 error, and is not queued in the
     * system. A dirty fix to this problem is to keep sending request
     * until the server responds with a status code other than 400, or
     * if ten requests in a row fails.
     */
    $http_status;
    $res;
    $count = 0;
    while (true) {
      $curl_handle=curl_init();
      curl_setopt($curl_handle, CURLOPT_URL, $url);
      curl_setopt($curl_handle, CURLOPT_CONNECTTIMEOUT, 2);
      curl_setopt($curl_handle, CURLOPT_RETURNTRANSFER, 1);
      curl_setopt($curl_handle, CURLOPT_USERAGENT, 'PHP curl');
      $res = curl_exec($curl_handle);
      $http_status = curl_getinfo($curl_handle, CURLINFO_HTTP_CODE);
      curl_close($curl_handle);

      if ($http_status==400) {
        $count++;
        continue;
      }
      if ($count < 10) continue;

      break;
    }
    /*
    FIX END
     */


    $json = json_decode($res,true);

    if ($http_status!=200) {
      # echo "file already added\n";

      $q = sprintf("SELECT movie_id FROM movie_format WHERE path='%s'", $json['dstURI']);

      $r = $sql->query($q);
      $insid = $r[0][0];

      break;
    }
    else {
      if ($insid==null) {
        $q = sprintf("INSERT INTO movie (title, author, original_path, original_bucket) VALUES ('%s', %s,'%s','%s');",
                     $filenameOriginal,
                     1, # user
                     $GLOBALS['CONF']['s3']['baseURI'].$bucket.'/'.$filename,
                     $bucket
                     );

        $sql->query($q,true);
        $insid = mysql_insert_id();
      }

      # add info to DB
      $q = sprintf("INSERT INTO movie_format (movie_id, format, path, ttc_id) VALUES(%s, '%s', '%s', '%s');",
                   $insid,
                   $formats[$i]['format'],
                   $json['dstURI'],
                   $json['id']
                   );

      $sql->query($q,true);

    }
  }

  $url = sprintf('http://dev.l6.no%sview/%s',
                 $GLOBALS['CONF']['path'],
                 $insid
                 );

  header('Location: '.$url);
}
?>