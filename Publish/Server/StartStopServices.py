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
#Name:          StartStopServices.py
#           
#Purpose:       Starts or stops ArcGIS Server services.
#
#==============================================================================
import sys, os, time, traceback
from datetime import datetime
totalSuccess = True

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

from AGSRestFunctions import getServiceList
from AGSRestFunctions import stopStartServices
from AGSRestFunctions import getServiceStatus

validTypes = ["MapServer", "ImageServer", "GeometryServer", "GeocodeServer",
              "GPServer", "FeatureServer", "GlobeServer", "GeoDataServer"]
userServiceStr = None
serviceList = None
scriptName = os.path.basename(sys.argv[0])

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------

if len(sys.argv) < 7:
    print '\n' + scriptName + ' <Server_Name> <Server_Port> <User_Name> <Password> <Use_SSL: Yes|No> <Start|Stop> {{folder/}service.type,...| Service_List_File}'
    print '\nWhere:'
    print '\n\t<Server_Name> (required) server name.'
    print '\n\t<Server_Port> (required) server port; if not using server port enter #'
    print '\n\t<User_Name> (required) user with admin or publisher permission.'
    print '\n\t<Password> (required) user password.'
    print '\n\t<Use_SSL: Yes|No> (required) Flag indicating if ArcGIS Server requires HTTPS.'
    print '\n\t<Start|Stop> (required) action to perform.'
    
    print '\n\t{{folder/}service.type,...| Service_List_File} (optional) to Start|Stop specific services, specify'
    print '\t\tcomma delimited list of services or specify a path to a file containing {{folder/}service.type entries.'
    print '\t\tIf specifying file, each {{folder/}service.type entry must be on a separate line.'
    
    print '\n\t\tWhere:'
    print '\t\t\t{:<8}{}'.format('folder', '- (optional) is name of folder service resides')
    print '\t\t\t{:<8}{}'.format('service', '- (required) is name of service')
    print '\t\t\t{:<8}{}'.format('type', '- (required) is the type of of service; valid values are:')
    print '\t\t\t\t' + str(validTypes)
    print '\n\t\t\tNOTE: To include spaces in this list, surround with double-quotes.'
    
    print '\n\t\tExamples:'
    print '\t\t\tMyServices.MapServer'
    print '\t\t\tUtilities/Geometry.GeometryServer'
    print '\t\t\tMyServices.MapServer,Utilities/Geometry.GeometryServer'
    print '\t\t\t"MyServices.MapServer, Utilities/Geometry.GeometryServer"\n'
    sys.exit(1)

serverName = sys.argv[1]
serverPort = sys.argv[2]
userName = sys.argv[3]
passWord = sys.argv[4]
useSSL = sys.argv[5]
serviceAction = sys.argv[6]
if len(sys.argv) == 8:
    userServiceStr = sys.argv[7]

if useSSL.strip().lower() in ['yes', 'ye', 'y']:
    useSSL = True
else:
    useSSL = False
    
# Perform some checks on the user specified service list
if userServiceStr is not None:
    
    serviceList = []
    
    # Read in the user specified serivces
    if os.path.exists(userServiceStr):
        # User has specified a path; make sure it's a file
        if not os.path.isfile(userServiceStr):
            print "Error: The specified Service_List_File " + userServiceStr + " is not a file.\n"
            sys.exit(1)

        f = open(userServiceStr, 'r')
        for service in f:
            serviceList.append(service.strip())
        f.close()
        if len(serviceList) == 0:
            print "Error: The specfied Service_List_File " + userServiceStr + " is empty.\n"
            sys.exit(1)
    else:
        serviceList = userServiceStr.replace(" ", ",").split(",")
    
    # if userServiceStr had more than one space between service values then there
    # will be 0-length string elements, so remove any elements with
    # 0-length strings.
    serviceList = [x for x in serviceList if len(x) > 0]
    
    # Make sure each service element has "." separator
    if len(serviceList) <> str(serviceList).count("."):
        print "Error: There are missing '.' delimiters between service name and type.\n"
        sys.exit(1)

    # Make sure each service element has a valid service "type"
    notValidTypes = []
    for x in [x.split(".")[1].lower() for x in serviceList]:
        if x not in [y.lower() for y in validTypes]:
            notValidTypes.append(x)
    if len(notValidTypes) > 0:
        print "Error: You have specified invalid 'type' values: " + str(notValidTypes)
        print "Valid values are: " + str(validTypes) + "\n"
        sys.exit(1)

if serverPort.strip() == '#':
    serverPort = None
            
validActionList = ["stop", "start"]
isActionValid = False

# Check if user specific valid actions
for validAction in validActionList:
    if validAction.lower() == serviceAction.lower():
        isActionValid = True
        break
if not isActionValid:
    print "User specified action '" + serviceAction + " is not valid."
    print "Valid actions are:" + str(validActionList) + "\n"
    sys.exit(1)

try:
    startTime = datetime.now()
 
    # ---------------------------------------------------------------------
    # Get list of all services/or user specified list
    # ---------------------------------------------------------------------
    if not serviceList:
        serviceList = getServiceList(serverName, serverPort, userName, passWord, useSSL)

    # Remove hosted services from list since these can't be started/stopped
    print '\nRemoving "Hosted" services from service list; these services can not be started/stopped.'
    serviceList = [x for x in serviceList if x.find('Hosted/') == -1]
    
    if len(serviceList) == 0:
        print "\t*ERROR: No services to " + serviceAction.title() + "."
        
    # ---------------------------------------------------------------------
    # Filter the service list and remove services that are already at the requested state
    # ---------------------------------------------------------------------
    
    if len(serviceList) > 0:
        
        actionStatusMap = {"STOP":"STOPPED", "START":"STARTED"}
        modServiceList = []
    
        print "\n{}".format("-" * 110)
        print "- Check status of specified services...\n"
        
        for service in serviceList:
            folder = None
            serviceNameAndType = service
            service = service.replace("//", "/")
            if service.find("/") > 0:
                folder = service.split("/")[0]
                serviceNameAndType = service.split("/")[1]
            
            serviceStatus = getServiceStatus(serverName, serverPort, userName, passWord, folder, serviceNameAndType, useSSL)
            realTimeState = serviceStatus.get("realTimeState")
            if realTimeState:
                if realTimeState.upper() == actionStatusMap[serviceAction.upper()]:
                    print "{:.<70}already at requested state '{}'.".format(service, realTimeState)
                else:
                    print "{:.<70}will {} the service.".format(service, serviceAction.lower())
                    modServiceList.append(service)
            else:
                print "{:.<70}{}".format(service, serviceStatus)

        
    # ---------------------------------------------------------------------
    # Start/Stop all services
    # ---------------------------------------------------------------------
    if len(modServiceList) > 0:
        print "\n{}".format("-" * 110)
        print "- Will attempt to " + serviceAction.lower() + " the specified services...\n"
        
        stopStartServices(serverName, serverPort, userName, passWord, \
                          serviceAction.title(), modServiceList, useSSL)
        
            
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
    endTime = datetime.now()
    print
    print "Done."
    print
    print "Start time: " + str(startTime)
    print "End time: " + str(endTime)
    if totalSuccess:
        sys.exit(0)
    else:
        sys.exit(1)