<?php

$wgGroupPermissions["sysop"]["*"] = true;
$wgGroupPermissions["sysop"]["read"] = true;
$wgGroupPermissions["sysop"]["createtalk"] = true;
$wgGroupPermissions["sysop"]["createpage"] = true;
$wgGroupPermissions["sysop"]["move-rootuserpages"] = true;
$wgGroupPermissions["sysop"]["movefile"] = true;
$wgGroupPermissions["sysop"]["move-categorypages"] = true;
$wgGroupPermissions["sysop"]["protect"] = true;
$wgGroupPermissions["sysop"]["editsitecss"] = true;
$wgGroupPermissions["sysop"]["editsitejson"] = true;
$wgGroupPermissions["sysop"]["editsitejs"] = true;
$wgGroupPermissions["sysop"]["editusercss"] = true;
$wgGroupPermissions["sysop"]["edituserjson"] = true;
$wgGroupPermissions["sysop"]["edituserjs"] = true;

# Uploads
ini_set('memory_limit', '512M');
ini_set('post_max_size', '200M');
ini_set('upload_max_filesize', '200M');
$wgMaxUploadSize = 1024*1024*200;

?>
