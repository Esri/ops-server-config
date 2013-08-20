#!/usr/bin/env python
import sys, os, time, traceback
from datetime import datetime

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

from AGSRestFunctions import getServiceList
from AGSRestFunctions import stopStartServices

validTypes = ["MapServer", "ImageServer", "GeometryServer", "GeocodeServer", "GPServer"]
userServiceStr = None
serviceList = None
scriptName = os.path.basename(sys.argv[0])

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------
serviceParam = '{folder//}service.type'

if len(sys.argv) < 7:
    print '\n' + scriptName + ' <Server_Name> <Server_Port> <User_Name> <Password> <Use_SSL: Yes|No> <Start|Stop> {' + serviceParam + ',...}'
    print '\nWhere:'
    print '\n\t<Server_Name> (required) server name.'
    print '\n\t<Server_Port> (required) server port; if not using server port enter #'
    print '\n\t<User_Name> (required) user with admin or publisher permission.'
    print '\n\t<Password> (required) user password.'
    print '\n\t<Use_SSL: Yes|No> (required) Flag indicating if ArcGIS Server requires HTTPS.'
    print '\n\t<Start|Stop> (required) action to perform.'
    
    print '\n\t{' + serviceParam + ',...} (optional) to Start|Stop specific services, specify'
    print '\t\tcomma delimited list of services using.'
    print '\t\tWhere:'
    print '\t\t\t{:<8}{}'.format('folder', '- (optional) is name of folder service resides')
    print '\t\t\t{:<8}{}'.format('service', '- (required) is name of service')
    print '\t\t\t{:<8}{}'.format('type', '- (required) is the type of of service; valid values are:')
    print '\t\t\t\t' + str(validTypes)
    print '\n\t\t\tNOTE: To include spaces in this list, surround with double-quotes.'
    
    print '\n\t\tExamples:'
    print '\t\t\tMyServices.MapServer'
    print '\t\t\tUtilities//Geometry.GeometryServer'
    print '\t\t\tMyServices.MapServer,Utilities//Geometry.GeometryServer'
    print '\t\t\t"MyServices.MapServer, Utilities//Geometry.GeometryServer"'
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
    serviceList = userServiceStr.replace(" ", ",").split(",")
    # if userServiceStr had more than one space between service values then there
    # will be 0-length string elements, so remove any elements with
    # 0-length strings.
    serviceList = [x for x in serviceList if len(x) > 0]
    
    # Make sure each service element has "." separator
    if len(serviceList) <> str(serviceList).count("."):
        print "Error: There are missing '.' delimiters between service name and type."
        sys.exit(1)
        
    # Make sure each service element has a valid service "type"
    notValidTypes = []
    for x in [x.split(".")[1].lower() for x in serviceList]:
        if x not in [y.lower() for y in validTypes]:
            notValidTypes.append(x)
    if len(notValidTypes) > 0:
        print "Error: You have specified invalid 'type' values: " + str(notValidTypes)
        print "Valid values are: " + str(validTypes)
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
    print "Valid actions are:" + str(validActionList)
    sys.exit(1)

try:
    startTime = datetime.now()
    totalSuccess = True
    
    # ---------------------------------------------------------------------
    # Print header
    # ---------------------------------------------------------------------
    print
    print "Start time: " + str(startTime)
    print
 
    # ---------------------------------------------------------------------
    # Get list of all services/or user specified list
    # ---------------------------------------------------------------------
    if not serviceList:
        serviceList = getServiceList(serverName, serverPort, userName, passWord, useSSL)
    
        # Append Geometry service to list
        serviceList.append(u'Utilities//Geometry.GeometryServer')
    
    if len(serviceList) == 0:
        print "\t*ERROR: No services to " + serviceAction.title() + "."
        
        
    # ---------------------------------------------------------------------
    # Start/Stop all services
    # ---------------------------------------------------------------------
    if len(serviceList) > 0:
        print "- Will attempt to " + serviceAction.lower() + " the following services..."
        for service in serviceList:
            print "\t" + service
        
        print "\n- Working..."
        stopStartServices(serverName, serverPort, userName, passWord, \
                          serviceAction.title(), serviceList, useSSL)
        
            
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
    endTime = datetime.now()
    print
    print "Done."
    print
    print "Start time: " + str(startTime)
    print "End time: " + str(endTime)