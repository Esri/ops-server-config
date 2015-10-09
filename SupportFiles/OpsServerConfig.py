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
#Name:      OpsServerConfig.py
#
#Purpose:   Sets various variables used by other installation scripts.
#
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
databasesToCreate = {"tds":[False, "TDS"], \
                    "intelfoundation":[False, "IntelFoundation"], \
                    "physicalnetworks":[False, "PhysicalNetworks"], \
                    "humint":[False, "HUMINT"], \
                    "imint":[False, "IMINT"], \
                    "sigint":[False, "SIGINT"], \
                    "allsource":[False, "AllSource"], \
                    "intelassessments":[False, "IntelAssessments"], \
                    "currentoperations":[False, "CurrentOperations"], \
                    "military":[False, "Military"]}

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
publishingDBServer = "my_db_server"
publishingFolder = r"\\my_data_server\root_data_folder"

# 'Registration Name' for data folder data store
dataFolderDStoreName = "OpsServerData"

# 'Publishing' path for temporary folder data stores
# Key is name of server where data folder is located; Value is path to "data" folder
installOnlyPublishingFolders = {"my_data_server1": r"\\my_data_server1\root_data_folder", "my_data_server2": r"\\my_data_server2\root_data_folder"}

# 'Publishing' server names for temporary database data stores
installOnlyPublishingDBServers = ["my_db_server1", "my_db_server2"]

# ----------------------------------------------------------------------------
# Set root path variables/root path functions

def getPostgreSQLRootPath():
    try:
        postgreSQLRootPath = os.environ['ops_postgresqlInstallDIR']
        return postgreSQLRootPath
    except KeyError, e:
        return None

def getOpsServerRootPath(dataDrive):
    return makePath(dataDrive, ["OpsServer"])

def getEnvDataRootPath(dataDrive):
    opsServerRootPath = getOpsServerRootPath(dataDrive)
    return os.path.join(opsServerRootPath, *["Data"])

def getDBConnFileRootPath(dataDrive):
    opsServerRootPath = getOpsServerRootPath(dataDrive)
    return os.path.join(opsServerRootPath, *["DBConnections"])

def getCacheRootPath(cacheDrive):
    return makePath(cacheDrive, ["arcgisserver", "directories", "arcgiscache"])

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

    # If user specified "all" then return list containing only this value
    if ops_type_all.lower() in specified_values:
        values_to_use = list(valid_ops_types)
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
