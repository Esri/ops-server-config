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
#Name:          AGSRestFunctions.py
#           
#Purpose:       Functions for administering and obtaining information about
#               the ArcGIS Server site or specific services
#
#==============================================================================
'''
---------------------------------
NOTE: downloaded from
http://blogs.esri.com/esri/arcgis/2012/07/05/downloadable-tools-for-arcgis-server-administration/
on July 6, 2012.

NOTE: commented out "upload" function since this depends on 3rd party module

History:
07/25/2013
    - Created this module based on AllFunctions.py module.
    - Modified all functions to use 'https' instead of 'http' to support our 10.2 OpsServer
        which is configured to 'HTTPS Only'.
    - Added new functions as necessary.
---------------------------------

This script provides functions used to administer ArcGIS Server 10.1.
Most functions below make calls to the REST Admin, using specific URLS to perform an action.
The functions below DO NOT make use of arcpy, as such they can be run on any machine with Python 2.7.x installed
This list is not intended to be a complete list of functions to work with ArcGIS Server. It does provide the most common
actions and templates to extend or a place to start your own.
See the REST Admin API for comprehensive commands and explanation.
Examples on how the functions are called can be found at the bottom of this file.

Date : June 15, 2012 

Author:        Kevin - khibma@esri.com
Contributors:  Jason - jscheirer@esri.com
               Sterling - squinn@esri.com
               Shreyas - sshinde@esri.com
               
These scripts provided as samples and are not supported through Esri Technical Support.
Please direct questions to either the Python user forum : http://forums.arcgis.com/forums/117-Python
or the ArcGIS Server General : http://forums.arcgis.com/forums/8-ArcGIS-Server-General

See the ArcGIS Server help for interactive scripts and further examples on using the REST Admin API through Python:
http://resources.arcgis.com/en/help/main/10.1/#/Scripting_ArcGIS_Server_administration/0154000005p3000000/
'''

# Required imports
import urllib
import urllib2
import json
import time

# Version of Python installed with 10.4 now validates SSL
# certificate. The try/except/else block was added to ignore
# certificate validation errors.
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

def gentoken(server, port, adminUser, adminPass, useSSL=True, expiration=60):
    #Re-usable function to get a token required for Admin changes
    
    query_dict = {'username':   adminUser,
                  'password':   adminPass,
                  'expiration': str(expiration),
                  'client':     'requestip'}
    
    query_string = urllib.urlencode(query_dict)
    
    url = "{}{}{}/arcgis/admin/generateToken".format(getProtocol(useSSL), server, getPort(port))
    
    token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())

    if "token" not in token:
        print token['messages']
        exit()
    else:
        # Return the token to the function which called for it
        return token['token']

def gentoken2(server_url, user_name, user_pass, expiration=60):
    #Re-usable function to get a token required for Admin changes
    
    query_dict = {'username':   user_name,
                  'password':   user_pass,
                  'expiration': str(expiration),
                  'client':     'requestip'}
    
    query_string = urllib.urlencode(query_dict)
    
    url = "{}/admin/generateToken".format(server_url)
    
    token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())
        
    if "token" not in token:
        print token['messages']
        exit()
    else:
        # Return the token to the function which called for it
        return token['token']


def modifyLogs(server, port, adminUser, adminPass, clearLogs, logLevel, useSSL=True, token=None):
    ''' Function to clear logs and modify log settings.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    clearLogs = True|False
    logLevel = SEVERE|WARNING|FINE|VERBOSE|DEBUG
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get tand set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)
    
    # Clear existing logs
    if clearLogs:
        clearLogs = "{}{}{}/arcgis/admin/logs/clean?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)
        status = urllib2.urlopen(clearLogs, ' ').read()    
    
        if 'success' in status:
            print "Cleared log files"
    
    # Get the current logDir, maxErrorReportsCount and maxLogFileAge as we dont want to modify those
    currLogSettings_url = "{}{}{}/arcgis/admin/logs/settings?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), token)
    logSettingProps = json.loads(urllib2.urlopen(currLogSettings_url, ' ').read())['settings'] 
    
    # Place the current settings, along with new log setting back into the payload
    logLevel_dict = {      "logDir": logSettingProps['logDir'],
                           "logLevel": logLevel,
                           "maxErrorReportsCount": logSettingProps['maxErrorReportsCount'],
                           "maxLogFileAge": logSettingProps['maxLogFileAge']                       
                    }
   
    # Modify the logLevel
    log_encode = urllib.urlencode(logLevel_dict)     
    logLevel_url = "{}{}{}/arcgis/admin/logs/settings/edit?f=json&token={}".format(getProtocol(useSSL), server, getPort(port), token)
    logStatus = json.loads(urllib.urlopen(logLevel_url, log_encode).read())
    
    
    if logStatus['status'] == 'success':
        print "Succesfully changed log level to {}".format(logLevel)        
    else:
        print "Log level not changed"
        
    return
        
        
def createFolder(server, port, adminUser, adminPass, folderName, folderDescription, useSSL=True, token=None):
    ''' Function to create a folder
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    folderName = String with a folder name
    folderDescription = String with a description for the folder
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    # Dictionary of properties to create a folder
    folderProp_dict = { "folderName": folderName,
                        "description": folderDescription                                            
                      }
    
    folder_encode = urllib.urlencode(folderProp_dict)            
    create = "{}{}{}/arcgis/admin/services/createFolder?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)    
    status = urllib2.urlopen(create, folder_encode).read()

    
    if 'success' in status:
        print "Created folder: {}".format(folderName)
    else:
        print "Could not create folder"  
        print status
        
    return
        

def getFolders(server, port, useSSL=True):
    ''' Function to get all folders on a server  
    Note: Uses the Services Directory, not the REST Admin
    '''        
    
    foldersURL = "{}{}{}/arcgis/rest/services/?f=pjson".format(getProtocol(useSSL), server, getPort(port))    
    status = json.loads(urllib2.urlopen(foldersURL, '').read())
        
    folders = status["folders"]
    
    # Return a list of folders to the function which called for them
    return folders


def renameService(server, port, adminUser, adminPass, service, newName, useSSL=True, token=None):
    ''' Function to rename a service
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    service = String of existing service with type separated by a period <serviceName>.<serviceType>
    newName = String of new service name
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)      
    
    # Dictionary of properties used to rename a service
    renameService_dict = { "serviceName": service.split('.')[0],
                           "serviceType": service.split('.')[1],
                           "serviceNewName" : newName
                         }
    
    rename_encode = urllib.urlencode(renameService_dict)            
    rename = "{}{}{}/arcgis/admin/services/renameService?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)    
    status = urllib2.urlopen(rename, rename_encode ).read()
    
    
    if 'success' in status:
        print "Succesfully renamed service to : {}".format(newName)
    else:
        print "Could not rename service"
        print status
        
    return

def getProtocol(useSSL):
    ''' Return proper protocol '''
    
    if useSSL:
        return "https://"
    else:
        return "http://"

def getPort(port):
    ''' Return string representing port parameter '''
    
    portStr = ""
    if port:
        if str(port).strip() == "#":
            portStr = ""
        else:
            portStr = ":" + str(port)
    
    return portStr

def stopStartServices(server, port, adminUser, adminPass, stopStart, serviceList, useSSL=True, token=None):  
    ''' Function to stop, start or delete a service.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    stopStart = Stop|Start|Delete
    serviceList = List of services. A service must be in the <name>.<type> notation
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get and set the token
    if token is None:       
        token = gentoken(server, port, adminUser, adminPass, useSSL)
    
    # modify the services(s)    
    for service in serviceList:
        op_service_url = "{}{}{}/arcgis/admin/services/{}/{}?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), service, stopStart, token)
        status = urllib2.urlopen(op_service_url, ' ').read()
        
        if 'success' in status:
            print (str(service) + " === " + str(stopStart))
        else:            
            print status
    
    return
        
        
def registerSOE(server, port, adminUser, adminPass, itemID, useSSL=True, token=None):
    ''' Function to upload a file to the REST Admin
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    itemID = itemID of an uploaded SOE the server will register.    
    If a token exists, you can pass one in for use.      '''
    
    # Get and set the token
    if token is None:  
        token = gentoken(server,  port, "admin", "admin")     
    
    # Registration of an SOE only requires an itemID. The single item dictionary is encoded in place
    SOE_encode = urllib.urlencode({"id":itemID})   
    
    register = "{}{}{}/arcgis/admin/services/types/extensions/register?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)    
    status = urllib2.urlopen(register, SOE_encode).read()
    
    if 'success' in status:
        print "Succesfully registed SOE"
    else:
        print "Could not register SOE"
        print status
    
    return      


def getServiceList(server, port, adminUser, adminPass, useSSL=True, token=None):
    ''' Function to get all services
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    Note: Will not return any services in the Utilities or System folder
    '''    
    
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    services = []    
    folder = ''    
    URL = "{}{}{}/arcgis/admin/services{}?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), folder, token)    

    serviceList = json.loads(urllib2.urlopen(URL).read())

    # Build up list of services at the root level
    for single in serviceList["services"]:
        services.append(single['serviceName'] + '.' + single['type'])
     
    # Build up list of folders and remove the System and Utilities folder (we dont want anyone playing with them)
    folderList = serviceList["folders"]
    folderList.remove("Utilities")             
    folderList.remove("System")
        
    if len(folderList) > 0:
        for folder in folderList:                                              
            URL = "{}{}{}/arcgis/admin/services/{}?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), folder, token)    
            fList = json.loads(urllib2.urlopen(URL).read())
            
            for single in fList["services"]:
                services.append(folder + "//" + single['serviceName'] + '.' + single['type'])                
     
    return services


def getServerInfo(server, port, adminUser, adminPass, useSSL=True, token=None):
    ''' Function to get and display a detailed report about a server
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    service = String of existing service with type seperated by a period <serviceName>.<serviceType>
    If a token exists, you can pass one in for use.  
    '''    
    
    def getJson(URL, endURL, token):    
    # Helper function to return JSON for a specific end point
    #    
        openURL = URL + endURL + "?token={}&f=json".format(token)    
        status = urllib2.urlopen(openURL, '').read()    
        outJson = json.loads(status)   
        
        return outJson       
        
    
    # Get tand set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)      
     
    report = ''
    URL = "{}{}{}/arcgis/admin/".format(getProtocol(useSSL), server, getPort(port))

    report += "*-----------------------------------------------*\n\n"
    
    # Get Cluster and Machine info
    jCluster = getJson(URL, "clusters", token)
    
    if len(jCluster["clusters"]) == 0:        
        report += "No clusters found\n\n"
    else:    
        for cluster in jCluster["clusters"]:    
            report += "Cluster: {} is {}\n".format(cluster["clusterName"], cluster["configuredState"])            
            if len(cluster["machineNames"])     == 0:
                report += "    No machines associated with cluster\n"                
            else:
                # Get individual Machine info
                for machine in cluster["machineNames"]:                    
                    jMachine = getJson(URL, "machines/" + machine, token)
                    report += "    Machine: {} is {}. (Platform: {})\n".format(machine, jMachine["configuredState"],jMachine["platform"])                    
        
                    
    # Get Version and Build
    jInfo = getJson(URL, "info", token)    
    report += "\nVersion: {}\nBuild:   {}\n\n".format(jInfo ["currentversion"], jInfo ["currentbuild"])
      

    # Get Log level
    jLog = getJson(URL, "logs/settings", token)    
    report += "Log level: {}\n\n".format(jLog["settings"]["logLevel"])
     
    
    #Get License information
    jLicense = getJson(URL, "system/licenses", token)
    report += "License is: {} / {}\n".format(jLicense["edition"]["name"], jLicense["level"]["name"])    
    if jLicense["edition"]["canExpire"] == True:
        import datetime
        d = datetime.date.fromtimestamp(jLicense["edition"]["expiration"] // 1000) #time in milliseconds since epoch
        report += "License set to expire: {}\n".format(datetime.datetime.strftime(d, '%Y-%m-%d'))        
    else:
        report += "License does not expire\n"        
    
        
    if len(jLicense["extensions"]) == 0:
        report += "No available extensions\n"        
    else:
        report += "Available Extenstions........\n"   
        for name in jLicense["extensions"]:            
            report += "extension:  {}\n".format(name["name"])            
               
    
    report += "\n*-----------------------------------------------*\n"
    
    print report

def getServicePortalProps(server, port, adminUser,  adminPass, folder, serviceNameAndType, useSSL=True, token=None):
    ''' Function to get the portal properties of the service
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''

    serviceInfo = getServiceInfo(server, port, adminUser,  adminPass, folder, serviceNameAndType, useSSL, token)
    servicePortalProps = serviceInfo.get("portalProperties")

    return servicePortalProps

def getServicePortalProps2(server_url, user_name,  user_pass, servicename_and_type, token=None):
    ''' Function to get the portal properties of the service
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''

    serviceInfo = getServiceInfo2(server_url, user_name,  user_pass, servicename_and_type, token)
    servicePortalProps = serviceInfo.get("portalProperties")
    
    return servicePortalProps

def getServiceInfo(server, port, adminUser,  adminPass, folder, serviceNameAndType, useSSL=True, token=None):
    ''' Function to get service item info
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    if folder is not None:
        folderServerNameType = folder + "/" + serviceNameAndType
    else:
        folderServerNameType = serviceNameAndType
        
    serviceInfo = {}       
    
    URL = "{}{}{}/arcgis/admin/services/{}?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), folderServerNameType, token)    

    serviceInfo = json.loads(urllib2.urlopen(URL).read())
    
    return serviceInfo


def getServiceInfo2(server_url, user_name,  user_pass, servicename_and_type, token=None):
    ''' Function to get service item info
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    
    if token is None:    
        token = gentoken2(server_url, user_name, user_pass)    
        
    serviceInfo = {}       
    URL = "{}/admin/services/{}?token={}&f=json".format(server_url, servicename_and_type, token)    

    serviceInfo = json.loads(urllib2.urlopen(URL).read())
    
    return serviceInfo

def getServiceStatus(server, port, adminUser,  adminPass, folder, serviceNameAndType, useSSL=True, token=None):
    ''' Function to get service status
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    if folder is not None:
        folderServerNameType = folder + "/" + serviceNameAndType
    else:
        folderServerNameType = serviceNameAndType
        
    serviceInfo = {}       
    URL = "{}{}{}/arcgis/admin/services/{}/status?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), folderServerNameType, token)    

    serviceInfo = json.loads(urllib2.urlopen(URL).read())
    
    return serviceInfo


def editServiceInfo(server, port, adminUser,  adminPass, folder, serviceNameAndType, serviceInfo, useSSL=True, token=None):
    ''' Function to edit service item info
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    if folder is not None:
        folderServerNameType = folder + "/" + serviceNameAndType
    else:
        folderServerNameType = serviceNameAndType
    
    updatedSvcJson = json.dumps(serviceInfo)
    
    prop_encode = urllib.urlencode({'service': updatedSvcJson})
    
    URL = "{}{}{}/arcgis/admin/services/{}/edit?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), folderServerNameType, token)    
    status = json.loads(urllib2.urlopen(URL, prop_encode).read())

    if status.get('status') == 'success':
        success = True
    else:
        success = False
        
    return success, status



def getServiceItemInfo(server, port, adminUser,  adminPass, folder, serverNameAndType, useSSL=True, token=None):
    ''' Function to get service item info
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    if folder is not None:
        folderServerNameType = folder + "/" + serverNameAndType
    else:
        folderServerNameType = serverNameAndType
        
    serviceItemInfo = {}       
    URL = "{}{}{}/arcgis/admin/services/{}/iteminfo?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), folderServerNameType, token)    

    serviceItemInfo = json.loads(urllib2.urlopen(URL).read())
    
    return serviceItemInfo

def getConfigStoreProperty(server, port, adminUser, adminPass, useSSL=True, token=None, property="connectionString"):
    ''' Function to get config store information
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    directories = {}       
    URL = "{}{}{}/arcgis/admin/system/configstore?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), token)    

    configStore = json.loads(urllib2.urlopen(URL).read())
    
    return configStore[property]

def getServerDirectories(server, port, adminUser, adminPass, useSSL=True, token=None):
    ''' Function to get all directories
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    serverDirectories = {}       
    URL = "{}{}{}/arcgis/admin/system/directories?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), token)    

    serverDirectories = json.loads(urllib2.urlopen(URL).read())
    
    return serverDirectories

def getServerDirectory(server, port, adminUser, adminPass, directoryType, useSSL=True, token=None):
    '''
    Get specific Server Directory json dictionary based on directoryType.
    Valid directoryType's are:
    CACHE, INDEX, INPUT, JOBREGISTRY, JOBS, OUTPUT, SYSTEM, UPLOADS, KML
    '''
    
    
    serverDirectories = getServerDirectories(server, port, adminUser, adminPass, useSSL, token=None)
    
    for serverDirectory in serverDirectories["directories"]:
        if serverDirectory["directoryType"] == directoryType.upper():
            break
    
    return serverDirectory

def getDataItemInfo(server, port, adminUser,  adminPass, dataItemPath, useSSL=True, token=None):
    ''' Function to get data item info
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.
    Example of "dataItemPath" is /fileShares/OpsEnvironment.
    '''    
    
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
        
    dataItemInfo = {}       
    URL = "{}{}{}/arcgis/admin/data/items{}?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), dataItemPath, token)    

    dataItemInfo = json.loads(urllib2.urlopen(URL).read())
    
    if dataItemInfo.get('status'):
        # The 'status' key only exists if there is an error.
        success = False
    else:
        success = True
        
    return success, dataItemInfo

def registerDataItem(server, port, adminUser, adminPass, item, useSSL=True, token=None):
    ''' Function to register a data store item
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    Requires item containing necessary json structure for data item.
    If a token exists, you can pass one in for use.  
    '''    
    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    item_encode = urllib.urlencode(item)            
    URL = "{}{}{}/arcgis/admin/data/registerItem?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)    
    status = json.loads(urllib2.urlopen(URL, item_encode).read())
    
    if status.get('status') == 'error':
        success = False
    elif status.get('success') == False:
        success = False
    elif status.get('success') == True:
        success = True
    else:
        success = False
        
    return success, status

def unregisterDataItem(server, port, adminUser, adminPass, itemPath, useSSL=True, token=None):
    ''' Function to unregister a data store item
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    item_encode = urllib.urlencode(itemPath)            
    URL = "{}{}{}/arcgis/admin/data/unregisterItem?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)    
    status = json.loads(urllib2.urlopen(URL, item_encode).read())

    if status.get('status') == 'error':
        success = False
    elif status.get('success') == False:
        success = False
    elif status.get('success') == True:
        success = True
    else:
        success = False

    return success, status

def validateDataItem(server, port, adminUser, adminPass, item, useSSL=True, token=None):
    ''' Function to validate a data store item
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''
    

    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    item_encode = urllib.urlencode(item)            
    URL = "{}{}{}/arcgis/admin/data/validateDataItem?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)    
    status = json.loads(urllib2.urlopen(URL, item_encode).read())
    
    if status.get('status') == 'success':
        success = True
    else:
        success = False
        
    return success, status

def getServicesDirectory(server, port, adminUser,  adminPass, useSSL=True, token=None):
    ''' Function to get properties related to the HTML view of the ArcGIS REST API.
        Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
        If a token exists, you can pass one in for use.
    '''
    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)

    URL = "{}{}{}/arcgis/admin/system/handlers/rest/servicesdirectory?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)    
    status = json.loads(urllib2.urlopen(URL, '').read())
    
    # If successful, the json won't contain a 'status' or 'success' key/values;
    # so test success by whether the json contains one of the services
    # directory keys that is expected
    if status.get('allowedOrigins'):
        success = True
    else:
        success = False
        
    return success, status

def editServicesDirectory(server, port, adminUser, adminPass,
                          allowed_origins, arcgis_com_map, arcgis_com_map_text,
                          jsapi_arcgis, jsapi_arcgis_css, jsapi_arcgis_css2,
                          jsapi_arcgis_sdk, services_dir_enabled, useSSL=True, token=None):
    '''
    Function to edit the properties related to the HTML view of the ArcGIS REST API.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.
    '''
    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    

    # The following are not required to be set to avoid the null pointer error:
    # consoleLogging, 'servicesDirEnabled'
    #
    # if 'servicesDirEnabled' is not in json, the script does not fail, but the property is set to false.
    #
    # if the following are not set then receive the error ["java.lang.NullPointerException"]
    #'allowedOrigins', 'jsapi.arcgis.css', 'arcgis.com.map.text', 'jsapi.arcgis.sdk',
    # 'arcgis.com.map', 'jsapi.arcgis', 'jsapi.arcgis.css2'

    prop_dict = dict()
    
    # Comma-separated list of URLs of domains allowed to make requests. * can be used to denote all domains.
    if allowed_origins:
        prop_dict['allowedOrigins'] = allowed_origins
    
    # URL of the map viewer application used for service previews.
    if arcgis_com_map:
        prop_dict['arcgis.com.map'] = arcgis_com_map
    
    # The text to use for the preview link that opens the map viewer.
    if arcgis_com_map_text:
        prop_dict['arcgis.com.map.text'] = arcgis_com_map_text
    
    # The URL of the JavaScript API to use for service previews.
    if jsapi_arcgis:
        prop_dict['jsapi.arcgis'] = jsapi_arcgis
    
    # CSS file associated with the ArcGIS API for JavaScript.
    if jsapi_arcgis_css:
        prop_dict['jsapi.arcgis.css'] = jsapi_arcgis_css
    
    # Additional CSS file associated with the ArcGIS API for JavaScript.
    if jsapi_arcgis_css2:
        prop_dict['jsapi.arcgis.css2'] = jsapi_arcgis_css2
    
    # URL of the ArcGIS API for JavaScript help.
    if jsapi_arcgis_sdk:
        prop_dict['jsapi.arcgis.sdk'] = jsapi_arcgis_sdk
    
    # Flag to enable/disable the HTML view of the services directory.
    # Note: using json.loads as a helper function to determine
    # if passed in value evaluates to boolean no matter if function
    # is passed in a string (ie. 'true' or 'false') or Python booleans
    # (i.e. True or False); string must be in lowercase for json.loads()
    # to evaluate.
    if json.loads(str(services_dir_enabled).lower()):
        prop_dict['servicesDirEnabled'] = 'true'
    else:
        prop_dict['servicesDirEnabled'] = 'false'
    
    prop_encode = urllib.urlencode(prop_dict)
    
    URL = "{}{}{}/arcgis/admin/system/handlers/rest/servicesdirectory/edit?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)    
    status = json.loads(urllib2.urlopen(URL, prop_encode).read())

    if status.get('status') == 'success':
        success = True
    else:
        success = False
        
    return success, status

def getServiceTypes(server, port, adminUser, adminPass, useSSL=True, token=None):
    ''' Function to get all supported service types (and extensions)
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    serviceTypesInfoList = []
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    types = {}       
    URL = "{}{}{}/arcgis/admin/services/types?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), token)    

    types = json.loads(urllib2.urlopen(URL).read())
    
    typeList = types.get('types')
    
    for serviceType in typeList:
        info = getServiceTypeExtensions(server, port, adminUser, adminPass, serviceType['Name'], useSSL, token)
        serviceTypesInfoList.append(info)
        
    return serviceTypesInfoList

def getServiceTypeExtensions(server, port, adminUser, adminPass, serviceType, useSSL=True, token=None):
    ''' Function to get service type extensions for the specified service type
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    serviceTypeAndExtensions = {}       
    URL = "{}{}{}/arcgis/admin/services/types/{}?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), serviceType, token)    

    serviceTypeAndExtensions = json.loads(urllib2.urlopen(URL).read())
    
    return serviceTypeAndExtensions

def getServiceManifest(server, port, adminUser,  adminPass, folder, serverNameAndType, useSSL=True, token=None):
    ''' Function to get service manifest
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    if folder is not None:
        folderServerNameType = folder + "/" + serverNameAndType
    else:
        folderServerNameType = serverNameAndType
        
    serviceManifest = {}       
    URL = "{}{}{}/arcgis/admin/services/{}/iteminfo/manifest/manifest.json?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), folderServerNameType, token)    

    serviceManifest = json.loads(urllib2.urlopen(URL).read())
    
    return serviceManifest

def getDBConnectionStrFromStr(server, port, adminUser, adminPass, dbConnectionString, useSSL=True, token=None):
    ''' Returns encrypted db connection string given the db connection string.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    
    in_param_dict = dict()
    in_param_dict['in_connDataType'] = 'CONNECTION_STRING'
    in_param_dict['in_inputData'] = dbConnectionString
    
    return _getDBConnectionString(server, port, adminUser, adminPass, in_param_dict, useSSL, token=None)
    
def _getDBConnectionString(server, port, adminUser, adminPass, in_param_dict, useSSL=True, token=None):
    ''' Executes "Get Database Connecting String" gp service task.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    

    results = None
    job_results = None
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    # Submit the job
    item_encode = urllib.urlencode(in_param_dict)            
    URL = "{}{}{}/arcgis/rest/services/System/PublishingTools/GPServer/Get%20Database%20Connection%20String/submitJob?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), token)    
    submit_results = json.loads(urllib2.urlopen(URL, item_encode).read())

    job_status = submit_results['jobStatus']
    job_id = submit_results['jobId']
    job_URL = "{}{}{}/arcgis/rest/services/System/PublishingTools/GPServer/Get%20Database%20Connection%20String/jobs/{}?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), job_id, token)
    
    # Check for job completion
    while job_status == 'esriJobSubmitted':
        time.sleep(2)
        job_results = json.loads(urllib2.urlopen(job_URL).read())
        job_status = job_results['jobStatus']
    
    # Check job completion status
    if job_status == 'esriJobFailed':
        success = False
        msgs = job_results['messages']
        results = []
        for msg in msgs:
            if msg['type'] == 'esriJobMessageTypeError':
                results.append(msg['description'])
    
    if job_status == 'esriJobSucceeded':
        success = True
        param_URL = job_results['results']['out_connectionString']['paramUrl']
        job_results_URL = "{}{}{}/arcgis/rest/services/System/PublishingTools/GPServer/Get%20Database%20Connection%20String/jobs/{}/{}?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), job_id, param_URL, token)
        out_connection_string = json.loads(urllib2.urlopen(job_results_URL).read())
        results = out_connection_string['value'].encode('ascii')
    
    return success, results

def getClusters(server, port, adminUser, adminPass, useSSL=True, token=None):
    ''' Function to get clusters.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.
    '''
    
    if token is None:
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    services = []    
    folder = ''    
    URL = "{}{}{}/arcgis/admin/clusters?f=pjson&token={}".format(getProtocol(useSSL), server, getPort(port), token)    

    clusters = json.loads(urllib2.urlopen(URL).read())

    return clusters.get('clusters')

def parseService(service):
    # Parse folder and service nameType
    folder = None
    serviceNameType = None
     
    parsedService = service.split('//')
    
    if len(parsedService) == 1:
        serviceNameType = parsedService[0]
    else:
        folder = parsedService[0]
        serviceNameType = parsedService[1]
        
    return folder, serviceNameType

def getHostedServiceDefinition(server, port, adminUser,  adminPass, folder, serviceNameAndType, useSSL=True, token=None):
    ''' Function to get the json "definition" of the service
    that can be passed to the updateHostedFeatureServiceDefintion function
    for editing service properties, such as Sync, Tracking, Export and Editing.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    
    definition = None
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass, useSSL)    
    
    if folder is not None:
        folderServerNameType = folder + "/" + serviceNameAndType
    else:
        folderServerNameType = serviceNameAndType
    
    serviceInfo = getServiceInfo(server, port, adminUser, adminPass, folder, serviceNameAndType)     
    
    definition = {}
    definition['capabilities'] = serviceInfo['capabilities']
    definition['allowGeometryUpdates'] = serviceInfo['jsonProperties']['allowGeometryUpdates']
    #definition['hasStaticData'] = serviceInfo['jsonProperties']['hasStaticData']
    definition['editorTrackingInfo'] = serviceInfo['jsonProperties']['editorTrackingInfo']
    
    jsonProperties = serviceInfo['jsonProperties']
    definition['allowGeometryUpdates'] = jsonProperties['allowGeometryUpdates']
    definition['editorTrackingInfo'] = jsonProperties['editorTrackingInfo']
    
    
    # if jsonProperties.get('hasStaticData'):
    #     definition['hasStaticData'] = jsonProperties['hasStaticData']
    #     print '\thasStaticData: {}'.format(definition['hasStaticData'])
    # else:
    #     layers = jsonProperties['layers']
    #     for i in layers.keys():
    #         has_static_data = layers[i].get('hasStaticData')
    #         print '\tlayer: {}, hasStaticData: {}'.format(i, has_static_data)
            
    
    
    return definition

def updateHostedFeatureServiceDefinition(server, port, adminUser,  adminPass, service, definition, useSSL=True, token=None):
    ''' Function to update hosted service properties,
    such as Sync, Tracking, Export and Editing.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''

    if token is None:
        token = gentoken(server, port, adminUser, adminPass, useSSL)
    
    definitionJson = json.dumps(definition)
    
    prop_encode = urllib.urlencode({'updateDefinition': definitionJson})
    print 'update function - service: {}'.format(service)
    URL = "{}{}{}/arcgis/rest/admin/services/{}/updateDefinition?token={}&f=json".format(getProtocol(useSSL), server, getPort(port), service.replace('.', '/'), token)

    status = json.loads(urllib2.urlopen(URL, prop_encode).read())

    if status.get('success'):
        success = True
    else:
        success = False
        
    return success, status