#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##
#       Project : dirindex
#       Version : 0.3.0
#   Description : A tool to create an HTML index starting from a directory.
#        Author : Muflone <muflone@vbsimple.net>
#     Copyright : 2012 Fabio Castelli
#       License : GPL-2+
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation; either version 2 of the License, or (at your option)
#  any later version.
# 
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
##

import os
import os.path
import magic
import time
import argparse
import sys
import ConfigParser

CFILES = 'files'
CDIRS = 'dirs'
APPNAME = 'dirindex'
VERSION = '0.3.0'
DATADIR = os.path.join(sys.prefix, 'share', 'dirindex')

class Template(object):
  def __init__(self, template):
    self.template = template
    # Read configuration file
    self.config = ConfigParser.ConfigParser()
    self.config.read([os.path.join(self.template, 'template.ini')])
    # Get files from template
    self.file_header = self.get_file_from_config('header', 'header.txt')
    self.file_footer = self.get_file_from_config('footer', 'footer.txt')
    self.file_rowfile = self.get_file_from_config('rowfile', 'rowfile.txt')
    self.file_rowdir = self.get_file_from_config('rowdir', 'rowdir.txt')
    GENERAL_SECTION = 'GENERAL'
    if self.config.has_section(GENERAL_SECTION):
      # Read template information in GENERAL section
      self.name = self.config.get(GENERAL_SECTION, 'name', '')
      self.description = self.config.get(GENERAL_SECTION, 'description', '')
      self.author = self.config.get(GENERAL_SECTION, 'author', '')
      self.url = self.config.get(GENERAL_SECTION, 'url', '')
      self.screenshot = self.config.get(GENERAL_SECTION, 'screenshot', '')
    else:
      # No GENERAL section found
      self.name, self.description, self.author, self.url, self.screenshot = \
      ['unknown'] * 5

  def get_file_from_config(self, option, defaultfile):
    # Read filename from the config and read its content
    FILES_SECTION = 'FILES'
    if self.config.has_section(FILES_SECTION):
      filename = self.config.get(FILES_SECTION, option, defaultfile)
    # If not specified use the default filename
    if not filename:
      filename = defaultfile
    return filename

  def load(self):
    # Read content of the files obtained from the configuration file
    with open(os.path.join(self.template, self.file_header), 'r') as f:
      self.request_header = f.read()
    with open(os.path.join(self.template, self.file_footer), 'r') as f:
      self.request_footer = f.read()
    with open(os.path.join(self.template, self.file_rowfile), 'r') as f:
      self.request_rowfile = f.read()
    with open(os.path.join(self.template, self.file_rowdir), 'r') as f:
      self.request_rowdir = f.read()

    # Define shortcuts for template requests
    requests = '%s %s %s %s' % (self.request_header, self.request_footer,
      self.request_rowfile, self.request_rowdir)
    self.size    = '{SIZE}'    in requests
    self.sizeb   = '{SIZEB}'   in requests
    self.sizek   = '{SIZEK}'   in requests
    self.sizem   = '{SIZEM}'   in requests
    self.sizeg   = '{SIZEG}'   in requests
    self.sizet   = '{SIZET}'   in requests
    self.type    = '{TYPE}'    in requests
    self.mime    = '{MIME}'    in requests
    self.splitl  = '{SPLITL}'  in requests
    self.splitr  = '{SPLITR}'  in requests
    self.rsplitl = '{RSPLITL}' in requests
    self.rsplitr = '{RSPLITR}' in requests
    self.ext     = '{EXT}'     in requests
    self.ctime   = '{CTIME}'   in requests
    self.mtime   = '{MTIME}'   in requests
    self.atime   = '{ATIME}'   in requests

class OutputFile(object):
  def __init__(self, template, path, index_name):
    self.template = template
    if index_name == '-':
      # Use stdout
      self.index_path = '-'
    else:
      # Use output file
      self.index_path = os.path.join(path, index_name)
      self.file_output = file(self.index_path, 'w')
  def _write(self, data):
    if self.index_path == '-':
      # Output to stdout
      print data
    else:
      # Output to file
      self.file_output.write(data)
  def write_header(self, **args):
    self._write(self.template.request_header.format(**args))
  def write_rowfile(self, **args):
    self._write(self.template.request_rowfile.format(**args))
  def write_rowdir(self, **args):
    self._write(self.template.request_rowdir.format(**args))
  def write_footer(self, **args):
    self._write(self.template.request_footer.format(**args))

class ScannerOptions(object):
  def __init__(self):
    choicesfd = (CFILES, CDIRS)
    parser = argparse.ArgumentParser(add_help=True,
      usage='%(prog)s [options] -t TEMPLATE -i INDEX PATH',
      description='Create an index file of files or directories')
    parser.add_argument('path'             , action='store', type=str,
      help='Directory to scan for files or directories')
    parser.add_argument('-V', '--version'  , action='version',
      help='Display the program version number and exit',
      version='%s %s' % (APPNAME, VERSION))
    parser.add_argument('-u', '--unit'     , action='store', type=int,
      help='Unit for size, use 1000 for KB or 1024 for KiB',
      default=1024)
    parser.add_argument('-f', '--dirfirst' , action='store_true',
      help='Put directories first, then all available files')

    group = parser.add_argument_group(title='Template')
    group.add_argument('-t', '--template' , action='store', type=str,
      help='Template for index filename',
      required=True)

    group = parser.add_argument_group(title='Index options')
    group.add_argument('-i', '--index'    , action='store', type=str,
      help='Index filename',
      required=True)
    group.add_argument('-O', '--omitindex', action='store_true',
      help='Omit the index file from the file listing')
    group.add_argument('-o', '--overwrite', action='store_true',
      help='Overwrite existing index files without confirmation')
    group.add_argument('-s', '--stdout'   , action='store_true',
      help='Write to standard output instead of index file')

    group = parser.add_argument_group(title='Time and date')
    group.add_argument('-l', '--localtime', action='store_true',
      help='Use localtime instead of UTC')
    group.add_argument('-d', '--datefmt'  , action='store', type=str,
      help='Date format as used by strftime (see man strftime)',
      default='%Y-%m-%d %H:%M')

    group = parser.add_argument_group(title='Inclusions and exclusions')
    group.add_argument('-X', '--exclude'  , action='append',
      help='Exclude files or directories from the scan',
      choices=choicesfd)
    group.add_argument('-H', '--hidden'   , action='append',
      help='Include hidden files or directories from the scan',
      choices=choicesfd)
    group.add_argument('-L', '--links'    , action='append',
      help='Include symlinks files or directories from the scan',
      choices=choicesfd)

    group = parser.add_argument_group(title='Recursion')
    group.add_argument('-r', '--recursive', action='store_true',
      help='Scan directories recursively')
    group.add_argument('-m', '--maxdepth' , action='store', type=int,
      help='Descend at most DEPTH levels of directories below',
      dest='depth', default=0)

    args = parser.parse_args()

    # Check for path existance
    if not os.path.exists(args.path):
      parser.exit(message='The specified path does not exist.\n')
    if not os.path.isdir(args.path):
      parser.exit(message='The specified path is not a directory.\n')

    # Check for template existance
    for templates in ('', 'templates', os.path.join(DATADIR, 'templates')):
      if os.path.isdir(os.path.join(templates, args.template)) and \
        os.path.isfile(os.path.join(templates, args.template, 'template.ini')):
        self.template = os.path.join(templates, args.template)
        break
    else:
      parser.exit(message='The specified template was not found.\n')
    # TODO: allow default settings in the template
    self.index = args.index
    self.path = args.path
    self.unit = args.unit
    self.mega = args.unit ** 2
    self.giga = args.unit ** 3
    self.tera = args.unit ** 4
    self.directories_first = args.dirfirst
    self.exclude_directories = args.exclude and CDIRS in args.exclude or False
    self.exclude_files = args.exclude and CFILES in args.exclude or False
    self.include_symlinks_directories = args.links and CDIRS in args.links or False
    self.include_symlinks_files = args.links and CFILES in args.links or False
    self.include_hidden_directories = args.hidden and CDIRS in args.hidden or False
    self.include_hidden_files = args.hidden and CFILES in args.hidden or False
    self.maxdepth = args.depth
    self.recursive = args.depth != 1 and args.recursive or False
    self.omit_index_listing = args.omitindex
    self.overwrite = args.overwrite
    self.write_to_stdout = args.stdout
    self.localtime = args.localtime
    self.dateformat = args.datefmt
    
class Scanner(object):
  def __init__(self, options, template):
    self.options = options
    self.template = template
    self.magic_types=magic.open(magic.MAGIC_NONE)
    self.magic_types.load()
    self.magic_mime=magic.open(magic.MIME_TYPE)
    self.magic_mime.load()
    self.abort = False

  def scan(self):
    self.abort = False
    self.root_dir = os.path.dirname(self.options.path)
    # Define time format functions for local or GMT time
    if self.options.localtime:
      self.getstrftime = lambda ftime: \
        time.strftime(self.options.dateformat, time.localtime(ftime))
    else:
      self.getstrftime = lambda ftime: \
        time.strftime(self.options.dateformat, time.gmtime(ftime))
    self.now = self.getstrftime(None)
    # Launch scan
    self._scan_directory(self.options.path, os.path.dirname(self.options.path), 1)
    # Cancelled scan
    if self.abort:
      print 'Procedure aborted'

  def _scan_directory(self, path, parent_dir, depth):
    # Exit when aborted
    if self.abort:
      return
    listItems = os.listdir(path)  
    listDirs = [item for item in listItems if os.path.isdir(os.path.join(path, item))]
    listFiles = [item for item in listItems if not os.path.isdir(os.path.join(path, item))]
    listItems = []
    if self.options.directories_first:
      # Sort directories first
      listDirs.sort()
      listFiles.sort()
    # Filter for directories
    if not self.options.exclude_directories:
      listItems = listDirs
    # Filter for files
    if not self.options.exclude_files:
      listItems.extend(listFiles)
    if not self.options.directories_first:
      # Sort files and directories together
      listItems.sort()
    # Creates index file
    index_path = os.path.join(path, self.options.index)
    if os.path.exists(index_path) and not self.options.overwrite and \
      not self.options.write_to_stdout:
      # Handle existing index file
      response = ''
      print 'Warning: the file %s already exists.' % index_path
      while response not in ('y', 'yes', 'n', 'no', 'a', 'all'):
        response = raw_input('Overwrite the file? ([y]es, [n]o, [a]ll) > ').lower()
        if response in ('n', 'no'):
          self.abort = True
        elif response in ('a', 'all'):
          self.options.overwrite = True
    # Exit when aborted
    if self.abort:
      return

    listDirs = []
    listFiles = []
    rownr = 0
    # FIXME: create a better error handling
    #try:
    if 1==1:
      for filename in listItems:
        # Scan every item inside the directory
        bExclude = False
        dictFileDetails = self._get_file_details(path, filename, depth)
        bIsDirectory = dictFileDetails['DIRECTORY'] == 'y'
        # Skip index if requested
        if filename == self.options.index and self.options.omit_index_listing:
          bExclude = True
        # Skip symlinks if not requested
        if dictFileDetails['LINK'] == 'y':
          if bIsDirectory and not self.options.include_symlinks_directories:
            bExclude = True
          if not bIsDirectory and not self.options.include_symlinks_files:
            bExclude = True
        # Skip hidden files/directories if not requested
        if dictFileDetails['HIDDEN'] == 'y':
          if bIsDirectory and not self.options.include_hidden_directories:
            bExclude = True
          if not bIsDirectory and not self.options.include_hidden_files:
            bExclude = True
        if not bExclude:
          # Add ROWNR field
          rownr += 1
          dictFileDetails['ROWNR'] = rownr
          # Append file details to files list
          listFiles.append(dictFileDetails)
          if bIsDirectory:
            # Delay subfolders scan
            listDirs.append(dictFileDetails['FULLPATH'])

      # Write result to file or stdout
      file_output = OutputFile(self.template, path,
        self.options.write_to_stdout and '-' or self.options.index)
      dictDirDetails = self._get_dir_details(os.path.basename(path), parent_dir,
        depth, len(listFiles))
      # Write header for folder
      file_output.write_header(**dictDirDetails)
      for item in listFiles:
        # Add COUNT field
        item['COUNT'] = len(listFiles)
        if item['DIRECTORY'] == 'y':
          # Write row for directory
          file_output.write_rowdir(**item)
        else:
          # Write row for file
          file_output.write_rowfile(**item)
      # Write footer for folder
      file_output.write_footer(**dictDirDetails)
        
      # Scan subfolders
      if self.options.recursive and \
        (self.options.maxdepth == 0 or depth < self.options.maxdepth):
        depth += 1
        for item in listDirs:
          self._scan_directory(item, path, depth)
    #except:
    #  print('ERROR')

  def _get_dir_details(self, dirname, path, depth, count):
    dirpath = os.path.join(path, dirname)
    return {
      'NAME': dirname,
      'PARENT': path,
      'PATH': os.path.relpath(dirpath, self.root_dir),
      'FULLPATH': dirpath,
      'DEPTH': depth,
      'COUNT': count,
      'ROWNR': 0,
      'NOW': self.now,
      'APPNAME': APPNAME,
      'VERSION': VERSION
    }

  def _get_file_details(self, path, fileName, depth):
    sFilePath = os.path.join(path, fileName)
  
    # Obtain file paths
    dictDetails = {}
    dictDetails['NAME'] = fileName
    dictDetails['PARENT'] = path
    #dictDetails['PATH'] = sFilePath[len(self.root_dir) + 1:]
    dictDetails['PATH'] = os.path.relpath(sFilePath, self.root_dir)
    dictDetails['FULLPATH'] = sFilePath
    dictDetails['DEPTH'] = depth
    dictDetails['INDEX'] = self.options.index
    # DESCRIPTION field placeholder
    dictDetails['DESCRIPTION'] = ''
    # ROWNR and COUNT placeholders, they will be set later after the scan
    # to properly set them if the file has to be skipped
    dictDetails['ROWNR'] = 0
    dictDetails['COUNT'] = 0
    # Scan date and time
    dictDetails['NOW'] = self.now
    # App version number
    dictDetails['APPNAME'] = APPNAME
    dictDetails['VERSION'] = VERSION
    # Obtain file attributes
    is_directory = os.path.isdir(sFilePath)
    # TODO: define format for DIRECTORY field in template
    dictDetails['DIRECTORY'] = is_directory and 'y' or 'n'
    # TODO: define format for LINK field in template
    dictDetails['LINK'] = os.path.islink(sFilePath) and 'y' or 'n'
    # TODO: define format for HIDDEN field in template
    dictDetails['HIDDEN'] = fileName[0] == '.' and 'y' or 'n'
    # Obtain the filesize
    if is_directory:
      # It's a directory
      lSize = 0
      # TODO: allow to define directories SIZE field in template
      dictDetails['SIZE'] = ''
    else:
      # It's a file
      lSize = os.path.getsize(sFilePath)
      if self.template.size:
        # TODO: define KB/MB/GB/TB constants in template
        # TODO: define format for SIZE field in template
        dictDetails['SIZE'] = lSize < self.options.unit and \
          '%d bytes' % lSize or \
          lSize / self.options.unit < self.options.unit and \
          '%d KB' % int(lSize / self.options.unit) or \
          lSize / self.options.mega < self.options.unit and \
          '%d MB' % int(lSize / self.options.mega) or \
          lSize / self.options.giga < self.options.unit and \
          '%d GB' % int(lSize / self.options.giga) or \
          '%d TB' % int(lSize / self.options.tera)
    if self.template.sizeb:
      dictDetails['SIZEB'] = lSize
    if self.template.sizek:
      dictDetails['SIZEK'] = int(lSize / self.options.unit)
    if self.template.sizem:
      dictDetails['SIZEM'] = int(lSize / self.options.mega)
    if self.template.sizeg:
      dictDetails['SIZEG'] = int(lSize / self.options.giga)
    if self.template.sizet:
      dictDetails['SIZET'] = int(lSize / self.options.tera)
    # Obtain file type and mime using magic
    if self.template.type:
      dictDetails['TYPE'] = self.magic_types.file(sFilePath)
    if self.template.mime:
      dictDetails['MIME'] = self.magic_mime.file(sFilePath)
    # Obtain groups before and after the first or last dot
    if self.template.splitl:
      dictDetails['SPLITL'] = fileName.split('.', 1)[0]
    if self.template.splitr:
      dictDetails['SPLITR'] = '.' in fileName and \
        fileName.split('.', 1)[1] or ''
    if self.template.rsplitl:
      dictDetails['RSPLITL'] = fileName.rsplit('.', 1)[0]
    if self.template.rsplitr:
      dictDetails['RSPLITR'] = '.' in fileName and \
        fileName.rsplit('.', 1)[1] or ''
    if self.template.ext:
      #dictDetails['EXT'] = '.' in fileName and fileName.count('.') and \
      #  fileName.rsplit('.', 1)[1] or ''
      dictDetails['EXT'] = os.path.splitext(fileName)[1]
    # Obtain creation, modification and access time,
    # which will be formatted using the dateformat
    if self.template.ctime:
      dictDetails['CTIME'] = self.getstrftime(os.path.getctime(sFilePath))
    if self.template.mtime:
      dictDetails['MTIME'] = self.getstrftime(os.path.getmtime(sFilePath))
    if self.template.atime:
      dictDetails['ATIME'] = self.getstrftime(os.path.getatime(sFilePath))
    return dictDetails

if __name__=='__main__':
  options = ScannerOptions()
  template = Template(options.template)
  print 'Using template %s (%s) from %s\nURL: %s\nScreenshot: %s' % (
    template.name, template.description, template.author,
    template.url, template.screenshot)
  template.load()
  scanner = Scanner(options, template)
  scanner.scan()
