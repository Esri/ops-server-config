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
#               [{"searchID": "GUID", "replaceID": "GUID"}]
#
#==============================================================================
import sys
import os
import time
import traceback
import json

from portalpy import Portal
from portalpy import TEXT_BASED_ITEM_TYPES

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

from Utilities import validate_user_repsonse_yesno

import logging
logging.basicConfig()

search_key = 'search'
replace_key = 'replace'

def format_item_info(item):
    itemID = item.get('id')
    itemTitle = item.get('title')
    itemOwner = item.get('owner')
    itemType = item.get('type')

    return "Id: {:<34}Owner: {:<25}Type: {:25}Title: {:<40}".format(
                                    itemID, itemOwner, itemType, itemTitle)
    
def print_args():
    """ Print script arguments """

    if len(sys.argv) < 5:
        print '\n' + os.path.basename(sys.argv[0]) + \
                    ' <PortalURL>' \
                    ' <AdminUser>' \
                    ' <AdminUserPassword>' \
                    ' <IdMappingFile>' \
                    ' {SearchQuery}'
        print '\nWhere:'
        print '\n\t<PortalURL> (required): URL of Portal ' \
                    '(i.e. https://fully_qualified_domain_name/arcgis)'
        print '\n\t<AdminUser> (required): Primary portal administrator user.'
        print '\n\t<AdminUserPassword> (required): Password for AdminUser.'
        print '\n\t<IdMappingFile> (required): file containing item id ' \
                'mapping information in the following JSON form:'
        print '\t\t[{"searchID": "GUID", "replaceID": "GUID"}, {"searchID": "GUID", "replaceID": "GUID"},...]'
        print '\n\t{SearchQuery} (optional): Portal serach query.'
        return None
    else:
        # Set variables from parameter values
        portal_address = sys.argv[1]
        adminuser = sys.argv[2]
        password = sys.argv[3]
        id_mapping_file_path = None
        search_query = None
        
        if len(sys.argv) >= 5:
            id_mapping_file_path = sys.argv[4].strip()

        if len(sys.argv) >= 6:
            search_query = sys.argv[5].strip()


        return portal_address, adminuser, password, id_mapping_file_path, search_query

def update_item_properties(portal, item, search, replace):
    ''' Search/replace values in the item json properties '''
    
    jsonPropsToUpdate = ['description', 'snippet', 'accessInformation', 'licenseInfo', 'url']
    for jsonProp in jsonPropsToUpdate:
        is_updated = False
        propertyValue = item.get(jsonProp)
        if propertyValue:
            if propertyValue.find(search) > -1:
                propertyValue = propertyValue.replace(search, replace)
                is_updated = True
            
            if is_updated:
                portal.update_item(item['id'], {jsonProp: propertyValue}) 

def update_item_data(portal, item, search, replace):
    ''' Search/replace values in the item data '''

    if item['type'] in TEXT_BASED_ITEM_TYPES:
        
        try:
            itemdata = portal.item_data(item['id'])
        except Exception as err:
            print('ERROR: Exception: update_item_data function could not get item data for item: "{}"'.format(str(item.get('title'))))
            itemdata = None
        
        if itemdata:
            
            is_updated = False
        
            if itemdata.find(search) > -1:
                itemdata = itemdata.replace(search, replace)
                is_updated = True
            
            if is_updated:
                portal.update_item(item['id'], {'text': itemdata})     


def main():
    exit_err_code = 1
    starting_cwd = os.getcwd()
    
    # Print/get script arguments
    results = print_args()
    if not results:
        sys.exit(exit_err_code)
    portal_address, adminuser, password, id_mapping_file_path, search_query = results
    
    total_success = True
    title_break_count = 100
    section_break_count = 75
    
    print '=' * title_break_count
    print 'Update Portal GUIDs'
    print '=' * title_break_count

    if not os.path.exists(id_mapping_file_path):
         print '\nFile {} does not exist. Exiting.'.format(id_mapping_file_path)
         sys.exit(0)
            
    try:
        
        portal = Portal(portal_address, adminuser, password)
        
        print '\n{}'.format('-' * section_break_count)
        print '- Searching for portal items...\n'
        items = portal.search(q=search_query, sort_field='owner')
        
        for item in items:
            print format_item_info(item)
            
        print '\nFound {} items.'.format(len(items))

        if len(items) > 0:
            user_response = raw_input("\nDo you want to continue with the update? Enter 'y' to continue: ")
            if validate_user_repsonse_yesno(user_response):
                
                # Open id mapping file
                file_dir = os.path.dirname(id_mapping_file_path)
                file_name = os.path.basename(id_mapping_file_path)
                if len(file_dir) == 0:
                    file_dir = os.getcwd()
                os.chdir(file_dir)
                id_mapping = json.load(open(file_name))
                
                print '\n{}'.format('-' * section_break_count)
                print '- Updating item and item data...\n'
                for item in items:
                    print format_item_info(item)
                    for id_map in id_mapping:
                        search = id_map.get(search_key)
                        replace = id_map.get(replace_key)
                        update_item_properties(portal, item, search, replace)
                        update_item_data(portal, item, search, replace)
                    
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
        os.chdir(starting_cwd)
        print '\nDone.'
        if total_success:
            sys.exit(0)
        else:
            sys.exit(exit_err_code)

if __name__ == "__main__":
    main()


