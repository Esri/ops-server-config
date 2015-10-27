#!/usr/bin/env python
#------------------------------------------------------------------------------
# Copyright 2014 Esri
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#==============================================================================
#Name:          UpdateWebApps.py
#
#Purpose:       Performs search/replace of server names and portal item ids
#               in files deployed to IIS.
#
#Prerequisites: Portal content must have already been published and web apps
#               deployed to IIS.
#
#==============================================================================
import os, sys, traceback, fnmatch, fileinput
import httplib, urllib, json
from Utilities import makePath
from Utilities import editFiles
from walkingDirTrees import listFiles
from Utilities import findFolderPath, findFilePath, findInFile
import json

is_debug = False
is_edit = True

scriptName = sys.argv[0]

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------   
if len(sys.argv) <> 5:
    print '\n' + scriptName + ' <RootFolderToSearch> <OldServerName> <NewServerName> <IDJsonFile>'
    print '\nWhere:'
    print '\n\t<RootFolderToSearch> (required): the path of the root folder to search for web files to edit.'
    print '\n\t<OldServerName> (required): the old server name'
    print '\n\t<NewServerName> (required): the new server name where web apps will running on'
    print '\n\t<IDJsonFile> (required): the file path to the .json file containing the old and new portal item ids.'
    print '\t\t\t(i.e. the file named "oldID_newID.json" that is created by the PublishContentPost.py script within'
    print '\t\t\t the source portal content folder)'
    print '\n\tNOTE: script only edits index.html, briefingbook_config.js, Config.js, and *.csv files;'
    print '\t\tSearch functionality is case-sensitive.'
    sys.exit(1)
    
    
# Set variables from script parameters
root_path = sys.argv[1]
old_hostname =  sys.argv[2]
new_hostname = sys.argv[3]
id_map_file = sys.argv[4]

# ------------------------------------------------------------------------------------
# Check if root folder and json file exist.
# ------------------------------------------------------------------------------------
if not os.path.exists(root_path):
    print '\nERROR: <RootFolderToSearch> folder ' + root_path + ' does not exist. Exiting script.'
    sys.exit(1)

if not os.path.isfile(id_map_file):
    print '\nERROR: <IDJsonFile> file ' + id_map_file + ' does not exist. Exiting script.'
    sys.exit(1) 
    
# ------------------------------------------------------------------------------------
# Create list of files to update
# ------------------------------------------------------------------------------------
files_to_update = []

files_to_update.extend(findFilePath(root_path, '*.js', returnFirst=False))
files_to_update.extend(findFilePath(root_path, '*.html', returnFirst=False))
files_to_update.extend(findFilePath(root_path, '*.json', returnFirst=False))
files_to_update.extend(findFilePath(root_path, '*.csv', returnFirst=False))
files_to_update.extend(findFilePath(root_path, '*.erb', returnFirst=False))
files_to_update.extend(findFilePath(root_path, '*.config', returnFirst=False))

total_files = len(files_to_update)

# ------------------------------------------------------------------------------------
# Create dictionary of search/replace values
# ------------------------------------------------------------------------------------
search_replace_map = {}

# Add old/new hostnames
search_replace_map[old_hostname] = new_hostname

# Load json file containing old/new ids
if id_map_file:
    os.chdir(os.path.dirname(id_map_file))
    id_map = json.load(open(os.path.basename(id_map_file)))
    
    if is_debug:
        print str(id_map)

    for i in id_map:
        try:
            # Read in search/replace values from hosted service
            # item mapping file
            search = i['search']
            replace = i['replace']
        except Exception as err:
            # Read in search/replace values from portal post script
            # item mapping file
            search = i
            replace = id_map[search]['id']

        search_replace_map[search] = replace
        
if is_debug:
    print '\n\n' + str(search_replace_map)
    
# ------------------------------------------------------------------------------------
# Replace values in each file
# ------------------------------------------------------------------------------------
section_break = '-' * 120

if is_edit:
    n = 1
    for myfile in files_to_update:
        print section_break
        print 'Editing file: {} ({} of {})'.format(myfile, n, total_files)  
        for line in fileinput.FileInput(myfile,inplace=1):
            # Also remove the newline character from end of line, otherwise
            # when "line" is printed below an extra newline character
            # will be embedded.
            for find_string, replace_string in search_replace_map.iteritems():
                find_str_list = [find_string, find_string.lower(), find_string.upper()]
                for find_str in find_str_list:
                    line = line.replace(find_str.encode('ascii'), replace_string.encode('ascii')).rstrip('\n')
            #!!! NOTE: you must print line to screen for "inplace" option to work
            print line
        print '\tDone.' 
        n = n + 1
print '\n\nDone updating values in files.'




