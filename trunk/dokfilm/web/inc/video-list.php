<br />
<div class="title">uploaded videos:</div>

<?php
$r = Database::getMovies(true);
echo Tools::printTableOfMovies($r);
?>
