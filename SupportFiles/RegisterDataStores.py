#==============================================================================
#Name:          RegisterDataStores.py
#Purpose:       Registers the servers data stores with the ArcGIS Server site.
#
#Prerequisites: The variables in the "Shared / Replicated Database Configuration"
#               section of the OpsServerConfig.py script must be set before
#               executing this script.
#
#History:       2012:   Initial code.
#
#==============================================================================
import sys, os, traceback

# For Http calls
import httplib, urllib, json

import OpsServerConfig
from Utilities import makePath

serverName = OpsServerConfig.serverName
serverPort = OpsServerConfig.serverPort
    
regFolders = True
regDatabases = True

def registerDataStores(sharedDataStoreConfig, forInstallPurposeOnly, username, password, dataDrive):
    
    success = True
    
    sharedDBConfig = sharedDataStoreConfig
    sharedFolderConfig = sharedDataStoreConfig

    try:
        opsServer = OpsServerConfig.getOpsServerRootPath(dataDrive)
	environmentData = OpsServerConfig.getEnvDataRootPath(dataDrive)
        clientServerName = OpsServerConfig.publishingDBServer
        clientFolderPath = OpsServerConfig.publishingFolder
	clientFolderDSName = OpsServerConfig.dataFolderDStoreName
        installOnlyClientFolders = OpsServerConfig.installOnlyPublishingFolders
        dbsToRegister = OpsServerConfig.databasesToCreate
        
        print
        print "\t-Register Data Stores with Site..."
        print
        
        # ---------------------------------------------------------------------
        # Register Folders by just using paths
        # ---------------------------------------------------------------------
        if regFolders:
            
            if forInstallPurposeOnly:
                clientFolderPaths = installOnlyClientFolders
            else:
                clientFolderPaths = {clientFolderDSName: clientFolderPath}
            
            for registrationName, clientFolderPath in clientFolderPaths.items():
                
                if sharedFolderConfig:
                    sharedStr = "shared"
                    clientPath = None
                else:
                    sharedStr = "replicated"
                    clientPath = clientFolderPath
                    
                print "\t\t-Registering folder " + environmentData + \
                    " with site as " + registrationName + " (" + sharedStr + ")..."
                
                # Create dictionary with JSON items common to all database cases
                # (i.e., managed, and non-managed shared and replicated)
                commonJSON = {'path':'/fileShares/' + registrationName, \
                            'type':'folder', \
                            'id':None, \
                            'clientPath':clientPath}
                
                if sharedFolderConfig:
                    # Shared
                    
                    commonJSON["info"] = {"dataStoreConnectionType":"shared", \
                                          "hostname":serverName, \
                                          "path":environmentData}
                    
                else:
                    # Replicated
                 
                    commonJSON["info"] = {"dataStoreConnectionType":"replicated", \
                                          "path":environmentData}
                
                itemJson = json.dumps(commonJSON)
                itemName = registrationName
                senditem(itemJson,itemName, username, password)
                print "\t\tDone."
                print
    
        # ---------------------------------------------------------------------
        # Register databases
        # (NOTE: Assumes database password is the same as that used to install
        # arcgis server)
        # ---------------------------------------------------------------------    
        if regDatabases:
            
            # Create database connection string template
            dbConnectionTemplateString = "SERVER=serverReplaceString;" + \
                "INSTANCE=sde:postgresql:serverReplaceString;DBCLIENT=postgresql;" + \
                "DB_CONNECTION_PROPERTIES=serverReplaceString;DATABASE=dbReplaceString;USER=sde;PASSWORD=" + \
                password + ";VERSION=sde.DEFAULT;AUTHENTICATION_MODE=DBMS"
    
            for db in dbsToRegister:
                
                isManaged = dbsToRegister[db][0]
                registrationName = dbsToRegister[db][1]
                
                # Do not register managed database if it is for
                # install purposes only
                if isManaged and forInstallPurposeOnly:
                    continueRegister = False
                else:
                    continueRegister = True
                
                if continueRegister:
                    
                    if forInstallPurposeOnly:
                        registrationName = registrationName + "_InstallOnly"
                    
                    managedStr = ""
                    if isManaged:
                        managedStr = "Managed"
                    else:
                        managedStr = "Non-managed"
                        if sharedDBConfig:
                            managedStr = managedStr + " - shared"
                        else:
                            managedStr = managedStr + " - replicated"
                    
                    print "\t\t-Registering " + db + " database with site as " + \
                        registrationName + " (" + managedStr + ")..."
                    
                    # Replace database place holder with name of database
                    connStr = dbConnectionTemplateString.replace("dbReplaceString", db)
                    clientConnStr = dbConnectionTemplateString.replace("dbReplaceString", db)
                    
                    # Replace server name place holder with name of server
                    connStr = connStr.replace("serverReplaceString", serverName)
                    clientConnStr = clientConnStr.replace("serverReplaceString", clientServerName)
                    
                    # Create dictionary with JSON items common to all database cases
                    # (i.e., managed, and non-managed shared and replicated)
                    commonJSON = {'path':'/enterpriseDatabases/' + registrationName, \
                                  'type':'egdb', \
                                  'id':None, \
                                  'clientPath':None}
                   
                    if isManaged:
                        # Managed
                        
                        commonJSON["info"] = {'connectionString': connStr, \
                                              "isManaged":True, \
                                              "dataStoreConnectionType":"serverOnly"}
                        
                    else:
                        
                        if sharedDBConfig:
                            # Shared
                            
                            commonJSON["info"] = {'connectionString': connStr, \
                                                  "isManaged":False, \
                                                  "dataStoreConnectionType":"shared"}
                            
                        else:
                            # Replicated
                         
                            commonJSON["info"] = {'clientConnectionString': clientConnStr, \
                                                'connectionString': connStr, \
                                                "isManaged":False, \
                                                "dataStoreConnectionType":"replicated"}
                    
                    itemJson = json.dumps(commonJSON)
                    itemName = db.upper() + " DB"
                    senditem(itemJson,itemName, username, password)
                    print "\t\tDone."
                    print

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
        return success
    
    
def senditem(itemJson,itemName, username, password):
    # Get a token

    token = getToken(username, password, serverName, serverPort)
    if token == "":
        print "Could not generate a token with the username and password provided."
        return
    
    # Construct URL to Register a folder http://server:port/arcgis/admin/data/registerItem
    dataItemURL = "/arcgis/admin/data/registerItem"
        
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}


    params = urllib.urlencode({'token': token, 'f': 'json', 'item':itemJson})
    #params = itemJson
    
    # Connect to URL and post parameters    
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", dataItemURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Error while attempting to register the data store."
        return
    else:
        data = response.read()
        httpConn.close()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(data):          
            print "Error returned by operation. " + data
        else:
            print "\t\t" + itemName + " Add successfully!"
        
def getToken(username, password, serverName, serverPort):
    # Token URL is typically http://server[:port]/arcgis/admin/generateToken
    tokenURL = "/arcgis/admin/generateToken"
    
    # URL-encode the token parameters
    params = urllib.urlencode({'username': username, 'password': password, 'client': 'requestip', 'f': 'json'})
    
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    
    # Connect to URL and post parameters
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", tokenURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Error while fetching tokens from admin URL. Please check the URL and try again."
        return
    else:
        data = response.read()
        httpConn.close()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(data):            
            return
        
        # Extract the toke from it
        token = json.loads(data)       
        return token['token']
    
#A function that checks that the input JSON object
#  is not an error object.    
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print "Error: JSON object returns an error. " + str(obj)
        return False
    else:
        return True

def unregisterDataStoreItem(username, password, itemPath):
    # Get a token

    token = getToken(username, password, serverName, serverPort)
    if token == "":
        print "Could not generate a token with the username and password provided."
        return
    
    # Construct URL to Register a folder http://server:port/arcgis/admin/data/registerItem
    dataItemURL = "/arcgis/admin/data/unregisterItem"
        
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    params = urllib.urlencode({'token': token, 'f': 'json', 'itemPath':itemPath})
    
    # Connect to URL and post parameters    
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", dataItemURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Error while attempting to unregister the data store '" + \
            itemPath + "'."
        return
    else:
        data = response.read()
        httpConn.close()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(data):          
            print "Error returned by operation. " + data
        else:
            print "\t\t" + itemPath + " unregistered successfully!"
            print "\t\tDone."
    
# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
