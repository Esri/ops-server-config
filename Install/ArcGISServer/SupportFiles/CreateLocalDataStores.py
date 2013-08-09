# coding: utf-8
#!/usr/bin/env python
#==============================================================================
#Name:          CreateLocalDataStores.py
#Purpose:       Creates folder and ArcSDE geodatabase datastores on server:
#		1) Creates root OpsServer folder and associated environment folder.
#		2) Creates database connection folder.
#		3) Creates ArcSDE geodatabases.
#		4) Creates ArcSDE geodatabase connection files.
#		5) Changes ownership of OpsServer folder and database
#		connection folder to account running the ArcGIS Server service.
#
#Prerequisites: None
#
#History:       2012:   	Initial code.
#		2013/02/26:	Modified to dynamically search for keycodes file
#					for licensing ent. geodatabases.
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

servername = OpsServerConfig.serverName
dbsToCreate = OpsServerConfig.databasesToCreate
rootPostgreSQLPath = OpsServerConfig.postgreSQLRootPath

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
        # For PostgreSQL, the database names should be lowercase
        # NOTE: connections will only be created for databases defined with
	# 	Managed flag is False since users should not be connecting
	#	to the managed database.
	# Modified 11/26/2012: modify so that connections are made to all
	# geodatabases; not just the un-managed geodatabases.
#	dbsToConnect = []
#	for db in dbsToCreate:
#            if not dbsToCreate[db][0]:
#		dbsToConnect.append(db)
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
	    # Commented out 3/21/2013: this warning message does not appear
	    # when creating the ent. gdb on PostgreSQL 9.2.2.
	    #print "\t***********************************************************"
	    #print "\tNOTE: You can ignore the following warning message, as the"
	    #print "\tgeodatabase is created correctly:"
	    #print '\t\tWARNING: invalid value for parameter "search_path": ""$user", public, sde"'
	    #print '\t\tDETAIL: schema "sde" does not exist'
	    #print "\t***********************************************************\n"
	    
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
                    " connections to environment databases..."
            print "\t\tFile: " + connectionFilePath 
            
            # Create a copy of the database list since the next operation
            # may remove items from the list
            dbsToConnectPostreSQLFile = list(dbsToConnect)
            
            # Determine if database entry already exists in file
            hbaFile = open(connectionFilePath, 'r')
            for fileLine in hbaFile:
                fileLine = fileLine.strip() #Remove trailing newline character
                for dbConnect in dbsToConnectPostreSQLFile:
                    connectionString = "host  " + dbConnect.lower() + "  all  0.0.0.0/0  md5"
                    if connectionString == fileLine:
                        #Entry already exists in file so remove entry from list
                        dbsToConnectPostreSQLFile.remove(dbConnect)
                        print "\t\tConnection info for database '" + dbConnect + "' already exists."
            hbaFile.close()
            
            if len(dbsToConnectPostreSQLFile) == 0:
                print "\t\tAll required connection entries already exist in file."
            else:
                #Append database entries
                hbaFile = open(connectionFilePath, 'a')
                for dbConnect in dbsToConnectPostreSQLFile:
                    print "\t\tAppending connection info for database '" + dbConnect + "'..."
                    hbaFile.write("host  " + dbConnect.lower() + "  all  0.0.0.0/0  md5" + '\n')
                hbaFile.close()
                
                # Reload config file
                print "\n\t-Reloading connection file..."
#                os.popen("”C:\Program files\PostgreSQL\9.0\bin\pg_ctl.exe” -D “C:\Program Files\PostgreSQL\9.0\data” reload")
		
		exeFile = findFilePath(rootPostgreSQLPath, "pg_ctl.exe")
		
		# Create path to "data" folder
		confFolder = os.path.dirname(connectionFilePath)
		
		# "Build" command line string and execute.
		exeCommand = "”" + exeFile + "” -D “" + confFolder + "” reload"
		os.popen(exeCommand)
	    
            print "\t\tDone."

        # ---------------------------------------------------------------------
        # Create SDE connection files to environment geodatabases
        # ---------------------------------------------------------------------
        
        if createSDEConnectionFiles:
            
            print "\n\t-Creating SDE connection files..."
            
            for db in dbsToCreate:
		# Create sde connection file if Managed flag is False.
		# Modified 11/26/2012: modify so that connections are made to all
		# geodatabases; not just the un-managed geodatabases.
		#if not dbsToCreate[db][0]:
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
