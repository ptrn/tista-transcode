<?php
require_once('sql.php');
require_once('tools.php');
require_once('fetcher.php');
require_once('video.php');
require_once('policy.php');
require_once('subs.php');
require_once('LoremIpsum.class.php');

$GLOBALS['CONF'] = array();
$GLOBALS['CONF']['path'] = '/dokfilm/';
$GLOBALS['CONF']['MIME'] = array('ogg'=>'video/ogg','mp4'=>'video/mp4');

$GLOBALS['CONF']['poster_path'] = 'http://s3-http.l6.no/dev/';
$GLOBALS['CONF']['video_path'] = 'http://s3-http.l6.no/dev/';

$GLOBALS['CONF']['s3'] = array();
$GLOBALS['CONF']['s3']['acl'] = 'public-read';
$GLOBALS['CONF']['s3']['contenttype'] = 'application/octet-stream';
$GLOBALS['CONF']['s3']['public'] = '';                          # REMOVED FROM PUBLIC REPOSITORY
$GLOBALS['CONF']['s3']['private'] = '';                         # REMOVED FROM PUBLIC REPOSITORY
$GLOBALS['CONF']['s3']['bucket'] = 'dokfilm-raw_up';
$GLOBALS['CONF']['s3']['baseURI'] = 'http://s3.amazonaws.com/';
$GLOBALS['CONF']['s3']['bucketURI'] = 'http://s3.amazonaws.com/dokfilm-raw_up';
$GLOBALS['CONF']['s3']['path'] = 'subdir/';
$GLOBALS['CONF']['s3']['getKeys'] = $GLOBALS['CONF']['path'].'upload/video/getkeys/';
$GLOBALS['CONF']['s3']['callbackURIBase'] = 'http://'.$_SERVER['SERVER_NAME'].$GLOBALS['CONF']['path'].'upload/video/finished/';

$GLOBALS['CONF']['ttc']['baseURI'] = 'http://dokfilm.l6.no/ttc/';
$GLOBALS['CONF']['ttc']['output'] = array(
                               array(
                                     'format'=>'mp4',
                                     'vcodec'=>'h.264',
                                     'acodec'=>'aac',
                                     'vbitrate'=>1024,
                                     'abitrate'=>128,
                                     'width'=>640,
                                     ),
                               array(
                                     'format'=>'ogg',
                                     'vcodec'=>'theora',
                                     'acodec'=>'vorbis',
                                     'vbitrate'=>1024,
                                     'abitrate'=>64,
                                     'width'=>640,
                                     ),
                               );

class User {
  public $id;
  public $username;
  public $email;
  public $enabled;

  public function __construct($id) {
    $this->id = $id;
    $this->getInfo();
  }

  public function getInfo() {
    $r = Database::getUser($this->id);

    $this->username = $r[0][1];
    $this->email = $r[0][2];
    $this->enabled = $r[0][3];
  }

  public function getUsername() { return $this->username; }
}

;

# SQL connections
$sql = null;

$sql = new MySQL('dokfilm','fKT8t9Dbm2Uj9bQM','dokfilm');

class Core {
  public static $escapeCharacters = array(
                                          array("\x00","\\x00"),
                                          array("\n","\\n"),
                                          array("\r","\\r"),
                                          array("\\","\\\\"),
                                          array("'","\\\'"),
                                          array("\"","\\\""),
                                          array("\x1a","\\x1a")
                                          );

  public static function escape($t) {
    return $t;

    for ($i=0; $i<count($c); $i++)
      $t = str_replace(
                       $this->escapeCharacters[$i][0],
                       $this->escapeCharacters[$i][1],
                       $t);
    return $t;
  }

  public static function unescape($t) {
    for ($i=0; $i<count($c); $i++)
      $t = str_replace(
                       $this->escapeCharacters[$i][1],
                       $this->escapeCharacters[$i][0],
                       $t);
    return $t;
  }
}
?>
