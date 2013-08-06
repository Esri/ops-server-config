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
                    "operationsgep":[False, "OperationsGEP"], \
                    "rtds":[False, "RTDS"]}


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

# Make sure the dictionary key value matches the registered data store path value
# minus the '/fileShares/' part of the path. The publishing scripts use this
# key to find the existing registered folder data store to extract the
# server path.
installOnlyPublishingFolders = {"OpsEnvironment": r"\\afmcomstaging\data"}

# ----------------------------------------------------------------------------
# Set root path variables/root path functions

postgreSQLRootPath = makePath("C", ["Program Files", "PostgreSQL"])

def getOpsServerRootPath(dataDrive):
    return makePath(dataDrive, ["OpsServer"])

def getEnvDataRootPath(dataDrive):
    opsServerRootPath = getOpsServerRootPath(dataDrive)
    return os.path.join(opsServerRootPath, *["Environment", "Data"])

def getDBConnFileRootPath(dataDrive):
    opsServerRootPath = getOpsServerRootPath(dataDrive)
    return os.path.join(opsServerRootPath, *["Environment", "DBConnections"])

def getCacheRootPath(cacheDrive):
    return makePath(cacheDrive, ["arcgisserver", "arcgiscache"])
