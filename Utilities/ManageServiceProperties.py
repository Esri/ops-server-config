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
#Name:          ManageServiceProperties.py
#
#Purpose:       Updates service properties based on values in Properties_File file.
#
#               1) Execute script using default REPORT option to create Properties_File
#               2) Edit service property values in Properties_File
#               3) Execute script using UPDATE option
#
#               Properties updated by script are:
#                   clusterName
#                   minInstancesPerNode
#                   maxInstancesPerNode
#
#               NOTE: Hosted services are excluded from update since
#                   properties of these services should not be updated.
#==============================================================================
import sys
import os
import traceback
import json
import logging
import time

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(
    sys.argv[0])), 'SupportFiles'))

from AGSRestFunctions import getServiceList
from AGSRestFunctions import getServiceInfo
from AGSRestFunctions import parseService
from AGSRestFunctions import editServiceInfo
from AGSRestFunctions import getClusters

# Defines which service json properties this script will update.
UPDATABLE_SERVICE_PROPERTIES = frozenset([
    'clusterName',
    'minInstancesPerNode',
    'maxInstancesPerNode'
    ])

# Defines valid script options
VALID_OPTIONS = frozenset([
    'REPORT',
    'UPDATE'
    ])

def print_args():
    """ Print script arguments """
    
    if len(sys.argv) < 7:
        print '\n' + os.path.basename(sys.argv[0]) + \
            ' <Server_FullyQualifiedDomainName>' + \
            ' <Server_Port>' + \
            ' <User_Name>' + \
            ' <Password>' + \
            ' <Use_SSL: Yes|No>' + \
            ' <Properties_File>' + \
            ' {Service_Property_Option}'
    
        print '\nWhere:'
        print '\n\t<Server_FullyQualifiedDomainName> (required): the fully qualified domain name of the ArcGIS Server machine.'
        print '\n\t<Server_Port> (required): the port number of the ArcGIS Server (specify # if no port).'
        print '\n\t<User_Name> (required): ArcGIS Server for ArcGIS site administrator.'
        print '\n\t<Password> (required): Password for ArcGIS Server for ArcGIS site administrator user.'
        print '\n\t<Use_SSL: Yes|No> (required) Flag indicating if ArcGIS Server requires HTTPS.'
        print '\n\t<Properties_File> (required) Path to file containing service properties.'
        print '\n\t{{Service_Property_Option}} (optional) {}'.format('|'.join(VALID_OPTIONS))
        print '\t\tREPORT: (default) - write service properties to Properties_File.'
        print '\t\tUPDATE: updates service properties based on contents of Properties_File.'
        print '\n\tNOTE: The following services properties can be reported/updated:'
        print '\t\t{}'.format(', '.join(UPDATABLE_SERVICE_PROPERTIES))
        return None
    
    else:
        
        # Set variables from parameter values
        server = sys.argv[1]
        port = sys.argv[2]
        adminuser = sys.argv[3]
        password = sys.argv[4]
        use_ssl = sys.argv[5]
        file_path = sys.argv[6]
        option = 'REPORT'
        
        if port.strip() == '#':
            port = None
        
        if use_ssl.strip().lower() in ['yes', 'ye', 'y']:
            use_ssl = True
        else:
            use_ssl = False
        
        if len(sys.argv) >= 8:
            option = sys.argv[7].upper()
            if option not in VALID_OPTIONS:
                print 'Specified "Service_Property_Option" parameter value is invalid.'
                return None
        
        if option == 'UPDATE':
            if not os.path.exists(file_path):
                print 'Specified "Service_Property_File" does not exist.'
                return None
                
    return server, port, adminuser, password, use_ssl, file_path, option

def read_file(file_path):
    
    # Read contents of file
    file_contents = []
    in_f = open(file_path, 'r')
    for line in in_f:
        file_contents.append(line.rstrip('\n'))
    in_f.close()

    return file_contents


def validate_file_contents(file_contents):
    
    valid = True

    for line in file_contents:
        try:
            line_json = json.loads(line)
        except:
            valid = False
            print 'ERROR: The following JSON structure is invalid: {}'.format(line)

    return valid

def main():
    exit_err_code = 1
    
    # Print/get script arguments
    results = print_args()
    if not results:
        sys.exit(exit_err_code)
    server, port, adminuser, password, use_ssl, file_path, option = results
    
    total_success = True
    title_break_count = 100
    section_break_count = 75
    search_query = None
    
    print '=' * title_break_count
    print 'ManageServiceProperties ({})'.format(option)
    print '=' * title_break_count
    
    clusters = getClusters(server, port, adminuser, password, use_ssl)
    cluster_names = [cluster['clusterName'] for cluster in clusters]

    try:
        services = getServiceList(server, port, adminuser, password, use_ssl)
        services = [service.replace('//', '/') for service in services]
        
        # Properties of hosted services should not be altered; remove hosted
        # services from the services list
        services = [x for x in services if x.find('Hosted/') == -1]
    
        # ---------------------------------------------------------------------
        # Report service properties
        # ---------------------------------------------------------------------
        if option == "REPORT":
            
            f = open(file_path, 'w')
            
            print 'Writing service property information to file (excluding hosted services)...\n'
            
            for service in services:
                folder, servicename_type = parseService(service)
                service_info = getServiceInfo(server, port, adminuser, password, folder, servicename_type, use_ssl)
                
                # Don't write service info if service is associated
                # with gp service. Service is edited through gp service.
                parent_name = service_info['properties'].get('parentName')
                if parent_name:
                    if parent_name.find('.GPServer') > -1:
                        continue
        
                write_str = '{{"service": "{}", "properties": {{"clusterName": "{}", "minInstancesPerNode": {}, "maxInstancesPerNode": {}}}}}\n'
                write_str = write_str.format(
                        service,
                        service_info['clusterName'],
                        service_info['minInstancesPerNode'],
                        service_info['maxInstancesPerNode']
                        )
                f.write(write_str)
            f.close
        
        # ---------------------------------------------------------------------
        # Update/Edit service properties
        # ---------------------------------------------------------------------
        if option == "UPDATE":
            
            file_contents = read_file(file_path)
            if not validate_file_contents(file_contents):
                raise Exception('File {} is not valid. Exiting script.'.format(file_path))
            
            for line in file_contents:
                print '\n{}'.format('-' * 90)
                line_json = json.loads(line)
                mod_service = line_json['service']
                mod_service_props = line_json['properties']
                print mod_service
                
                if mod_service.find('Hosted/') > -1:
                    print '\n\tWARNING: Skipping update. Hosted service properties should not be updated.'
                    continue
                
                if mod_service not in services:
                    print '\n\tWARNING: Can not find specified service: {}. Skipping update.\n'.format(mod_service)
                    continue
                
                # Get the current service properties
                folder, servicename_type = parseService(mod_service)
                service_info = getServiceInfo(server, port, adminuser, password, folder, servicename_type, use_ssl)
        
                # Don't write service info if service is associated
                # with gp service. Service is edited through gp service.
                parent_name = service_info['properties'].get('parentName')
                if parent_name:
                    if parent_name.find('.GPServer') > -1:
                        '\n\tWARNING: Can not edit service associated with GP service. Skipping update.\n'
                        continue
                
                # Print the original and new service property values.
                # Also check if properties have actually changed.
                print '\t{:<25}: {:<20}{:<5}{:<20}'.format('', 'Orig. Value', '', 'New Value')
                has_changes = False
                is_valid = True
                for prop in mod_service_props.keys():
                    
                    if mod_service_props[prop] != service_info[prop]:
                        has_changes = True
                    print '\t{:<25}: {:<20}{:<5}{:<20}'.format(prop, service_info[prop], '', mod_service_props[prop])
                    
                    # Validate 'clusterName'
                    if prop == 'clusterName':
                        if mod_service_props[prop] not in cluster_names:
                            is_valid = False
                            print '***ERROR: Value for property "{}": "{}" is NOT valid. Skipping update.'.format(prop, mod_service_props[prop])
                
                    # Validate that specific properties are numeric
                    if prop in ['minInstancesPerNode', 'minInstancesPerNode']:
                        if not isinstance(mod_service_props[prop], (int)):
                            is_valid = False
                            print '***ERROR: Value for property "{}": {} is NOT integer. Skipping update.'.format(prop, mod_service_props[prop])
                    
                if not is_valid:
                    continue
                
                if not has_changes:
                    print '\n\tWARNING: no changes to service properties. Skipping update.\n'
                    continue
                
                # Update the service properties from the contents of the file
                for prop in mod_service_props.keys():
                    service_info[prop] = mod_service_props[prop]
                
                # Save the service properties to the service
                print '\n\tSaving updates to service.'
                success, status = editServiceInfo(server, port, adminuser, password, folder, servicename_type, service_info)
                if success:
                    print '\tDone.'
                else:
                    total_success = False
                    print '**** ERROR: Update of service was not successful.'
                    print 'status: ' + str(status)
            
                time.sleep(15)
                
    except:
        total_success = False
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
     
        # Concatenate information together concerning the error 
        # into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + \
                "\nError Info:\n" + str(sys.exc_info()[1])
        
        # Print Python error messages for use in Python / Python Window
        print
        print "***** ERROR ENCOUNTERED *****"
        print pymsg + "\n"
        
    finally:
        print '\nDone.'
        if total_success:
            sys.exit(0)
        else:
            sys.exit(exit_err_code)

if __name__ == "__main__":
    main()


