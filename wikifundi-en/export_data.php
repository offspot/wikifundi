<?php

  header("Content-Type: application/x-bzip2");
  header("Content-Disposition: attachment; filename=\"wikifundi-data.tar.bz\"");

  passthru("tar -C /var/www/ -cj data",$err);
  
  exit();
  
?>
