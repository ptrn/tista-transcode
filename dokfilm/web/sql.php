<?php
class MySQL {
  private $user = null;
  private $pass = null;
  private $host = 'localhost';
  private $connection = null;
  private $database = null;
  private $count = 0;

  public function __construct($user,$pass,$database=null) {
    // D begin
    /*
    echo $user."<br />";
    echo $pass."<br />";
    echo $database."<br />";
    echo "<hr />";
    */
    // D end

    $this->user = $user;
    $this->pass = $pass;
    $this->connect();
    if ($database!=null) $this->setDatabase($database);
  }

  private function connect() {
    $this->connection = mysql_connect($this->host,$this->user,$this->pass);
  }

  public function disconnect() {
    if ($this->connection==null) return;
    mysql_connect($this->connection);
    $this->connection = null;
  }

  public function setDatabase($db) {
    $this->database = $db;
    mysql_select_db($this->database, $this->connection);
  }

  public function query($q,$i=false) {
    if ($this->database==null) return;

    $r = mysql_query($q);

    # if this is an insert query, return
    if ($i) return;

    $a = array();

    $c = 0;
    while ($t = mysql_fetch_array($r)) {
      for($i = 0; $i < mysql_num_fields($r); $i++) $a[$c][$i] = $t[$i];
      $c++;
    }

    return $a;
  }
}
?>