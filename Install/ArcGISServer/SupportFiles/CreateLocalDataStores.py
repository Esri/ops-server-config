# coding: utf-8
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
#Name:          CreateLocalDataStores.py
#
#Purpose:       Creates folder and ArcSDE geodatabase datastores on server:
#		1) Creates root OpsServer folder and associated environment folder.
#		2) Creates database connection folder.
#		3) Creates ArcSDE geodatabases.
#		4) Creates ArcSDE geodatabase connection files.
#		5) Changes ownership of OpsServer folder and database
#		connection folder to account running the ArcGIS Server service.
#
#Prerequisites: ArcGIS Server and PostgreSQL must be installed.
#
#==============================================================================
import os, sys, traceback

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilesPath = os.path.join(
    os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0])))), "SupportFiles")

sys.path.append(supportFilesPath)

import OpsServerConfig
import arcpy
from Utilities import makePath
from Utilities import changeOwnership
from Utilities import findFilePath
from Utilities import findInFile

servername = OpsServerConfig.serverName
dbsToCreate = OpsServerConfig.databasesToCreate
rootPostgreSQLPath = OpsServerConfig.getPostgreSQLRootPath()

createLocalEnvFolders = True
createEnterpriseGDBs = True
updatePostgreSQLConnectionFile = True
createSDEConnectionFiles = True

def createDataStores(agsServerAccount, password, dataDrive):
    success = True
    
    try:
	
	opsServer = OpsServerConfig.getOpsServerRootPath(dataDrive)
	environmentData = OpsServerConfig.getEnvDataRootPath(dataDrive)
	dbConnFileRootPath = OpsServerConfig.getDBConnFileRootPath(dataDrive)
	
        print
        print "--Create Local Data Stores..."
	
        # Create local variables to use for both creating enterprise
        # geodatabases and creating connection files.
        dbPlatform = "POSTGRESQL"
        accountAuthentication = "DATABASE_AUTH"
        dbAdmin = "postgres"    #For PostgreSQL this is the postgres superuser
        gdbAdminName = "sde"    #For PostreSQL this must be 'sde'
	
	# 2/26/2013: Modified to dynamically search for keycodes file instead of
	# hardcoding to specific version of the software.
        #pathList = ["Program Files", "ESRI", "License10.1", "sysgen", "keycodes"]
	#authorizationFile = makePath("C", pathList)
	pathList = ["Program Files", "ESRI"]
	authorizationFile = findFilePath(makePath("C", pathList), "keycodes")
        

        # Create list of database names to create connection file.
	dbsToConnect = []
	for db in dbsToCreate:
	    dbsToConnect.append(db)
		
        # ---------------------------------------------------------------------
        # Create local environment data folders
        # ---------------------------------------------------------------------
        
        if createLocalEnvFolders:
            
            print "\n\t-Creating local environment data folders..."
            
            foldersToCreate = []
            foldersToCreate.append(environmentData)
	    foldersToCreate.append(dbConnFileRootPath)
		
            if not os.path.exists(environmentData):
                for folder in foldersToCreate:
                    print "\t\tCreating folder: " + folder
                    os.makedirs(folder)
                print "\t\tDone."
                print
                
		changeOwnership(opsServer, agsServerAccount)

        # ---------------------------------------------------------------------
        # Create local enterprise databases
        # ---------------------------------------------------------------------
        
        if createEnterpriseGDBs:
            
            print "\n\t-Creating local enterprise geodatabases" + \
                    " (this will take a few minutes)...\n"
	    
            for db in dbsToCreate:
                print "\t\tCreating geodatabase '" + db + "'..."
                arcpy.CreateEnterpriseGeodatabase_management(dbPlatform,
                                                            "localhost",
                                                            db,
                                                            accountAuthentication,
                                                            dbAdmin,
                                                            password,
                                                            "",
                                                            gdbAdminName,
                                                            password,
                                                            "",
                                                            authorizationFile)
		print "\t\tDone.\n"

        # ---------------------------------------------------------------------
        # Update PostgreSQL connection file to allow remote connections
        #   to environment databases
        # ---------------------------------------------------------------------
        
        if updatePostgreSQLConnectionFile:
	    connectionFilePath = findFilePath(rootPostgreSQLPath, "pg_hba.conf")
            
            print "\n\t-Updating PostgreSQL connection file to allow remote" + \
                    " connections to databases..."
            print "\t\tFile: " + connectionFilePath 
            	    
	    # Create list of PostgreSQL connection entries
	    postgreSQLConnEntries = []
	    postgreSQLConnEntries.append("host all all 0.0.0.0/0 md5")	#IPv4
	    postgreSQLConnEntries.append("host all all ::/0 md5")  	#IPv6
		
	    # Determine if connection entry already exists in file
	    for postgreSQLConnEntry in postgreSQLConnEntries:
		if findInFile(connectionFilePath, postgreSQLConnEntry):
		    #Entry already exists in file so remove entry from list
		    postgreSQLConnEntries.remove(postgreSQLConnEntry)	    

	    # Add connection entries
	    if len(postgreSQLConnEntries) > 0:
                hbaFile = open(connectionFilePath, 'a')
                for postgreSQLConnEntry in postgreSQLConnEntries:
                    hbaFile.write("{}\n".format(postgreSQLConnEntry))
                hbaFile.close()

                # Reload config file
                print "\n\t-Reloading connection file..."
		exeFile = findFilePath(rootPostgreSQLPath, "pg_ctl.exe")
		confFolder = os.path.dirname(connectionFilePath)
		exeCommand = "”" + exeFile + "” -D “" + confFolder + "” reload"
		os.popen(exeCommand)		
		
            print "\t\tDone."

        # ---------------------------------------------------------------------
        # Create SDE connection files to environment geodatabases
        # ---------------------------------------------------------------------
        
        if createSDEConnectionFiles:
            
            print "\n\t-Creating SDE connection files..."
            
            for db in dbsToCreate:
		outFile = dbsToCreate[db][1] + ".sde"
		
		# Set output folder location
		outFolder = dbConnFileRootPath
		sdeFilePath = os.path.join(outFolder, outFile)
		
		# If SDE connection file already exists, delete it.
		if os.path.exists(sdeFilePath):
		    print "\t\t* Deleting existing file " + sdeFilePath
		    os.remove(sdeFilePath)
		    print "\t\tRe-creating connection file " + sdeFilePath
		else:
		    print "\t\tCreating connection file " + sdeFilePath
		
		arcpy.CreateDatabaseConnection_management(outFolder,
							  outFile,
							  dbPlatform,
							  servername,
							  accountAuthentication,
							  gdbAdminName,
							  password,
							  "SAVE_USERNAME",
							  db.lower(),
							  "#",
							  "TRANSACTIONAL",
							  "sde.DEFAULT",
							  "#")
		    
		print "\t\tDone.\n"
		# Change ownership of sde file
		changeOwnership(sdeFilePath, agsServerAccount)

    except:
        success = False
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
     
        # Concatenate information together concerning the error into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages() + "\n"
        
        # Print Python error messages for use in Python / Python Window
        print
        print "***** ERROR ENCOUNTERED *****"
        print pymsg + "\n"
        print msgs
        
    finally:
        # Return success flag
        return success
