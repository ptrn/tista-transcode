<?php
header('Content-type: text/plain');

# $c = "";
# $f = fopen("subs.srt", "r");
# while(!feof($f)) $c .= fgets($f);
# fclose($f);
# 
# echo $c;

$i = new Importer();
echo $i->__toString();
echo "\n\n-----------------\n\n\n";
$i->split();

class Importer {
  private $content;
  private $entries;
  
  public function __construct() {
    $this->content = '';
    $f = fopen("subs.srt", "r");
    while(!feof($f)) $this->content .= str_replace("\r",'',fgets($f));
    fclose($f);
  }

  public function split() {
    # print_r(split("\n\n",$this->content));
    # return;
    $a = split("\n\n",$this->content);
    $this->entries = array();

    echo 'count: '.count($a)."\n";

    for ($i=0; $i<count($a); $i++) {
      echo $a[$i]."\n\n";

      continue;
      for ($j=0; $j<count($t[$i]); $j++) echo sprintf("%s\n",$t[$i][$j]);
      echo "\n\n";
    }
  }

  public function __toString() { return $this->content; }
}
?>