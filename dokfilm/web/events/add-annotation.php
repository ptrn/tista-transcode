<?php
require_once('../core.php');

header('Content-Type: text/plain');

# this filter defines a max video length of 10 hours, 59 minutes and 59 seconds
# seconds could be altered to decimal numbers
$filters = array(
                 "id" => array(
                                 "filter"=>FILTER_VALIDATE_INT
                               ),
                 "from-h" => array(
                                 "filter"=>FILTER_VALIDATE_INT,
                                 "options"=>array(
                                                  "min_range"=>0,
                                                  "max_range"=>10
                                                  )
                                 ),
                 "from-m" => array(
                                 "filter"=>FILTER_VALIDATE_INT,
                                 "options"=>array(
                                                  "min_range"=>0,
                                                  "max_range"=>59
                                                  )
                                 ),
                 "from-s" => array(
                                 "filter"=>FILTER_VALIDATE_INT,
                                 "options"=>array(
                                                  "min_range"=>0,
                                                  "max_range"=>59
                                                  )
                                 ),
                 "to-h" => array(
                                 "filter"=>FILTER_VALIDATE_INT,
                                 "options"=>array(
                                                  "min_range"=>0,
                                                  "max_range"=>10
                                                  )
                                 ),
                 "to-m" => array(
                                 "filter"=>FILTER_VALIDATE_INT,
                                 "options"=>array(
                                                  "min_range"=>0,
                                                  "max_range"=>59
                                                  )
                                 ),
                 "to-s" => array(
                                 "filter"=>FILTER_VALIDATE_INT,
                                 "options"=>array(
                                                  "min_range"=>0,
                                                  "max_range"=>59
                                                  )
                                 )
                 );

$result = filter_input_array(INPUT_GET, $filters);



$ok = true;

if (!$result['id']) {
  $ok = false;
  echo "id not given";
}
elseif (!Video::valid($_GET['id'])) {
  $ok = false;
  echo "id not valid";
}

if (!$result['from-m']) {
  if ($_GET['from-m']!=0) {
    echo "from-m not valid";
    $ok = false;
  }
}

if (!$result['from-s']) {
  if ($_GET['from-s']!=0) {
    echo "from-s not valid";
    $ok = false;
  }
}

if (!$result['to-m']) {
  if ($_GET['to-m']!=0) {
    echo "to-m not valid";
    $ok = false;
  }
}

if (!$result['to-s']) {
  if ($_GET['to-s']!=0) {
    echo "to-s not valid";
    $ok = false;
  }
}

if ($ok) {
  $from = Subs::mergeTime($_GET['from-h'],$_GET['from-m'],$_GET['from-s']);
  $to = Subs::mergeTime($_GET['to-h'],$_GET['to-m'],$_GET['to-s']);

  if ($from >= $to) {
    echo "from is before to\n";
    $ok = false;
  }
}

# user input is valid
if ($ok) {
  $sub = new Subs($_GET['id']);
  $sub->addOne(
               Subs::mergeTime($_GET['from-h'],$_GET['from-m'],$_GET['from-s']),
               Subs::mergeTime($_GET['to-h'],$_GET['to-m'],$_GET['to-s']),
               $_GET['text']
               );
  $sub->submitToDatabase();
}
else
  echo("Invalid user input!");
?>