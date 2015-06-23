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
#Name:          ValidateHostedServiceSources.py
#
#Purpose:       -Checks if each hosted service has an associated source item.
#               -Checks if each source item has an associated hosted service.
#               -Checks if owners of hosted service/source item match.
#
#               NOTE: currently only validates service definition source items.
#==============================================================================
import sys
import os
import traceback
import json
import logging
import time
import tempfile
import shutil

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(
    sys.argv[0])), 'SupportFiles'))
sys.path.append(os.path.join(os.path.join(os.path.dirname(
    os.path.dirname(sys.argv[0])), 'Publish'), 'Portal'))

from portalpy import Portal
from GetSDFiles import extractFromSDFile
from Utilities import findFilePath
from FindOrphanedHostedServices import get_hosted_service_items

def print_args():
    """ Print script arguments """

    if len(sys.argv) < 4:
        print '\n' + os.path.basename(sys.argv[0]) + \
                    ' <PortalURL>' \
                    ' <AdminUser>' \
                    ' <AdminUserPassword>'
        print '\nWhere:'
        print '\n\t<PortalURL> (required): URL of Portal ' \
                    '(i.e. https://fully_qualified_domain_name/arcgis)'
        print '\n\t<AdminUser> (required): Primary portal administrator user.'
        print '\n\t<AdminUserPassword> (required): Password for AdminUser.'
        return None
    else:
        # Set variables from parameter values
        portal_address = sys.argv[1]
        adminuser = sys.argv[2]
        password = sys.argv[3]

        return portal_address, adminuser, password


def main():
    exit_err_code = 1
    
    # Print/get script arguments
    results = print_args()
    if not results:
        sys.exit(exit_err_code)
    portal_address, adminuser, password = results
    
    total_success = True
    title_break_count = 100
    section_break_count = 75
    search_query = None
    
    print '=' * title_break_count
    print 'Validate Hosted Service Sources'
    print '=' * title_break_count
    
    source_items = []
    hosted_items = []
    
    root_folder_path = None
    root_folder_path = tempfile.mkdtemp()
    print 'Temporary directory: {}'.format(root_folder_path)
    
    orig_dir = os.getcwd()
    
    try:
        portal = Portal(portal_address, adminuser, password)
        items = portal.search()
        
        # ---------------------------------------------------------------------
        #  Get info about hosted service source items
        # (currently service definitions)
        # ---------------------------------------------------------------------
        
        for item in items:
            
            if item['type'] == 'Service Definition':
                
                print '\nDownloading and extracting Service Definition item {}'.format(item['id'])
                
                # Download .sd file
                download_root_path = os.path.join(root_folder_path, item['id'])
                os.mkdir(download_root_path)
                download_path = portal.item_datad(item['id'], download_root_path)
                
                # Extract serviceconfiguration.json file from downloaded .sd file
                file_name = 'serviceconfiguration.json'
                extract_path = download_path.replace('.sd', '')
                #print extract_path
                os.mkdir(extract_path)
                err_stat = extractFromSDFile(download_path, extract_path, file_name)
                print 'Extract status: {}'.format(err_stat)
        
                # Open extract .json file
                file_path = findFilePath(extract_path, file_name)
                os.chdir(os.path.dirname(file_path))
                service_config = json.load(open(file_name))
                
                # [{id: val, owner: val, title: val, type: val
                # service_config: {stuff from .json file}}]
                d = {
                    'id': item['id'],
                    'owner': item['owner'],
                    'title': item['title'],
                    'type': item['type'],
                    'service_config': service_config
                    }
                source_items.append(d)

        # ---------------------------------------------------------------------
        # Get info about hosted service items
        # ---------------------------------------------------------------------
        print '\nDetermine what hosted services exist...'
        h_service_items = get_hosted_service_items(portal, items)
        
        for item in h_service_items:
            d = {
                'id': item['id'],
                'owner': item['owner'],
                'title': item['title'],
                'type': item['type'],
                'url': item['url']
                }
            hosted_items.append(d)

        # ---------------------------------------------------------------------
        # For each hosted service find the associated source item
        # ---------------------------------------------------------------------
        print '=' * section_break_count
        print '\nDetermine which source items are associated with each hosted service...'
        print '=' * section_break_count
        num_hosted_no_match = 0
        num_hosted_match = 0
        num_hosted_mismatch_owner = 0
        write_str = "\tid: {:<34}owner: {:<20}type: {:<25}service: {:<50}\n"
        
        for hosted_d in hosted_items:
            found = False
            found_num = 0
            
            # Get last components of URL (i.e., SRTM_V2_56020/FeatureServer)
            hosted_url = '/'.join(hosted_d['url'].split('/')[-2:])
            
            print '\n{}'.format('-' * 100)
            print 'Hosted Service Item:   Title - "{}"\n'.format(hosted_d['title'])
            
            hosted_str = write_str.format(
                hosted_d['id'],
                hosted_d['owner'],
                hosted_d['type'],
                hosted_url)
            print hosted_str
            
            # Look for match in source items
            print '\tMatching Source Item:'

            for source_d in source_items:
                src_service_info = source_d['service_config']['service']
                src_service_name = src_service_info['serviceName']
                src_service_type = src_service_info['type']
                src_service_url = '{}/{}'.format(src_service_name, src_service_type)
                if hosted_url == src_service_url:
                    found = True
                    found_num += 1
        
                    match_str = write_str.format(
                        source_d['id'],
                        source_d['owner'],
                        source_d['type'],
                        src_service_url)
                    print '\n\tTitle: "{}"'.format(source_d['title'])
                    print match_str
                    
                    if source_d['owner'] != hosted_d['owner']:
                        print '*** ERROR: owner does not match hosted service item owner.'
                        num_hosted_mismatch_owner += 1
                        
            if found_num == 0:
                print '*** ERROR: no matching source item found.'
            if found_num > 1:
                print '*** ERROR: there is more then one matching source item found.'
                
            if found:
                num_hosted_match += 1
            else:
                num_hosted_no_match += 1
    

        # ---------------------------------------------------------------------
        # For each source item find the associated hosted service
        # ---------------------------------------------------------------------
        print '=' * section_break_count
        print '\nDetermine which hosted services are associated with each source item...'
        print '=' * section_break_count
        num_source_no_match = 0
        num_source_match = 0
        num_source_mismatch_owner = 0
        write_str = "\tid: {:<34}owner: {:<20}type: {:<25}service: {:<50}\n"
        
        for source_d in source_items:
            found = False
            found_num = 0
        
            src_service_info = source_d['service_config']['service']
            src_service_name = src_service_info['serviceName']
            src_service_type = src_service_info['type']
            src_service_url = '{}/{}'.format(src_service_name, src_service_type)
                
                
            print '\n{}'.format('-' * 100)
            print 'Source Item:   Title - "{}"\n'.format(source_d['title'])
            
            source_str = write_str.format(
                source_d['id'],
                source_d['owner'],
                source_d['type'],
                src_service_url)
            print source_str
            
            # Look for match in source items
            print '\tMatching Hosted Service:'
        
            for hosted_d in hosted_items:
        
                # Get last components of URL (i.e., SRTM_V2_56020/FeatureServer)
                hosted_url = '/'.join(hosted_d['url'].split('/')[-2:])
            
                if hosted_url == src_service_url:
                    found = True
                    found_num += 1
        
                    match_str = write_str.format(
                        hosted_d['id'],
                        hosted_d['owner'],
                        hosted_d['type'],
                        hosted_url)
                    print '\n\tTitle: "{}"'.format(hosted_d['title'])
                    print match_str
            
                    if hosted_d['owner'] != source_d['owner']:
                        print '*** ERROR: owner does not match associated source owner.'
                        num_source_mismatch_owner += 1
                        
            if found_num == 0:
                print '*** ERROR: no matching hosted service found.'
            if found_num > 1:
                print '*** ERROR: there is more then one hosted service found.'
                
            if found:
                num_source_match += 1
            else:
                num_source_no_match += 1

        print '\n{}'.format('=' * section_break_count)
        print 'Summary:\n'
        print 'Number of hosted services: {}'.format(len(hosted_items))
        print 'With matching source item: {}'.format(num_hosted_match)
        print 'With NO matching source item: {}'.format(num_hosted_no_match)
        print 'With mis-matching owners: {}'.format(num_hosted_mismatch_owner)

        print '\nNumber of source items: {}'.format(len(source_items))
        print 'With matching hosted service: {}'.format(num_source_match)
        print 'With NO matching hosted service: {}'.format(num_source_no_match)        
        print 'With mis-matching owners: {}'.format(num_source_mismatch_owner)
        
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
        os.chdir(orig_dir)
        if root_folder_path:
            shutil.rmtree(root_folder_path)
            
        print '\nDone.'
        if total_success:
            sys.exit(0)
        else:
            sys.exit(exit_err_code)

if __name__ == "__main__":
    main()


