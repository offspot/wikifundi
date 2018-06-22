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
  -p, --no-sync : do not copy anything (default : false)
  -m, --no-modify : do not modify pages (default : false)
  -r, --resume : try to resume previous sync (default : false)
  -e, --export-dir <directory> : write resume files in this directory (default : current directory)
  -w, --thumbwidth :try to download thumbnail image with this width instead original image (default : 1024)
  -s, --maxsize : do not files download greater to this limit (default : 100MB)
  -a, --async : execute mirroring in async mode (5 threads / cpu). No works with SQLITE database. (default : false)
  
 exemples :
 ./wikimedia_sync.py -m 5MB -w 2000 config.json : sync page, templates, files and modify pages. Do not copy file > 5MB and Copy images (jpeg and png) in 2000px (if available).
 ./wikimedia_sync.py -tu config.json : sync and modify pages. Do not copy dependances (templates and files).
 ./wikimedia_sync.py -p config.json : just modify pages.
 ./wikimedia_sync.py -pm config.json : do anything.
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

DEFAULT_OPTIONS = dict(
    force = False, 
    pagesSync = True,    
    templatesSync = True, 
    templatesDepSync = True, 
    filesUpload = True,
    modifyPages = True,
    exportDir = "." ,
    resume = False,
    thumbWidth = 1024  ,
    maxSize = 100*1024*1024*1024, 
    async = False
)

# try to download thumb only for this mime type 
# (is needed fot not try with no thumbnaible files )
thumbmime = ['image/jpeg','image/png']

##############################
# Logs

def log(o) :
  sys.stdout.buffer.write((str(o)+"\n").encode("utf-8"))
  sys.stdout.flush()
  
def log_err(o) :
  sys.stderr.buffer.write((str(o)+"\n").encode("utf-8"))  
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
      log_err ("No previous list of %s is found" % fileName)
  return []   
  

###############################################
# Get dependencies of WikiPages
  
def mapTitle(pages) : 
  return [ p.title() for p in pages ]   
  
def getTemplateTitlesFromPage(siteSrc, nbPages, iTitles) :
  (i,title) = iTitles
  
  p = Page(siteSrc, title)
  
  if ( p.is_filepage()  ):
    # check if the file is in a specific file repository
    f = FilePage(siteSrc.image_repository(), title)
    if(f.exists()):
      # get template on page in specific file repository
      tplt = f.templates()
    else:
      # get templates from original site
      tplt = p.templates()
  else:
  # get templates
    tplt = p.templates()
    
  nbTplt = len(tplt)
  if(nbTplt > 0):
    log ("%i/%i Process %s : %i templates found " % 
            (i+1,nbPages,title,nbTplt))
  else:
    log ("%i/%i Process %s :no templates found " % 
            (i+1,nbPages,title))            
  return mapTitle(tplt)
  
def getFilesFromPage(siteSrc, nbPages, iTitles) : 
  (i,title) = iTitles
  
  pages = Page(siteSrc, title).imagelinks()
  
  nbFiles = len(list(pages))
  if(nbFiles > 0):
    log ("%i/%i Process %s : %i files found" % 
             (i+1,nbPages,title,nbFiles))
  else:
    log ("%i/%i Process %s : no files found" % 
             (i+1,nbPages,title))  
  return mapTitle(pages)  
  
def getPagesTitleFromCategorie(site, categories):
  pages = []
  cats = [(Category(
              site,
              c['title']),
              c['namespace'] if ("namespace" in c) else None,
              c['recurse'] if ("recurse" in c) else 0,
          ) for c in categories ]
  # retrieve all pages from categories
  for (cat,ns,r) in cats :
    pages.append(cat.title())
    log ("Retrieve pages from %s" % cat.title())
    # add pages to sync of this categorie
    pages.extend(mapTitle(cat.articles( namespaces=ns, recurse=r )))
    
  return pages  
  
###########################################
# Modify wiki pages

def getPageSrcDstFromTitle(src, dst, pageTitle):
  p = Page(src, pageTitle)
  ns = p.namespace()
  
  # specific case for "Project pages"
  # TODO : use an option ! 
  if(ns.id == 4 or ns.id == 102):
    if(ns.subpages):
      subPage = pageTitle.split("/",1)
      if(len(subPage) > 1):
        title = subPage[1]
      else:
        title = pageTitle
  else:
    title = pageTitle
  
  newPage = Page(dst, title)
  
  if(newPage.site != dst):
    newPage = Page(dst, newPage.titleWithoutNamespace(), ns.id)
  
  return (p,newPage,ns)

def emptyPage(src, dst, nbPages, iTitles)  :
  (i,title) = iTitles
  (pSrc,p,ns) = getPageSrcDstFromTitle(src,dst,title)
  try:
    p.text = ""
    
    log ("%i/%i Empty of %s " % 
          (i+1,nbPages,title))

    if(dst.editpage(p)):
      return 1
    
  except Exception as e:
      log_err ("Error to empty page %s (%s)" % 
        (title, e))
  return 0  
  
def subsOnPage(src, dst, subs, nbPages, iTitles)  :
  (i,title) = iTitles
  (pSrc,p,ns) = getPageSrcDstFromTitle(src,dst,title)
  try:
    
    for s in subs :
      pattern = s[0]
      repl = s[1]
      p.text = re.sub(pattern, repl, p.text)
      
    log ("%i/%i Modification of %s " % 
      (i+1,nbPages,title))
      
    if(dst.editpage(p)):
      return 1
    
  except Exception as e:
      log_err ("Error to modify page %s (%s)" % 
        (title, e))
  return 0  
  
#####################################  
# Mirroring wiki pages 
    
def syncPage(src, dst, force, checkRedirect, nbPages, iTitles):
  """Synchronize ONE wiki pages from src to dst
  
     return true if success
  """

  (i,pageTitle) = iTitles
  (p,newPage,ns) = getPageSrcDstFromTitle(src,dst,pageTitle)
     
  try:      
    # if page exist on dest and no force -> do not sync this page
    # always copy page for "Project pages"
    # TODO : use an option ! 
    if((not force) and newPage.exists() and ns.id != 4 and ns.id != 102):  
      log ("%i/%i %s already exist. Use -f to force" % (i+1,nbPages,pageTitle))
      return 0
    
    #sync also the redirect target 
    if(checkRedirect and p.isRedirectPage()):
      syncPage(src, dst, force, False, nbPages, 
        (i,p.getRedirectTarget().title()))

    # copy the content of the page
    newPage.text = p.text 
    
    log ("%i/%i Copy %s" % (i+1,nbPages,pageTitle))
    
    # commit the new page on dest wiki
    if ( dst.editpage(newPage) ):
      return 1
      
  except Exception as e:
    log_err ("Error on copy page %s (%s)" 
              % (pageTitle, e))
    
  return 0
  
def uploadFile(src, srcFileRepo, dst, maxwith, maxsize, nbFiles, iTitles ):
  (i,fileTitle) = iTitles

  # create a new file on dest wiki
  pageDst = FilePage(dst, fileTitle)
  f = FilePage(srcFileRepo, fileTitle)
  
  try:
    # if page not exist in image repo
    # get from site src
    if(not f.exists()):
      f = FilePage(src, fileTitle)

    # get thumbnail instead original file
    #  only avaible if file is in thumbmime list
    if( f.latest_file_info['mime'] in thumbmime ):
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
                  comment="mirroring", text=f.text, 
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
# Mapping

def subsOnPages(src, dst, pages, subs) :  
  subs = partial(subsOnPage,src,dst,subs,len(pages))
  return sum(map(subs,enumerate(pages)))

def emptyPages(src, dst, pages) : 
  empty = partial(emptyPage,src,dst,len(pages))
  return sum(map(empty,enumerate(pages)))
  
def uploadFilesWithThreadPool(src, srcFileRepo, dst, files, maxwith, maxsize) :
  upload = partial(uploadFile,src, srcFileRepo, 
                    dst, maxwith, maxsize,len(files))
  with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:                  
    return sum(ex.map(upload,enumerate(files)))
  return 0  
  
def uploadFiles(src, srcFileRepo, dst, files, maxwith, maxsize) :
  upload = partial(uploadFile,src, srcFileRepo, 
                    dst, maxwith, maxsize,len(files))
  return sum(map(upload,enumerate(files)))  
  
def syncPagesWithThreadPool(src, dst, pages, force = False): 
  sync = partial(syncPage, src,dst,force,True, len(pages))
  with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    return sum(ex.map(sync,enumerate(pages)))
  return 0

def syncPages(src, dst, pages, force = False): 
  sync = partial(syncPage, src,dst,force,True, len(pages))
  return sum(map(sync,enumerate(pages)))
    
def getTemplatesFromPages(siteSrc, pages) :
  getTplt = partial(getTemplateTitlesFromPage, siteSrc, len(pages))
  templates = []
  for tList in map(getTplt,enumerate(pages)):
    templates.extend(tList)
  # apply set() to delete duplicate
  return list(set(templates))  
   
def getFilesFromPages(siteSrc, pages) :
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
  # apply modifications
  nbMods = 0   

  for mod in modifications :
    pageMods = []
    if('pages' in mod):
      for regex in mod['pages']:
        # get all pages to modify from regex
        pageMods.extend (filter( 
                 lambda p : re.search(regex,p), 
                 pages
               ))
    
    if('categories' in mod):
        pageMods.extend (getPagesTitleFromCategorie(siteSrc, 
                          mod['categories']))
    
    if('namespaces' in mod):
      for ns in mod['namespaces']:
        pageMods.extend (mapTitle(siteDst.allpages(namespace=ns)))               
         
    # apply set() on pageMods to delete duplicate
    pageModsUniq = list(set(pageMods))
            
    if('substitutions' in mod):
      # get all supstitution to apply on list of pages
      subs = map( 
               lambda s : (re.compile(s['pattern']),s['repl']), 
               mod['substitutions']
             )
      nbMods += subsOnPages(siteSrc, siteDst, pageModsUniq, list(subs))
        
    if('empty' in mod):
      nbMods += emptyPages(siteSrc, siteDst, pageModsUniq) 
  
  return nbMods;
  
def mirroringPagesWithDependances( siteSrc, siteDst, 
                              pages, options) : 
  """ Get the dependances of pages (templates and files),
      sync all pages and upload files contained in the pages
  
    options : dict from args scripts
    
    return the number of succes synchronized pages and files 
  """
  
  # get options
  force = options['force']
  exportDir = options["exportDir"]
  
  log ("%i pages to sync" % len(pages))
  # export titles of collected pages to sync
  exportPagesTitle(pages,"pages",exportDir)
    
  # try to restore previous state
  templates = importPagesTitle("templates",exportDir)
  if(options['templatesSync']):
    if(options['resume'] and len(templates) > 0):
      # the imported file contains all templates to sync
      options['templatesDepSync'] = False
    else:
      # collect template used by pages
      templates = getTemplatesFromPages(siteSrc, pages)
      exportPagesTitle(templates,"templates",exportDir)
    log ("%i templates to sync" % len(templates))
    
  # try to restore previous state
  files = importPagesTitle("files",exportDir)
  if(options['filesUpload']) :
    if((not options['resume']) or (len(files) == 0)):
      #collect files used by pages
      files = getFilesFromPages(siteSrc, pages)
      exportPagesTitle(files,"files",exportDir)
    log ("%i files to sync" % len(files))
    
  if(options['templatesDepSync']):    
    dependances = getTemplatesFromPages(siteSrc, files+templates)
    #delete duplicate
    templates = list(set(templates+dependances))
    exportPagesTitle(templates,"templates",exportDir)
    log ("%i templates to sync" % len(templates))
    
  #sync all pages, templates and associated files
  nbPageSync = 0
  nbPageUpload = 0
  
  if(options["async"]):
    log ("====== Sync pages with %i thread pool" % MAX_WORKERS)
    nbPageSync += syncPagesWithThreadPool(siteSrc, siteDst, 
                                            pages, force )  
      
    if(options['templatesSync']):
      log ("====== Sync template with %i thread pool" % MAX_WORKERS)
      nbPageSync += syncPagesWithThreadPool(siteSrc, siteDst, 
                                              templates, force )
      
    if(options['filesUpload']):
      log ("====== Upload files with %i thread pool" % MAX_WORKERS)
      nbPageUpload += uploadFilesWithThreadPool (siteSrc, siteSrc.image_repository(), siteDst, 
                files, options["thumbWidth"], options["maxSize"])
  else:
    log ("====== Sync pages")
    nbPageSync += syncPages(siteSrc, siteDst, pages, force )  
      
    if(options['templatesSync']):
      log ("====== Sync template")
      nbPageSync += syncPages(siteSrc, siteDst, templates, force )
      
    if(options['filesUpload']):
      log ("====== Upload files")
      nbPageUpload += uploadFiles (siteSrc, siteSrc.image_repository(), siteDst, 
                files, options["thumbWidth"], options["maxSize"])  
              
  return (nbPageSync,nbPageUpload)
        
def mirroringAndModifyPages(
  srcFam, srcCode, dstFam, dstCode, 
  pagesName, categories, 
  modifications, options) :
  """Synchronize wiki pages from named page list
        and named categories list
    
    return the number of succes synchronized pages and files
    
  """  
  
  # configure sites
  siteSrc = Site(fam=srcFam,code=srcCode)
  siteDst = Site(fam=dstFam,code=dstCode)
  
  # logging now to modify pages on dest
  siteDst.login()
  
  # disable slow down wiki write mechanics 
  siteDst.throttle.maxdelay=0  
  
  # init pages to copy
  pages = pagesName
  
  nbMods = 0
  nbPagesSync = 0
  nbPagesUpload = 0
  
  # get pages in categories
  if( categories ):
    pages.extend(getPagesTitleFromCategorie(siteSrc, categories))

    
  if( options["pagesSync"] ):
    # copy all pages !
    (nbPagesSync,nbPagesUpload) = mirroringPagesWithDependances(
                                    siteSrc, siteDst, pages, options)    

  if( modifications and options["modifyPages"] ):
    nbMods =  modifyPages(siteSrc, siteDst, pages, modifications)        
      
  return (nbPagesSync,nbPagesUpload,nbMods)

def processConfig(cfg, options):
  """Synchronize wiki pages from loaded config
    
    return the number of succes synchronized pages, files and 
          modifications
  """
  try:

    src = cfg['sites']['src']
    dst = cfg['sites']['dst']
    pages = cfg['pages']
    cats = cfg['categories']
    mods = cfg['modifications']
    
    (nbPagesSync,nbPagesUpload,nbMods) = mirroringAndModifyPages(
      src['fam'], src['code'], 
      dst['fam'], dst['code'], 
      pages, cats, mods, options
    )
    
    log ("%i pages copied, %i files copied, %i pages modified" 
              % (nbPagesSync,nbPagesUpload,nbMods))

  except KeyError as e:
    log_err ("KeyError error in mirroring file : %s" % e)
      

######################################
# Main parts

def main():
  options = DEFAULT_OPTIONS
  
  try:
    opts, args = getopt.getopt(sys.argv[1:], 
      "hftdupmre:w:s:a", 
      [ "help",
        "force",
        "no-sync-templates",
        "no-sync-dependances-templates",
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
      options["templatesDepSync"] = False
    if opt in ("-d", "--no-sync-dependances-templates"):
      options["templatesDepSync"] = False
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
            
  # check coherence, fix if needed
  if(not options["pagesSync"]):
      options["templatesSync"] = False
      options["templatesDepSync"] = False
      options["filesUpload"] = False

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
  

