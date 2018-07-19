#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# author : Florent Kaisser <florent@kaisser.name>
# maintainer : Kiwix

"""
 wikimedia_sync.py

 Copy WikiMedia pages from a Wiki source (ex : a Wikipedia) to a Wiki
 destionation (like a third-party wikis).

 A config file given in args contain name of pages and categories to
 synchronize, and Wiki source and destination.

 usage : ./wikimedia_sync.py [options] config_file1.json, config_file2.json, ...

 options :
  -f, --force : always copy  the content (even if page exist on site dest) (default : false)
  -t, --no-sync-templates : do not copy templates used by the pages to sync. (default : false)
  -u, --no-upload-files : do not copy files (images, css, js, sounds, ...) used by the pages to sync (default : false)
  -p, --no-sync : do not copy pages (default : false)
  -m, --no-modify : do not modify pages (default : false)
  -r, --resume : try to resume previous sync (default : false). Associate with -d0 to not re-process dependency search.
  -d, --dependance-nb-parse : number of dependance parsing (default : 2)
  -x, --expand-text : copy the generated content of a page (default : false)
  -e, --export-dir <directory> : write resume files in this directory (default : current directory)
  -w, --thumbwidth :try to download thumbnail image with this width instead original image (default : 1024)
  -s, --maxsize : do not files download greater to this limit (default : 200MB)
  -a, --async : execute mirroring in async mode (5 threads / cpu). No works with SQLITE database. (default : false)

 examples :
 ./wikimedia_sync.py -m 5MB -w 2000 config.json : sync page, templates, files and modify pages. Do not copy file > 5MB and Copy images (jpeg and png) in 2000px (if available).
 ./wikimedia_sync.py -d0 config.json : sync and modify pages. Do not process dependances (templates and files).
 ./wikimedia_sync.py -utd0 config.json : just copy and modify pages.
 ./wikimedia_sync.py -rputd0 config.json : just modify previously copied pages.
 ./wikimedia_sync.py -putmd0 config.json : do anything.
 ./wikimedia_sync.py -af config.json : copy all pages and their dependencies in async mode.

 json file config :

   {
    //the site must be configured in user-config.py file (see below)
    "sites":{
      "src":{ //set the site where to get the pages.
        "fam": "wikipedia",
        "code": "en"
      },
      "dst":{ //set the site where to copy the pages
        "fam": "kiwix",
        "code": "en"
      }
    },

    // list of page to copy
    "pages":[
     "Page1",
     "Page2"
     "MediaWiki:Common.css",
     "MediaWiki:Vector.js",
     ...
    ],

    // list of categories to copy
    "categories":[
      {
        "title":"Category 1",
        "namespace":0,
        "recurse":1
      },
      {
        "title":"Category 2",
        "namespace":4,
        "recurse":0
      }
      ...
    ],

    // list of modification on dest after copy
    "modifications":[
      {
        // modifications on pages mathing with RegEx1 and RegEx2
        "pages":["RegEx1","RegEx2"],
        // apply a list of substitutions on this pages
        // see https://docs.python.org/2/library/re.html#re.sub
        "substitutions":[
          {
            "pattern":"Pattern 1",
            "repl":"Remplacement 1"
          },
          {
            "pattern":"Pattern 2",
            "repl":"Remplacement 2"
          }
          ...
        ]
      },
      {
        // modifications on pages in Category 1 and 2
         "categories":[
            {
              "title":"Category 1",
              "namespace":0,
              "recurse":1
            },
            {
              "title":"Category 2",
              "namespace":4,
              "recurse":0
            }
            ...
          ],
        "substitutions":[
          {
            "pattern":"Pattern 3",
            "repl":"Remplacement 3"
          }
          ...
        ]
      },
      {
        // modifications on pages in namespaces 0 and 4
        "namespaces":[0,4],
        "substitutions":[
          {
            "pattern":"Pattern 4",
            "repl":"Remplacement 4"
          }
          ...
        ]
      },
      {
        "pages":["Page1"],
        "empty":true
      },
      {
        "pages":["Page2"],
        "delete":true
      }
      ...
    ]
  }

 IMPORTANT : We must have user-password.py and user-config.py in same
 directory of this script or set PYWIKIBOT2_DIR to congigure pywikibot.
 See : https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py

 author : Florent Kaisser <florent@kaisser.name>
 maintainer : Kiwix
"""

# To use WikiMedia API
from pywikibot import Site,Page,FilePage,Category, textlib

# To load JSON file config and check options
import sys
import json
import getopt

# To use regular expression
import re

# To use multi-threading
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count

MAX_WORKERS = cpu_count() * 5
LIMIT_DEPTH_SUBCAT = 5
DEFAULT_OPTIONS = dict(
    force = False,
    pagesSync = True,
    templatesSync = True,
    nbDepParse = 2,
    expandText = False,
    filesUpload = True,
    modifyPages = True,
    exportDir = "." ,
    resume = False,
    thumbWidth = 1024  ,
    maxSize = 200*1024*1024,
    async = False
)

#TODO : put in config file
# try to download thumb only for this mime type
# (is needed fot not try with no thumbnaible files )
THUMB_MIME = ['image/jpeg','image/png']
# always force copy this pages
ALWAYS_FORCE = ['Main Page','MediaWiki:Licenses']
# regex to exclude dependances
DEP_EXLUDE = "/Documentation$"

##############################
# Logs

def log(o) :
  sys.stdout.buffer.write((str(o)+"\n").encode("utf-8"))
  sys.stdout.flush()

def log_err(o) :
  sys.stderr.buffer.write(("ERROR : "+str(o)+"\n").encode("utf-8"))
  sys.stderr.flush()

#####################################
# Export/Import

def exportPagesTitle(pages, fileName, directory):
  with open("%s/mirroring_export_%s.json" % (directory,fileName),
    'w',encoding='utf-8') as f:
      f.write(json.dumps(pages, sort_keys=True, indent=4,ensure_ascii=False))

def importPagesTitle(fileName, directory):
  try :
    with open("%s/mirroring_export_%s.json" % (directory,fileName),
      'r', encoding='utf-8') as f:
        return json.load(f)
  except FileNotFoundError:
      log ("previous list of %s not found" % fileName)
  return []

###############################################
# Get dependencies of WikiPages

def mapTitle(pages):
  """ Map title from list of Page instance to list of String
  """
  return [ p.title() for p in pages ]

def getPageFromTitle(siteSrc, title):
  """ Search page from title from siteSrc wiki
    or file repository used by siteSrc
  """
  p = Page(siteSrc, title)
  fileRepo = siteSrc.image_repository()

  if ( fileRepo and p.is_filepage()  ):
    # if is a file, test on file repository (assume namespace is "File")
    return FilePage(fileRepo, re.sub(".*:","File:",title))
  elif( fileRepo and not p.exists() ):
    # if no exist on this repository, test on file repository
    # (case when template on file repository)
    return Page(fileRepo, title)

  return p

def getTemplateTitlesFromPage(siteSrc, exclude, nbPages, iTitles):
  """ Return a list of templates titles used by the page identified by her title

    siteSrc : page site
    exclude : regex to exclude template of the returned list
    nbPages : total number of pages in process template search (for log)
    iTitles[0] : page number in process template search (for log)
    iTitles[1] : title of the page containing templates to return
  """
  (i,title) = iTitles

  p = getPageFromTitle(siteSrc,title)

  # if not exist, abord
  if(not p.exists()):
    log_err ("%s not exist on source (%s) !" % (p.title(),str(p.site)))
    return []

  # get templates titles and apply exclude dependances filter
  tpltTitle = list(
                filter(
                   lambda t : not re.search(exclude,t),
                      mapTitle(p.templates())))

  nbTplt = len(tpltTitle)
  if(nbTplt > 0):
    log ("%i/%i Process %s : %i templates found " %
            (i+1,nbPages,title,nbTplt))
  else:
    log ("%i/%i Process %s :no templates found " %
            (i+1,nbPages,title))
  return tpltTitle;

def getFilesFromPage(siteSrc, nbPages, iTitles):
  """ Return list of files titles used by a page

    siteSrc : page site
    nbPages : total number of pages in process template search (for log)
    iTitles[0] : page number in process template search (for log)
    iTitles[1] : title of the page containing templates to return
  """
  (i,title) = iTitles

  p = getPageFromTitle(siteSrc,title)

  # if not exist, abord
  if(not p.exists()):
    log_err ("%s not exist on source (%s) !" % (p.title(),str(p.site)))
    return []

  # get files
  files = p.imagelinks()

  # remove redirection if list of file
  if(p.is_filepage()):
    files = filter( lambda f : not f.isRedirectPage(),files)

  nbFiles = len(list(files))
  if(nbFiles > 0):
    log ("%i/%i Process %s : %i files found" %
             (i+1,nbPages,title,nbFiles))
  else:
    log ("%i/%i Process %s : no files found" %
             (i+1,nbPages,title))

  # just return the title, no an instance of FilePage
  return mapTitle(files)

def imagesUsedByAllFilePage(site):
  for title,images in map(  lambda f : (f.title(),f.imagelinks()),
                        site.allimages()):
      log ("Process %s" % title)
      for i in images:
        yield i.title()

def getPagesTitleFromCategorieWithSubCat(cat, ns, recurse):
    log ("Retrieve pages from %s" % cat.title())

    return [cat.title()] \
            + [ subcat.title() for subcat in cat.subcategories() ] \
            +  mapTitle(cat.articles( namespaces=ns, recurse=recurse ))

def getPagesTitleFromCategories(site, categories, depth = 0):
  """ Return all pages from categories"""
  pages = []
  for c in categories :
    ns = c['namespace'] if ("namespace" in c) else None
    r = c['recurse'] if ("recurse" in c) else 0
    cat = Category(site,c['title'])

    pages.extend(getPagesTitleFromCategorieWithSubCat(cat,ns,r))

  return pages

###########################################
# Modify wiki pages

def removeSubPageOfProject(pageTitle, ns):
  """ specific case for project pages"""
  if(ns.id == 4 or ns.id == 102):
    if(ns.subpages):
      subPage = pageTitle.split("/",1)
      if(len(subPage) > 1):
        return subPage[1]
      else:
        return pageTitle
  else:
    return pageTitle

def getPageSrcDstFromTitle(src, dst, pageTitle,
                            primary = True, checkExist = True):
  """ return a tuple of :
      - source page instance,
      - new page instance on the destination,
      - namespace of the page

    src : page site source
    dst : page site destination
    pageTitle : title of page to copy
    primary : True if the page is not a dependance
    checkExist : check if page exist on source
  """
  p = Page(src, pageTitle)
  fileRepo = src.image_repository()
  ns = p.namespace()

  # for dependency (ns != 0)
  # if not exist on this site, test on file repository
  if(ns != 0 and checkExist and fileRepo and (not p.exists())):
     return getPageSrcDstFromTitle(
                fileRepo,dst,re.sub(".*:",str(ns),pageTitle),False,False)

  if(primary):
    return (p, Page(dst, removeSubPageOfProject(pageTitle, ns)), ns)
  else:
    return (p, Page(dst, pageTitle), ns)

def deletePage(src, dst, nbPages, iTitles):
  """ mark page to delete

    src : page site source
    dst : page site destination
    nbPages : total number of pages in deleting process (for log)
    iTitles[0] : page number in deleting process (for log)
    iTitles[1] : title of the page to delete
  """
  (i,title) = iTitles
  try:
    (pSrc,p,ns) = getPageSrcDstFromTitle(src,dst,title)

    log ("%i/%i Delete %s " %
          (i+1,nbPages,title))

    if(p.delete("Page not needed for Wikifundi", False, True, True)):
      return 1

  except Exception as e:
      log_err ("Error to delete page %s (%s)" %
        (title, e))
  return 0

def emptyPage(src, dst, nbPages, iTitles)  :
  """ empty a page

    src : page site source
    dst : page site destination
    nbPages : total number of pages in empty process (for log)
    iTitles[0] : page number in empty process (for log)
    iTitles[1] : title of the page to empty
  """
  (i,title) = iTitles
  try:
    (pSrc,p,ns) = getPageSrcDstFromTitle(src,dst,title)

    p.text = ""

    log ("%i/%i Empty of %s " %
          (i+1,nbPages,title))

    if(dst.editpage(p)):
      return 1

  except Exception as e:
      log_err ("Error to empty page %s (%s)" %
        (title, e))
  return 0

def subsOnPage(src, dst, subs, nbPages, iTitles):
  """ applies substitutions on page text

    src : page site source
    dst : page site destination
    subs : list of pair of args :
            - pattern to match (regex)
            - replacement text to substitut at matched regex
    nbPages : total number of pages in subs process (for log)
    iTitles[0] : total page number in subs process (for log)
    iTitles[1] : title of the page to apply subs
  """
  (i,title) = iTitles
  try:
    (pSrc,p,ns) = getPageSrcDstFromTitle(src,dst,title)

    if(p.exists()):
      for s in subs :
        pattern = s[0]
        repl = s[1]
        p.text = re.sub(pattern, repl, p.text)

      log ("%i/%i Process %s " %
        (i+1,nbPages,title))

      if(dst.editpage(p)):
        return 1

  except Exception as e:
      log_err ("Error to modify page %s (%s)" %
        (title, e))
  return 0

#####################################
# Mirroring wiki pages

def syncPage(src, dst, force, checkRedirect, expandText,
                primary, nbPages, iTitles):
  """ Copy ONE wiki pages from src to dst

     src : source site
     dst : destination site
     force : copy page if already exist
     checkRedirect : if true, follow redirect and copy also the targe
     expandText : use expandText méthode instead
                  text variable to get page content
     primary : if False, the page to copy is not a dependance
     nbPages : total number of pages in copy process (for log)
     iTitles[0] : page number in copy process (for log)
     iTitles[1] : title of the page to copy

     return true if success
  """

  (i,pageTitle) = iTitles
  try:
    (p,newPage,ns) = getPageSrcDstFromTitle(src,dst,pageTitle,primary)

    # do not copy page in "Main" namespace if it's dependency
    if((not primary) and ns == 0):
      return 0

    # if the page not exists, abord
    if(not p.exists()):
      log_err ("%s not exist on source !" % pageTitle)
      return 0

    log ("%i/%i %s Copy %s (%s) -> %s (%s)" % (i+1,nbPages,pageTitle,p.title(),
		str(p.namespace()),newPage.title(),str(newPage.namespace())))

    # if page exist on dest and no force -> do not sync this page
    if((not force)  and (not (newPage.title() in ALWAYS_FORCE))
		    and  newPage.exists() ):
      log ("%i/%i %s already exist. Use -f to force" % (i+1,nbPages,pageTitle))
      return 0

    # sync also the redirect target
    if(checkRedirect and p.isRedirectPage()):
      syncPage(src, dst, force, False, expandText, primary,
	nbPages,(i,p.getRedirectTarget().title()))

    # copy the content of the page
    if ( expandText ) :
      newPage.text = p.expand_text()
    else:
      newPage.text = p.text

    # commit the new page on dest wiki
    if ( dst.editpage(newPage) ):
      return 1

  except Exception as e:
    log_err ("Error on copy page %s (%s)"
              % (pageTitle, e))

  return 0

def uploadFile(src, srcFileRepo, dst, maxwith, maxsize, nbFiles, iTitles):
  """ Synchronize ONE wiki pages from src to dst

     src : source site
     srcFileRepo : file repository associate to source site
     dst : destination site
     maxwith : max with of an image (use thumb if upper)
     maxsize : max size of a page (ignore if upper)
     nbPages : total number of pages in copy process (for log)
     iTitles[0] : page number in copy process (for log)
     iTitles[1] : title of the page to copy

     return true if success
  """

  (i,fileTitle) = iTitles

  # check if file repo is None
  if(not srcFileRepo):
    srcFileRepo = src

  try:
    # try first on File Repository (assume always namespace "File")
    titleRepo = re.sub(".*:","File:",fileTitle)
    f = FilePage(srcFileRepo, titleRepo)

    # if page not exist in image repo
    # get from site src
    if(f.exists()):
      pageDst = FilePage(dst, titleRepo)
    else:
      f = FilePage(src, fileTitle)
      pageDst = FilePage(dst, fileTitle)

    # get thumbnail instead original file
    #  only avaible if file is in THUMB_MIME list
    if( f.latest_file_info['mime'] in THUMB_MIME ):
      url = f.get_file_url(maxwith)
      maxsize = 0 # do not check thumbnail file size
    else:
      url = f.get_file_url()

    size = f.latest_file_info['size']

    # if already exist, no upload
    # and check size limit
    if( not pageDst.exists()
        and (maxsize == 0 or size < maxsize )):

      # show informations
      log ("%i/%i Uploading file %s [%s] (%1.2f MB)" %
        (i+1, nbFiles,  fileTitle,
            url, size / 1024.0 / 1024.0))

      # start upload !
      if(dst.upload( pageDst, source_url=url,
                  comment="mirroring", text=f.expand_text(),
                  ignore_warnings = True, report_success = False)):
        return 1
    else:
      log ("%i/%i file already uploaded or to large %s [%s] (%1.2f MB)" %
        (i+1, nbFiles,  fileTitle,
            url, size / 1024.0 / 1024.0))

  except Exception as e:
    log_err ("Error on upload file %s (%s)" %
            (fileTitle,e))
  return 0

########################################################
# Mapping functions
# allow to use async mapping

def subsOnPages(src, dst, pages, subs) :
  subs = partial(subsOnPage,src,dst,subs,len(pages))
  return sum(map(subs,enumerate(pages)))

def emptyPages(src, dst, pages) :
  empty = partial(emptyPage,src,dst,len(pages))
  return sum(map(empty,enumerate(pages)))

def deletePages(src, dst, pages) :
  delete = partial(deletePage,src,dst,len(pages))
  return sum(map(delete,enumerate(pages)))

def uploadFilesWithThreadPool(src, srcFileRepo, dst, files, maxwith, maxsize):
  upload = partial(uploadFile,src, srcFileRepo,
                    dst, maxwith, maxsize,len(files))
  with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    return sum(ex.map(upload,enumerate(files)))
  return 0

def uploadFiles(src, srcFileRepo, dst, files, maxwith, maxsize):
  upload = partial(uploadFile,src, srcFileRepo,
                    dst, maxwith, maxsize,len(files))
  return sum(map(upload,enumerate(files)))

def syncPagesWithThreadPool(src, dst, pages, expandText,
                              primary, force = False):
  sync = partial(syncPage, src,dst,force,True,
                  expandText, primary,  len(pages))
  with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    return sum(ex.map(sync,enumerate(pages)))
  return 0

def syncPages(src, dst, pages, expandText, primary, force = False):
  sync = partial(syncPage, src,dst,force,True,
                  expandText, primary,  len(pages))
  return sum(map(sync,enumerate(pages)))

def getTemplatesFromPages(siteSrc, pages, exclude):
  getTplt = partial(getTemplateTitlesFromPage, siteSrc, exclude, len(pages))
  templates = []
  for tList in map(getTplt,enumerate(pages)):
    templates.extend(tList)
  # apply set() to delete duplicate
  return list(set(templates))

def getFilesFromPages(siteSrc, pages):
  getFiles = partial(getFilesFromPage, siteSrc, len(pages))
  files = []
  for fList in map(getFiles,enumerate(pages)):
    files.extend(fList)
  # apply set() to delete duplicate
  return list(set(files))

######################################
# Entry points

def modifyPages(siteSrc, siteDst,
               pages, modifications):
  """ modify wiki pages on siteDst from pages titles

    siteSrc : source site
    siteDst : destination site
    pages : list of pages titles to modified
    modifications : list of modification options

    return the number of succes modified pages
  """

  # apply modifications
  nbMods = 0

  #add existing pages in dst
  #pages.extend(mapTitle(siteDst.allpages()))

  for mod in modifications :
    pageMods = []
    if('pages' in mod):
      for regex in mod['pages']:
        # get all pages matched by regex
        pageMods.extend (filter(
                 lambda p : re.search(regex,p),
                 pages
               ))

    if('categories' in mod):
        pageMods.extend (getPagesTitleFromCategories(siteSrc,
                          mod['categories']))

    if('namespaces' in mod):
      for ns in mod['namespaces']:
        pageMods.extend (mapTitle(siteDst.allpages(namespace=ns)))

    # apply set() on pageMods to delete duplicate
    pageModsUniq = list(set(pageMods))

    if('substitutions' in mod):
      # get all supstitution to apply on list of pages
      subs = map(
               lambda s : (re.compile(s['pattern'],re.DOTALL),s['repl']),
               mod['substitutions']
             )
      nbMods += subsOnPages(siteSrc, siteDst, pageModsUniq, list(subs))

    if('empty' in mod):
      nbMods += emptyPages(siteSrc, siteDst, pageModsUniq)

    if('delete' in mod):
      nbMods += deletePages(siteSrc, siteDst, pageModsUniq)

  return nbMods

def mirroringAndModifyPages(
  srcFam, srcCode, dstFam, dstCode,
  pagesName, categories,
  modifications, options) :
  """ Synchronize wiki pages from named page list
        and named categories list

    return the number of succes synchronized pages and files
  """

  # get options
  force = options['force']
  exportDir = options["exportDir"]
  expandText = options["expandText"]

  # configure sites
  siteSrc = Site(fam=srcFam,code=srcCode)
  siteDst = Site(fam=dstFam,code=dstCode)

  # logging now to modify pages on dest
  siteDst.login()

  # disable slow down wiki write mechanics
  siteDst.throttle.maxdelay=0

  # init pages to copy
  pages = pagesName
  templates = []
  files = []

  # regex compile to exlucde dependances pages
  reg_exlude_dep = re.compile(DEP_EXLUDE)

  nbMods = 0
  nbPagesSync = 0
  nbPagesUpload = 0
  nbPagesTemplate = 0

  # get pages in categories
  if( categories ):
    pages.extend(getPagesTitleFromCategories(siteSrc, categories))

  exportPagesTitle(pages,"pages",exportDir)

  # try to resume
  if( options["resume"] ):
    templates = importPagesTitle("templates",exportDir)
    files = importPagesTitle("files",exportDir)

  # get files to copy
  if(options['filesUpload']) :
    log ("====== Collect Files Dependances")
    # do not get images on templates (to avoid to many unused files)
    files = getFilesFromPages(siteSrc, pages)
    log ("%i files to sync" % len(files))
    exportPagesTitle(files,"files",exportDir)

  # get templates to copy
  for i in range(options["nbDepParse"]):
      log ("==============================")
      log ("====== Collect Templates Dependances #%i" % i)
      depTmpt = getTemplatesFromPages(siteSrc, pages + templates,
                                        reg_exlude_dep)
      log ("%i templates to sync" % len(templates))

      # update list of templates and files
      #  with duplicates removed
      templates = list(set(templates + depTmpt))
      exportPagesTitle(templates,"templates",exportDir)

  # sync all pages, templates and associated files
  log ("======================")
  log ("====== Start Mirroring")

  # Now, upload file, templates and pages !
  # The ORDER is important !
  if(options["async"]):
    if(options['filesUpload']):
      log ("====== Upload files with %i thread pool" % MAX_WORKERS)
      nbPagesUpload = uploadFilesWithThreadPool (
                siteSrc, siteSrc.image_repository(), siteDst,
                files, options["thumbWidth"], options["maxSize"])
      log ("====== Upload images used by all file pages with %i thread pool"
                                                            % MAX_WORKERS)
      nbPagesUpload += uploadFilesWithThreadPool (
                siteSrc, siteSrc.image_repository(), siteDst,
                set(imagesUsedByAllFilePage(siteDst)),
                options["thumbWidth"], options["maxSize"])
    if(options['templatesSync']):
      log ("====== Sync template with %i thread pool" % MAX_WORKERS)
      nbPagesTemplate = syncPagesWithThreadPool(siteSrc, siteDst,
                        templates,expandText, False, force)

    if( options["pagesSync"] ):
      log ("====== Sync pages with %i thread pool" % MAX_WORKERS)
      nbPagesSync = syncPagesWithThreadPool(siteSrc, siteDst,
			pages, expandText, True, force)
  else:
    if(options['filesUpload']):
      log ("====== Upload files")
      nbPagesUpload = uploadFiles (
                siteSrc, siteSrc.image_repository(), siteDst,
                files, options["thumbWidth"], options["maxSize"])
      log ("====== Upload images used by all file pages")
      nbPagesUpload += uploadFiles (
                siteSrc, siteSrc.image_repository(), siteDst,
                set(imagesUsedByAllFilePage(siteDst)),
                options["thumbWidth"], options["maxSize"])
    if(options['templatesSync']):
      log ("====== Sync template")
      nbPagesTemplate = syncPages(siteSrc, siteDst,
                        templates, expandText, False ,force )

    if( options["pagesSync"] ):
      log ("====== Sync pages")
      nbPagesSync = syncPages(siteSrc, siteDst,
			pages, expandText, True,force)

  if( modifications and options["modifyPages"] ):
    log ("============================")
    log ("====== Process Modifications")
    nbMods =  modifyPages(siteSrc, siteDst,
                          pages + templates + files, modifications)
    log ("====== Commit all pages ")
    subsOnPages(siteSrc, siteDst, pages + templates, [])

  return (nbPagesSync,nbPagesUpload,nbPagesTemplate,nbMods)

def processConfig(cfg, options):
  """ Synchronize wiki pages from loaded config

    return the number of succes synchronized pages, files and modifications
  """
  try:

    src = cfg['sites']['src']
    dst = cfg['sites']['dst']
    pages = cfg['pages']
    cats = cfg['categories']
    mods = cfg['modifications']

    (nbPagesSync,nbPagesUpload,nbPagesTemplate,nbMods) \
        = mirroringAndModifyPages(
            src['fam'], src['code'],
            dst['fam'], dst['code'],
            pages, cats, mods, options
        )

    log ("%i pages copied, \
          %i files copied, \
          %i templates copied, \
          %i pages modified"
        % (nbPagesSync,nbPagesUpload,nbPagesTemplate,nbMods))

  except KeyError as e:
    log_err ("KeyError error in mirroring file : %s" % e)

######################################
# Main parts

def main():
  options = DEFAULT_OPTIONS

  try:
    opts, args = getopt.getopt(sys.argv[1:],
      "hftd:xupmre:w:s:a",
      [ "help",
        "force",
        "no-sync-templates",
        "dependance-nb-parse",
        "expand-text",
        "no-upload-files",
        "no-sync",
        "no-modify",
        "resume",
        "export-dir",
        "thumbwidth",
        "maxsize",
        "async"
      ]
    )

  except (getopt.error, msg):
    log_err (("args error : %s" % str(msg)))
    log_err ("Use --help to show help instructions")
    sys.exit(2)

  # parse args
  for (opt, arg) in opts:
    if opt in ("-h", "--help"):
      log(__doc__)
      sys.exit(0)
    if opt in ("-f", "--force"):
      options["force"] = True
    if opt in ("-t", "--no-sync-templates"):
      options["templatesSync"] = False
    if opt in ("-d", "--dependance-nb-parse"):
      options["nbDepParse"] = int(arg)
    if opt in ("-x", "--expand-text"):
      options["expandText"] = True
    if opt in ("-u", "--no-upload-files"):
      options["filesUpload"] = False
    if opt in ("-p", "--no-sync"):
      options["pagesSync"] = False
    if opt in ("-m", "--no-modify"):
      options["modifyPages"] = False
    if opt in ("-r", "--resume"):
      options["resume"] = True
    if opt in ("-e", "--export-dir"):
      options["exportDir"] = arg
    if opt in ("-w", "--thumbwidth"):
      options["thumbWidth"] = int(arg)
    if opt in ("-s", "--maxsize"):
      options["maxSize"] = int(arg)
    if opt in ("-a", "--async"):
      options["async"] = True

  log (options)

  # process each config file
  for filename in args:
    log ("Process %s" % filename)

    with open(filename, 'r', encoding='utf-8') as cfgfile:
      try:
        processConfig(json.load(cfgfile),options)
      except json.decoder.JSONDecodeError as e:
        log_err ("Syntax error in mirroring file : %s" % e)

if __name__ == "__main__":
  main()
