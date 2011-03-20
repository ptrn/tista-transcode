<?php
class Database {
  public static function getMovies($subs=false) {
    $r1 = $GLOBALS['sql']->query('SELECT id, title, false FROM movie ORDER BY id;');
    $r2 = $GLOBALS['sql']->query('SELECT movie_id, COUNT(*) FROM annotation GROUP BY movie_id ORDER BY id;');

    for ($i=0; $i<count($r2); $i++) {
      for ($j=0; $j<count($r1); $j++) {
        if ($r2[$i][0]==$r1[$j][0]) {
          $r1[$j][2] = true;
          break;
        }
      }
    }

    return $r1;
  }

  public static function getFormats($i) {
    return $GLOBALS['sql']->query(sprintf('SELECT * FROM movie_format WHERE movie_id=%s;',$i));
  }

  public static function getMovie($i) {
    return $GLOBALS['sql']->query(sprintf('SELECT m.id, m.title, m.description, m.duration, m.author FROM movie m WHERE m.id=%s',$i));
  }

  public static function getUser($i) {
    return $GLOBALS['sql']->query(sprintf('SELECT id, username, email, enabled FROM `user` WHERE id=%s',$i));
  }

  public static function getMovieFormats($i) {
    return $GLOBALS['sql']->query(sprintf('SELECT movie_id, format, path, ttc_id FROM movie_format m WHERE movie_id=%s;',$i));
  }

  public static function getAnnotations($i) {
    return $GLOBALS['sql']->query(sprintf('SELECT id, content, timeFrom, timeDuration FROM annotation WHERE movie_id=%s ORDER BY timeFrom, timeDuration;',$i));
  }

  public static function getAnnotationNumber($i) {
    $r = $GLOBALS['sql']->query(sprintf('SELECT COUNT(*) FROM annotation WHERE movie_id=%s;',$i));
    return $r[0][0];
  }

  public static function isValidMovie($i) {
    global $sql;
    if (!is_numeric($i)) return false;
    if ($i<1) return false;

    $r = $GLOBALS['sql']->query(sprintf("SELECT COUNT(*) FROM movie WHERE id=%s;",$i));
    return $r[0][0]==1;
  }
}
?>