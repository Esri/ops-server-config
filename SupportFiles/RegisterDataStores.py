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
from DataStore import create_shared_folder_item
from DataStore import create_replicated_folder_item
from DataStore import register
from DataStore import create_managed_entdb_item
from DataStore import create_shared_entdb_item
from DataStore import create_replicated_entdb_item
from DataStore import create_postgresql_db_connection_str

serverName = OpsServerConfig.serverName
serverPort = OpsServerConfig.serverPort
    
regFolders = True
regDatabases = True

def registerDataStores(sharedDataStoreConfig, forInstallPurposeOnly, username, password, dataDrive):
    
    successRegister = True
    
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
        
        print "\n\t-Register Data Stores with Site...\n"
        
        # ---------------------------------------------------------------------
        # Register Folders by just using paths
        # ---------------------------------------------------------------------
        if regFolders:
            
            if forInstallPurposeOnly:
                clientFolderPaths = installOnlyClientFolders
            else:
                clientFolderPaths = {clientFolderDSName: clientFolderPath}
            
            for registrationName, clientFolderPath in clientFolderPaths.items():
                
		# Create folder data store item
                if sharedFolderConfig:
                    sharedStr = "shared"
		    dsPath, dsItem = create_shared_folder_item(registrationName, environmentData, serverName)
		    
                else:
                    sharedStr = "replicated"
                    dsPath, dsItem = create_replicated_folder_item(registrationName, clientFolderPath, environmentData)

		# Register the data store item
		print "\t\t-Registering folder " + environmentData + " with site as " + registrationName + " (" + sharedStr + ")..."
		success, response = register(serverName, serverPort, username, password, dsItem, useSSL=False)
		if success:
		    print "\t\tDone.\n"
		else:
		    successRegister = False
		    print "ERROR:" + str(response)

        ## ---------------------------------------------------------------------
        ## Register databases
        ## (NOTE: Assumes database password is the same as that used to install
        ## arcgis server)
        ## ---------------------------------------------------------------------
	if regDatabases:
        
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
                    
		    success, server_db_conn = create_postgresql_db_connection_str(
                                        serverName, serverPort, username, password,
                                        serverName, db, 'sde', password, useSSL=False, token=None, encrypt_dbpassword=False)
		    if not success:
			successRegister = False
			print "ERROR: error encountered while creating server database connection string -"
			print str(server_db_conn)
		    
                    if forInstallPurposeOnly:
                        registrationName = registrationName + "_InstallOnly"
                    
                    managedStr = ""
                    if isManaged:
                        managedStr = "Managed"
			dsPath, dsItem = create_managed_entdb_item(registrationName, server_db_conn)
			
                    else:
                        managedStr = "Non-managed"
                        if sharedDBConfig:
                            managedStr = managedStr + " - shared"
			    dsPath, dsItem = create_shared_entdb_item(registrationName, server_db_conn)
			    
                        else:
                            managedStr = managedStr + " - replicated"
			    
			    success, publisher_db_conn = create_postgresql_db_connection_str(
                                        serverName, serverPort, username, password,
                                        clientServerName, db, 'sde', password, useSSL=False, token=None, encrypt_dbpassword=False)
			    if not success:
				successRegister = False
				print "ERROR: error encountered while creating publisher database connection string -"
				print str(publisher_db_conn)
			
			    dsPath, dsItem = create_replicated_entdb_item(registrationName, publisher_db_conn, server_db_conn)
			    
                    print "\t\t-Registering " + db + " database with site as " + registrationName + " (" + managedStr + ")..."
		    success, response = register(serverName, serverPort, username, password, dsItem, useSSL=False)
		    if success:
			print "\t\tDone.\n"
		    else:
			successRegister = False
			print "ERROR:" + str(response)
		    

    except:
        successRegister = False
        
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
        return successRegister
    
# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
