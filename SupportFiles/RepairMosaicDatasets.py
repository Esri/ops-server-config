#!/usr/bin/env python
import os, arcpy, sys, traceback

import OpsServerConfig
from UtilitiesArcPy import repairMosaicDatasetPaths
from UtilitiesArcPy import checkResults
from Utilities import findFolderPath

#origPath = OpsServerConfig.publishingFolder
installOnlyPublishingFolders = OpsServerConfig.installOnlyPublishingFolders
printMsg = True

def repairMosaicDatasets(dataDrive):
    
    try:
        
        totalSuccess = True
        
        newPath = OpsServerConfig.getEnvDataRootPath(dataDrive)

        # "Create" RepairMosaicDatasetPaths GP tool Original Path/New Path
        # parameter string
        repairOrigNewPath = ""
        for regName in installOnlyPublishingFolders.keys():
            repairOrigNewPath = repairOrigNewPath + "; " + \
                    installOnlyPublishingFolders[regName] + " " + newPath
        # Remove leading semicolon
        repairOrigNewPath = repairOrigNewPath.replace("; ", "", 1)

        
        #repairOrigNewPath = origPath + " " + newPath
        rootSearchPath = newPath
        
        
        # Get list of all folders ending in ".gdb"
        print
        print "Searching " + rootSearchPath + " looking for file geodatabases..."
        gdbList = findFolderPath(rootSearchPath, "*.gdb", False)
        
        # Ensure that list only contains entries that are local geodatabase
        # (file geodatabase); just in case there happens to be a folder with ".gdb"
        # that is not a geodatabase
        gdbList[:] = [gdb for gdb in gdbList if
                      arcpy.Describe(gdb).workspaceType.upper() == "LOCALDATABASE"]
        
        # Loop through all file geodatabases and repair paths for any non-referenced
        # mosaic datasets
        for gdb in gdbList:
            print
            print "Found file geodatabase: " + gdb
            print "\tChecking for existence of non-referenced mosaic datasets..."
            
            # Get any mosaic datasets in geodatabase
            arcpy.env.workspace = gdb
            mdList = arcpy.ListDatasets("*", "Mosaic")
            
            # Modify list to contain only non-reference mosaic datasets
            mdList[:] = [md for md in mdList if not arcpy.Describe(md).referenced]
            
            if len(mdList) == 0:
                print "\tNone found."
            else:
                print "\tFound " + str(len(mdList)) + " non-referenced mosaic dataset(s)."
            
            for md in mdList:
                print
                print "\tReparing paths in mosaic dataset '" + md + "'..."
                results = repairMosaicDatasetPaths(md, repairOrigNewPath)
                success = checkResults(results, printMsg)
                if not success:
                    totalSuccess = success
    
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
        if totalSuccess:
            print "Done repairing mosaic dataset paths."
        else:
            print "ERROR occurred during mosaic dataset path repair."
        print
        
        return totalSuccess
    