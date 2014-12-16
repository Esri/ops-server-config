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
#Name:          ConfigureFiles.py
#
#Purpose:       Functions for installing JavaScript API and editing
#               various portal and JavaScript API configuration files.
#
#Comments:      No longer used. Used in earlier builds of ArcGIS Portal which did
#               not install the JavaScript API.
#
#==============================================================================
## Configure Server for Standalone setup with javascript API assumes default doc type was set in IIS during server install batch
import OpsServerConfig
import zipfile
import os, sys, traceback, fnmatch, fileinput
import httplib, urllib, json
from Utilities import makePath
from Utilities import editFiles
from walkingDirTrees import listFiles
from Utilities import findFolderPath

import shutil

fqdn = OpsServerConfig.serverFullyQualifiedDomainName


extractJSZip = True
moveJS = True
editJSFiles = True

def installJS(jsAPIZipFilePath, jsAPIInstallRootPath, jsAPIVersion):
    success = True
    
    try:
         
        extractLocation = makePath("C", ["OpsServerInstallTemp"])
        #webRoot = makePath("C", ["inetpub", "wwwroot"])
        # for portal only install webRoot would be C:\portal\portal\webapps\docroot
        
        # -----------------------------------------------------------------------
        # Install Javascript API
        # -----------------------------------------------------------------------
        if extractJSZip:
            print ""
            print "\t--Extracting JavaScript API from " + jsAPIZipFilePath
            print "\t\tto " + extractLocation + \
                    " (this will take a few minutes)..."
            
            jsZipFile = zipfile.ZipFile(jsAPIZipFilePath)
            jsZipFile.extractall(extractLocation)
            
            print "\tDone."
        
        # -----------------------------------------------------------------------
        # Move Javascript API directory from temporary extraction location to
        #   web server root directory
        # -----------------------------------------------------------------------
        if moveJS:
            verNumInFileName = jsAPIVersion.replace(".", "")

            # 2013/02/19.
            # Since 3.3 version of JavaScript API does not have "arcgis_js_api" folder,
            # I'm modifying code so that path to source JS version folder is not
            # assumed to be under "arcgis_js_api/library" folder; will dynamically
            # determine folder by searching for "jsAPIVersion" folder.
            
            #sourceJSDir = os.path.join(extractLocation,
            #    *["arcgis_js_v" + verNumInFileName + "_api", "arcgis_js_api", "library", jsAPIVersion])
            
            searchRootDir = os.path.join(extractLocation, *["arcgis_js_v" + verNumInFileName + "_api"])
            print "\n\tSearching extract folder '" + searchRootDir + "' for " + "'" + jsAPIVersion + "' folder..."
            sourceJSDir = findFolderPath(searchRootDir, jsAPIVersion)
            
            destinationJSDir = os.path.join(jsAPIInstallRootPath, "arcgis_js_api", "library", jsAPIVersion)
            
            print "\n\t--Moving JavaScript API directory " + sourceJSDir + " to "  + \
                    destinationJSDir + "..."
            
            # CR: 236276 - Modify ConfigureJavaScriptAPI.py to delete JavaScript
            # API folder if it already exists in destination.
            print "\t\tChecking if folder " + destinationJSDir + " already exists..."
            if os.path.exists(destinationJSDir):
                print "\t\t*Folder already exists. Deleting..."
                shutil.rmtree(destinationJSDir)
                print "\t\tDone."
            print "\t\tMoving folder..."
            #end CR
            os.path.dirname
            if not os.path.exists(os.path.dirname(destinationJSDir)):
                os.makedirs(os.path.dirname(destinationJSDir))
            os.rename (sourceJSDir,destinationJSDir)

            print "\t\tDone."
    
        # -----------------------------------------------------------------------
        # Edit JavaScript API files (replace with current server URL)
        # -----------------------------------------------------------------------    
        if editJSFiles:
            print
            print "\t--Edit JavaScript API files..."
            print
            
            rootPath = os.path.join(jsAPIInstallRootPath, *["arcgis_js_api", "library", jsAPIVersion])
            
            editJavaScriptAPIFiles(rootPath, jsAPIVersion)
            

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
            

def findInFile(filePath, strToFind):
    foundInLine = None
    if os.path.exists(filePath):
        f = open(filePath, "r")
        for line in f:
            # remove leading/trailing spaces
            line = line.strip()
            if line.find(strToFind) > -1:
                foundInLine = line
                ##print "\tfoundInLine: " + foundInLine
                break
    else:
        print "\tError: File " + filePath + " does not exist."
    
    return foundInLine


def editJavaScriptAPIFiles(rootPathToSearch, jsAPIVersion):
    # Edit all files under "rootPathToSearch" path which have
    # pattern "[HOSTNAME_AND_PATH_TO_JSAPI]" and replace with
    # appropriate URL of server.
    
    searchString = "[HOSTNAME_AND_PATH_TO_JSAPI]"
    replaceStringPrefix = fqdn + "/arcgis_js_api/library/" + jsAPIVersion
    
    foundList = []
    
    # Get list of all files under root path
    print
    print "\t\tSearching root folder '" + rootPathToSearch + "' for files to edit..."
    print
    
    fileList = listFiles(rootPathToSearch)
    
    for filePath in fileList:
        found = findInFile(filePath, searchString)
        if found is not None:
            foundList.append(filePath)
    
    if len(foundList) == 0:
        print
        print "\t\t*** Error: there are no JavaScript API files to edit."
        print
    else:
        # Replace search string with appropriate URL
        for filePath in foundList:
            if filePath.find(os.sep + "jsapicompact" + os.sep) > 0:
                replaceString = replaceStringPrefix + "/jsapicompact/"
            else:
                replaceString = replaceStringPrefix + "/jsapi/"
                
            editFiles([filePath], searchString, replaceString)
        
        print "\t\tDone."


def updatePortalOptions(portalWebAppRootPath, agsFullyQualifiedDomainName):
    # portalWebAppRootPath = web app root path, i.e., 'C:\portal\portal\webapps'

    success = True
    
    agsFQDN = agsFullyQualifiedDomainName.lower()
    
    agsPort = OpsServerConfig.serverPort
    
    jsAPIVersion = "3.3"
    
    try:
        print
        print "--Edit Portal files..."
        print
        
        filelist = []
        #List of Files
        filelist.append(os.path.join(portalWebAppRootPath, *["arcgis#home", "js", "esri", "arcgisonline", "config.js"]))
        filelist.append(os.path.join(portalWebAppRootPath, *["arcgis#explorer", "ClientBin", "config.json"]))
        filelist.append(os.path.join(portalWebAppRootPath, *["docroot", "arcgismobile.txt"]))
        filelist.append(os.path.join(portalWebAppRootPath, *["docroot", "arcgismobile_ssl.txt"]))
        filelist.append(os.path.join(portalWebAppRootPath, *["arcgis#home", "webmap", "embedViewer.html"]))
        filelist.append(os.path.join(portalWebAppRootPath, *["arcgis#home", "webmap", "presentation.html"]))
        
        #
        # DO NOT EDIT ANY OF THE WEB APP TEMPLATE FILES AT THIS TIME. 10/15/2012.
        #
        ##Add All Web App templates to "filelist"
        ##for path, dirs, files in os.walk(os.path.abspath(r'C:\portal\portal\webapps\home\webmap\templates')):
        #for path, dirs, files in os.walk(os.path.abspath(os.path.join(portalWebAppRootPath, *["home", "webmap", "templates"]))):
        #    for filename in fnmatch.filter(files, "index.html"):
        #        filelist.append(os.path.join(path, filename))
    
    
        for f in filelist:
            print "\t-Editing file: " + f + "..."
            for line in fileinput.FileInput(f,inplace=1):
                
                # GeocodeServer
                line = line.replace("tasks.arcgis.com/ArcGIS/rest/services/WorldLocator/GeocodeServer",
                    "{}:{}/arcgis/rest/services/Locators/Geonames/GeocodeServer".format(agsFQDN, agsPort))

                line = line.replace("tasksdev.arcgis.com/ArcGIS/rest/services/WorldLocator/geocodeserver",
                    "{}:{}/arcgis/rest/services/Locators/Geonames/GeocodeServer".format(agsFQDN, agsPort))
                
                # GeometryServer
                line = line.replace("utility.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer",
                    "{}:{}/arcgis/rest/services/Utilities/Geometry/GeometryServer".format(agsFQDN, agsPort))

                line = line.replace("tasks.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer",
                    "{}:{}/arcgis/rest/services/Utilities/Geometry/GeometryServer".format(agsFQDN, agsPort))
                
                # Java Script API
                line = line.replace("serverapi.arcgisonline.com/jsapi/arcgis/?v={}".format(jsAPIVersion),
                    "{}/arcgis_js_api/library/{}/jsapi".format(agsFQDN, jsAPIVersion))

                line = line.replace("serverapi.arcgisonline.com/jsapi/arcgis/?v={}".format(jsAPIVersion + "compact"),
                    "{}/arcgis_js_api/library/{}/jsapicompact".format(agsFQDN, jsAPIVersion))
                
                line = line.replace("serverapi.arcgisonline.com/jsapi/arcgis/{}".format(jsAPIVersion),
                    "{}/arcgis_js_api/library/{}/jsapi".format(agsFQDN, jsAPIVersion))
                
                print line
        print "\tDone."
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


def editRestConfigFile(restConfigPropFilePath):
    # restConfigPropFilePath - file path to rest-config.properties file
    #   for example: C:\Program Files\ArcGIS\Server\framework\runtime\tomcat\
    #       webapps\arcgis#rest\WEB-INF\classes\resources
    #
    success = True
    
    
    try:
        
        restf = []
        
        ## Create ".bak" file of original file in case this script
        ## is run a second time then file we edit will have the "findString"
        #restConfigPropFilePathBackUp = restConfigPropFilePath + ".bak"
        #print "\tCreate back-up of rest-config.properties file if it does not exist..."
        #if not os.path.exists(restConfigPropFilePathBackUp):
        #    print "\tCreating back-up file..."
        #    #shutil.copy2(restConfigPropFilePath, restConfigPropFilePathBackUp)
        #    shutil.copyfile(restConfigPropFilePath, restConfigPropFilePathBackUp)
        #    print "\tDone."
        #
        ## Double-check that back up file was created above.
        #if os.path.exists(restConfigPropFilePathBackUp):
        #    
        #    # If Back up file exists, delete non-back up file so we can
        #    # copy the backup file as new non-back up file.
        #    print "\tDelete existing rest-config.properties file if it does exist..."
        #    if os.path.exists(restConfigPropFilePath):
        #        print "\t*File exists; deleting..."
        #        os.remove(restConfigPropFilePath)
        #        print "\tDone."
        #    
        #    print "\tCopy rest-config.properties.bak file to rest-config.properties file..."
        #    #shutil.copy2(restConfigPropFilePathBackUp, restConfigPropFilePath)
        #    shutil.copyfile(restConfigPropFilePathBackUp, restConfigPropFilePath)
        #    print "\tDone."
            
        
        restf.append(restConfigPropFilePath)
        
        # Commented out 6/17/2013; going to change URLs to point to JS API installed by portal install
        ### Determine version of Java Script specified in rest properties file
        ##findString = findInFile(restConfigPropFilePath, "jsapi.arcgis=")
        ##jsAPIVersion = findString.split("?v=")[1]
        ##
        ###Edit 1
        ##replaceString = "jsapi.arcgis=http://" + \
        ##    fqdn + "/arcgis_js_api/library/" + jsAPIVersion + "/jsapi/?v=" + jsAPIVersion
        ##editFiles(restf, findString, replaceString)
        ##
        ###Edit 2
        ##findString = findInFile(restConfigPropFilePath, "jsapi.arcgis.css=")
        ##replaceString = "jsapi.arcgis.css=http://" + \
        ##            fqdn + "/arcgis_js_api/library/" + jsAPIVersion + \
        ##            "/jsapi/js/dojo/dijit/themes/tundra/tundra.css"
        ##editFiles(restf, findString, replaceString)
        
        #TODO: this code assumes that you are requiring SSL (https)
        protocol_fqdn = "https://" + fqdn
        
        #Edit 1
        find = "jsapi.arcgis="
        findString = findInFile(restConfigPropFilePath, find)
        replaceString = find + protocol_fqdn + "/arcgis/jsapi/jsapi/"
        editFiles(restf, findString, replaceString)
        
        #Edit 2
        find = "jsapi.arcgis.css="
        findString = findInFile(restConfigPropFilePath, find)
        replaceString = find + protocol_fqdn + "/arcgis/home/js/dojo/dijit/themes/tundra/tundra.css"
        editFiles(restf, findString, replaceString)       
        
        #Edit 3
        find = "jsapi.arcgis.css2="
        findString = findInFile(restConfigPropFilePath, find)
        replaceString = find + protocol_fqdn + "/arcgis/home/js/esri/css/esri.css"
        editFiles(restf, findString, replaceString)        

        #Edit 4
        find = "arcgis.com.map="
        findString = findInFile(restConfigPropFilePath, find)
        replaceString = find + protocol_fqdn + "/arcgis/home/webmap/viewer.html"
        editFiles(restf, findString, replaceString)         

        #Edit 5
        find = "arcgis.com.map.text="
        findString = findInFile(restConfigPropFilePath, find)
        replaceString = find + "Portal Map"
        editFiles(restf, findString, replaceString)
        
        print "\tDone."

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

# Script start
if __name__ == "__main__":
    sys.exit(installjs(sys.argv[1:]))
