#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import os.path
import getopt
import magic
import time

class Template(object):
  def __init__(self, header, rowset, footer):
    with open(header, 'r') as f:
      self.request_header = f.read()
    with open(rowset, 'r') as f:
      self.request_rowset = f.read()
    with open(footer, 'r') as f:
      self.request_footer = f.read()
    # Define shortcuts for template requests
    self.size = '{SIZE}' in self.request_rowset
    self.sizeb = '{SIZEB}' in self.request_rowset
    self.sizek = '{SIZEK}' in self.request_rowset
    self.sizem = '{SIZEM}' in self.request_rowset
    self.sizeg = '{SIZEG}' in self.request_rowset
    self.sizet = '{SIZET}' in self.request_rowset
    self.type = '{TYPE}' in self.request_rowset
    self.mime = '{MIME}' in self.request_rowset
    self.splitl = '{SPLITL}' in self.request_rowset
    self.splitr = '{SPLITR}' in self.request_rowset
    self.rsplitl = '{RSPLITL}' in self.request_rowset
    self.rsplitr = '{RSPLITR}' in self.request_rowset
    self.ext = '{EXT}' in self.request_rowset
    self.ctime = '{CTIME}' in self.request_rowset
    self.mtime = '{MTIME}' in self.request_rowset
    self.atime = '{ATIME}' in self.request_rowset

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
  def write_rowset(self, **args):
    self._write(self.template.request_rowset.format(**args))
  def write_footer(self, **args):
    self._write(self.template.request_footer.format(**args))

class ScannerOptions(object):
  def __init__(self, unit, directories_first, 
    include_directories, include_files, 
    include_symlinks_directories, include_symlinks_files,
    include_hidden_directories, include_hidden_files,
    recursive, max_depth, index_name, omit_index_listing, overwrite,
    write_to_stdout, localtime, timeformat):
    self.unit = unit
    self.mega = unit ** 2
    self.giga = unit ** 3
    self.tera = unit ** 4
    self.directories_first = directories_first
    self.include_directories = include_directories
    self.include_files = include_files
    self.include_symlinks_directories = include_symlinks_directories
    self.include_symlinks_files = include_symlinks_files
    self.include_hidden_directories = include_hidden_directories
    self.include_hidden_files = include_hidden_files
    self.max_depth = max_depth
    self.recursive = self.max_depth != 1 and recursive or False
    self.index_name = index_name
    self.omit_index_listing = omit_index_listing
    self.overwrite = overwrite
    self.write_to_stdout = write_to_stdout
    self.localtime = localtime
    self.timeformat = timeformat
    
class Scanner(object):
  def __init__(self, options):
    self.template = None
    self.options = options
    self.magic_types=magic.open(magic.MAGIC_NONE)
    self.magic_types.load()
    self.magic_mime=magic.open(magic.MIME_TYPE)
    self.magic_mime.load()
    self.abort = False

  def scan(self, path, template):
    self.template = template
    self.abort = False
    self.root_dir = os.path.dirname(path)
    # Define time format functions for local or GMT time
    if self.options.localtime:
      self.getstrftime = lambda ftime: \
        time.strftime(self.options.timeformat, time.localtime(ftime))
    else:
      self.getstrftime = lambda ftime: \
        time.strftime(self.options.timeformat, time.gmtime(ftime))
    # Launch scan
    self._scan_directory(path, os.path.dirname(path), 1)
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
    if self.options.include_directories:
      listItems = listDirs
    # Filter for files
    if self.options.include_files:
      listItems.extend(listFiles)
    if not self.options.directories_first:
      # Sort files and directories together
      listItems.sort()
    # Creates index file
    index_path = os.path.join(path, self.options.index_name)
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

    # Write result to file or stdout
    file_output = OutputFile(self.template, path,
      self.options.write_to_stdout and '-' or self.options.index_name)
    dictDirDetails = self._get_dir_details(os.path.basename(path), parent_dir, depth)
    # Write header for folder
    file_output.write_header(**dictDirDetails)
    listDirs = []
    #try:
    if 1==1:
      for filename in listItems:
        # Scan every item inside the directory
        bExclude = False
        dictFileDetails = self._get_file_details(path, filename, depth)
        bIsDirectory = dictFileDetails['DIRECTORY'] == 'y'
        # Skip index if requested
        if filename == self.options.index_name and self.options.omit_index_listing:
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
          if bIsDirectory:
            # Delay subfolders scan
            listDirs.append(dictFileDetails['FULLPATH'])
          # Write row for file
          file_output.write_rowset(**dictFileDetails)
      # Scan subfolders
      if self.options.recursive and \
        (self.options.max_depth == 0 or depth < self.options.max_depth):
        depth += 1
        for subdir in listDirs:
          self._scan_directory(subdir, path, depth)
    #except:
    #  print('ERROR')
    # Write footer for folder
    file_output.write_footer(**dictDirDetails)

  def _get_dir_details(self, dirname, path, depth):
    dirpath = os.path.join(path, dirname)
    return {
      'NAME': dirname,
      'PARENT': path,
      'PATH': os.path.relpath(dirpath, self.root_dir),
      'FULLPATH': dirpath,
      'DEPTH': depth
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
    # Obtain file attributes
    is_directory = os.path.isdir(sFilePath)
    dictDetails['DIRECTORY'] = is_directory and 'y' or 'n'
    dictDetails['LINK'] = os.path.islink(sFilePath) and 'y' or 'n'
    dictDetails['HIDDEN'] = fileName[0] == '.' and 'y' or 'n'
    # Obtain the filesize
    if is_directory:
      # It's a directory
      lSize = 0
      dictDetails['SIZE'] = ''
    else:
      # It's a file
      lSize = os.path.getsize(sFilePath)
      if self.template.size:
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
      dictDetails['EXT'] = '.' in fileName and fileName.count('.') and \
        fileName.rsplit('.', 1)[1] or ''
    # Obtain creation, modification and access time,
    # which will be formatted using the timeformat
    if self.template.ctime:
      dictDetails['CTIME'] = self.getstrftime(os.path.getctime(sFilePath))
    if self.template.mtime:
      dictDetails['MTIME'] = self.getstrftime(os.path.getmtime(sFilePath))
    if self.template.atime:
      dictDetails['ATIME'] = self.getstrftime(os.path.getatime(sFilePath))
    return dictDetails

if __name__=='__main__':
  options = ScannerOptions(unit=1024, directories_first=True,
    include_directories=True, include_files=True,
    include_symlinks_directories=True, include_symlinks_files=True,
    include_hidden_directories=False, include_hidden_files=False,
    recursive=True, max_depth=0,
    index_name='index.html', omit_index_listing=True, overwrite=False,
    write_to_stdout=True,
    localtime=True, timeformat='%Y-%m-%d %H:%M'
  )
  template = Template(
    'templates/stdout/header.txt',
    'templates/stdout/row.txt',
    'templates/stdout/footer.txt')
  scanner = Scanner(options)
  scanner.scan(os.path.expanduser('~/Prova'), template)
