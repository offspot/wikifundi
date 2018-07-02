<?php
header("HTTP/1.0 503 Mirroring in progress ...");
?>
<html>
<h1><a href="http://www.wikifundi.org"><img height="128" src="http://www.wikifundi.org/wp-content/uploads/2016/09/WikiFundi-logo.png"></img></a></h1>
<h2>Mirroring in progress ...</h2>
<body>
<p>
	<h3>Mirroring log :</h3>
	<pre>

<?php
	passthru('tail -n 20  /var/www/data/log/mirroring.log',$err);
?>

	</pre>
        <a href="../w/data/log/mirroring.log">Download the complet log</a>
</p>
</body>
</html>
