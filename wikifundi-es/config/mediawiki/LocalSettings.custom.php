<?php

# General
$wgLanguageCode     = "es";
$wgSitename         = "WikiFundi";

# Site language
$wgLanguageCode = "es";
$wgUploadWizardConfig['uwLanguages'] = array( 'es' => 'Spanish' );

# Database settings
$wgDBtype        = "sqlite";
$wgDBserver      = "";
$wgDBname        = "mw_wikifundi_es";
$wgDBuser        = "";
$wgDBpassword    = "";
$wgSQLiteDataDir = "/var/www/data";

# Set ES Wikipedia namespace
$wgExtraNamespaces[NS_FOO] = "Wikipedia";
$wgExtraNamespaces[NS_FOO_TALK] = "Wikipedia_talk"; // Note underscores in the namespace name.

# Custom logo
$wgLogo = "/logo.png";
$wgRightsIcon = "/A_WikiAfrica_project.png";

# License
$wgRightsUrl = 'https://creativecommons.org/licenses/by-sa/4.0/';

# Uploads
ini_set('memory_limit', '512M');
ini_set('post_max_size', '5M');
ini_set('upload_max_filesize', '5M');
$wgMaxUploadSize = 1024*1024*5;

$wgHooks['SkinTemplateOutputPageBeforeExec'][] = function( $sk, &$tpl ) {
	$tpl->set( 'contact', $sk->footerLink( 'contact', 'contactpage' ) );
	$tpl->data['footerlinks']['places'][] = 'contact';
	return true;
};

$wgHooks['SkinTemplateOutputPageBeforeExec'][] = function( $sk, &$tpl ) {
	$tpl->set( 'credit', $sk->footerLink( 'credit', 'creditpage' ) );
	$tpl->data['footerlinks']['places'][] = 'credit';
	return true;
};

require_once("$IP/LocalSettings.mirroring.php");
require_once("$IP/LocalSettings.debug.php");

function WikifundiPasswordPolicy($policyVal, $user, $password) {
    return Status::newGood();
}

$wgPasswordPolicy['checks']['MinimalPasswordLength'] = 'WikifundiPasswordPolicy';
$wgPasswordPolicy['checks']['PasswordCannotMatchUsername'] = 'WikifundiPasswordPolicy';
$wgPasswordPolicy['checks']['PasswordCannotMatchBlacklist'] = 'WikifundiPasswordPolicy';
$wgPasswordPolicy['checks']['PasswordCannotBePopular'] = 'WikifundiPasswordPolicy';

?>