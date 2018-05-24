#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 wikimedia_sync.py

 usage : ./wikimedia_sync.py <config_file.yml>

 author : Florent Kaisser

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

# For load YAML file config
import sys
import json

# We use typing 
from typing import List
PageList = List[Page]
FileList = List[FilePage]

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
    tplt = p.templates()
    nbTplt = len(tplt)
    if(nbTplt > 0):
      print ("Process %i templates of %s" % (nbTplt, p.title()))
      templates += tplt
      
  return list(set(templates))  
  
def getFilesFromPages(pages : PageList) -> FileList :
  images = []
  for p in pages :
    img = list(p.imagelinks())
    nbImg = len(img)
    if(nbImg > 0):
      print ("Process %i images of %s" % (nbImg, p.title()))
      images += img  
  return list(set(images))
  
def syncPagesWithDependances( siteSrc : Site, siteDst : Site, 
                              pages : PageList, options : dict) -> int: 

  #get dependances
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


######################################
# Main parts

def main(fileconfig):
  options = dict(force = False, templatesSync = True, templatesDepSync = True, filesUpload = True)

  with open(fileconfig, 'r') as jsonfile:
    cfg = json.load(jsonfile)
    src = cfg['sites']['src']
    dst = cfg['sites']['dst']
    pages = cfg['pages']
    cats = cfg['categories']
    
    nb = syncPagesAndCategories(src['fam'], src['code'], dst['fam'], 
      dst['code'], pages, cats, options)
      
    print ("%i pages synchronized" % nb)

if __name__ == "__main__":
  if(len(sys.argv)>1):
    main(sys.argv[1])
  else:
    print ("Usage : ./wikimedia_sync.py <config_file.yml>")
  

######################################
# Test parts

def test() -> bool:
  siteSrc = Site(fam="wikipedia",code="en")
  siteDst = Site(fam="kiwix")
  pages = [Page(siteSrc,"New_York_City"), 
           Page(siteSrc,"Paris"), 
           Page(siteSrc,"Geneva") ]
           
  simpleTest = (syncPages(siteSrc, siteDst, pages) == 3)
  
  pagesName = ["The_Handmaid's_Tale_(TV_series)","Black_Mirror","The_Wire"]
  catsName = ["Cuba","Lille"]
  
  mainTest = ( syncPagesAndCategories("wikipedia","en","kiwix","kiwix",
                pagesName, catsName ) == 27)
  
  return simpleTest and mainTest

#if __name__ == "__main__":
#  if test():
#    print ("Test OK")
#  else:
#    print ("Test Error")
