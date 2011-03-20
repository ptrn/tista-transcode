<?php
class Video {
  private $id;
  private $title;
  private $description;
  private $duration;
  private $author;
  private $formats = array();
  private $annotationCount;

  public function __construct($id) {
    $this->id = $id;
    $this->parseDb();
  }

  private function parseDb() {
    $i = Database::getMovie($this->id);
    $f = Database::getMovieFormats($this->id);
    $this->annotationCount = Database::getAnnotationNumber($this->id);

    $this->title = $i[0][1];
    $this->description = $i[0][2];
    $this->duration = intval($i[0][3]);
    $this->author = new User($i[0][4]);

    for ($i=0; $i<count($f); $i++)
      $this->formats[] = new Format($f[$i][1],$f[$i][2],$f[$i][3]);
  }

  public function getVideoTag() {
    $t = '';

    $t .= sprintf('<div id="movie_title">%s</div>',$this->title);
    $t .= sprintf('<div id="movie_author">by %s</div>',$this->author->getUsername());

    $r = $GLOBALS['CONF']['path'].'img/';

    $err = -1;
    $err_t = array(
                   array('error','<img src="'.$r.'dot-red.png" />this video is not processed yet<script type="text/javascript">setTimeout("window.location.reload()",60000)</script>'),
                   array('warn','<img src="'.$r.'dot-yellow.png" />this video is not fully processed, and might not be playable in your browser')
                   );

    $pro = new Processed($this->formats);

    if ($pro->any()) {
      if ($pro->remaining()>0) $err = 1;
    }
    else $err = 0;

    if ($err!=-1)
      $t .= sprintf('<div id="movie_msg" class="msg_%s">%s</div>',
                    $err_t[$err][0],
                    $err_t[$err][1]
                    );

    $t .= sprintf('<video id="vid" controls ondurationchange="anno.durationChanged()">');

    for ($i=0; $i<count($this->formats); $i++) {
      $t .= sprintf('<source type="%s" src="%s"></source>',
                    $GLOBALS['CONF']['MIME'][$this->formats[$i]->getFormat()],
                    $this->formats[$i]->getPath()
                    );
    }
    $t .= '</video>';

    # generates random description for video
    # begin
    $generator = new LoremIpsumGenerator;
    $o = $generator->getContent(40);
    # end

    $t .= sprintf('<div id="movie_desc">%s</div>',$o);
    $a = new Annotation($this->id);

    $t .= '<div id="movie_annot_upload">';
    $t .= sprintf('<form action="%supload/subs/submit/" method="POST" enctype="multipart/form-data">',
                  $GLOBALS['CONF']['path']);
    $t .= sprintf('<input name="id" type="hidden" value="%s" />',
                  $this->id);
    $t .= 'upload annotations (strict SRT): <input name="file" type="file" /><input value="Upload" type="submit" /></form>';
    $t .= '</div>';

    $t .= '<div id="movie_annot_add">';
    $t .= sprintf('<form action="%sadd/annotation/%s/" method="GET">',
                  $GLOBALS['CONF']['path'],
                  $this->id
                  );
    $t .= '<u>add annotation</u><br /><div id="time-from"></div><div id="time-from"></div><textarea name="text" rows="2" cols="85"></textarea><input value="Add" type="submit" />';
    $t .= '</form>';
    $t .= '</div>';

    $t .= sprintf('<script type="text/javascript">%s</script>',$a->getJSON());
    $t .= '<div id="movie_annot">
<div class="annotation"></div>
</div>';

    return $t;
  }

  public static function valid($id) { return Database::isValidMovie($id); }
}

class Annotation {
  public $id;

  public function __construct($id) {
    $this->id = $id;
  }

  public function getJSON() {
    $a = array();

    $r = Database::getAnnotations($this->id);

    for ($i=0; $i<count($r); $i++) {
      $tmp = array();
      $tmp['id'] = $r[$i][0];
      # needs better replacing
      $tmp['content'] = str_replace("\\",'',$r[$i][1]);
      $tmp['timeStart'] = $r[$i][2];
      $tmp['timeEnd'] = $r[$i][3];
      $a[] = $tmp;
    }

    return 'var annotations = '.json_encode($a).';';

    return $t;
  }
}

class Format {
  public $format;
  public $path;
  public $ttc_id;

  public function __construct($f,$p,$t) {
    $this->format = $f;
    $this->path = $p;
    $this->ttc_id = $t;
  }

  public function getFormat() { return $this->format; }
  public function getPath() { return $this->path; }
  public function getTTCid() { return $this->ttc_id; }
}

class Processed {
  private $ok;
  private $nok;

  public function __construct($formats) {
    $base = $GLOBALS['CONF']['ttc']['baseURI'].'jobs/get_job_info?id=';

    $this->ok = 0;
    $this->nok = 0;

    for ($i=0; $i<count($formats); $i++) {
      $url = $base.$formats[$i]->getTTCid();

      $res = file_get_contents($url);

      $json = json_decode($res,true);

      if ($json['state']=='f') $this->ok++;
      else $this->nok++;
    }
  }

  public function any() { return $this->ok; }

  public function finished() { return ($this->nok==0); }

  public function remaining() { return $this->nok; }
}
?>