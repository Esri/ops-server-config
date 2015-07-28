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
#Name:          FindOrphanedHostedServices.py
#
#Purpose:       Lists the hosted services, and "orphanded" hosted services,
#               and if there are any "orphanced" hosted services determines
#               the item mapping back to original. Writes this item mapping
#               to a file in the following JSON form:
#               [{"search": "GUID", "replace": "GUID"}]
#
#==============================================================================
import sys
import os
import time
import traceback
import json

from portalpy import Portal
from PublishHostedServices import find_orig_service_item_id

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

from Utilities import validate_user_repsonse_yesno

import logging
logging.basicConfig()

delete_option_values = ['NO_DELETE', 'DELETE']

search_key = 'search'
replace_key = 'replace'

def format_item_info(item):
    itemID = item.get('id')
    itemTitle = item.get('title')
    itemOwner = item.get('owner')
    itemType = item.get('type')
    itemURL = item.get('url')
    service = itemURL.split('/Hosted/')[1]

    return "Id: {:<34}Owner: {:<25}Type: {:<20}URL: {}".format(
                                    itemID, itemOwner, itemType, service)
    
def print_args():
    """ Print script arguments """

    if len(sys.argv) < 4:
        print '\n' + os.path.basename(sys.argv[0]) + \
                    ' <PortalURL>' \
                    ' <AdminUser>' \
                    ' <AdminUserPassword>' \
                    ' {delete_orphaned_items}'
        print '\nWhere:'
        print '\n\t<PortalURL> (required): URL of Portal ' \
                    '(i.e. https://fully_qualified_domain_name/arcgis)'
        print '\n\t<AdminUser> (required): Primary portal administrator user.'
        print '\n\t<AdminUserPassword> (required): Password for AdminUser.'
        print '\n\t{delete_orphaned_items} (optional): ' + \
                                ' | '.join(delete_option_values)
        return None
    else:
        # Set variables from parameter values
        portal_address = sys.argv[1]
        adminuser = sys.argv[2]
        password = sys.argv[3]
        delete_option = False
        if len(sys.argv) >= 5:
            delete_option = sys.argv[4].strip().upper()
            if delete_option not in delete_option_values:
                print '\nInvalid "delete_orphaned_items" parameter value "{}".'.format(delete_option)
                print 'Must be one of the following values: {}'.format(', '.join(delete_option_values))
                return None
            if delete_option == 'DELETE':
                delete_option = True

        return portal_address, adminuser, password, delete_option

def get_hosted_service_items(portal, items=None):
    '''
    Return all hosted service items.
    If "items" is specified, function will return
    subset of "items" that are hosted service items.
    '''
    hosted_service_items = []
    if items is None:
        items = portal.search()
    for item in items:
        if 'Hosted Service' in item['typeKeywords']:
            hosted_service_items.append(item)
    return hosted_service_items    

def get_orphaned_hosted_service_items(portal):
    
    p_hosted_service_items = []
    items = portal.search()
    for item in items:
        url = item.get('url')
        if url:
            if url.find('/Hosted/') > -1 and \
                    'Hosted Service' not in item['typeKeywords'] and \
                                            'Hosted Service' in item['tags']:
                p_hosted_service_items.append(item)
    return p_hosted_service_items

def create_search_replace_id_map(portal):
    '''
    Maps orphaned hosted service item to hosted service item.
    Returns list of dictionary objects containing searchID/replaceID
    key/value pairs
    '''
    item_mapping = []
    
    o_hosted_service_items = get_orphaned_hosted_service_items(portal)
    hosted_service_items = get_hosted_service_items(portal)
    
    if len(o_hosted_service_items) > 0 and len(hosted_service_items) > 0:
        for hosted_service_item in hosted_service_items:
            orig_new_info = {}
            o_service_item_id = find_orig_service_item_id(portal, hosted_service_item['id'])
            if not o_service_item_id:
                continue
            orig_new_info[search_key] = o_service_item_id
            orig_new_info[replace_key] = hosted_service_item['id']
            item_mapping.append(orig_new_info)
    
    return item_mapping

def main():
    exit_err_code = 1
    
    # Print/get script arguments
    results = print_args()
    if not results:
        sys.exit(exit_err_code)
    portal_address, adminuser, password, delete_option = results
    
    total_success = True
    title_break_count = 150
    section_break_count = 100
    
    print '=' * title_break_count
    print 'Find Hosted Services'
    print '=' * title_break_count
    
    try:
        file_name = 'hosted_service_item_mapping.json'
        if os.path.exists(file_name):
            os.remove(file_name)
                
        portal = Portal(portal_address, adminuser, password)
        
        print '\n{}'.format('-' * section_break_count)
        print '- Searching for hosted service items...'
        hosted_service_items = get_hosted_service_items(portal)
        
        print '- Found {} hosted service items:'.format(len(hosted_service_items))
        for hosted_service_item in hosted_service_items:
            print format_item_info(hosted_service_item)
        
        print '\n{}'.format('-' * section_break_count)
        print '- Searching for orphaned hosted service items...'
        o_hosted_service_items = get_orphaned_hosted_service_items(portal)
        
        print '- Found {} orphaned hosted service items:'.format(len(o_hosted_service_items))
        for o_hosted_service_item in o_hosted_service_items:
            print format_item_info(o_hosted_service_item)
        
        print '\n{}'.format('-' * section_break_count)
        print '- Map orphaned hosted service item to hosted service item...'
        item_mapping = create_search_replace_id_map(portal)
        if len(item_mapping) == 0:
            print 'No orphaned service items to map.'
            
        if len(item_mapping) > 0:
            for hosted_service_item in hosted_service_items:
                orphanedID = 'NOT FOUND'
                for id_map in item_mapping:
                    if hosted_service_item['id'] == id_map[replace_key]:
                        orphanedID = id_map[search_key]
                print format_item_info(hosted_service_item) + \
                                ' ***[OrphanedID: {}]'.format(orphanedID)
            
            print '\nNOTE: item mapping info written to file "{}" in directory: {}'.format(file_name, os.getcwd())
            json.dump(item_mapping, open(file_name,'w'))
        
        if len(o_hosted_service_items) > 0 and delete_option:
            print '\n{}'.format('-' * section_break_count)
            print '- You selected to delete orphaned hosted service items.'
            print '  Will delete the following items...'
            
            for o_hosted_service_item in o_hosted_service_items:
                print format_item_info(o_hosted_service_item)
        
            user_response = raw_input("\nDo you want to continue with the delete? Enter 'y' to continue: ")
    
            if validate_user_repsonse_yesno(user_response):
                for o_hosted_service_item in o_hosted_service_items:
                    print 'Deleting...'
                    print '\t{}'.format(format_item_info(o_hosted_service_item))
                    resp = portal.delete_item(o_hosted_service_item['id'])
                    print resp
                
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


