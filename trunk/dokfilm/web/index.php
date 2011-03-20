<?php
require_once('core.php');
?>
<html>
  <head>
    <link rel="stylesheet" href="<?php echo $GLOBALS['CONF']['path'] ?>style.css" type="text/css" />
    <script type="text/javascript" src="<?php echo $GLOBALS['CONF']['path'] ?>js/jquery-min.js"> </script>
    <script type="text/javascript" src="<?php echo $GLOBALS['CONF']['path'] ?>js/core.js"> </script>
    <script type="text/javascript" src="<?php echo $GLOBALS['CONF']['path'] ?>js/upload.js"> </script>
    <script type="text/javascript" src="<?php echo $GLOBALS['CONF']['path'] ?>js/annotations.js"> </script>
  </head>

  <body>
    <div id="container">
      <div id="header">
        prototype
      </div>

      <div id="menu">
        <a href="<?php echo $GLOBALS['CONF']['path'] ?>">Index</a>
      </div>

      <div id="content">
        <div id="box">
<?php
switch ($_GET['v']) {
case 'l':
  include('inc/upload-video.php');
  include('inc/video-list.php');
  break;
case 'us':
  include('inc/upload-subs.php');
  break;
case 'uss':
  include('inc/upload-subs-submit.php');
  break;
case 'uv':
  include('inc/upload-video.php');
  break;
case 'v':
  include('inc/video-view.php');
  break;
default:
  include('inc/upload-video.php');
  include('inc/video-list.php');
  break;
}

?>
        </div>
      </div>

      <div id="footer">
        lekker, spennende informasjon
      </div>
    </div>
  </body>
</html>
