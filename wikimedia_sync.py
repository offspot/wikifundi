#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# author : Florent Kaisser
# maintainer : kwix

"""
 wikimedia_sync.py

 usage : ./wikimedia_sync.py [options] config_file1.json, config_file2.json, ...

 Copy WikiMedia pages from a Wiki source (ex : a Wikipedia) to a Wiki 
 destionation (like a third-party wikis).

 A config file given in args contain name of pages and categories to 
 synchronize, and Wiki source and destination.

 IMPORTANT : We must have user-password.py and user-config.py in same 
 directory of this script to congigure pywikibot. 
 See : https://www.mediawiki.org/wiki/Manual:Pywikibot/user-config.py
"""

# For use WikiMedia API
from pywikibot import Site,Page,FilePage,Category,logging

# For load JSON file config and check options
import sys
import json
import getopt

# We use typing 
from typing import List
PageList = List[Page]
FileList = List[FilePage]

DEFAULT_OPTIONS = dict(
    force = False, 
    templatesSync = True, 
    templatesDepSync = True, 
    filesUpload = True)

def uploadFiles(src : Site, dst : Site, files : FileList) -> int :

  nbImages = len(files)
  for i,f in enumerate(files):
    try:
      pageDst = FilePage(dst, f.title())
      if(not pageDst.exists()):
        print ("== %i/%i Upload file %s" % (i+1, nbImages,  f.title()))
        dst.upload( pageDst, source_url=f.get_file_url(), comment=f.title(), text=f.text, ignore_warnings = False)
                    
    except Exception:
      print ("Error on upload file %s" % f.title())

def syncPages(src : Site, dst : Site, pages : PageList, force = False) -> int: 
  """Synchronize wiki pages from src to dst
    
    return the number of synchronized pages succes
  """
  
  nbSyncPage = 0
  nbPage = len(pages)
  
  for i,p in enumerate(pages):

    title = p.title()
    print ("== %i/%i Sync %s " % (i+1,nbPage,title))
    
    try:      
      # create a new page on dest wiki
      newPage = Page(dst, title)
      
      if((not force) and newPage.exists()):  
        print ("Page %s exist" % title)
      # sometime, pywikibot return a page in a different site, 
      # here check this
      elif(newPage.site == dst):
      #elif(newPage.canBeEdited()):
        # copy the content of the page
        newPage.text = p.text
        
        # commit the new page on dest wiki
        if (dst.editpage(newPage)):
          nbSyncPage = nbSyncPage + 1
        else:
          print ("Error on saving page %s" % title)
      else:
        print ("Page %s not editable on dest" % title)
    except Exception:
      print ("Error on sync page %s" % title)
      
  return nbSyncPage
  
def getTemplatesFromPages(pages : PageList) -> PageList :
  templates = []
  for p in pages :
    # get templates used by p
    tplt = p.templates()
    nbTplt = len(tplt)
    if(nbTplt > 0):
      print ("Process %i templates of %s" % (nbTplt, p.title()))
      templates += tplt
      
  return list(set(templates))  
  
def getFilesFromPages(pages : PageList) -> FileList :
  files = []
  for p in pages :
    # get files used by p
    f = list(p.imagelinks())
    nbFiles = len(f)
    if(nbImg > 0):
      print ("Process %i images of %s" % (nbFiles, p.title()))
      images += f  
  return list(set(images))
  
def syncPagesWithDependances( siteSrc : Site, siteDst : Site, 
                              pages : PageList, options : dict) -> int: 

  #get templates and files used by pages
  
  if(options['filesUpload']) :
    images = getFilesFromPages(pages)
    
  if(options['templatesSync']):
    templates = getTemplatesFromPages(pages)
    
  if(options['templatesDepSync']):    
    dependances = getTemplatesFromPages(templates)
  
  #sync all pages, templates and associated files
  nbPageSync = 0
  
  if(options['templatesDepSync']):
    print ("====== Sync template dependances")
    nbPageSync += syncPages(siteSrc, siteDst, dependances, options['force'] )
    
  if(options['templatesSync']):
    print ("====== Sync template")
    nbPageSync += syncPages(siteSrc, siteDst, templates, options['force'] )
    
  print ("====== Sync pages")
  nbPageSync += syncPages(siteSrc, siteDst, pages, options['force'] )  
  
  if(options['filesUpload']):
    print ("====== Upload files")
    uploadFiles (siteSrc, siteDst, images)  
  
  return nbPageSync;  
  
def syncPagesAndCategories(
  srcFam : str, srcCode : str, dstFam : str, dstCode : str, 
  pagesName : List[str], categoriesName : List[str], 
  options : dict) -> int :
  """Synchronize wiki pages from named page list
        and named categories list
    
    return the number of synchronized pages succes
  """  
  
  # configure sites
  siteSrc = Site(fam=srcFam,code=srcCode)
  siteDst = Site(fam=dstFam,code=dstCode)
  
  siteDst.login()
  
  #disable mechanics to slow down wiki write
  siteDst.throttle.maxdelay=0  
  
  pages = []
  
  if( pagesName ):
    # pages from their names
    pages += [ Page(siteSrc, name) for name in pagesName ]
  
  if( categoriesName ):
    # retrieve all pages from categories
    categories = [ Category(siteSrc,name) for name in categoriesName ]
    for cat in categories :
      pages += [ Page(siteSrc, cat.title()) ]
      print ("Retrieve pages from " + cat.title())
      # add pages of this categorie to pages list to sync
      pages += list( cat.articles() )
  
  #sync all pages !
  return syncPagesWithDependances(siteSrc, siteDst, pages, options)    


def syncFromJSONFile(fileconfig, options):
  print ("Process %s" % fileconfig)

  with open(fileconfig, 'r') as jsonfile:
    cfg = json.load(jsonfile)
    src = cfg['sites']['src']
    dst = cfg['sites']['dst']
    pages = cfg['pages']
    cats = cfg['categories']
    
    nb = syncPagesAndCategories(src['fam'], src['code'], dst['fam'], 
      dst['code'], pages, cats, options)
      
    print ("%i pages synchronized" % nb)

######################################
# Main parts

def main():
  options = DEFAULT_OPTIONS
  
  try:
    opts, args = getopt.getopt(sys.argv[1:], 
      "hftdu", 
      [ "help",
        "force",
        "sync-templates",
        "sync-dependances-templates",
        "upload-files"
      ]
    )
  except (getopt.error, msg):
    print (("args error : %s" % str(msg)))
    print ("Use --help to show help instructions")
    sys.exit(2)

  # parse args
  for (opt, arg) in opts:
    if opt in ("-h", "--help"):
      print(__doc__)
      sys.exit(0)
    if opt in ("-f", "--force"):
      options["force"] = True
    if opt in ("-t", "--sync-templates"):
      options["templatesSync"] = True
    if opt in ("-d", "--sync-dependances-templates"):
      options["templatesDepSync"] = True
    if opt in ("-u", "--upload-files"):  
      options["filesUpload"] = True
      
  # check coherence, fix if needed
  if(options["templatesDepSync"] and not options["templatesSync"]):
      options["templatesSync"] = True

  # process each config file
  for arg in args:
    syncFromJSONFile(arg,options)
    
if __name__ == "__main__":
  main()

######################################
# Test parts

def test():
  syncFromJSONFile("test.json", DEFAULT_OPTIONS)

