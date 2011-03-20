<?php
$id = (isset($_GET['m']) ? $_GET['m'] : false);
if ($id!=false) {
  $v = Video::valid($id);

  if ($v) {
    $vid = new Video($id);
    echo $vid->getVideoTag();
  }
  else
    echo 'requested video not valid';
}
?>