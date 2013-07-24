#!/usr/bin/env python
import sys, os, time, traceback
from datetime import datetime

# Add ConfigureOpsServer\SupportFiles subfolder to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

import walkingDirTrees
from UtilitiesArcPy import uploadServiceDefinition
from UtilitiesArcPy import createAGSConnectionFile
from UtilitiesArcPy import checkResults
from RegisterDataStores import registerDataStores
from RegisterDataStores import unregisterDataStoreItem
import OpsServerConfig
from AllFunctions import getDataItemInfo

scriptName = os.path.basename(sys.argv[0])
filePattern = "*.sd"

regDataStores = True
publishServiceDefs = True
unregDataStores = True

dbsToUnregister = OpsServerConfig.databasesToCreate
installOnlyClientFolders = OpsServerConfig.installOnlyPublishingFolders

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------
if len(sys.argv) <> 6:
    print "\n" + scriptName + " <Server_Name> <Server_Port> <User_Name> " + \
                            "<Password> <Service_Definition_Root_Folder_Path>"
    print "\nWhere:"
    print "\n\t<Server_Name> (required parameter) ArcGIS Server server name."
    print "\n\t<Server_Port> (required parameter) ArcGIS Server port number."
    print "\n\t<User_Name> (required parameter) ArcGIS Server site administrator user name."
    print "\n\t<Password> (required parameter) ArcGIS Server site administrator password."
    print "\n\t<Service_Definition_Root_Folder_Path> (required parameter) is the path of the root folder"
    print "\t\tcontaing the service definition (.sd) files to upload (publish)."
    print
    sys.exit(1)

serverName = sys.argv[1]
serverPort = sys.argv[2]
userName = sys.argv[3]
passWord = sys.argv[4]
rootSDFolderPath = sys.argv[5]

sharedDataStoreConfig = False
installPurposeOnly = True
agsPubConnectionFile = None
dataDrive = None

if not os.path.exists(rootSDFolderPath):
    print
    print "\n<Service_Definition_Root_Folder_Path> path " + rootSDFolderPath + " does not exist.\n"
    sys.exit(1)

def createAGSConnFile(servername, username, password, serverport):

    success = True
    printMsg = True
    agsConnFilePath = None
    
    try:
        
        # Set connection folder and file variables
        fileRoot = "ConfigureOpsServer"
        scriptPath = sys.argv[0]
        agsConnFolderPath = scriptPath[:(scriptPath.find(fileRoot) + len(fileRoot))]
        agsConnFile = "OpsServer_publish.ags"
        agsConnFilePath = agsConnFolderPath + os.sep + agsConnFile
        
        results = createAGSConnectionFile(agsConnFolderPath, agsConnFile, servername,
                            username, password, serverport, "PUBLISH_GIS_SERVICES")
        success = checkResults(results, printMsg)
        
        if not os.path.exists(agsConnFilePath):
            agsConnFilePath = None
            
    except:
        success = False
        
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
        # Return success flag
        return agsConnFilePath
    
    
try:
    startTime = datetime.now()
    success = True
    
    # ---------------------------------------------------------------------
    # Print header
    # ---------------------------------------------------------------------
    print "\n===================================================================================="
    print "Publishing Services to ArcGIS Server site"
    print "===================================================================================="
    print "Start time: " + str(startTime) + "\n"
 
    # Create AGS publisher connection file
    
    print "\n- Creating ArcGIS Server publisher connection file...\n"
    
    agsPubConnectionFile = createAGSConnFile(serverName, userName, passWord, serverPort)
    
    if agsPubConnectionFile is None:
        
        success = False
        
        print "\nERROR: Could not create publisher connection file " + agsPubConnectionFile
        print "Exiting publishing script.\n"
    
    else:
        print "\tCreated connection file: " + agsPubConnectionFile
        
    # Determine the drive letter of the data drive using the information
    # from the registered folder data store "OpsEnvironment". This drive
    # letter is required in order to register data stores.
    if success:
        
        print "\n- Determining data drive from registered data store information...\n"
        
        dataItemInfo = getDataItemInfo(serverName, serverPort, userName,
                                       passWord, "/fileShares/OpsEnvironment")
        if "info" not in dataItemInfo:
            
            success = False

            print "\nERROR: Could not determine the data drive based on the " + \
                        "registered data store information."
            print "Exiting publishing script.\n"
        
        else:
            path = dataItemInfo["info"]["path"]
            dataDrive = os.path.splitdrive(path)[0].replace(":","")
            print "\tData drive is: " + dataDrive + "\n"
    
    
    if success:

        if regDataStores:
            # ---------------------------------------------------------------------
            # Create "replicated" set of data stores that will only be used
            # during publishing.
            # ---------------------------------------------------------------------
            print "---------------------------------------------------------------------------"
            print "- Creating temporary 'replicated' set of data stores to use during publishing..."
            print "---------------------------------------------------------------------------"
            print
            registerDataStores(sharedDataStoreConfig, installPurposeOnly,
                                                userName, passWord, dataDrive)
     
        if publishServiceDefs:
            # ---------------------------------------------------------------------
            # Traverse SD root folder and look for .sd files
            # ---------------------------------------------------------------------
            print
            print "---------------------------------------------------------------------------"
            print "- Traversing folder structure " + rootSDFolderPath
            print "\tlooking for service definition files (" + filePattern + ")..."
            print "---------------------------------------------------------------------------"
            print
            sdFilePaths = walkingDirTrees.listFiles(rootSDFolderPath, filePattern)
            
            numFilesFound = len(sdFilePaths)
            
            if numFilesFound == 0:
                success = False
                print "\t************************"
                print "\t*ERROR: Did not find any .sd files."
                print "\t************************"
            else:
                print "\t- Found the following " + str(numFilesFound) + " .sd files:"
                print
                for sdFilePath in sdFilePaths:
                    print "\t\t" + sdFilePath
            print
            print
                
                
            # ---------------------------------------------------------------------
            # Upload (publish) each of the .sd files
            # ---------------------------------------------------------------------
            if success:
                
                print "---------------------------------------------------------------------------"
                print "- Uploading (publishing) service definition (*.sd) files..."
                print "---------------------------------------------------------------------------"
                print
                
                for sdFilePath in sdFilePaths:
                    print "\t- Uploading '" + sdFilePath + "'..."
                    
                    results = uploadServiceDefinition(sdFilePath, agsPubConnectionFile)
                    
                    if results[0]:
                        print "\tDone."
                    else:
                        success = False
                        print
                        print "\t**********************************************"
                        print "\t*ERROR encountered:"
                        print results[1]
                        print "\t**********************************************"
                    print
                    print
        
        if unregDataStores:
            print "---------------------------------------------------------------------------"
            print "- Unregister temporary 'replicated' set of data stores used for publishing..."
            print "---------------------------------------------------------------------------"
            print
            
            print "\t-Unregister Data Stores with Site...\n"
            
            unregisterList = []
            
            #Add database related data stores to unregister list
            for db in dbsToUnregister:
                isManaged = dbsToUnregister[db][0]
                registrationName = dbsToUnregister[db][1] + "_InstallOnly"
                if not isManaged:
                    unregisterList.append("/enterpriseDatabases/" + registrationName)
            
            #Add folders to unregister list
            for registrationName in installOnlyClientFolders.keys():
                unregisterList.append("/fileShares/" + registrationName)
            
            #Unregister
            for dsPath in unregisterList:
                print
                print "\t\t-Unregistering data store '" + dsPath + "'..." 
                unregisterDataStoreItem(userName, passWord, dsPath)
        
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
    endTime = datetime.now()
    print
    print
    if success:
        print "Publishing services to Ops Server completed successfully."
    else:
        print "***** ERROR: Publishing services to ArcGIS Server site was _NOT_ completed successfully."
    print
    print
    print "Start time: " + str(startTime)
    print "End time: " + str(endTime)
    

