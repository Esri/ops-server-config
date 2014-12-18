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
import sys, os, traceback
import arcpy
     
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
    
    try:
        arcpy.env.workspace = sourceGDBPath
        allDatasetsList = []
        featClassList = arcpy.ListFeatureClasses()
        datasetList = arcpy.ListDatasets()
        tableList = arcpy.ListTables()

        # arcpy.ListFeatureClass has bug where it will return raster datasets;
        # so the following code will add datasets to allDatasetsList if
        # it does not already exist

        # the following single line will merge lists; however, the ListFeatureClass
        # and ListDatasets return the raster dataset name in different cases (i.e.
        # ListFeatureClasses will return as original case, but ListDatasets
        # will lowercase the complete name so the following single line of code
        # views these items as unique and not the same
        
        #allDatasetsList = list(set(featClassList + datasetList + tableList))

        # So explicitly search lists to see if item already exists in
        # allDatasetList list.
        listOfLists = [featClassList, datasetList, tableList]
        for dsList in listOfLists:
            for ds in dsList:
                exists = False
                for x in allDatasetsList:
                    if ds.lower() == x.lower():
                        exists = True
                if not exists:
                    allDatasetsList.append(ds)
        
        if allDatasetsList != None:
            for dataset in allDatasetsList:
                srcPath = os.path.join(sourceGDBPath, dataset)
                destPath = os.path.join(destinationGDBPath, dataset)
                print "\tDataset: " + dataset
                if arcpy.Exists(destPath):
                    print "\t\tWARNING: Will not copy dataset."
                    print "\t\tDataset already exists in destination: " + destPath
                    print "\t\t(If dataset is participating in a relationship, then might have been copied when parent was copied)."
                else:
                    print "\tCopying..."
                    results = copyData(srcPath, destPath)
                    copySuccess = checkResults(results, printMsg)
                    if not copySuccess:
                        success = False
    except:
        success = False
        pymsg = "\tError Info:\n\t" + str(sys.exc_info()[1])
        
    finally:
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