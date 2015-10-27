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
#Name:      UtilitiesArcPy.py
#
#Purpose:   Various functions which utilize the ArcPy module.
#
#==============================================================================
import sys, os, traceback, time
import arcpy

class LicenseError(Exception):
    pass

def uploadServiceDefinition(sdFilePath, agsPubConnectionFile, startService=True):
    success = True
    pymsg = ""
    
    try:
        if startService:
            startService = "STARTED"
        else:
            startService = "STOPPED"
            
        arcpy.UploadServiceDefinition_server(sdFilePath, agsPubConnectionFile, in_startupType=startService, in_cluster='default')
        
    except:
        success = False
        pymsg = "\tError Info:\n\t" + str(sys.exc_info()[1])
        
    finally:
        return [success, pymsg]


def copyData(sourcePath, destinationPath, dataType=""):
    success = True
    pymsg = ""
    
    try:
        if arcpy.Exists(destinationPath):
            print "\tWARNING: dataset already exists in destination: " + destinationPath
            print "\tIf dataset is participating in a relationship, then might have been copied when parent was copied."
        else:
            arcpy.Copy_management(sourcePath, destinationPath)
        
    except:
        success = False
        pymsg = "\tError Info:\n\t" + str(sys.exc_info()[1])
        
    finally:
        return [success, pymsg]

def copyGDBData(sourceGDBPath, destinationGDBPath):
    success = True
    pymsg = ""
    printMsg = True
    debug = False
    
    try:
        #startTime = datetime.now()
        print '\n{:<14}{:<100}'.format("Source:", sourceGDBPath)
        print '{:<14}{:<100}\n'.format("Destination:", destinationGDBPath)
        
        # Verify input parameter types
        
        # Check out extensions
        print "- Check out network license..."
        if arcpy.CheckExtension("Network") == "Available":
            arcpy.CheckOutExtension("Network")
        else:
            # Raise a custom exception
            raise LicenseError
        
        descGDB = arcpy.Describe(sourceGDBPath)
        
        if debug:
            # Print some Describe Object properties
            if hasattr(descGDB, "name"):
                print "Name:        " + descGDB.name
            if hasattr(descGDB, "dataType"):
                print "DataType:    " + descGDB.dataType
            if hasattr(descGDB, "catalogPath"):
                print "CatalogPath: " + descGDB.catalogPath
        
        # Find children datasets
        datasets = []
        copyExcludeList = []
        for child in descGDB.children:
            if child.dataType != "RelationshipClass":
                datasets.append(child.name)
            else:
                descRel = arcpy.Describe(sourceGDBPath + "/" + child.name)
                for destClassName in descRel.destinationClassNames:
                    copyExcludeList.append(destClassName)
        
        # Do not copy the datasets that are the destination datasets in
        #   relationships since these datasets will automatically be
        #   copied when the origin datasets are copied
        copyList = [dataset for dataset in datasets if dataset not in copyExcludeList]
        
        if debug:
            print "\nAll datasets (excluding relationship classes):"
            print datasets
            print "\nDestination tables involved in relationship classes:"
            print copyExcludeList
            print "\nCopy the following:"
            print copyList
            
        if len(copyList) > 0:
            n = 1
            print "- Copying database data..."
            for dataset in copyList:
                srcPath = os.path.join(sourceGDBPath, dataset)
                destPath = os.path.join(destinationGDBPath, dataset)
                print "\tDataset: {} ({}/{})".format(dataset, n, len(copyList))
                if arcpy.Exists(destPath):
                    print "\t\tWARNING: Will not copy dataset."
                    print "\t\tDataset already exists in destination: " + destPath
                    print "\t\t(If dataset is participating in a relationship, then it was copied when origin dataset(s) was copied)."
                else:
                    print "\tCopying..."
                    results = copyData(srcPath, destPath)
                    copySuccess = checkResults(results, printMsg)
                    if not copySuccess:
                        success = False
                n = n + 1
        else:
            print "- No database data to copy."
            
    except LicenseError:
        success = False
        print "ERROR: Network license is unavailable"
    except:
        success = False
        pymsg = "\tError Info:\n\t" + str(sys.exc_info()[1])
        
    finally:
        arcpy.CheckInExtension("Network")
        # print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("Start time:", startTime)
        # print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("End time:", datetime.now())
        return [success, pymsg]

def checkResults(results, printMsg):
    
    success = results[0]
    
    if printMsg:
        if success:
            print "\tDone."
        else:
            print
            print "\t**********************************************"
            print "\t*ERROR encountered:"
            print results[1]
            print "\t**********************************************"
            print
        
    return success


def repairMosaicDatasetPaths(mosaicDatasetPath, pathsList):
    success = True
    pymsg = ""
    
    try:
        
        arcpy.RepairMosaicDatasetPaths_management(mosaicDatasetPath, pathsList)
        
    except:
        success = False
        pymsg = "\tError Info:\n\t" + str(sys.exc_info()[1])
        
    finally:
        return [success, pymsg]

def createAGSConnectionFile(agsConnFolderPath, agsConnFile, serverName,
                            userName, passWord, port=6080, useSSL=False,
                            connectionType="ADMINISTER_GIS_SERVICES",
                            serverType="ARCGIS_SERVER",
                            saveUserNamePassWord="SAVE_USERNAME"):
    success = True
    pymsg = ""
    
    try:
        
        agsConnFilePath = agsConnFolderPath + os.sep + agsConnFile
        
        # Delete connection file if it already exists
        if os.path.exists(agsConnFilePath):
            os.remove(agsConnFilePath)
        
        # Build URL
        if useSSL:
            targetAGSURL = "https"
        else:
            targetAGSURL = "http"
        
        targetAGSURL = "{}://{}".format(targetAGSURL, serverName)
        
        if port:
            targetAGSURL = "{}:{}".format(targetAGSURL, port)
        
        targetAGSURL = "{}/arcgis/admin".format(targetAGSURL)
        
        # Create connection file
        arcpy.mapping.CreateGISServerConnectionFile(
            connectionType, agsConnFolderPath, agsConnFile,
            targetAGSURL, serverType, True, None, userName, passWord,
            saveUserNamePassWord)
        
    except:
        success = False
        pymsg = "\tError Info:\n\t" + str(sys.exc_info()[1])
        
    finally:
        return [success, pymsg]