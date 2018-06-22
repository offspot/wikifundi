<?php

  $wgSitename = "mywiki";
  $wgLanguageCode = "all";

  include 'w/LocalSettings.custom.php';
  
  $filename=strtolower($wgSitename."-".$wgLanguageCode."_".date('Y-m-d').".tar.bz2");

  header("Content-Type: application/x-bzip2");
  header("Content-Disposition: attachment; filename=\"".$filename."\"");

  passthru("tar -C /var/www/ -cj --exclude=data/log* data",$err);
  

  exit();
  
?>
