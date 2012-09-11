#!/usr/bin/env python2

import os
import os.path
import getopt
import magic

class Template(object):
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
  def __init__(self, divider, directories_first, 
    include_directories, include_files,
    include_hidden_directories, include_hidden_files,
    recursive, max_depth):
    self.divider = divider
    self.directories_first = directories_first
    self.include_directories = include_directories
    self.include_files = include_files
    self.include_hidden_directories = include_hidden_directories
    self.include_hidden_files = include_hidden_files
    self.max_depth = max_depth
    self.recursive = self.max_depth != 1 and recursive or False
    
class Scanner(object):
  def __init__(self, options):
    self.template = None
    self.options = options
    self.magic_types=magic.open(magic.MAGIC_NONE)
    self.magic_types.load()
    self.magic_mime=magic.open(magic.MIME_TYPE)
    self.magic_mime.load()
  
  def scan(self, path, template):
    self.template = Template(template)
    self._scan_directory(path, 1)

  def _scan_directory(self, path, depth):
    listItems = os.listdir(path)  
    if self.options.directories_first:
      # Sort directories first
      listDirs = [item for item in listItems if os.path.isdir(os.path.join(path, item))]
      listDirs.sort()
      listFiles = [item for item in listItems if not os.path.isdir(os.path.join(path, item))]
      listFiles.sort()
      listItems = []
      if self.options.include_directories:
        # Include directories
        listItems = listDirs
      if self.options.include_files:
        # Include files
        listItems.extend(listFiles)
    else:
      # Sort files and directories together
      listItems.sort()
  
    listDirs = []
    #try:
    if 1==1:
      for fileName in listItems:
        # Scan every item inside the directory
        dictDetails = self._get_file_details(path, fileName, depth)
        if dictDetails['FORD'] == 'd':
          # Delay subfolders scan
          listDirs.append(dictDetails['PATH'])
        
        self.template.write(**dictDetails)
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
    dictDetails['PATH'] = sFilePath
    dictDetails['DEPTH'] = depth
    dictDetails['FORD'] = os.path.isdir(sFilePath) and 'd' or 'f'
    lSize = dictDetails['FORD'] == 'f' and os.path.getsize(sFilePath) or 0
    if self.template.size:
      dictDetails['SIZE'] = lSize < self.options.divider and \
        '%d B' % lSize or \
        lSize / self.options.divider < self.options.divider and \
        '%d KB' % int(lSize / self.options.divider) or \
        lSize / self.options.divider ** 2 < self.options.divider and \
        '%d MB' % int(lSize / self.options.divider ** 2) or \
        lSize / self.divider ** 3 < self.options.divider and \
        '%d GB' % int(lSize / self.options.divider ** 3) or \
        '%d TB' % int(lSize / self.options.divider ** 4)
    if self.template.sizeb:
      dictDetails['SIZEB'] = lSize
    if self.template.sizek:
      dictDetails['SIZEK'] = int(lSize / self.options.divider)
    if self.template.sizem:
      dictDetails['SIZEM'] = int(lSize / self.options.divider ** 2)
    if self.template.sizeg:
      dictDetails['SIZEG'] = int(lSize / self.options.divider ** 3)
    if self.template.sizet:
      dictDetails['SIZET'] = int(lSize / self.options.divider ** 4)
    if self.template.type:
      dictDetails['TYPE'] = self.magic_types.file(sFilePath)
    if self.template.mime:
      dictDetails['MIME'] = self.magic_mime.file(sFilePath)
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
        '.%s' % fileName.rsplit('.',1 )[1] or ''
    return dictDetails

if __name__=='__main__':
  options = ScannerOptions(1024, True, True, True, True, True, True, 2)
  scanner = Scanner(options)
  scanner.scan(os.path.expanduser('~'), "{FORD} {PATH} {EXT} {TYPE} {MIME}")
