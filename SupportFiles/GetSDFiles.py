#!/usr/bin/env python
#==============================================================================
#Name:          GetSDFiles.py
#Purpose:       Copies the latest service definition files for specified
#               ArcGIS Server site.
#
#Prerequisites: 
#
#History:       2013/07/26:   Initial code.
#
#==============================================================================
import sys, os, traceback, datetime, json, subprocess, tempfile
from walkingDirTrees import listFiles
from AGSRestFunctions import getServerDirectory
from AGSRestFunctions import getServiceList
from shutil import copy2
from shutil import rmtree
from socket import getfqdn

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
        
        print '\n' + scriptName + ' <AGSFullyQualifiedDomainName> <Port> <AdminUser> <AdminPassword> <REPORT|COPY> {CopyToFolder}'
    
        print '\nWhere:'
        print '\n\t<AGSFullyQualifiedDomainName> (required parameter): the fully qualified domain name of th ArcGIS Server.'
        print '\n\t<Port> (required parameter): the port number of the ArcGIS Server (specify # if no port).'
        print '\n\t<AdminUser> (required parameter): ArcGIS Server site administrator.'
        print '\n\t<AdminPassword> (required parameter): Password for ArcGIS Server site administrator.'
        print '\n\t<REPORT|COPY> (required parameter): \tREPORT - provides status report without copying service definitions;'
        print '\n\t\t\t\t\t\tCOPY - provides status report and copies service definitions.'
        print '\n\t{CopyToFolder} (required parameter if using "COPY" option ): Folder where the service definitions are to be copied.'
        print '\nNOTE: this script must be executed from the ArcGIS Server machine.\n'
        return None
    
    else:
        
        # Set variables from parameter values
        server = sys.argv[1]
        port = sys.argv[2]
        adminuser = sys.argv[3]
        password = sys.argv[4]
        exeType = sys.argv[5]
        targetFolder = None
        if len(sys.argv) == 7:
            targetFolder = sys.argv[6]
        
        # Process/validate variables
        if getfqdn().lower() <> server.lower().strip():
            print '\nThe specified "server" ' + server + ' is not the local machine ' + getfqdn().lower() + '. Exiting script.'
            return None
        
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
        
    return server, port, adminuser, password, doCopy, targetFolder

def extractFromSDFile(sdFile, extractFolder, fileToExtract=None):
    ''' Extract file from compressed .sd file '''
    
    sevenZipExePath = r'C:\Program Files\7-Zip\7z.exe'
    
    # 'Build' 7zip command line arguments
    # -y switch suppresses the overwrite user query if the file already exists.
    exeArgs = sevenZipExePath + ' e ' + sdFile + ' -o' + extractFolder + ' ' + fileToExtract + ' -y'
    print sectionBreak1
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
    ''' Return collection of ArcGIS Server services '''
    
    agsServices = {}
    
    # Get all services that exist on server
    allServices = getServiceList(server, port, adminuser, password)
    
    # Remove certain services from collection
    excludeServices = ['SampleWorldCities.MapServer']
    services = [service for service in allServices if service not in excludeServices]
    
    # Create dictionary from list of services; values are None.
    agsServices = dict.fromkeys(services)
    
    if debug:
        print "\nwithin get_ags_servides function:"
        print "agsServices:"
        print agsServices   
    
    return agsServices

def filesToCopy(sdFiles, agsServices):
    ''' Return collection of service definition files to copy '''
    
    # The service definition files that should be copied are those
    # that exist for each existing ArcGIS Server serice.
    sdFilesToCopy = {}
    for i in agsServices:
        if i in sdFiles:
            sdFilesToCopy[i] = sdFiles[i]
    
    if debug:
        print '\nwithin filesToCopy function:'
        print 'sdFilesToCopy variable...'
        for key, value in sdFilesToCopy.iteritems():
            print str(key) + ' = ' + str(value)
    
    return sdFilesToCopy

def copySDFiles(sdFilesToCopy, targetFolder):
    ''' Copy SD files to target folder '''
    
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
    print sectionBreak

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
    
def main():
    
    # Check arguments
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    server, port, adminuser, password, doCopy, targetFolder = results
    
    if debug:
        print server, port, adminuser, password, doCopy, targetFolder
    
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
 
    # Determine which sd files to copy
    sdFilesToCopy = filesToCopy(sdFiles, agsServices)
    
    # Copy sd files
    if doCopy:
        copySDFiles(sdFilesToCopy, targetFolder)
    
    # Print report
    report(sdFilesToCopy, agsServices)
    
    print '\nDone.'
    
if __name__ == "__main__":
    main()
