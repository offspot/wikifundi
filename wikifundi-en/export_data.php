<?php
  $excludeArgs = "--exclude=data/log* --exclude=data/images/thumb* --exclude=data/images/archive*";
  $workingDir = "/var/www/";
  $exportDir = "data";
  $wgSitename = "mywiki";
  $wgLanguageCode = "all";
  $IP = "w";

  include "$IP/LocalSettings.custom.php" ;
  
  $filename=strtolower($wgSitename."-".$wgLanguageCode."_".date('Y-m-d'));

  if (isset($_GET["format"]) && $_GET["format"] == "tar")
  {
    $type="x-tar";
    $ext="tar";
    $cmd="tar -C ".$workingDir." -c ".$excludeArgs." ".$exportDir;
  }else{
    $type="x-bzip2";
    $ext="tar.bz2";
    $cmd="tar -C ".$workingDir." -cj ".$excludeArgs." ".$exportDir;
  }
  
  $headerContentType = "Content-Type: application/".$type;
  $headerContentDisposition = "Content-Disposition: attachment; filename=\"".$filename.".".$ext."\"";

  header($headerContentType);
  header($headerContentDisposition);
  passthru($cmd,$err);

  exit();
  
?>
