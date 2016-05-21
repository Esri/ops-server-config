#!/usr/bin/env python
#------------------------------------------------------------------------------
# Copyright 2016 Esri
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
#Name:          WriteHostedSceneServiceDefinitions.py
#           
#Purpose:       Output JSON file of all hosted scene service definitions
#               (i.e. /rest/services/Hosted/"service"/SceneServer)
#
#==============================================================================
import sys
import os
import traceback
import datetime
import ast
import copy
import json
 
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), 'SupportFiles'))

from AGSRestFunctions import getServiceList
from AGSRestFunctions import getServiceJSON
from AGSRestFunctions import parseService
from AGSRestFunctions import getServicePortalProps

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), 'Publish', 'Portal'))
from portalpy import Portal


scriptName = os.path.basename(sys.argv[0])
exitErrCode = 1
debug = False
sectionBreak = '=' * 175
sectionBreak1 = '-' * 175


def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) < 7:
        
        print '\n' + scriptName + ' <Server_FullyQualifiedDomainName> <Server_Port> <User_Name> <Password> <Use_SSL: Yes|No> <Output_Folder> {Owners}'
    
        print '\nWhere:'
        print '\n\t<Server_FullyQualifiedDomainName> (required): the fully qualified domain name of the ArcGIS Server machine.'
        print '\n\t<Server_Port> (required): the port number of the ArcGIS Server (specify # if no port).'
        print '\n\t<User_Name> (required): ArcGIS Server for ArcGIS site administrator.'
        print '\n\t<Password> (required): Password for ArcGIS Server for ArcGIS site administrator user.'
        print '\n\t<Use_SSL: Yes|No> (required): Flag indicating if ArcGIS Server requires HTTPS.'
        print '\n\t<Output_Folder> (required): Path and name of folder to write scene service definition files.'
        print '\n\t{Owners} (optional) list of owners to filter (only info for services owned by these accounts'
        print '\t\twill be written to output file).'
        print '\n\t\t- List must be comma delimited list (spaces can be included after commas, but list'
        print '\t\t  must be enclosed by quotes).'
        print '\t\t- Owner names are case sensitive.'
        return None
    
    else:
        
        # Set variables from parameter values
        server = sys.argv[1]
        port = sys.argv[2]
        adminuser = sys.argv[3]
        password = sys.argv[4]
        use_ssl = sys.argv[5]
        output_folder  = sys.argv[6]
        
        owners = None
        if len(sys.argv) > 7:
            owners = sys.argv[7]
            owners = owners.replace(' ', '').split(',')
 
        if port.strip() == '#':
            port = None
        
        if use_ssl.strip().lower() in ['yes', 'ye', 'y']:
            use_ssl = True
        else:
            use_ssl = False
        
    return server, port, adminuser, password, use_ssl, output_folder, owners

def get_invalid_owners(portal, owners):
    invalid_users = []
    if owners:
        org_users = portal.org_users()
        users = [org_user['username'] for org_user in org_users]
        invalid_users = [owner for owner in owners if owner not in users]
    return invalid_users
    
def main():
    
    totalSuccess = True
    
    # -------------------------------------------------
    # Check arguments
    # -------------------------------------------------
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    server, port, adminuser, password, use_ssl, output_folder, owners = results
    
    if debug:
        print server, port, adminuser, password, use_ssl, output_folder, owners
    
    if use_ssl:
        protocol = 'https'
    else:
        protocol = 'http'
            
    try:
        
        # Create connection to portal; need to get service item owner information
        portal = Portal('https://' + server + ':7443/arcgis', adminuser, password)
        
        # Verify if user specify owners exist
        invalid_owners = get_invalid_owners(portal, owners)
        
        if len(invalid_owners) > 0:
            print '\nThe following owners do not exist. Exiting script: \n{}'.format(', '.join(invalid_owners))
            totalSuccess = False
        
        else:
            
            # Get all services that exist on server
            all_services = getServiceList(server, port, adminuser, password)
            all_services = [service.replace('//', '/') for service in all_services]
            
            # Create collection of only hosted services
            print '\n{}'.format('=' * 80)
            print 'Extracting scene service definition information for hosted scene services'
            print 'that meet criteria.'
            print '{}\n'.format('=' * 80)
            
            total_scene_services = 0
            total_files_created = 0
            
            for service in all_services:
                folder, serviceNameType = parseService(service)

                if serviceNameType.endswith('.SceneServer'):
                    total_scene_services += 1
                    print '-' * 80
                    print 'Service: {}'.format(service)
                    
                    portal_props = getServicePortalProps(server, port, adminuser, password, folder, serviceNameType)
                    
                    if portal_props:
                        if portal_props['isHosted']:
                            portal_items = portal_props['portalItems']
                            for portal_item in portal_items: #NOTE: for hosted services there should only be one portal item
                                do_write = True
                                
                                item_id = portal_item['itemID']
                                item = portal.item(item_id)
                                
                                if item is None:
                                    print '\tPortal item {} for service does not exist.'.format(item_id)
                                    item_owner = None
                                else:
                                    item_owner = item['owner']
                                    item_title = item['title']
                                    
                                print 'Item id: {}, Owner: {}, Title: {}'.format(item_id, item_owner, item_title)
                                
                                if owners:
                                    if item_owner not in owners:
                                        do_write = False
                                
                                if do_write:
                                    
                                    service_json = getServiceJSON(server, port, adminuser, password, folder, serviceNameType)
                                    
                                    definition = {}
                                    definition['name'] = item_title
                                    definition['serviceDescription'] = service_json
                                    
                                    output_file = os.path.join(output_folder, serviceNameType.replace('.SceneServer', '') + '_sceneserver.json')
                                    
                                    # Write info to json file
                                    print '\nWriting "definition" to file {}'.format(output_file)
                                    json.dump(definition, open(output_file,'w'))
                                    total_files_created += 1
                                
                                else:
                                    print 'Does not meet criteria. Will not write "definition" file.'
        print '-' * 80
        print '\nTotal number of scene services: {}'.format(total_scene_services)
        print 'Total number of scene service definition files created: {}'.format(total_files_created)
        print '\nDone.\n'
        
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
