#!/usr/bin/env python
#==============================================================================
#Name:      OpsServerConfig.py
#Purpose:   Sets various variables used by other installation scripts.
#
#History:   Fixed CR 239,138 08/03/2012 - "Modify OpsServerConfig.py script to
#               automatically obtain the fully qualified domain name of the
#               server." Replaced "platform" module with "socket" module, and
#               used getfqdn and gethostname functions.
#
#           Fixed CR 239,142 "Alter default value for "sharing" variables.
#               Change to False."
#==============================================================================
import os
import socket
from Utilities import makePath

valid_ops_types = ['All', 'Land', 'Maritime', 'Intel', 'Air', 'NG']

# ----------------------------------------------------------------------------
# Server name/domain/port related information

# Get server name without domain, i.e. mymachine
serverName = socket.gethostname().lower()

# Get server name with domain, i.e. mymachine.esri.com
serverFullyQualifiedDomainName = socket.getfqdn().lower()

# Get domain name, i.e. esri.com
serverDomain = serverFullyQualifiedDomainName.replace(serverName, "")[1:]

# Set ArcGIS Server port number
serverPort = 6080

serverDrive = 'c'       # Drive where software will be installed

# ----------------------------------------------------------------------------
# "Name of database": True/False - Flag indicating whether database
#   will be registered with ArcGIS Server as managed.
# Also SDE connection files will be created for all databases not registered
# as managed.
# NOTE: only one database should be registered as managed

# Syntax: ["databasename": [Managed (True or False), AGS registration name]
# 'AGS registration name' is "label" given to the data store.
databasesToCreate = {"operations":[True,"Operations"], \
                    "utds":[False, "UTDS"], \
                    "economic":[False, "Economic"], \
                    "imagery":[False, "Imagery"], \
                    "infrastructure":[False, "Infrastructure"], \
                    "physical":[False, "Physical"], \
                    "political":[False, "Political"], \
                    "social":[False, "Social"], \
                    "rtds":[False, "RTDS"], \
                    "currentoperations":[False, "CurrentOperations"], \
                    "military":[False, "Military"], \
                    "information":[False, "Information"], \
                    "workflow":[False, "Workflow"]}


# ----------------------------------------------------------------------------
# Shared / Replicated Database Configuration
#
# Set with database configuration used during publishing.
# Set to True if you want to use shared configuration (i.e
# publisher databases and ArcGIS Server databases are the same );
# Set to False if you want to use a replicated configuration
# (i.e. publisher database is different then the ArcGIS
# Server database)
sharedDataStoreConfig = True

# Set following variable to which server containing the
# publisher database. Variable only used when
# variable "sharedDBConfigForPublishing" = False
publishingDBServer = "afmcomstaging"
publishingFolder = r"\\disldb\development\Commercial\OPSServer\LandOps\Server\Staging\Data"

# 'Registration Name' for data folder data store
dataFolderDStoreName = "OpsServerData"

# Make sure the dictionary key value matches the registered data store path value
# minus the '/fileShares/' part of the path. The publishing scripts use this
# key to find the existing registered folder data store to extract the
# server path.
installOnlyPublishingFolders = {dataFolderDStoreName: r"\\afmcomstaging\data"}

# ----------------------------------------------------------------------------
# Set root path variables/root path functions

postgreSQLRootPath = os.environ['ops_postgresqlInstallDIR']

def getOpsServerRootPath(dataDrive):
    return makePath(dataDrive, ["OpsServer"])

def getEnvDataRootPath(dataDrive):
    opsServerRootPath = getOpsServerRootPath(dataDrive)
    return os.path.join(opsServerRootPath, *["Data"])

def getDBConnFileRootPath(dataDrive):
    opsServerRootPath = getOpsServerRootPath(dataDrive)
    return os.path.join(opsServerRootPath, *["DBConnections"])

def getCacheRootPath(cacheDrive):
    return makePath(cacheDrive, ["arcgisserver", "arcgiscache"])

# ----------------------------------------------------------------------------
# Other functions

def validateOpsTypes(specified_ops_types):
    
    is_valid = True
    values_to_use = []
    ops_type_all = "all"
    
    # Create copy of valid value list (so we can alter values) and convert to lower case
    valid_values = [element.lower().strip() for element in list(valid_ops_types)]
    
    # Convert user specified list of ops types to list and convert
    # to lower case and remove any leading or trailing "whitespace"
    # this handles cases where user entered spaces between
    # values i.e. "Land, Maritime".
    specified_values = [element.lower().strip() for element in specified_ops_types.split(",")]
    
    #print "specified_values: " + str(specified_values)

    # If user specified "all" then return list containing only this value
    if ops_type_all.lower() in specified_values:
        #values_to_use.append(ops_type_all.lower())
        values_to_use = list(valid_ops_types)
        #print "values_to_use:  " + str(values_to_use)
        return True, values_to_use
    
    # Check if user specified valid ops types
    for ops_type in specified_values:
        if ops_type not in valid_values:
            return False, values_to_use
        values_to_use.append(ops_type)
    
    # If the user has specified at least one valid value then add "all" to list
    # so that the load function will publish items that have the "all" to addition
    # to the items with the other tags specified.
    if len(values_to_use) > 0:
        values_to_use.append(ops_type_all)
        
    return is_valid, values_to_use

def hasOpsTypeTags(find_tags, tags_to_search):
    '''Determines if specific "OpsServer" values exist in list of tags'''
    found = False
    
    DEBUG = False
    
    # Create list of possible "OpsServer" type tag prefixes; i.e. in case someone didn't
    # specify the correct prefix.
    ops_type_flags = ["opsserver", "opsservers", "opserver", "opservers", "opssrver", "opssrvr"]
    
    # Convert find_tags to lower case and remove and leading/trailing spaces
    find_tags_mod = [element.lower().strip().encode("ascii") for element in list(find_tags)]
    
    # Convert tags_to_search to lower case and remove and leading/trailing spaces
    tags_to_search_mod = [element.lower().strip().encode("ascii") for element in list(tags_to_search)]
    
    if DEBUG:
        print "In tags_exist function: "
        print "\tfind_tags_mod: " + str(find_tags_mod)
        print "\ttags_to_search_mod: " + str(tags_to_search_mod)
        print "\tops_type_flags: " + str(ops_type_flags)
    
    # Loop through tags to search and look for the find tags
    for search in tags_to_search_mod:
        search = search.replace(" ","")
        
        if DEBUG:
            print "\tsearch: " + search
            
        if search.find(":") > -1:
            
            if DEBUG:
                print "\tI'm in the find : if statement"
                
            element1 = search.split(":")[0]
            element2 = search.split(":")[1]
            
            if DEBUG:
                print "\t\telement1: " + element1
                print "\t\telement2: " + element2
                
            if element1 in ops_type_flags:
                if element2 in find_tags_mod:
                    found = True
                    
    if DEBUG:
        print "\tfound: " + str(found)
        
    return found