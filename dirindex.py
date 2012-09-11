#!/usr/bin/env python2

import os
import os.path
import getopt
import magic

class RowTemplate(object):
  def __init__(self, request):
    print request
    self.request = request
    self.size = '{SIZE}' in request
    self.sizeb = '{SIZEB}' in request
    self.sizek = '{SIZEK}' in request
    self.sizem = '{SIZEM}' in request
    self.sizeg = '{SIZEG}' in request
    self.sizet = '{SIZET}' in request
    self.type = '{TYPE}' in request
    self.mime = '{MIME}' in request
    self.splitl = '{SPLITL}' in request
    self.splitr = '{SPLITR}' in request
    self.rsplitl = '{RSPLITL}' in request
    self.rsplitr = '{RSPLITR}' in request
    self.ext = '{EXT}' in request
  
  def write(self, **args):
    print(self.request.format(**args))

class ScannerOptions(object):
  def __init__(self, unit, directories_first, 
    include_directories, include_files, 
    include_symlinks_directories, include_symlinks_files,
    include_hidden_directories, include_hidden_files,
    recursive, max_depth):
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
    
class Scanner(object):
  def __init__(self, options):
    self.row_template = None
    self.options = options
    self.magic_types=magic.open(magic.MAGIC_NONE)
    self.magic_types.load()
    self.magic_mime=magic.open(magic.MIME_TYPE)
    self.magic_mime.load()
  
  def scan(self, path, row_template):
    self.row_template = RowTemplate(row_template)
    self.root = path
    self._scan_directory(path, 1)

  def _scan_directory(self, path, depth):
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
  
    listDirs = []
    #try:
    if 1==1:
      for fileName in listItems:
        # Scan every item inside the directory
        bInclude = True
        dictDetails = self._get_file_details(path, fileName, depth)
        bIsDirectory = dictDetails['DIRECTORY'] == 'y'
        # Skip symlinks if not requested
        if dictDetails['LINK'] == 'y':
          if bIsDirectory and not self.options.include_symlinks_directories:
            bInclude = False
          if not bIsDirectory and not self.options.include_symlinks_files:
            bInclude = False
        # Skip hidden files/directories if not requested
        if dictDetails['HIDDEN'] == 'y':
          if bIsDirectory and not self.options.include_hidden_directories:
            bInclude = False
          if not bIsDirectory and not self.options.include_hidden_files:
            bInclude = False
        if bInclude:
          if bIsDirectory:
            # Delay subfolders scan
            listDirs.append(dictDetails['PATH'])
          self.row_template.write(**dictDetails)
      if self.options.recursive and \
        (self.options.max_depth == 0 or depth < self.options.max_depth):
        depth += 1
        for subdir in listDirs:
          self._scan_directory(subdir, depth)
    #except:
    #  print('ERROR')
    

  def _get_file_details(self, path, fileName, depth):
    sFilePath = os.path.join(path, fileName)
  
    # Obtain file details
    dictDetails = {}
    dictDetails['FILENAME'] = fileName
    dictDetails['PARENT'] = path
    dictDetails['PATH'] = sFilePath[len(self.root) + 1:]
    dictDetails['FULLPATH'] = sFilePath
    dictDetails['DEPTH'] = depth
    dictDetails['DIRECTORY'] = os.path.isdir(sFilePath) and 'y' or 'n'
    dictDetails['LINK'] = os.path.islink(sFilePath) and 'y' or 'n'
    dictDetails['HIDDEN'] = fileName[0] == '.' and 'y' or 'n'
    lSize = dictDetails['DIRECTORY'] == 'n' and os.path.getsize(sFilePath) or 0
    if self.row_template.size:
      dictDetails['SIZE'] = lSize < self.options.unit and \
        '%d B' % lSize or \
        lSize / self.options.unit < self.options.unit and \
        '%d KB' % int(lSize / self.options.unit) or \
        lSize / self.options.mega < self.options.unit and \
        '%d MB' % int(lSize / self.options.mega) or \
        lSize / self.options.giga < self.options.unit and \
        '%d GB' % int(lSize / self.options.giga) or \
        '%d TB' % int(lSize / self.options.tera)
    if self.row_template.sizeb:
      dictDetails['SIZEB'] = lSize
    if self.row_template.sizek:
      dictDetails['SIZEK'] = int(lSize / self.options.unit)
    if self.row_template.sizem:
      dictDetails['SIZEM'] = int(lSize / self.options.mega)
    if self.row_template.sizeg:
      dictDetails['SIZEG'] = int(lSize / self.options.giga)
    if self.row_template.sizet:
      dictDetails['SIZET'] = int(lSize / self.options.tera)
    if self.row_template.type:
      dictDetails['TYPE'] = self.magic_types.file(sFilePath)
    if self.row_template.mime:
      dictDetails['MIME'] = self.magic_mime.file(sFilePath)
    if self.row_template.splitl:
      dictDetails['SPLITL'] = fileName.split('.', 1)[0]
    if self.row_template.splitr:
      dictDetails['SPLITR'] = '.' in fileName and \
        fileName.split('.', 1)[1] or ''
    if self.row_template.rsplitl:
      dictDetails['RSPLITL'] = fileName.rsplit('.', 1)[0]
    if self.row_template.rsplitr:
      dictDetails['RSPLITR'] = '.' in fileName and \
        fileName.rsplit('.', 1)[1] or ''
    if self.row_template.ext:
      dictDetails['EXT'] = '.' in fileName and fileName.count('.') and \
        fileName.rsplit('.', 1)[1] or ''
    return dictDetails

if __name__=='__main__':
  options = ScannerOptions(unit=1024, directories_first=True,
    include_directories=True, include_files=True,
    include_symlinks_directories=True, include_symlinks_files=True,
    include_hidden_directories=False, include_hidden_files=False,
    recursive=True, max_depth=1)
  scanner = Scanner(options)
  scanner.scan(os.path.expanduser('~'), "{DIRECTORY} {LINK} {PATH} .{EXT}")
