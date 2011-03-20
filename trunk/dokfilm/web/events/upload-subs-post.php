<?php
require_once('../core.php');

$id = $_POST['id'];

$raw = '';
$f = fopen($_FILES["file"]["tmp_name"], "r");
while(feof($f) == false)
  $raw .= utf8_encode(str_replace("\r","",fgets($f)));
fclose($f); 

$blocks = explode("\n\n",$raw);

$subs = new Subs($id);

for ($i=0; $i<count($blocks); $i++) {
  $subs->add($blocks[$i]);
  continue;

  $sp = explode("\n",$blocks[$i],3);
}

$subs->toString();
$subs->submitToDatabase();
?>