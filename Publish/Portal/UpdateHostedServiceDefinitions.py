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
#Name:          UpdateHostedServiceDefinitions.py
#           
#Purpose:       Update hosted feature service definitions (i.e. service Sync,
#               Tracking, Export and edting properties) using JSON file
#               created by WriteHostedServiceDefinitions.py.
#
#==============================================================================
import sys
import os
import time
import traceback
import json
from datetime import datetime
totalSuccess = True

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

from AGSRestFunctions import updateHostedFeatureServiceDefinition

scriptName = os.path.basename(sys.argv[0])
exitErrCode = 1

def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) < 7:
        
        print '\n' + scriptName + ' <Server_FullyQualifiedDomainName> <Server_Port> <User_Name> <Password> <Use_SSL: Yes|No> <Hosted_Service_Definition_File>'
    
        print '\nWhere:'
        print '\n\t<Server_FullyQualifiedDomainName> (required): the fully qualified domain name of the ArcGIS Server machine.'
        print '\n\t<Server_Port> (required): the port number of the ArcGIS Server (specify # if no port).'
        print '\n\t<User_Name> (required): ArcGIS Server for ArcGIS site administrator.'
        print '\n\t<Password> (required): Password for ArcGIS Server for ArcGIS site administrator user.'
        print '\n\t<Use_SSL: Yes|No> (required): Flag indicating if ArcGIS Server requires HTTPS.'
        print '\n\t<Hosted_Service_Definition_File> (required) the json file containing the hosted service definitions (created by WriteHostedServiceDefintions.py).'
        return None
    
    else:
        
        # Set variables from parameter values
        server = sys.argv[1]
        port = sys.argv[2]
        adminuser = sys.argv[3]
        password = sys.argv[4]
        use_ssl = sys.argv[5]
        input_file  = sys.argv[6]

        if port.strip() == '#':
            port = None
        
        if use_ssl.strip().lower() in ['yes', 'ye', 'y']:
            use_ssl = True
        else:
            use_ssl = False
        
        if not os.path.isfile(input_file):
            print '\nERROR: The <Hosted_Service_Definition_File> path {} does not exist or is not a file. Exiting script.\n'.format(input_file)
            return None

    return server, port, adminuser, password, use_ssl, input_file

def main():
    
    totalSuccess = True
    
    # -------------------------------------------------
    # Check arguments
    # -------------------------------------------------
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    server, port, adminuser, password, use_ssl, input_file = results
    
    if use_ssl:
        protocol = 'https'
    else:
        protocol = 'http'
            
    try:
        
        os.chdir(os.path.dirname(input_file))
        definitions = json.load(open(os.path.basename(input_file)))

        print '\n{}'.format('=' * 80)
        print 'Updating service definition information for hosted feature services'
        print '(i.e. editing, sync, export, tracking properties)'
        print '{}\n'.format('=' * 80)
        
        total_num = len(definitions.keys())
        n = 0
        for service in definitions.keys():
            n = n + 1
            print '-' * 80
            print 'Service: {} ({} out of {})'.format(service, n, total_num)
            
            definition = definitions[service]['updateDefinition']
            
            success, status = updateHostedFeatureServiceDefinition(server, port, adminuser, password, service, definition, use_ssl)
            print 'Update successful: {}'.format(success)
            if not success:
                totalSuccess = False
                print 'ERROR: {}'.format(status)
        
        print '\n\nDone executing {}.\n'.format(scriptName)
        
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
            sys.exit(exitErrCode)
        
        
if __name__ == "__main__":
    main()
