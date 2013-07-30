'''
---------------------------------
Eric's NOTEs:
NOTE: downloaded from
http://blogs.esri.com/esri/arcgis/2012/07/05/downloadable-tools-for-arcgis-server-administration/
on July 6, 2012.

NOTE: commented out "upload" function since this depends on 3rd party module

History:
07/25/2013 - Eric Linz
    - Created this module based on AllFunctions.py module.
    - Modified all functions to use 'https' instead of 'http' to support our 10.2 OpsServer
        which is configured to 'HTTPS Only'.
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
    
def gentoken(server, port, adminUser, adminPass, expiration=60):
    #Re-usable function to get a token required for Admin changes
    
    query_dict = {'username':   adminUser,
                  'password':   adminPass,
                  'expiration': str(expiration),
                  'client':     'requestip'}
    
    query_string = urllib.urlencode(query_dict)
    
    if port:
        url = "https://{}:{}/arcgis/admin/generateToken".format(server, port)
    else:
        url = "https://{}/arcgis/admin/generateToken".format(server)
    
    token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())
        
    if "token" not in token:
        print token['messages']
        exit()
    else:
        # Return the token to the function which called for it
        return token['token']
    
    
def modifyLogs(server, port, adminUser, adminPass, clearLogs, logLevel, token=None):
    ''' Function to clear logs and modify log settings.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    clearLogs = True|False
    logLevel = SEVERE|WARNING|FINE|VERBOSE|DEBUG
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get tand set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)
    
    # Clear existing logs
    if clearLogs:
        clearLogs = "https://{}/arcgis/admin/logs/clean?token={}&f=json".format(server, token)
        status = urllib2.urlopen(clearLogs, ' ').read()    
    
        if 'success' in status:
            print "Cleared log files"
    
    # Get the current logDir, maxErrorReportsCount and maxLogFileAge as we dont want to modify those
    currLogSettings_url = "https://{}/arcgis/admin/logs/settings?f=pjson&token={}".format(server, token)
    logSettingProps = json.loads(urllib2.urlopen(currLogSettings_url, ' ').read())['settings'] 
    
    # Place the current settings, along with new log setting back into the payload
    logLevel_dict = {      "logDir": logSettingProps['logDir'],
                           "logLevel": logLevel,
                           "maxErrorReportsCount": logSettingProps['maxErrorReportsCount'],
                           "maxLogFileAge": logSettingProps['maxLogFileAge']                       
                    }
   
    # Modify the logLevel
    log_encode = urllib.urlencode(logLevel_dict)     
    logLevel_url = "https://{}/arcgis/admin/logs/settings/edit?f=json&token={}".format(server, token)
    logStatus = json.loads(urllib.urlopen(logLevel_url, log_encode).read())
    
    
    if logStatus['status'] == 'success':
        print "Succesfully changed log level to {}".format(logLevel)        
    else:
        print "Log level not changed"
        
    return
        
        
def createFolder(server, port, adminUser, adminPass, folderName, folderDescription, token=None):
    ''' Function to create a folder
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    folderName = String with a folder name
    folderDescription = String with a description for the folder
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)    
    
    # Dictionary of properties to create a folder
    folderProp_dict = { "folderName": folderName,
                        "description": folderDescription                                            
                      }
    
    folder_encode = urllib.urlencode(folderProp_dict)            
    create = "https://{}/arcgis/admin/services/createFolder?token={}&f=json".format(server, token)    
    status = urllib2.urlopen(create, folder_encode).read()

    
    if 'success' in status:
        print "Created folder: {}".format(folderName)
    else:
        print "Could not create folder"  
        print status
        
    return
        

def getFolders(server, port):
    ''' Function to get all folders on a server  
    Note: Uses the Services Directory, not the REST Admin
    '''        
    
    foldersURL = "https://{}/arcgis/rest/services/?f=pjson".format(server)    
    status = json.loads(urllib2.urlopen(folders, '').read())
        
    folders = status["folders"]
    
    # Return a list of folders to the function which called for them
    return folders


def renameService(server, port, adminUser, adminPass, service, newName, token=None):
    ''' Function to rename a service
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    service = String of existing service with type separated by a period <serviceName>.<serviceType>
    newName = String of new service name
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get and set the token
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)      
    
    # Dictionary of properties used to rename a service
    renameService_dict = { "serviceName": service.split('.')[0],
                           "serviceType": service.split('.')[1],
                           "serviceNewName" : newName
                         }
    
    rename_encode = urllib.urlencode(renameService_dict)            
    rename = "https://{}/arcgis/admin/services/renameService?token={}&f=json".format(server, token)    
    status = urllib2.urlopen(rename, rename_encode ).read()
    
    
    if 'success' in status:
        print "Succesfully renamed service to : {}".format(newName)
    else:
        print "Could not rename service"
        print status
        
    return
 
def stopStartServices(server, port, adminUser, adminPass, stopStart, serviceList, token=None):  
    ''' Function to stop, start or delete a service.
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    stopStart = Stop|Start|Delete
    serviceList = List of services. A service must be in the <name>.<type> notation
    If a token exists, you can pass one in for use.  
    '''    
    
    # Get and set the token
    if token is None:       
        token = gentoken(server, port, adminUser, adminPass)
    
    # modify the services(s)    
    for service in serviceList:
        op_service_url = "https://{}/arcgis/admin/services/{}/{}?token={}&f=json".format(server, service, stopStart, token)
        status = urllib2.urlopen(op_service_url, ' ').read()
        
        if 'success' in status:
            print (str(service) + " === " + str(stopStart))
        else:            
            print status
    
    return 

# Eric L. commented out 7/6/2012; this function depends on 3rd party "requests"
# module that I don't want to add to StarTeam. Not big deal since I dont'
# think we need this; at least not yet.
#
#def upload(server, port, adminUser, adminPass, fileinput, token=None):
#    ''' Function to upload a file to the REST Admin
#    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
#    fileinput = path to file to upload. (file upload will be done in binary)
#    NOTE: Dependency on 3rd party module "requests" for file upload 
#        > http://docs.python-requests.org/en/latest/index.html
#    If a token exists, you can pass one in for use.  
#    '''  
#
#    # 3rd party module dependency
#    import requests
#    
#    # Get and set the token
#    if token is None:  
#        token = gentoken(server, port, adminUser, adminPass)     
#  
#    # Properties used to upload a file using the request module
#    files = {"itemFile": open(fileinput, 'rb')}
#    files["f"] = "json"        
#    
#    URL='http://{}:{}/arcgis/admin/uploads/upload'.format(server)
#    response = requests.post(URL+"?token="+token, files=files);
#         
#    json_response = json.loads(response.text)
#    
#    if "item" in json_response:                
#        itemID = json_response["item"]["itemID"]     
#        #Note : this function calls the registerSOE function. Remove next line if unnecessary
#        registerSOE(server, port, adminUser, adminPass, itemID)        
#    else:
#        print json_response
#        
#    return
        
        
def registerSOE(server, port, adminUser, adminPass, itemID, token=None):
    ''' Function to upload a file to the REST Admin
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    itemID = itemID of an uploaded SOE the server will register.    
    If a token exists, you can pass one in for use.      '''
    
    # Get and set the token
    if token is None:  
        token = gentoken(server,  port, "admin", "admin")     
    
    # Registration of an SOE only requires an itemID. The single item dictionary is encoded in place
    SOE_encode = urllib.urlencode({"id":itemID})   
    
    register = "https://{}/arcgis/admin/services/types/extensions/register?token={}&f=json".format(server, token)    
    status = urllib2.urlopen(register, SOE_encode).read()
    
    if 'success' in status:
        print "Succesfully registed SOE"
    else:
        print "Could not register SOE"
        print status
    
    return      


def getServiceList(server, port, adminUser, adminPass, token=None):
    ''' Function to get all services
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    Note: Will not return any services in the Utilities or System folder
    '''    
    
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)    
    
    services = []    
    folder = ''    
    URL = "https://{}/arcgis/admin/services{}?f=pjson&token={}".format(server, folder, token)    

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
            URL = "https://{}/arcgis/admin/services/{}?f=pjson&token={}".format(server, folder, token)    
            fList = json.loads(urllib2.urlopen(URL).read())
            
            for single in fList["services"]:
                services.append(folder + "//" + single['serviceName'] + '.' + single['type'])                
    #Commented out, Eric L. July 6, 2012
    #print services    
    return services


def getServerInfo(server, port, adminUser, adminPass, token=None):
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
        token = gentoken(server, port, adminUser, adminPass)      
     
    report = ''
    URL = "https://{}/arcgis/admin/".format(server)

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


def getServiceInfo(server, port, adminUser,  adminPass, folder, serviceNameAndType, token=None):
    ''' Function to get service item info
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    # Created: Eric L.
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)    
    
    if folder is not None:
        folderServerNameType = folder + "/" + serviceNameAndType
    else:
        folderServerNameType = serviceNameAndType
        
    serviceInfo = {}       
    URL = "https://{}/arcgis/admin/services/{}?f=pjson&token={}".format(server, folderServerNameType, token)    

    serviceInfo = json.loads(urllib2.urlopen(URL).read())
    
    return serviceInfo

def getServiceItemInfo(server, port, adminUser,  adminPass, folder, serverNameAndType, token=None):
    ''' Function to get service item info
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    # Created: Eric L
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)    
    
    if folder is not None:
        folderServerNameType = folder + "/" + serverNameAndType
    else:
        folderServerNameType = serverNameAndType
        
    serviceItemInfo = {}       
    URL = "https://{}/arcgis/admin/services/{}/iteminfo?f=pjson&token={}".format(server, folderServerNameType, token)    

    serviceItemInfo = json.loads(urllib2.urlopen(URL).read())
    
    return serviceItemInfo

def getConfigStoreProperty(server, port, adminUser, adminPass, token=None, property="connectionString"):
    ''' Function to get config store information
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    # Created: Eric L
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)    
    
    directories = {}       
    URL = "https://{}/arcgis/admin/system/configstore?f=pjson&token={}".format(server, token)    

    configStore = json.loads(urllib2.urlopen(URL).read())
    
    return configStore[property]

def getServerDirectories(server, port, adminUser, adminPass, token=None):
    ''' Function to get all directories
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.  
    '''    
    # Created: Eric L
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)    
    
    serverDirectories = {}       
    URL = "https://{}/arcgis/admin/system/directories?f=pjson&token={}".format(server, token)    

    serverDirectories = json.loads(urllib2.urlopen(URL).read())
    
    return serverDirectories

def getServerDirectory(server, port, adminUser, adminPass, directoryType, token=None):
    '''
    Get specific Server Directory json dictionary based on directoryType.
    Valid directoryType's are:
    CACHE, INDEX, INPUT, JOBREGISTRY, JOBS, OUTPUT, SYSTEM, UPLOADS, KML
    '''
    # Created: Eric L
    
    serverDirectories = getServerDirectories(server, port, adminUser, adminPass)
    
    for serverDirectory in serverDirectories["directories"]:
        if serverDirectory["directoryType"] == directoryType.upper():
            break
    
    return serverDirectory

def getDataItemInfo(server, port, adminUser,  adminPass, dataItemPath, token=None):
    ''' Function to get data item info
    Requires Admin user/password, as well as server and port (necessary to construct token if one does not exist).
    If a token exists, you can pass one in for use.
    Example of "dataItemPath" is /fileShares/OpsEnvironment.
    '''    
    # Created: Eric L
    
    if token is None:    
        token = gentoken(server, port, adminUser, adminPass)    
        
    dataItemInfo = {}       
    URL = "https://{}/arcgis/admin/data/items{}?f=pjson&token={}".format(server, dataItemPath, token)    

    dataItemInfo = json.loads(urllib2.urlopen(URL).read())
    
    return dataItemInfo

# Eric L. commented out 7/6/2012
###### EXAMPLE CALLS TO ABOVE FUNCTIONS #####
#
## Register an SOE:
#upload("prodSrv", 6080, "admin", "admin", r"c:\development\SOES\querySOE.soe")
#
## Stop 3 services from a list:
#serviceList = ["CitizenMapping.MapServer","CitizenInput.GPServer","basemap.MapServer"]
#stopStartServices("prodSrv", 6080, "admin", "admin", "Stop", serviceList)
#
## Get all services on a server and start them all:
#server = "prodSrv"
#port = 6080
#admin = "admin"
#apass = "admin"
#serviceList = getServiceList(server, port, admin, apass)
#stopStartServices(server, port, admin, apass, "Start", serviceList)
#
## Clear log files and change to Debug:
#modifyLogs("prodSrv", 6080, "admin", "admin", True, "DEBUG")
#
## Create a folder:
#createFolder("prodSrv", 6080, "admin", "admin", "testServices", "Folder for test services")
#
## Get a list of folders and assign to a variable:
#serverFolders = getFolders("prodSrv", 6080)
#print serverFolders
#
## Print out information about a server
#getServerInfo("gizmo", 6080, "admin", "admin")