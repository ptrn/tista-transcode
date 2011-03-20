<?php
require_once('core.php');

class Policy {
  private $acl;
  private $contenttype;
  private $public;
  private $private;
  private $policy;
  private $bucket;
  private $bucketURI;
  private $filename;
  private $filenameOriginal;
  private $extension;

  public function __construct($filenameOriginal) {
    $this->setFilenameOriginal($filenameOriginal);
    $this->setExtension($filenameOriginal);
    $this->generateFilename();
    $this->generatePolicy();
  }

  # TODO: make private
  public function generatePolicy() {
    $date = date('Y-m-d').'T'.date('H:i:s').'.000Z';
    $file = $this->filename;

    $t = sprintf('{
  "expiration": "%s",
  "conditions": [
    {"bucket": "%s" },
    {"acl": "public-read" },
    {"success_action_redirect": "%s"},
    ["starts-with", "$key", ""],
    ["starts-with", "$Content-Type", "application/octet-stream"],
  ]
}', $date, $this->getBucket(), $this->getCallbackURI());

    $this->policy = $t;
  }

  private function setExtension($fno) {
    $r = explode('.',$fno);

    $this->extension = $r[count($r)-1];
  }

  private function setFilenameOriginal($fno) {
    $r1 = explode('/',$fno);

    $r2 = explode('.',$r1[count($r1)-1]);

    $f = '';
    for ($i=0; $i<count($r2)-1; $i++) {
      $f .= $r2[$i];
      if ($i<count($r2)-2) $f .= '.';
    }

    $this->filenameOriginal = $f;
  }

  private function generateFilename() {
    $t = '';

    for ($i=0; $i<32; $i++) {
      $r = rand(0,61);

      if ($r<10) $t .= $r;
      else if($r<36) $t .= chr($r-10+65);
      else $t .= chr($r-36+97);
    }

    $this->filename = $t;
  }

  public function getACL() { return $GLOBALS['CONF']['s3']['acl']; }

  public function getBucket() { return $GLOBALS['CONF']['s3']['bucket']; }

  public function getBucketURI() {
    return $GLOBALS['CONF']['s3']['bucketURI'];
  }

  public function getCallbackURI() {
    return $GLOBALS['CONF']['s3']['callbackURIBase'].$this->filename.'/'.$this->filenameOriginal.'/';
  }

  public function getContentType() {
    return $GLOBALS['CONF']['s3']['contenttype'];
  }

  public function getExtension() { return $this->extension; }

  public function getFilename() {
    return $GLOBALS['CONF']['s3']['path'].$this->filename.'.'.$this->extension;
  }

  public function getFilenameOriginal() { return $this->filenameOriginal; }

  public function getPublic() { return $GLOBALS['CONF']['s3']['public']; }

  public function getPolicy() { return base64_encode($this->policy); }

  public function getSignature() {
    $b = $this->getPolicy();
    return $this->hex2b64($this->hmacsha1($GLOBALS['CONF']['s3']['private'],$b));
  }

  /*
   * Calculate HMAC-SHA1 according to RFC2104
   * See http://www.faqs.org/rfcs/rfc2104.html
   */
  private function hmacsha1($key,$data) {
    $blocksize=64;
    $hashfunc='sha1';
    if (strlen($key)>$blocksize)
      $key=pack('H*', $hashfunc($key));
    $key=str_pad($key,$blocksize,chr(0x00));
    $ipad=str_repeat(chr(0x36),$blocksize);
    $opad=str_repeat(chr(0x5c),$blocksize);
    $hmac = pack(
                 'H*',$hashfunc(
                                ($key^$opad).pack(
                                                  'H*',$hashfunc(
                                                                 ($key^$ipad).$data
                                                                 )
                                                  )
                                )
                 );
    return bin2hex($hmac);
  }
  
  /*
   * Used to encode a field for Amazon Auth
   * (taken from the Amazon S3 PHP example library)
   */
  private function hex2b64($str)
  {
    $raw = '';
    for ($i=0; $i < strlen($str); $i+=2)
      {
        $raw .= chr(hexdec(substr($str, $i, 2)));
      }
    return base64_encode($raw);
  }
}
?>