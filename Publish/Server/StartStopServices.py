#!/usr/bin/env python
import sys, os, time, traceback
from datetime import datetime

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

from AGSRestFunctions import getServiceList
from AGSRestFunctions import stopStartServices

scriptName = os.path.basename(sys.argv[0])

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------   
if len(sys.argv) <> 6:
    print "\n" + scriptName + " <Server_Name> <Server_Port> <User_Name> <Password> <Start|Stop>"
    print "\nWhere:"
    print "\n\t<Server_Name> (required parameter) server name."
    print "\n\t<Server_Port> (required parameter) server port; if not using server port enter '#'"
    print "\n\t<User_Name> (required parameter) user that admin or publisher permission."
    print "\n\t<Password> (required parameter) user password."
    print "\n\t<Start|Stop> (required parameter) action to perform."
    print
    sys.exit(1)

serverName = sys.argv[1]
serverPort = sys.argv[2]
userName = sys.argv[3]
passWord = sys.argv[4]
serviceAction = sys.argv[5]

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
    print "===================================================================================="
    print serviceAction.title() + " all services on server"
    print "===================================================================================="
    print "Start time: " + str(startTime)
    print
 
    # ---------------------------------------------------------------------
    # Get list of all services
    # ---------------------------------------------------------------------
    serviceList = getServiceList(serverName, serverPort, userName, passWord)
    
    # Append Geometry service to list
    serviceList.append(u'Utilities//Geometry.GeometryServer')
    
    if len(serviceList) == 0:
        print "\t*ERROR: No services to " + serviceAction.title() + "."
        
        
    # ---------------------------------------------------------------------
    # Start/Stop all services
    # ---------------------------------------------------------------------
    if len(serviceList) > 0:
        print "- Found the following services..."
        print
        for service in serviceList:
            print "\t" + service
        print
        print
        print "- Attempting to " + serviceAction.lower() + " the services listed above..."
        print
        stopStartServices(serverName, serverPort, userName, passWord, \
                          serviceAction.title(), serviceList)
        
            
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