#!/usr/bin/env python
import sys, os, traceback
import arcpy
     
def uploadServiceDefinition(sdFilePath, agsPubConnectionFile):
    success = True
    pymsg = ""
    
    try:
        
        arcpy.UploadServiceDefinition_server(sdFilePath, agsPubConnectionFile)
        
    except:
        success = False
        pymsg = "\tError Info:\n\t" + str(sys.exc_info()[1])
        
    finally:
        return [success, pymsg]


def copyData(sourcePath, destinationPath, dataType=""):
    success = True
    pymsg = ""
    
    try:
        
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
        #print "featClassList: " + str(featClassList)
        datasetList = arcpy.ListDatasets()
        #print "datasetList: " + str(datasetList)
        tableList = arcpy.ListTables()
        #print "tableList: " + str(tableList)

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
                    
        #print "allDatasetsList: "
        #for ds in allDatasetsList:
        #    print "\t" + ds
        #datasetList.extend(tableList)
        
        if allDatasetsList != None:
            for dataset in allDatasetsList:
                srcPath = os.path.join(sourceGDBPath, dataset)
                destPath = os.path.join(destinationGDBPath, dataset)
                print "\tCopying " + dataset + "..."
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
                            userName, passWord, port=6080,
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
        
        # Set URL
        targetAGSURL = "http://{}:{}/arcgis/admin".format(serverName, port)
        
        # Create connection file
        arcpy.mapping.CreateGISServerConnectionFile(
            connectionType, agsConnFolderPath, agsConnFile,
            targetAGSURL, serverType, True, None, userName, passWord,
            saveUserNamePassWord)
        #print arcpy.GetMessages()
        
    except:
        success = False
        pymsg = "\tError Info:\n\t" + str(sys.exc_info()[1])
        
    finally:
        return [success, pymsg]