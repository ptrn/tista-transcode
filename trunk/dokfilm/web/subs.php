<?php
class Subs {
  private $videoID;
  private $data;

  public function __construct($videoID) {
    $this->videoID = $videoID;
    $this->data = array();
  }

  public function add($d) {
    $s = explode("\n",$d,3);
    $t =$this->parseTime($s[1]);

    $this->data[] = new SubEntry($t[0],$t[1],$s[2]);
  }

  public function addOne($from,$to,$text) {
    $this->data[] = new SubEntry($from,$to,$text);
  }

  public static function mergeTime($h,$m,$s) {
    $ms = 0;
    # $ms += $];               # milliseconds
    $ms += $s*1000;          # seconds
    $ms += $m*1000*60;       # minutes
    $ms += $h*1000*60*3600;  # hours

    return $ms;
  }

  private function parseTime($d) {
    $r1 = explode(' --> ',$d);     # splits to to and from

    $t = array(0,0);

    for ($i=0; $i<2; $i++) {       # get time, from and to
      $r2 = explode(',',$r1[$i]);  # get milliseconds
      $r3 = explode(':',$r2[0]);   # get hours, minutes and seconds

      $ms = 0;
      $ms += $r2[1];               # milliseconds
      $ms += $r3[2]*1000;          # seconds
      $ms += $r3[1]*1000*60;       # minutes
      $ms += $r3[0]*1000*60*3600;  # hours

      $t[$i] = $ms;                # stores data
    }

    return $t;
  }

  public function toString() {
    return;
    for ($i=0; $i<count($this->data); $i++) {
      echo $this->data[$i]->getFrom()."<br />\n";
      echo $this->data[$i]->getTo()."<br />\n";
      echo str_replace("\n"," ",$this->data[$i]->getData())."<br />\n";
      echo '<br />';
    }    
  }

  public function submitToDatabase() {
    $q = 'INSERT INTO annotation (user_id,movie_id,content,timeFrom,timeDuration) VALUES ';

    $uid = 1;

    for ($i=0; $i<count($this->data); $i++) {
      $q .= sprintf("(%s,%s,'%s',%s,%s)",
                    $uid,
                    $this->videoID,
                    mysql_real_escape_string($this->data[$i]->getData()),
                    $this->data[$i]->getFrom(),
                    $this->data[$i]->getTo()
                    );
      if ($i<count($this->data)-1) $q .= ',';
    }

    $q .= ';';

    $GLOBALS['sql']->query($q,true);

    $url = $GLOBALS['CONF']['path'].'view/'.$this->videoID;
    header('Location: '.$url);
  }
}

class SubEntry {
  public $from;
  public $to;
  public $data;

  public function __construct($tf,$tt,$d) {
    $this->from = intval($tf);
    $this->to = intval($tt);
    $this->data = $d;
  }

  public function getFrom() { return $this->from; }
  public function getTo() { return $this->to; }
  public function getData() { return $this->data; }
}
?>