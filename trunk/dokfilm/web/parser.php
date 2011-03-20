<?php
header('Content-type: text/plain');

$c = "";
$f = fopen("ted-richard-subtitle.dat", "r");
while(!feof($f)) $c .= fgets($f);
fclose($f);

$o = 12.5;
$r = json_decode($c,true);

echo "INSERT INTO annotation(user_id,movie_id,content,enabled,timeFrom,timeDuration) VALUES\n";
$l = count($r['captions']);
for ($i=0; $i<$l; $i++) {
  $timeFrom = round($r['captions'][$i]['startTime']/1000,3)+$o;
  $timeTo = round($r['captions'][$i]['duration']/1000,3);
  $content = $r['captions'][$i]['content'];
  $content = str_replace("'","\\'",$content);
  $content = str_replace("\"","\\\"",$content);
  echo sprintf("  (1, 1, '%s', 1, '%s', '%s')",$content,$timeFrom,$timeTo).($i!=$l-1?',':'');
  if ($i==$l-1) echo ";\n";
  echo "\n";
}



$c = "";
$f = fopen("ted-derek-subtitle.dat", "r");
while(!feof($f)) $c .= fgets($f);
fclose($f);

$o = 12.5;
$r = json_decode($c,true);

echo "INSERT INTO annotation(user_id,movie_id,content,enabled,timeFrom,timeDuration) VALUES\n";
$l = count($r['captions']);
for ($i=0; $i<$l; $i++) {
  $timeFrom = round($r['captions'][$i]['startTime']/1000,3)+$o;
  $timeTo = round($r['captions'][$i]['duration']/1000,3);
  $content = $r['captions'][$i]['content'];
  $content = str_replace("'","\\'",$content);
  $content = str_replace("\"","\\\"",$content);
  echo sprintf("  (1, 2, '%s', 1, '%s', '%s')",$content,$timeFrom,$timeTo).($i!=$l-1?',':'')."\n";
}
?>