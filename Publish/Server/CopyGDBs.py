#!/usr/bin/env python
#------------------------------------------------------------------------------
# Copyright 2015 Esri
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
#Name:      CopyGDBs.py
#
#Purpose:   Copy contents of multiple geodatabases given folder path of source
#               and destination SDE connection files/file geodatabases.
#
#==============================================================================
import arcpy
import sys, traceback, time, os

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilePath = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles")
sys.path.append(supportFilePath)

from datetime import datetime
from UtilitiesArcPy import checkResults, copyGDBData
from Utilities import intersect, findFilePath, findFolderPath

scriptName = sys.argv[0]

if len(sys.argv) <> 3:
    print "\n" + scriptName + " <SourceFolder> <DestinationFolder>"
    print "\nWhere:"
    print "\n\t<SourceFolder> (required): folder path of SDE connection files/file geodatabases."
    print "\n\t<DestinationFolder> (required): folder path of SDE connection files/file geodatabases."
    print
    sys.exit(1)

srcPath = sys.argv[1]
destPath = sys.argv[2]

# ---------------------------------------------------------------------
# Check parameters
# ---------------------------------------------------------------------
goodParameters = True

# Check path parameter to make sure they exist

if not os.path.exists(srcPath):
    print "\nThe path specified for parameter <SourceFolder>" + \
                " (" + srcPath + ") does not exist."
    goodParameters = False

if not os.path.exists(destPath):
    print "\nThe path specified for parameter <DestinationFolder>" + \
                " (" + destPath + ") does not exist."
    goodParameters = False

# Exit script if parameters are not valid.
if not goodParameters:
    print "\nInvalid script parameters. Exiting " + scriptName + "."
    sys.exit(1)

printMsg = True
totalCopySuccess = True


try:
    
    #startTime = datetime.now()
    
    # ----------------------------------------
    # Determine which databases to copy
    # ----------------------------------------
    print "- Determining which databases to copy..."
    
    # Get list of all workspaces in destination folder
    # (these could be file or enterprise geodatabases)
    destDBPathsSDE = findFilePath(destPath, "*.sde", returnFirst=False)
    destDBPathsFGDB = findFolderPath(destPath, "*.gdb", returnFirst=False)
    destDBPaths = destDBPathsSDE + destDBPathsFGDB
    
    # Create dictionary where destination db name is key and
    # path to workspace is value.
    destDBs = {}
    for dbPath in destDBPaths:
        destDBs[os.path.basename(dbPath).split(".")[0].lower()] = dbPath
    
    # Get list of all workspaces in source folder
    # (these could be file or enterprise geodatabases)
    srcDBPathsSDE = findFilePath(srcPath, "*.sde", returnFirst=False)
    srcDBPathsFGDB = findFolderPath(srcPath, "*.gdb", returnFirst=False)
    srcDBPaths = srcDBPathsSDE + srcDBPathsFGDB
    
    # Create dictionary where source db name is key and
    # path to workspace is value.    
    srcDBs = {}
    for dbPath in srcDBPaths:
        srcDBs[os.path.basename(dbPath).split(".")[0].lower()] = dbPath
    
    # Create list of db names that exist as keys in both source and
    # destination dictionaries
    dbsToCopy = intersect(srcDBs, destDBs)
    
    if len(dbsToCopy) == 0:
        continueCopy = False
        totalCopySuccess = False
        print
        print "\tERROR: There are no databases to copy!"
        print
    else:
        continueCopy = True
    
    if continueCopy:
        for db in dbsToCopy:
            print "-" * 80
            print "- Copying " + db.upper() + " database data..."
            srcPath = srcDBs[db]
            destPath = destDBs[db]
            results = copyGDBData(srcPath, destPath)
            success = checkResults(results, printMsg)
            if not success:
                totalCopySuccess = success

      
except:
    
    # Get the traceback object
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
 
    # Concatenate information together concerning the error into a message string
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
 
    # Print Python error messages for use in Python / Python Window
    print
    print "***** ERROR ENCOUNTERED *****"
    print pymsg + "\n"
    
finally:
    if totalCopySuccess:
        print "\nData copy was successful."
    else:
        print "\nERROR occurred during data copy."
        
    # print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("Start time:", startTime)
    # print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("End time:", datetime.now())

    if totalCopySuccess:
         sys.exit(0)
    else:
         sys.exit(1)

