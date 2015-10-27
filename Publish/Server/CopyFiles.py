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
#Name:      CopyFiles.py
#
#Purpose:   Copy folders/files from source folder to desintation folder
#
#==============================================================================
import arcpy
import sys
import traceback
import time
import os

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilePath = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles")
sys.path.append(supportFilePath)

from datetime import datetime
from Utilities import changeOwnership
from Utilities import getFreeSpace
from Utilities import getDirSize
from UtilitiesArcPy import checkResults
from UtilitiesArcPy import copyData
from walkingDirTrees import listFiles

scriptName = sys.argv[0]

if len(sys.argv) < 3:
    print "\n" + scriptName + " <SourceFolder> <DestinationFolder>"
    print "\nWhere:"
    print "\n\t<SourceFolder> (required): path of source folder to copy."
    print "\n\t<DestinationFolder> (required): path of folder where source folder will be copied."
    print
    sys.exit(1)


# script parameter:
src_folder = sys.argv[1]
dest_folder = sys.argv[2]
owner_account = None
# if len(sys.argv) > 3:
#     owner_account = sys.argv[3]

# ---------------------------------------------------------------------
# Check parameters
# ---------------------------------------------------------------------
goodParameters = True

# Check path parameter to make sure they exist

if not os.path.exists(src_folder):
    print "\nThe path specified for parameter <SourceFolder>" + \
                " (" + src_folder + ") does not exist."
    goodParameters = False

if not os.path.exists(dest_folder):
    print "\nThe path specified for parameter <dest_folder>" + \
                " (" + dest_folder + ") does not exist."
    goodParameters = False

# Exit script if parameters are not valid.
if not goodParameters:
    print "\nInvalid script parameters. Exiting " + scriptName + "."
    sys.exit(1)

printMsg = True
totalCopySuccess = True


def copyDataFolders(srcRootPath, destRootPath, ownerAccount=None):
    copySuccess = True
    
    # Check if there is available space on destination drive
    # to copy folders.
    freeSpace = getFreeSpace(destRootPath, "GB")
    
    # Get total size of source folders
    srcSize = getDirSize(srcRootPath, "GB")

    print '{:<34}{:>10.4f}{:>3}'.format("Available space to copy folders:", freeSpace, " GB")
    print '{:<34}{:>10.4f}{:>3}'.format("Size of folders to copy:", srcSize, " GB")
    print
        
    if srcSize >= freeSpace:
        totalCopySuccess = False
        print
        print "ERROR: Not enough available space to copy folders/files."
        print 
    else:
        
        # Get list of top-level directories and files
        returnFolders = 1   #Yes
        recursive = 0       #No
        dirList = listFiles(srcRootPath, "*", recursive, returnFolders)
        
        x = 0
        for srcPath in dirList:
            # List may have files so test for directory
            if os.path.isdir(srcPath):
                pathType = "Folder"
            elif os.path.isfile(srcPath):
                pathType = "File"
            else:
                pathType = ""
                
            # "Create" destination path
            destPath = os.path.join(destRootPath, os.path.basename(srcPath))
            
            print
            print "- Copying " + pathType.lower() + "..."
            print '{:<16}{:<100}'.format("\tSource:", srcPath)
            print '{:<16}{:<100}'.format("\tDestination:", destPath)
            
            # Copy data and check results
            results = copyData(srcPath, destPath)
            success = checkResults(results, printMsg)
            if not success:
                copySuccess = success
                
            # Change ownership function doesn't seem to be working
            # so for time being lets comment out this function call.
            # if not success:
            #     copySuccess = success
            # else:
            #     if ownerAccount:
            #         changeOwnership(destPath, ownerAccount)
                    
    return copySuccess

try:
    
    startTime = datetime.now()
    print "\n=============================================================="
    print "Copying files..."
    print "==============================================================\n"
    print '{:<25}{}'.format("Source folder:", src_folder)
    print '{:<25}{}\n'.format("Destination folder:", dest_folder)
    success = copyDataFolders(src_folder, dest_folder, owner_account)
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
        print "\n\nFile copy was successful.\n"
    else:
        print "\n\nERROR occurred during file copy.\n"
        
    print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("Start time:", startTime)
    endTime = datetime.now()
    print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("End time:", endTime)
    print '\nDone.'

    if totalCopySuccess:
         sys.exit(0)
    else:
         sys.exit(1)
