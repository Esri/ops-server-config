#!/usr/bin/env python
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
if len(sys.argv) < 4:
    print '\n' + scriptName + ' <RootFolderToSearch> <OldServerName> <NewServerName> {IDJsonFile}'
    print '\nWhere:'
    print '\n\t<RootFolderToSearch> (required): the path of the root folder to search for web files to edit.'
    print '\n\t<OldServerName> (required): the old server name, for example afmcomstaging.esri.com'
    print '\n\t<NewServerName> (required): the new server name where web apps will running on'
    print '\n\t{IDJsonFile} (optional): the file path to the .json file containing the old and new portal item ids.'
    print '\t\t\t(i.e. the file named "oldID_newID.json" that is created by the PublishContentPost.py script within'
    print '\t\t\t the source portal content folder)'
    print '\n\tNOTE: script only edits index.html, briefingbook_config.js, Config.js, and *.csv files;'
    print '\t\tSearch functionality is case-sensitive.'
    sys.exit(1)
    
    
# Set variables from script parameters
root_path = sys.argv[1]
old_hostname =  sys.argv[2]
new_hostname = sys.argv[3]
id_map_file = None
if len(sys.argv) == 5:
    id_map_file = sys.argv[4]

# ------------------------------------------------------------------------------------
# Find all briefingbook_config.js and index.html files
# ------------------------------------------------------------------------------------
files_to_update = []
config_files = findFilePath(root_path, 'briefingbook_config.js', returnFirst=False)
config2_files = findFilePath(root_path, 'Config.js', returnFirst=False)
index_files = findFilePath(root_path, 'index.html', returnFirst=False)
csv_files = findFilePath(root_path, '*.csv', returnFirst=False)

files_to_update.extend(config_files)
files_to_update.extend(config2_files)
files_to_update.extend(index_files)
files_to_update.extend(csv_files)

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

    # Add the old/new IDs
    for orig_id, item_info in id_map.iteritems():
        search_replace_map[orig_id] = item_info['id']

if is_debug:
    print '\n\n' + str(search_replace_map)
    
# ------------------------------------------------------------------------------------
# Replace values in each file
# ------------------------------------------------------------------------------------
section_break = '-' * 120

if is_edit:
    for myfile in files_to_update:
        print section_break
        print 'Editing file: ' + myfile
            
        for line in fileinput.FileInput(myfile,inplace=1):
            # Also remove the newline character from end of line, otherwise
            # when "line" is printed below an extra newline character
            # will be embedded.
            for find_string, replace_string in search_replace_map.iteritems():
                line = line.replace(find_string.encode('ascii'), replace_string.encode('ascii')).rstrip('\n')
            #!!! NOTE: you must print line to screen for "inplace" option to work
            print line
        print '\tDone.' 

print '\n\nDone updating values in files.'




