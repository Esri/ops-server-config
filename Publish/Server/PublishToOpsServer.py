#!/usr/bin/env python
import sys, os, time, traceback
from datetime import datetime

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

import walkingDirTrees
from UtilitiesArcPy import uploadServiceDefinition
from UtilitiesArcPy import createAGSConnectionFile
from UtilitiesArcPy import checkResults
import OpsServerConfig
import DataStore

scriptName = os.path.basename(sys.argv[0])
filePattern = "*.sd"
totalSuccess = True

doFindSDFiles = True
doCreateAGSConnFile = True
doRegDataStores = True
doPublishServiceDefs = True
doUnregDataStores = True

publishingDBServer = OpsServerConfig.publishingDBServer
databases = OpsServerConfig.databasesToCreate
dbuser = "sde"
installOnlyPublishingFolders = OpsServerConfig.installOnlyPublishingFolders

# Used for testing the unregister data stores function
#dataStorePaths = ['/fileShares/OpsEnvironment_InstallOnly',
#                  '/enterpriseDatabases/Economic_InstallOnly',
#                 '/enterpriseDatabases/Imagery_InstallOnly',
#                 '/enterpriseDatabases/Infrastructure_InstallOnly',
#                 '/enterpriseDatabases/OperationsGEP_InstallOnly',
#                 '/enterpriseDatabases/Physical_InstallOnly',
#                 '/enterpriseDatabases/Political_InstallOnly',
#                 '/enterpriseDatabases/RTDS_InstallOnly',
#                 '/enterpriseDatabases/Social_InstallOnly',
#                 '/enterpriseDatabases/UTDS_InstallOnly']


installOnlyClientFolders = OpsServerConfig.installOnlyPublishingFolders
useSSL = True

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------
if len(sys.argv) <> 6:
    print "\n" + scriptName + " <Server_FullyQualifiedDomainName> <Server_Port> <User_Name> " + \
                            "<Password> <Service_Definition_Root_Folder_Path>"
    print "\nWhere:"
    print "\n\t<Server_FullyQualifiedDomainName> (required parameter) Fully qualified domain name of ArcGIS Server."
    print "\n\t<Server_Port> (required parameter) ArcGIS Server port number; if not using server port enter '#'"
    print "\n\t<User_Name> (required parameter) ArcGIS Server site administrator user name."
    print "\n\t<Password> (required parameter) ArcGIS Server site administrator password."
    print "\n\t<Service_Definition_Root_Folder_Path> (required parameter) is the path of the root folder"
    print "\t\tcontaing the service definition (.sd) files to upload (publish)."
    print
    sys.exit(1)

serverFQDN = sys.argv[1]
serverPort = sys.argv[2]
userName = sys.argv[3]
passWord = sys.argv[4]
rootSDFolderPath = sys.argv[5]

server = serverFQDN.split('.')[0]

agsPubConnectionFile = None

if serverPort.strip() == '#':
    serverPort = None
    
if not os.path.exists(rootSDFolderPath):
    print
    print "\n<Service_Definition_Root_Folder_Path> path " + rootSDFolderPath + " does not exist.\n"
    sys.exit(1)

def createAGSConnFile(servername, username, password, serverport, useSSL):

    success = True
    printMsg = True
    agsConnFilePath = None
    
    try:
        
        # Set connection folder and file variables
        agsConnFolderPath = os.path.dirname(sys.argv[0])
        agsConnFile = "OpsServer_publish.ags"
        agsConnFilePath = os.path.join(agsConnFolderPath, agsConnFile)
        
        results = createAGSConnectionFile(agsConnFolderPath, agsConnFile, servername,
                            username, password, serverport, useSSL, "PUBLISH_GIS_SERVICES")
        
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
    
def registerDataStores():
    registerSuccessful = True
    dataStorePaths = []
    # ---------------------------------------------------------------------
    # Create "replicated" set of data stores that will only be used
    # during publishing.
    # ---------------------------------------------------------------------
    print "\n---------------------------------------------------------------------------"
    print "- Registering temporary 'replicated' set of data stores to use during publishing..."
    print "---------------------------------------------------------------------------"
    print
 
    regNameAppend = "_InstallOnly"
    
    # Register folder
    
    # Get data folder based on the existing folder data store
    for regName in installOnlyPublishingFolders.keys():
        searchPath = "/fileShares/" + regName
        success, item = DataStore.getitem(serverFQDN, serverPort, userName, passWord, searchPath)
        
        if not success:
            registerSuccessful = False
            print "ERROR: Could not find existing data store item " + searchPath + \
                    ". Can't register temp data store " + regName + regNameAppend
        else:
            pubFolderPath = installOnlyPublishingFolders[regName]
            serverFolderPath = item['info']['path'].encode('ascii')
            
            dsPath, dsItem = DataStore.create_replicated_folder_item(
                                regName + regNameAppend, pubFolderPath, serverFolderPath)
            
            print "\n\tFolder: Publisher - " + pubFolderPath + "; Server - " + serverFolderPath
            print "\t\t" + dsPath
            
            # Add data store path to list of data stores to unregister
            dataStorePaths.append(dsPath)
            
            # Register the data store item
            success, response = DataStore.register(serverFQDN, serverPort, userName, passWord, dsItem)
            if success:
                print "\tDone."
            else:
                registerSuccessful = False
                print "ERROR:" + str(response)
                
                
    # Register databases
    for db in databases:
        isManaged = databases[db][0]
        registrationName = databases[db][1]
        
        if not isManaged:
            print "\n\tDatabase: " + db
            
            # Create the publishing database connection string
            pub_db_conn = DataStore.create_postgresql_db_connection_str(
                                    publishingDBServer, db, dbuser, passWord)
            
            # Create the server database connection string
            server_db_conn = DataStore.create_postgresql_db_connection_str(
                                    server, db, dbuser, passWord)
            
            # Create the data store item
            dsPath, dsItem = DataStore.create_replicated_entdb_item(
                                    registrationName + regNameAppend, pub_db_conn, server_db_conn)
            print "\t\t" + dsPath
            
            # Add data store path to list of data stores to unregister
            dataStorePaths.append(dsPath)
            
            # Register the data store item
            success, response = DataStore.register(serverFQDN, serverPort, userName, passWord, dsItem)
            if success:
                print "\tDone."
            else:
                registerSuccessful = False
                print "ERROR:" + str(response)
                    
    return registerSuccessful, dataStorePaths     

def unregisterDataStores(dataStorePaths):
    unregisterSuccessful = True
    print "\n---------------------------------------------------------------------------"
    print "- Unregister temporary 'replicated' set of data stores used for publishing..."
    print "---------------------------------------------------------------------------"
    
    for itemPath in dataStorePaths:
        print "\n\t" + itemPath
        success, response = DataStore.unregister(serverFQDN, serverPort, userName, passWord, itemPath)
        if success:
            print "\tDone."
        else:
            unregisterSuccessful = False
            print "ERROR:" + str(response)
                
    return unregisterSuccessful

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

    # ---------------------------------------------------------------------
    # Traverse SD root folder and look for .sd files
    # ---------------------------------------------------------------------
    if doFindSDFiles:

        print "\n---------------------------------------------------------------------------"
        print "- Looking for service definition files (" + filePattern + ") in folder:"
        print "\t" + rootSDFolderPath
        print "---------------------------------------------------------------------------"
        sdFilePaths = walkingDirTrees.listFiles(rootSDFolderPath, filePattern)
        
        numFilesFound = len(sdFilePaths)
        
        if numFilesFound == 0:
            totalSuccess = False
            raise Exception("ERROR: No .sd files were found in folder '" + rootSDFolderPath + "'. Can't continue publishing.")
        
        print "- Found the following " + str(numFilesFound) + " .sd files:\n"
        for sdFilePath in sdFilePaths:
            print "\t" + sdFilePath + "\n"        
        
    # ---------------------------------------------------------------------
    # Create AGS publisher connection file
    # ---------------------------------------------------------------------
    if doCreateAGSConnFile:
        print "\n---------------------------------------------------------------------------"
        print "- Creating ArcGIS Server publisher connection file..."
        print "---------------------------------------------------------------------------"
        
        agsPubConnectionFile = createAGSConnFile(serverFQDN, userName, passWord, serverPort, useSSL)
        
        if agsPubConnectionFile is None:
            totalSuccess = False
            raise Exception("ERROR: Encountered error creating AGS connection file . Can't continue publishing.")
        else:
            print "\tCreated connection file: " + agsPubConnectionFile + "\n"
    
    # ---------------------------------------------------------------------
    # Register data stores
    # ---------------------------------------------------------------------
    if doRegDataStores:
        success, dataStorePaths = registerDataStores()
        if not success:
            totalSuccess = success
            raise Exception("ERROR: Encountered error during registering of temporary data stores. Can't continue publishing.")
    
    # ---------------------------------------------------------------------
    # Publish service definition files
    # ---------------------------------------------------------------------
    if doPublishServiceDefs:
            
        print "\n---------------------------------------------------------------------------"
        print "- Uploading (publishing) service definition (*.sd) files..."
        print "---------------------------------------------------------------------------"
        print
        
        for sdFilePath in sdFilePaths:
            print "\t- Uploading '" + sdFilePath + "'..."
            
            results = uploadServiceDefinition(sdFilePath, agsPubConnectionFile)
            
            if results[0]:
                print "\tDone.\n"
            else:
                totalSuccess = False
                print "\n\t**********************************************"
                print "\t*ERROR encountered:"
                print results[1]
                print "\n\t**********************************************\n"
        
    # ---------------------------------------------------------------------
    # Unregister data stores
    # ---------------------------------------------------------------------
    if doUnregDataStores:
        success = unregisterDataStores(dataStorePaths)
        if not success:
            totalSuccess = success
            raise Exception("ERROR: Encountered error during unregistering of temporary data stores.")

except:
    totalSuccess = False
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
    if totalSuccess:
        print "Publishing services to Ops Server completed successfully."
    else:
        print "***** ERROR: Publishing services to ArcGIS Server site was _NOT_ completed successfully."
    print
    print "Start time: " + str(startTime)
    print "End time: " + str(endTime)
    

