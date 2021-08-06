WikiFundi
=========

WikiFundi is a solution which provide a pre-configured Mediawiki in a
similar way like Wikipedia. Probably the easiest way to train users if
you do not have access to Internet!

Install empty MediaWiki 
-----------------------
Run for english version :

```
docker run -p 80:80 -v ${PWD}/data-init:/var/www/data -it ghcr.io/offspot/wikifundi-en
```

For french version :

```
docker run -p 80:80 -v ${PWD}/data-init:/var/www/data -it ghcr.io/offspot/wikifundi-fr
```

Go to  [http://localhost/](http://localhost/)

Default admin logging :

* User : admin
* Password : mediawikipass

Mirroring with WikiFundi
------------------------

You can lauch mirroring by changing environments variables MIRRORING :

`docker run -p 80:80 -e MIRRORING=1 -v ${PWD}/data:/var/www/data -it ghcr.io/offspot/wikifundi-en`
 
You can also change options script with MIRRORING_OPTIONS : 

* `-f, --force` : always copy  the content (even if page exist on site dest) (default : false)
* `-t, --no-sync-templates` : do not copy templates used by the pages to sync. (default : false)
* `-u, --no-upload-files` : do not copy files (images, css, js, sounds, ...) used by the pages to sync (default : false)
* `-p, --no-sync` : do not copy pages (default : false)
* `-m, --no-modify` : do not modify pages (default : false)
* `-r, --resume` : try to resume previous sync (default : false). Associate with -d0 to not re-process dependency search.
* `-d, --dependance-nb-parse` : number of dependance parsing (default : 2)
* `-x, --expand-text` : copy the generated content of a page (default : false)
* `-e, --export-dir <directory>` : write resume files in this directory (default : current directory)
* `-w, --thumbwidth` :try to download thumbnail image with this width instead original image (default : 1024)
* `-s, --maxsize` : do not files download greater to this limit (default : 200MB)
* `-a, --async` : execute mirroring in async mode (5 threads / cpu). No works with SQLITE database. (default : false)
  
Examples :

* `MIRRORING_OPTIONS='-m 5MB -w 2000'` : sync page, templates, files and modify pages. Do not copy file > 5MB and Copy images (jpeg and png) in 2000px (if available).
* `MIRRORING_OPTIONS='-d0'` : sync and modify pages. Do not process dependances (templates and files).
* `MIRRORING_OPTIONS='-utd0'` : just copy and modify pages.
* `MIRRORING_OPTIONS='-rputd0'` : just modify previously copied pages. 
* `MIRRORING_OPTIONS='-putmd0'` : do anything.
* `MIRRORING_OPTIONS='-af'` : copy all pages and their dependencies in async mode.
 
After mirroring, you can generate tarball by going [http://localhost/export_data.php](http://localhost/export_data.php). A README file is in this tarball to explain an installation without Docker.

Other options
-------------

* `CLEAN=1` : delete old revisions and archived files. 
* `DEBUG=1` : show debug informations in pages
* `GO_BASH=1` : lauch bash instead services

Build your Docker image
-----------------------
The WikiFundi image extends the `openzim/mediawiki` Docker image to
allow mirroring a existing wiki (by example Wikipedia) and
use this wiki offline.

The config files are located in `config` directory.

This directory contain the configuration of :

* `mirroring/mirroring.json` : 
    Pages to copy from an other wiki and modifications after copy. 
    Read help part of `wikimedia_sync.py` to get file structure.
* `mirroring/deleteBatch.txt` :
    List of pages to delete. You can also use `mirroring.json` to mark pages to delete, but human interevention is needed to really delete pages.
* `mediawiki/LocalSettings.custom.php` : 
    You can customise the Mediawiki by editing your this file. 
    If you want to know more, have a look to [documentation](https://www.mediawiki.org/wiki/Manual:LocalSettings.php)
* `parsoid/config.yaml` :
    Parsoid config file (allow to use VisualEdit)
* `pywikibot/user-config.py` :
    [Configure pywikibot library](https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py) to use MediaWiki API (needed for mirroring)

You can also customize your logo in `assets/images` as customize the `assets/docs/README` embeded with data 

To build and run :

```
docker build -t wikifundi_en wikifundi_en 
docker run -p 80:80 -v ${PWD}/data:/var/www/data -it wikifundi_en
```
As french version, yon can extend ghcr.io/offspot/wikifundi-en to create an image for other Wikipedia language or other wiki.

Managing Wikifundi with Sloppy hosting
--------------------------------------
You can use `./install_sloppy_cli.sh` to install Sloppy CLI. We must define SLOPPY_TOKEN environnement variable with your token. Then, we can us `wikifundi_management.sh` to manage Wikifundi :

* `./wikifundi_management.sh restart <LANG>` : restart <LANG> instance. If not LANG is defined, restart all instance.
* `./wikifundi_management.sh full_mirroring` : delete all Wikifundi instances (!!) and lauch mirroring
* `./wikifundi_management.sh partial_mirroring` : lauch a mirroring which force copy pages exclusively (no copy files and templates)
* `./wikifundi_management.sh delete_all` : delete all instance
* `./wikifundi_management.sh wait_running` : wait until all instances are ready 
* `./wikifundi_management.sh cron` : start full mirroring on sunday and partial mirroring the other day
 
 Author
 ------
 Florent Kaisser <florent.pro@kaisser.name>

 Version
 -------
 2.0
