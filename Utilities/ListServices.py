#!/usr/bin/env python
#------------------------------------------------------------------------------
# Copyright 2015 Esri
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
#Name:          ListServices.py
#           
#Purpose:       Output list of services in specified ArcGIS Server site.
#
#==============================================================================
import sys, os, traceback, datetime, ast, copy, json

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), 'SupportFiles'))

from AGSRestFunctions import getServiceList
#from AGSRestFunctions import getServiceManifest

scriptName = os.path.basename(sys.argv[0])
exitErrCode = 1
debug = False
sectionBreak = '=' * 175
sectionBreak1 = '-' * 175


def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) <> 6:
        
        print '\n' + scriptName + ' <Server_FullyQualifiedDomainName> <Server_Port> <User_Name> <Password> <Use_SSL: Yes|No>'
    
        print '\nWhere:'
        print '\n\t<Server_FullyQualifiedDomainName> (required): the fully qualified domain name of the ArcGIS Server machine.'
        print '\n\t<Server_Port> (required): the port number of the ArcGIS Server (specify # if no port).'
        print '\n\t<User_Name> (required): ArcGIS Server for ArcGIS site administrator.'
        print '\n\t<Password> (required): Password for ArcGIS Server for ArcGIS site administrator user.'
        print '\n\t<Use_SSL: Yes|No> (required) Flag indicating if ArcGIS Server requires HTTPS.\n'
        return None
    
    else:
        
        # Set variables from parameter values
        server = sys.argv[1]
        port = sys.argv[2]
        adminuser = sys.argv[3]
        password = sys.argv[4]
        useSSL = sys.argv[5]
        
        if port.strip() == '#':
            port = None
        
        if useSSL.strip().lower() in ['yes', 'ye', 'y']:
            useSSL = True
        else:
            useSSL = False
        
    return server, port, adminuser, password, useSSL

def main():
    
    totalSuccess = True
    
    # -------------------------------------------------
    # Check arguments
    # -------------------------------------------------
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    server, port, adminuser, password, useSSL = results
    
    if debug:
        print server, port, adminuser, password, useSSL
    
    try:            
        # ------------------------------------------------- 
        # Get all services that exist on server
        # -------------------------------------------------
        if useSSL:
            protocol = 'https'
        else:
            protocol = 'http'
            
        allServices = getServiceList(server, port, adminuser, password)
        
        # Remove certain services from collection
        #excludeServices = ['SampleWorldCities.MapServer']
        excludeServices = []
        services = [service for service in allServices if service not in excludeServices]
        services = [service.replace('//', '/') for service in allServices]
        
        if len(services) == 0:
            raise Exception('ERROR: There are no user published ArcGIS Server services. Have you published the ArcGIS Server services?')
        
        # -------------------------------------------------
        # List service workspaces
        # -------------------------------------------------
        numServices = len(services)
        i = 0
        
        for service in services:
            i += 1
            print service
        #print 'Total: {}'.format(i)
                    
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
