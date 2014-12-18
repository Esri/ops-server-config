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
#Name:          PreConfigurationChecks.py
#
#Purpose:       Checks if ArcGIS Server site and ArcSDE geodatabases
#               already exist.
#
#==============================================================================
import sys, os, traceback

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilesPath = os.path.join(
    os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0])))), "SupportFiles")

sys.path.append(supportFilesPath)

import httplib, urllib, json
import arcpy
import OpsServerConfig
import subprocess
from Utilities import makePath
from Utilities import findFilePath
from Utilities import editFiles

serverName = OpsServerConfig.serverName
serverPort = OpsServerConfig.serverPort
dbsForOpsServer = OpsServerConfig.databasesToCreate
rootPostgreSQLPath = OpsServerConfig.getPostgreSQLRootPath()

siteExistsCheck = True
dbExistsCheck = True

def PreConfigChecks(agsSiteAdminUserName, password):
    try:
    
        success = True
        msgPrefix = "Failed: "
        print
        print "--Running pre-configuration checks..."
        print
        
        # ---------------------------------------------------------------------
        # Check if site already exists
        # ---------------------------------------------------------------------
        if siteExistsCheck:
            print "\t-Checking if ArcGIS Server site already exists on server '" + serverName + "'"
            token = getToken(agsSiteAdminUserName, password, serverName, serverPort)
	    print
            if token is None:
                # Site does not exist; so configuration can continue.
                print "\tPassed: ArcGIS Server site does _not_ exist.\n"
                success = True
            else:
                # Site EXISTS; so we don't want configuration of server to continue.
                print "\t**Failed: ArcGIS Server site already exists.\n"
                success = False
	    print
	    
        # ---------------------------------------------------------------------
        # Check if databases already exist
        # ---------------------------------------------------------------------           
        
        if dbExistsCheck:
            print "\t-Checking if databases already exist..."
            print
            dbList = getPostgreSQLDatabases(password)
            
            #Convert list to comma-separated string
            dbListAsStr = str(dbList).strip('[]')
            dbListAsStr = dbListAsStr.replace("'", "").lower()
            
            print
            for db in dbsForOpsServer:
                if dbListAsStr.find(db.lower()) > -1:
                    success = False
                    print "\t\t**Failed: database '" + db + "' already exists."
                else:
                    print "\t\tPassed: database '" + db + "' does _not_ exist."
            
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
    

def getPostgreSQLDatabases(password):
    try:
        dbList = []
        f = ""
        confFileExists = False
 
        # ---------------------------------------------------------------------
        # Create path variables
        # ---------------------------------------------------------------------
        confFileFolder = os.path.join(os.environ['APPDATA'], "postgresql")
        confFilePath = os.path.join(confFileFolder, "pgpass.conf")
        
	#Location where calling script is located
        scriptFileFolder = os.path.dirname(sys.argv[0])
	
	#supportFilesPath = os.path.join(scriptFileFolder, "SupportFiles")
        scriptFilePath =  os.path.join(scriptFileFolder, "RunPostgreSQLStatement.bat")
        outFile = os.path.join(scriptFileFolder, "DatabaseOutput.txt")

        # Delete file containing database names (outFile) if it already exists
        if os.path.exists(outFile):
            os.remove(outFile)
            
        # ---------------------------------------------------------------------
        # Create postgreSQL password configuration file
        # NOTE: must be located in %APPDATA%\postgresql folder and must
        # be called pgpass.conf
        # ---------------------------------------------------------------------
        # The script file runs psql.exe which will prompt for a password
        # unless the pgpass.config file contains the connection information.
        # The file should have the following format:
        # hostname:port:database:username:password
        confString = "localhost:5432:postgres:postgres:" + password
        
        # Create postgres folder if it does not exist.
        if not os.path.exists(confFileFolder):
            os.makedirs(confFileFolder)
        
        # Check if config file already exists
        if os.path.exists(confFilePath):
            confFileExists = True
            os.rename(confFilePath, confFilePath + ".bak")
        
        # File doesn't exist so create it using the w mode
        conf_f = open(confFilePath, "w")
        
        # Write to config file
        conf_f.write(confString + "\n")
        conf_f.close()
        
        # ---------------------------------------------------------------------
        # Create batch file with psql command
        # ---------------------------------------------------------------------
        print "\t\t-Creating batch file: " + scriptFilePath + "..."
	psqlExePath = findFilePath(rootPostgreSQLPath, "psql.exe")
    
        strToWrite = '"' + psqlExePath + '" -U postgres -p 5432 -d postgres ' + \
                '-h localhost -f ' + scriptFileFolder + os.sep + \
		'ListPostgresDatabases.sql > ' + outFile
	
        # Create file/overwrite existing
        batFile_f = open(scriptFilePath, "w")
        batFile_f.write(strToWrite + "\n")
        batFile_f.close()
        
        # ---------------------------------------------------------------------
        # Run batch file that connects to postgreSQL postgres database
        # and queries pg_database table.
        # ---------------------------------------------------------------------
        print "\t\t-Executing batch file (" + scriptFilePath + ")"
        print "\t\tto determine existing PostgreSQL databases..."
            
        #Run batch file that executes sql statement
        subprocess.call(scriptFilePath)
        
        # Read output file and add database names to list
        if os.path.exists(outFile):
            f = open(outFile, "r")
            for line in f:
                # remove leading/trailing spaces
                line = line.strip()
                if line == "datname" or line.find("--") <> -1 or \
                    line.find(" rows") <> -1:
                    # skip line
                    continue
                if len(line) > 0:
                    #added this check because it extra blank line is
                    # in file
                    dbList.append(line)
            
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
        if f:
            f.close()
        if conf_f:
            conf_f.close()
            
        # Delete the config file we created
        os.remove(confFilePath)
        
        # Rename backup config if existed
        if confFileExists:
            os.rename(confFilePath + ".bak", confFilePath)

        return dbList


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
        return None
    else:
        data = response.read()
        httpConn.close()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(data):            
            return None
        
        # Extract the toke from it
        token = json.loads(data)       
        return token['token']


#A function that checks that the input JSON object
#  is not an error object.    
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        #print "Error: JSON object returns an error. " + str(obj)
        return False
    else:
        return True
    