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
#Name:          GetSDFiles.py
#
#Purpose:       Copies the latest service definition files for specified
#               ArcGIS Server site.
#
#Prerequisites: 7-zip must be installed. Change path set in variable
#               'sevenZipExePath' if necessary.
#
#==============================================================================
import sys, os, traceback, datetime, json, subprocess, tempfile
from walkingDirTrees import listFiles
from AGSRestFunctions import getServerDirectory
from AGSRestFunctions import getServiceList
from AGSRestFunctions import getServiceInfo
from shutil import copy2
from shutil import rmtree
from socket import getfqdn
import copy, json

# Add Publish/Portal to sys path inorder to import
#   modules in subfolder
supportFilesPath = os.path.join(
    os.path.dirname(os.path.dirname(sys.argv[0])), 'Publish', 'Portal')
sys.path.append(supportFilesPath)
from portalpy import Portal

sevenZipExePath = r'C:\Program Files\7-Zip\7z.exe'

scriptName = sys.argv[0]
exitErrCode = 1
debug = False
sdFilePattern = '*.sd'
sectionBreak = '=' * 175
sectionBreak1 = '-' * 175

def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) < 6:
        
        print '\n' + scriptName + ' <AGSFullyQualifiedDomainName> <Port> <AdminUser> <AdminPassword> <REPORT|COPY> {CopyToFolder} {Owners}'
    
        print '\nWhere:'
        print '\n\t<AGSFullyQualifiedDomainName> (required parameter): the fully qualified domain name of th ArcGIS Server.'
        print '\n\t<Port> (required parameter): the port number of the ArcGIS Server (specify # if no port).'
        print '\n\t<AdminUser> (required parameter): ArcGIS Server site administrator.'
        print '\n\t<AdminPassword> (required parameter): Password for ArcGIS Server site administrator.'
        print '\n\t<REPORT|COPY> (required parameter): \tREPORT - provides status report without copying service definitions;'
        print '\n\t\t\t\t\t\tCOPY - provides status report and copies service definitions.'
        print '\n\t{CopyToFolder} (required parameter if using "COPY" option ): Folder where the service definitions are to be copied.'
        print '\n\t{Owners} (optional) list of owners to filter the service definition files (only services associated with the portal items '
        print '\t\t"owned" by these users *** [AND SHARED WITH "EVERYONE"] *** will be copied).'
        print '\n\t\t- List must be comma delimited list (spaces can be included after commas, but list must be enclosed by quotes).'
        print '\t\t- Owner names are case sensitive.'
        print '\nNOTE: if not executed on the ArcGIS Server machine, the ArcGIS Server "Directories" (see Manager) have to be UNC paths'
        print 'and given the appropriate OS permissions.'
        return None
    
    else:
        
        # Set variables from parameter values
        server = sys.argv[1]
        port = sys.argv[2]
        adminuser = sys.argv[3]
        password = sys.argv[4]
        exeType = sys.argv[5]
        targetFolder = None
        specified_users = None
        users = None
        if len(sys.argv) >= 7:
            targetFolder = sys.argv[6]
        if len(sys.argv) >= 8:
            specified_users = sys.argv[7]
        
        # Process/validate variables
        
        # 19 May 2015: Comment out requirement that script has to be executed on the
        #   ArcGIS Server machine.
        # if getfqdn().lower() <> server.lower().strip():
        #     print '\nThe specified "server" ' + server + ' is not the local machine ' + getfqdn().lower() + '. Exiting script.'
        #     return None
        
        if port.strip() == '#':
            port = None
      
        exeType = exeType.upper().strip()
        if exeType <> 'REPORT' and exeType <> 'COPY':
            print '\nExecution option parameter <REPORT|COPY> must be either REPORT or COPY. Exiting script.'
            return None
        
        if exeType == 'COPY':
            doCopy = True
        else:
            doCopy = False
        
        if doCopy:
            if not targetFolder:
                print '\nYou have selected to COPY the service definitions, but did not specify the <CopyToFolder> parameter. Exiting script.'
                return None
            
            if not os.path.exists(targetFolder):
                print '\n<CopyToFolder> folder ' + targetFolder + ' does not exist. Exiting script.'
                return None
            
            if len(os.listdir(targetFolder)) > 0:
                print '\n<CopyToFolder> folder ' + targetFolder + ' is not empty; remove contents. Exiting script.'
                return None
        
        if specified_users:
            users = specified_users.replace(' ', '').split(',')
            
    return server, port, adminuser, password, doCopy, targetFolder, users

def extractFromSDFile(sdFile, extractFolder, fileToExtract=None):
    ''' Extract file from compressed .sd file '''
    
    # 'Build' 7zip command line arguments
    # -y switch suppresses the overwrite user query if the file already exists.
    exeArgs = '{} e {} -o{}'.format(sevenZipExePath, sdFile, extractFolder)
    if fileToExtract:
        exeArgs += ' {}'.format(fileToExtract)
    exeArgs += ' -y'
    #print sectionBreak1
    exitCode = subprocess.call(exeArgs)
    return exitCode

def get_sd_files(sdRootFolder):
    ''' Return collection of latest .sd files contained with specified root folder '''
        
    fileInfo = dict()
    
    # Create temporary extract folder
    extractFolder = tempfile.mkdtemp()
    
    # Search for all .sd files contained with specified folder
    sdFilePaths = listFiles(sdRootFolder, sdFilePattern)
    
    # Create collection containing only the latest "version" of each .sd file
    for sdFile in sdFilePaths:

        # Extract service configuration json file from compressed .sd file
        extractFile = 'serviceconfiguration.json'
        jsonFile = os.path.join(extractFolder, extractFile)
        extractFromSDFile(sdFile, extractFolder, extractFile)
        
        # Extract service information from the service config json file
        os.chdir(extractFolder)
        serviceConfig = json.load(open(extractFile))
        folderName = serviceConfig['folderName']
        serviceName = serviceConfig['service']['serviceName']
        serviceType = serviceConfig['service']['type']
        
        # Create dictionary key (syntax: Folder//ServerName.ServiceType)
        fileKey = serviceName + '.' + serviceType
        if folderName:
            fileKey = folderName + '//' + fileKey
            
        # Get file creation/modified times (values in epoch time)
        # TODO: decide if we need to use creation or modified time (or compare the two)
        #  dates and use newest date to use as comparsion
        # Think we should use modfied time, because I've seen cases where you copy the file and the
        # creation time will reflect when you have copied the file and modified time reflected
        # the original creation date.
        creationTime = os.path.getctime(sdFile)
        modifiedTime = os.path.getmtime(sdFile)
        compareTime = modifiedTime # set which time to compare here; downstream code uses 'compareTime' variable.
        
        if fileKey in fileInfo:
            # Compare time of file that exists in collection and replace with
            # current file if timestamp is newer
            fileTime = fileInfo[fileKey]['timestamp']
            if compareTime > fileTime:
                fileInfo[fileKey] = {'path': sdFile, 'timestamp': compareTime}
        else:
            fileInfo[fileKey] = {'path': sdFile, 'timestamp': compareTime}
    
    if debug:
        print '\nwithin the get_sd_files function...'
        print 'fileInfo variable...'
        for i in fileInfo:
            print i + ': ' + fileInfo[i]['path'] + ': ' + str(fileInfo[i]['timestamp'])
    
    # Delete temporary extract folder
    # TODO: see if I can fix the error that is thrown when running the following code:
    # 'WindowsError: [Error 32] The process cannot access the file because it is being used
    # by another process'
    #if os.path.exists(extractFolder):
    #    rmtree(extractFolder)
    
    return fileInfo

def get_ags_services(server, port, adminuser, password):
    ''' Return collection of ArcGIS Server services and service info'''
    
    agsServices = {}
    
    # Get all services that exist on server
    allServices = getServiceList(server, port, adminuser, password)
    
    # Remove certain services from collection
    excludeServices = ['SampleWorldCities.MapServer']
    services = [service for service in allServices if service not in excludeServices]
    
    # Create dictionary from list of services; values are None.
    for service in services:
        
        parsedService = service.split('//')
        folder = None
        if len(parsedService) == 1:
            serviceNameType = parsedService[0]
        else:
            folder = parsedService[0]
            serviceNameType = parsedService[1]
            
        info = getServiceInfo(server, port, adminuser, password, folder, serviceNameType)
        agsServices[service] = info
        
    if debug:
        print "\nwithin get_ags_servides function:"
        print "agsServices:"
        print agsServices   
    
    return agsServices

def filesToCopy(sdFiles, agsServices, copyItemIDs=None):
    ''' Return collection of service definition files to copy '''

    # The service definition files that should be copied are those
    # that exist for each existing ArcGIS Server serice.
    sdFilesToCopy = {}
    for i in agsServices:
        serviceInfo = agsServices[i]
        portalItemsJson = serviceInfo['portalProperties']['portalItems']
        if i in sdFiles:
            if copyItemIDs:
                if portalItemsJson:
                    for portalItemJson in portalItemsJson:
                        itemID = portalItemJson['itemID']
                        if itemID in copyItemIDs:
                            sdFilesToCopy[i] = sdFiles[i]
            else:
                sdFilesToCopy[i] = sdFiles[i]
    
    if debug:
        print '\nwithin filesToCopy function:'
        print 'sdFilesToCopy variable...'
        for key, value in sdFilesToCopy.iteritems():
            print str(key) + ' = ' + str(value)
    
    return sdFilesToCopy


def copySDFiles(sdFilesToCopy, targetFolder, agsServices, portalProps):
    '''Copy SD files to target folder.
    Pass in collection of service info to dump to file system.'''
    
    print '\n' + sectionBreak
    print 'Copy SD Files...'
    print sectionBreak
    print '{:<60s}{} {:<100s}'.format('Service Folder//Name.Type', '|', 'SD File Path: From/To')
    print sectionBreak1
    for service, serviceInfo in sdFilesToCopy.iteritems():
        sdFilePath = serviceInfo['path']
        sdFile = os.path.basename(sdFilePath)
        sdParentFolder = os.path.basename(os.path.dirname(sdFilePath))
        outputFolder = os.path.join(targetFolder, sdParentFolder)
        outputFilePath = os.path.join(outputFolder, sdFile)
        print '{:<60s}{}{:<100s}'.format(service, '|', ' From: ' + sdFilePath)
        print '{:>61s}{:<100s}'.format('|', ' To: ' + outputFilePath)
        
        # Create target folder if it does not exist and copy file
        if not os.path.exists(outputFolder):
            os.makedirs(outputFolder)
        copy2(sdFilePath, outputFilePath)
        
        os.chdir(outputFolder)
        
        serviceInfo = agsServices[service]
        json.dump(serviceInfo, open(os.path.splitext(sdFile)[0] + '_s_info.json','w'))
        
        props = portalProps[service]
        json.dump(props, open(os.path.splitext(sdFile)[0] + '_p_info.json','w'))
        
    print sectionBreak

def getPortalPropsForServices(portal, agsServices):
    
    allServicesProps = None
    
    if not agsServices:
        return None
    
    allServicesProps = {}
    for service, info in agsServices.iteritems():
        allTags = []
        props = info.get('portalProperties')
        if props:
            outProps = copy.deepcopy(props)
            portalItems = props['portalItems']
            print '-' * 40
            for i in range(len(portalItems)):
                itemID = portalItems[i]['itemID']
                itemType = portalItems[i]['type']
                item = portal.item(itemID)
                
                if not item:
                    outProps['portalItems'][i]['itemExists'] = False
                    print 'ERROR: Service "' + service + '" is associated with a portal item (' + \
                        itemID + '; ' + itemType + ') that does not exist.'
                    outProps['portalItems'][i]['itemInfo'] = None
                    outProps['portalItems'][i]['itemSharing'] = None
                    outProps['portalItems'][i]['itemGroups'] = None
                    continue
                else:
                    groups = []
                    outProps['portalItems'][i]['itemExists'] = True
                    print '       Service "' + service + '" has an associated item (' + \
                    itemID + '; ' + itemType + ')'
                    item_info, item_sharing, item_folder_id = portal.user_item(itemID)
                    outProps['portalItems'][i]['itemInfo'] = item_info
                    outProps['portalItems'][i]['itemSharing'] = item_sharing
                    group_ids = item_sharing['groups']
                    for group_id in group_ids:
                        groups.append(portal.group(group_id))
                    outProps['portalItems'][i]['itemGroups'] = groups
        
            allServicesProps[service] = outProps
    
    return allServicesProps

def getPortalTags(portal, itemIDs):
    ''' Return list of unique tag elements '''
    allTags = []
    for itemID in itemIDs:
        tags = portal.item(itemID).get('tags')
        if tags:
            allTags.extend(tags)
    uniqueTags = list(set(allTags))

    if len(uniqueTags) == 0:
        uniqueTags = None

    return uniqueTags
    
def report(sdFiles, agsServices):
    ''' Report issues with the .sd files and ArcGIS Services '''
    
    sectionLen = 175
    totalNumServices = len(agsServices.keys())
    totalNumSDFiles = len(sdFiles.keys())
    totalNumMissingSDFiles = 0
    
    print '\n\n' + sectionBreak
    print 'Report:'
    print sectionBreak
    print '{:<60s}{} {:<100s}'.format('Service Folder//Name.Type', '|', 'SD File Path')
    print sectionBreak1
    for service in agsServices:
        if service in sdFiles:
            printLine = '{:<60s}{} {:<100s}'.format(service, '|', sdFiles[service]['path'])
        else:
            totalNumMissingSDFiles = totalNumMissingSDFiles + 1
            printLine = '{:<60s}{} {:<100s}'.format(service, '|', '***ERROR: SD file does not exist for this service.***')
        print printLine
        
    print sectionBreak1
    print 'Summary:'
    
    print '{:28s}{:5d}'.format('Total Num Services:', totalNumServices)
    print '{:28s}{:5d}'.format('Total Num SD Files to copy:', totalNumSDFiles)
    if totalNumMissingSDFiles == 0:
        printLine = '{:28s}{:5d}'.format('Total Num Missing SD Files:', totalNumMissingSDFiles)
    else:
        printLine = '{:28s}{:5d}{:8}'.format('Total Num Missing SD Files:', totalNumMissingSDFiles, ' (ERROR)')
    print printLine
    
    print sectionBreak

def getItemsIDs(portal, users):
    # Return list of ids of items owned by users (only finds items shared with 'Everyone')
    ids = []
    
    for user in users:
        q = 'owner:' + user
        items = portal.search(['id','type','url','title','owner'], q)
    
        if items:
            for item in items:
                if item.get('url'):
                    #print item.get('id'), item.get('owner'), item.get('type')
                    ids.append(item.get('id'))
        
    if len(ids) == 0:
        ids = None
        
    return ids

def main():
    
    totalSuccess = True
    
    # Before executing rest of script, lets check if 7-zip exe exists
    if not os.path.exists(sevenZipExePath):
        print 'ERROR: File path set by "sevenZipExePath" variable (' + \
            sevenZipExePath + ') does not exist. Exiting script.'
        sys.exit(exitErrCode)
    
    # Check arguments
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
        
    try:
        server, port, adminuser, password, doCopy, targetFolder, users = results
        
        if debug:
            print server, port, adminuser, password, doCopy, targetFolder, users
        
        # Determine where admins upload folder is located on server
        uploadsFolderInfo = getServerDirectory(server, port, adminuser, password, "UPLOADS")
        sdRootFolder = os.path.join(uploadsFolderInfo['physicalPath'], 'admin')
        print '\nNOTE: Uploads\admin folder is: ' + sdRootFolder + '\n'
        if not os.path.exists(sdRootFolder):
            print '\nERROR: the uploads\\admin folder ' + sdRootFolder + ' does not exist. Exiting script.'
            sys.exit(exitErrCode)
            
        # Get collection of .sd files
        sdFiles = get_sd_files(sdRootFolder)
        
        # Get collection of ArcGIS Service services on server
        agsServices = get_ags_services(server, port, adminuser, password)
        
        # Get the portal properties for each portal item referenced by the service
        # according to the services' json info
        
        portal = Portal('https://' + server + ':7443/arcgis', adminuser, password)
        
        props = getPortalPropsForServices(portal, agsServices)
        
        # Get list of item ids for all specified users
        userItemIDs = None
        if users:
            userItemIDs = getItemsIDs(portal, users)
        
        # Determine which sd files to copy
        sdFilesToCopy = filesToCopy(sdFiles, agsServices, userItemIDs)
        
        # Copy sd files
        if doCopy:
            copySDFiles(sdFilesToCopy, targetFolder, agsServices, props)
        
        # Print report
        report(sdFilesToCopy, agsServices)
        
        print '\nDone.'
        
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
        if totalSuccess:
            sys.exit(0)
        else:
            sys.exit(1)
    
if __name__ == "__main__":
    main()
