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
#Name:      CopyData.py
#
#Purpose:   Copy data/cache files and database contents from staging location
#           to Ops Server
#
#==============================================================================
import arcpy
import sys, traceback, time, os

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilePath = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles")
sys.path.append(supportFilePath)


import OpsServerConfig
from datetime import datetime
from Utilities import changeOwnership, makePath, getFreeSpace
from Utilities import getDirSize, findFilePath, intersect, doesDriveExist
from UtilitiesArcPy import checkResults, copyData, copyGDBData
from walkingDirTrees import listFiles
from RepairMosaicDatasets import repairMosaicDatasets


copyDBs = True
copyFolders = True
copyCacheData = True
repairMDPaths = True

scriptName = sys.argv[0]

if len(sys.argv) <> 7:
    print "\n" + scriptName + " <SourceDataFolder> <SourceCacheFolder> " + \
            "<SourceDatabaseFolder> <AGSServiceAccount> <DataDriveLetter> " + \
            "<CacheDriveLetter>"
    print "\nWhere:"
    print "\n\t<SourceDataFolder> (required parameter): path to the source data folder."
    print "\n\t<SourceCacheFolder> (required parameter): path to the source caches folder."
    print "\n\t<SourceDatabaseFolder> (required parameter): path to the source 'DistributionEntGDBs' folder."
    print "\n\t<AGSServiceAccount> (required parameter): ArcGIS Server service account."
    print "\n\t<DataDriveLetter> (required parameter): the drive letter where the"
    print "\n\t\t\tdestination 'Data' folder is located."
    print "\n\t<CacheDriveLetter> (required parameter): the drive letter where the"
    print "\n\t\t\tdestination 'arcgiscache' folder is located."
    print
    sys.exit(1)


# script parameter:
StagingFolder = sys.argv[1]
StagingCacheFolder = sys.argv[2]
StagingDBFolder = sys.argv[3]
agsServerAccount = sys.argv[4]
dataDrive = sys.argv[5]
cacheDrive = sys.argv[6]

# ---------------------------------------------------------------------
# Check parameters
# ---------------------------------------------------------------------
goodParameters = True

# Check path parameter to make sure they exist

if not os.path.exists(StagingFolder):
    print "\nThe path specified for parameter <SourceDataFolder>" + \
                " (" + StagingFolder + ") does not exist."
    goodParameters = False

if not os.path.exists(StagingCacheFolder):
    print "\nThe path specified for parameter <SourceCacheFolder>" + \
                " (" + StagingCacheFolder + ") does not exist."
    goodParameters = False
    
if not os.path.exists(StagingDBFolder):
    print "\nThe path specified for parameter <SourceDatabaseFolder>" + \
                " (" + StagingDBFolder + ") does not exist."
    goodParameters = False



# Check if specified drives exist.

if not doesDriveExist(dataDrive):
    print "\nThe drive specified for parameter <DataDriveLetter>" + \
                " (" + dataDrive + ") is an invalid drive."
    goodParameters = False

if not doesDriveExist(cacheDrive):
    print "\nThe drive specified for parameter <CacheDriveLetter>" + \
                " (" + cacheDrive + ") is an invalid drive."
    goodParameters = False

# Exit script if parameters are not valid.
if not goodParameters:
    print "\nInvalid script parameters. Exiting " + scriptName + "."
    sys.exit(1)


DestinationDBFolder = OpsServerConfig.getDBConnFileRootPath(dataDrive)
DestinationCacheFolder = OpsServerConfig.getCacheRootPath(cacheDrive)
DestinationFolder = OpsServerConfig.getEnvDataRootPath(dataDrive)

modifyOwnershipList = []
printMsg = True
totalCopySuccess = True
totalRepairMDSuccess = True


def copyDataFolders(srcRootPath, destRootPath, ownerAccount):
    copySuccess = True
    
    # Check if there is available space on destination drive
    # to copy folders.
    freeSpace = getFreeSpace(destRootPath, "GB")
    
    # Get total size of source folders
    srcSize = getDirSize(srcRootPath, "GB")

    print
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
            else:
                print
                changeOwnership(destPath, ownerAccount)
                    
    return copySuccess

try:
    
    startTime = datetime.now()
    print
    print "=============================================================="
    print "Copying data..."
    print "=============================================================="
    print '{:<28}{:%Y-%m-%d %H:%M:%S}'.format("Start time:", startTime)
    print
    
    # ---------------------------------------------------------------------
    # Copy databases
    # ---------------------------------------------------------------------
    
    if copyDBs:
        
        print "--------------------------------------------"
        print "Copy databases..."
        print "--------------------------------------------"
        print
        
        # ----------------------------------------
        # Determine which databases to copy
        # ----------------------------------------
        print "- Determining which databases to copy..."
        
        # Get list of all workspaces in destination folder files
        # (these could be file or enterprise geodatabases)
        arcpy.env.workspace = DestinationDBFolder
        destDBPathsSDE = arcpy.ListWorkspaces("*", "SDE")
        destDBPathsFGDB = arcpy.ListWorkspaces("*", "FileGDB")
        destDBPaths = destDBPathsSDE + destDBPathsFGDB
        
        # Create dictionary where destination db name is key and
        # path to workspace is value.
        destDBs = {}
        for dbPath in destDBPaths:
            destDBs[os.path.basename(dbPath).split(".")[0].lower()] = dbPath
        
        # Get list of all workspaces in staging db folder
        # (these could be file or enterprise geodatabases)
        arcpy.env.workspace = StagingDBFolder
        srcDBPathsSDE = arcpy.ListWorkspaces("*", "SDE")
        srcDBPathsFGDB = arcpy.ListWorkspaces("*", "FileGDB")
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
            print
            print "\tERROR: There are no databases to copy!"
            print
        else:
            continueCopy = True
        
        if continueCopy:
            print
            print "- Checking out Network Analyst license..."
            # Check out network extension
            if arcpy.CheckExtension("Network") == "Available":
                arcpy.CheckOutExtension("Network")
                continueCopy = True
            else:
                continueCopy = False
                print
                print "\tERROR: Network Analyst extension license unavailable. Can't copy databases."
                print
        
        if continueCopy:
            for db in dbsToCopy:
                print
                print "- Copying " + db.upper() + " database data..."
                srcPath = srcDBs[db]
                destPath = destDBs[db]
                print '{:<14}{:<100}'.format("\tSource:", srcPath)
                print '{:<14}{:<100}'.format("\tDestination:", destPath)
                print
                results = copyGDBData(srcPath, destPath)
                print
                success = checkResults(results, printMsg)
                if not success:
                    totalCopySuccess = success
    
    # ---------------------------------------------------------------------
    # Copy Folders (except cache folders)
    # ---------------------------------------------------------------------
    
    if copyFolders:
    
        print "--------------------------------------------"
        print "Copy folders..."
        print "--------------------------------------------"
        
        success = copyDataFolders(StagingFolder, DestinationFolder, agsServerAccount)
        if not success:
            totalCopySuccess = success
    
    # ---------------------------------------------------------------------
    # Copy Cache folders
    # ---------------------------------------------------------------------      
    if copyCacheData:
        print
        print "--------------------------------------------"
        print "Copy cache folders..."
        print "--------------------------------------------"
        print

        success = copyDataFolders(StagingCacheFolder, DestinationCacheFolder, agsServerAccount)
        if not success:
            totalCopySuccess = success

    # ---------------------------------------------------------------------
    # Repair Mosaic Dataset Paths
    # ---------------------------------------------------------------------                
    if repairMDPaths:

        print
        print "--------------------------------------------"
        print "Repair paths in file geodatabase mosaic datasets..."
        print "--------------------------------------------"
        print
        
        success = repairMosaicDatasets(dataDrive)
        totalRepairMDSuccess = success
        
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
    print
    print
    
    if copyDBs or copyFolders or copyCacheData:
        if totalCopySuccess:
            print "Data copy was successful."
        else:
            print "ERROR occurred during data copy."
    
    if repairMDPaths:
        if totalRepairMDSuccess:
            print "Repairing paths in file geodatabase mosaic datasets was successful."
        else:
            print "ERROR occurred during repair paths in file geodatabase mosaic datasets."
    print
        
    print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("Start time:", startTime)
    endTime = datetime.now()
    print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("End time:", endTime)


