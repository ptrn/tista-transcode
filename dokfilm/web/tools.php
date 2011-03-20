<?php
class Tools {
  # not used anymore
  public static function printTable($a) {
    $t = '';
    if (count($a)<1) return $t;

    $t .= '<table>';
    for ($i=0; $i<count($a);$i++) {
      $t .= '<tr>';
      for ($j=0; $j<count($a[$i]);$j++) $t .= sprintf('<td>%s</td>',$a[$i][$j]);
      $t .= '</tr>';
    }
    $t .= '</table>';

    return $t;
  }

  public static function printTableOfMovies($a) {
    $t = '';
    if (count($a)<1) return $t;

    for ($i=0; $i<count($a);$i++)
      $t .= sprintf('<div>%s<a href="%sview/%s">%s</a></div>',
                    ($a[$i][2]?'<img src="'.$GLOBALS['CONF']['path'].'img/annot.png" />':''),
                    $GLOBALS['CONF']['path'],
                    $a[$i][0],
                    $a[$i][1]
                    );

    return $t;
  }
}
?>