<?php

# General
$wgLanguageCode     = "en";
$wgSitename         = "WikiFundi";

# Site language 
$wgLanguageCode = "en";
$wgUploadWizardConfig['uwLanguages'] = array( 'en' => 'English' );

# Database settings
$wgDBtype        = "sqlite";
$wgDBserver      = "";
$wgDBname        = "mw_wikifundi_en";
$wgDBuser        = "";
$wgDBpassword    = "";
$wgSQLiteDataDir = "/var/www/data";

# Custom logo
$wgLogo = "/logo.png";

# Uploads
ini_set('memory_limit', '512M');
ini_set('post_max_size', '5M');
ini_set('upload_max_filesize', '5M');
$wgMaxUploadSize = 1024*1024*5;

?>
