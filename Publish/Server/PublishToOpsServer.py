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
import json

DEBUG = False

# Store list of valid Ops Server type values
valid_ops_types = OpsServerConfig.valid_ops_types

scriptName = os.path.basename(sys.argv[0])
filePattern = "*.sd"
totalSuccess = True
specified_users = None
specified_groups = None

doFindSDFiles = True
doCreateAGSConnFile = True
doRegDataStores = True
doPublishServiceDefs = True
doUnregDataStores = True

#publishingDBServer = OpsServerConfig.publishingDBServer
databases = OpsServerConfig.databasesToCreate
dbuser = "sde"
installOnlyPublishingFolders = OpsServerConfig.installOnlyPublishingFolders
installOnlyPublishingDBServers = OpsServerConfig.installOnlyPublishingDBServers
dataFolderDStoreName = OpsServerConfig.dataFolderDStoreName

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


#installOnlyClientFolders = OpsServerConfig.installOnlyPublishingFolders

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------
if len(sys.argv) < 8:
    print "\n" + scriptName + " <Server_FullyQualifiedDomainName> <Server_Port> <User_Name> " + \
                            "<Password> <Use_SSL: Yes|No> <Start_Service: Yes|No>"
    print "\t\t<Service_Definition_Root_Folder_Path> {OwnersToPublish} {GroupsToPublish}"
    
    print '\nWhere:'
    print '\n\t<Server_FullyQualifiedDomainName> (required) Fully qualified domain name of ArcGIS Server.'
    print '\n\t<Server_Port> (required) ArcGIS Server port number; if not using server port enter #'
    print '\n\t<User_Name> (required) ArcGIS Server site administrator user name.'
    print '\n\t<Password> (required) ArcGIS Server site administrator password.'
    print '\n\t<Use_SSL: Yes|No> (required) Flag indicating if you want to connect to ArcGIS Server using HTTPS.'
    print '\n\t<Start_Service: Yes|No> (required) Flag indicating if the service should be started after publishing.'
    print '\n\t<Service_Definition_Root_Folder_Path> (required parameter) is the path of the root folder containg the service definition (.sd) files to upload (publish).'
    
    print '\n\t{Owners_To_Publish} (optional parameter):'
    print '\t\t-By default, all services are published regardless of the owner.'
    print '\t\t-Specify # placeholder character if you want to publish services for all owners and you are specifying {Groups_To_Publish} values'
    print '\t\t-To publish services for only specific owners specify pipe "|" delimited list of owner names, i.e. "Owner|Owner|...".'
    print '\t\t-To publish services for ALL owners except specific owners, specify pipe "|" delimited list of owners to exclude with "-" prefix, i.e. "-Owner|Owner|...".'
    print '\t\t-NOTE: Owner names are case sensitive.'
    print '\t\t-NOTE: Parameter value MUST be surrounded by double-quotes.'
    
    print '\n\t{Groups_To_Publish} (optional parameter):'
    print '\t\t-To publish services shared with specific portal groups specify a pipe "|" delimited list of groups using the syntax "GroupOwner:GroupTitle|GroupOwner:GroupTitle|...".'
    print '\t\t-NOTE: GroupOwner and GroupTitle values are case sensitive.'
    print '\t\t-NOTE: Parameter value MUST be surrounded by double-quotes.'
    print
    sys.exit(1)

serverFQDN = sys.argv[1]
serverPort = sys.argv[2]
userName = sys.argv[3]
passWord = sys.argv[4]
useSSL = sys.argv[5]
startService = sys.argv[6]
rootSDFolderPath = sys.argv[7]

if len(sys.argv) > 8:
    specified_users = sys.argv[8]
    if specified_users.strip().lower() == '#':
        specified_users = None
        
if len(sys.argv) > 9:
    specified_groups = sys.argv[9]
    specified_groups = [group.strip() for group in specified_groups.split('|')]
    
if len(sys.argv) > 10:
    print "You entered too many script parameters."
    sys.exit(1)

if useSSL.strip().lower() in ['yes', 'ye', 'y']:
    useSSL = True
else:
    useSSL = False

if startService.strip().lower() in ['yes', 'ye', 'y']:
    startService = True
else:
    startService = False
    
if DEBUG:
    print "serverFQDN: " + str(serverFQDN)
    print "serverPort: " + str(serverPort)
    print "userName: " + str(userName)
    print "passWord: " + str(passWord)
    if specified_users:
        print "specifiedUsers: " + str(specified_users)    
    if specified_groups:
        print "specified_groups: " + str(specified_groups)
        
excludeUsers = None
includeUsers = None
if specified_users:
    if specified_users.find('-') == 0:
        excludeUsers = specified_users.replace('-', '', 1).replace(' ', '').split('|')
    else:
        includeUsers = specified_users.replace(' ', '').split('|')

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
    
    # Register folders
    for pubFolderServerName in installOnlyPublishingFolders.keys():
        
        registrationName = dataFolderDStoreName + "_" + pubFolderServerName + regNameAppend
        
        # Get data folder based on the existing folder data store
        searchPath = "/fileShares/" + dataFolderDStoreName
        success, item = DataStore.getitem(serverFQDN, serverPort, userName, passWord, searchPath, useSSL)
        
        if not success:
            registerSuccessful = False
            print "ERROR: Could not find existing data store item " + searchPath + \
                    ". Can't register temp data store " + registrationName
        else:
            serverFolderPath = item['info']['path'].encode('ascii')
            pubFolderPath = installOnlyPublishingFolders[pubFolderServerName]
            dsPath, dsItem = DataStore.create_replicated_folder_item(
                                registrationName, pubFolderPath, serverFolderPath)
            
            print "\n\n\tServer: " + pubFolderServerName
            print "\t\tFolder: Publisher - " + pubFolderPath + "; Server - " + serverFolderPath
            print "\t\t" + dsPath
            
            # Add data store path to list of data stores to unregister
            dataStorePaths.append(dsPath)
            
            # Register the data store item
            success, response = DataStore.register(serverFQDN, serverPort, userName, passWord, dsItem, useSSL)
            if success:
                print "\tDone."
            else:
                registerSuccessful = False
                print "ERROR:" + str(response)
                
                
    # Register databases
    for db in databases:
        isManaged = databases[db][0]
        
        if not isManaged:
            print "\n\n\tDatabase: " + db
            
            for publishingDBServer in installOnlyPublishingDBServers:
                
                registrationName = databases[db][1] + "_" + publishingDBServer + regNameAppend
                
                # Create the publishing database connection string
                success, pub_db_conn = DataStore.create_postgresql_db_connection_str(
                                        serverFQDN, serverPort, userName, passWord,
                                        publishingDBServer, db, dbuser, passWord, useSSL)
                if not success:
                    registerSuccessful = False
                    print "ERROR: error encountered while creating publishing database connection string -"
                    print str(pub_db_conn)
                
                # Create the server database connection string
                success, server_db_conn = DataStore.create_postgresql_db_connection_str(
                                        serverFQDN, serverPort, userName, passWord,
                                        server, db, dbuser, passWord, useSSL)
                if not success:
                    registerSuccessful = False
                    print "ERROR: error encountered while creating server database connection string -"
                    print str(server_db_conn)
                    
                # Create the data store item
                dsPath, dsItem = DataStore.create_replicated_entdb_item(
                                        registrationName, pub_db_conn, server_db_conn)
                print "\t\t" + dsPath
                
                # Add data store path to list of data stores to unregister
                dataStorePaths.append(dsPath)
                
                # Register the data store item
                success, response = DataStore.register(serverFQDN, serverPort, userName, passWord, dsItem, useSSL)
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
        success, response = DataStore.unregister(serverFQDN, serverPort, userName, passWord, itemPath, useSSL)
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
        
        i = 1
        for sdFilePath in sdFilePaths:
            doPublish = True
            owners = None
            tags = None
            print "\n- Service Definition: " + sdFilePath + " (" + str(i) + " of " + str(numFilesFound) + ")..."
            
            # Extract info from portal info json file for the .sd file
            sdFolder = os.path.dirname(sdFilePath)
            fileNameNoExt = os.path.splitext(os.path.basename(sdFilePath))[0]
            os.chdir(sdFolder)
            p_info = json.load(open(fileNameNoExt + '_p_info.json'))
            portalItems = p_info.get('portalItems')
            
            # Get all the portal item owners for this service from the JSON
            owners = []
            if portalItems:
                for item in portalItems:
                    itemInfo = item.get('itemInfo')
                    if itemInfo:
                        owner = itemInfo.get('owner')
                        if owner:
                            owners.append(owner.encode('ascii'))
                owners = list(set(owners))
            
            # Get the shared portal groups for all the portal items associated
            # with this service from the JSON
            groups = []
            for item in portalItems:
                itemGroups = item.get('itemGroups')
                if itemGroups:
                    for itemGroup in item['itemGroups']:
                        groupOwner = itemGroup['owner']
                        groupTitle = itemGroup['title']
                    groups.append('{}:{}'.format(groupOwner, groupTitle).encode('ascii'))
            groups = list(set(groups))
            
            # Evaluate if the service should be published based on owners
            if specified_users:
                if excludeUsers:
                    doPublish = True
                    for user in excludeUsers:
                        if user in owners:
                            doPublish = False
                elif includeUsers:
                    doPublish = False
                    for user in includeUsers:
                        if user in owners:
                            doPublish = True
            
            # Evaluate if the service should be published based on group membership
            if doPublish:
                if specified_groups:
                    doPublish = False
                    for specified_group in specified_groups:
                        if specified_group in groups:
                            doPublish = True
            
            print '\tOwners: ' + str(owners)
            print '\tGroups: ' + str(groups)
            print "\tPublish service? " + str(doPublish)
            
            # Set to false just to test logic
            if doPublish:
                results = uploadServiceDefinition(sdFilePath, agsPubConnectionFile, startService)
                if results[0]:
                    print "\tDone.\n"
                else:
                    totalSuccess = False
                    print "\n\t**********************************************"
                    print "\t*ERROR encountered:"
                    print results[1]
                    print "\n\t**********************************************\n"

            i = i + 1
            time.sleep(5)
            
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
    

