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
#Name:          PrepItemsForExtract.py
#
#Purpose:       Prepare portal items for extract:
#               - Add "Hosted Service" tag to hosted service items
#
#==============================================================================
import sys
import os
import traceback
import logging

from portalpy import Portal
from FindOrphanedHostedServices import get_hosted_service_items

logging.basicConfig()
    
def format_hosted_item_info(item):
    itemID = item.get('id')
    itemTitle = item.get('title')
    itemOwner = item.get('owner')
    itemType = item.get('type')
    itemURL = item.get('url')
    service = itemURL.split('/Hosted/')[1]

    return "Id: {:<34}Owner: {:<22}Type: {:<17}URL: {:<50}Title: {:<30}".format(
                                    itemID, itemOwner, itemType, service, itemTitle)

def format_item_info(item):
    itemID = item.get('id')
    itemTitle = item.get('title')
    itemOwner = item.get('owner')
    itemType = item.get('type')

    return "Id: {:<34}Owner: {:<25}Type: {:25}Title: {:<40}".format(
                                    itemID, itemOwner, itemType, itemTitle)
    
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
    print 'Prepare Items for Extract'
    print '=' * title_break_count
            
    try:
        
        portal = Portal(portal_address, adminuser, password)
        
        items = portal.search(q=search_query, sort_field='owner')
        
        # ---------------------------------------------------------------------
        # Prepare hosted service items
        # ---------------------------------------------------------------------
        # Add new tag to hosted service so we can identify the original
        # hosted service after the portal items are published to a new portal
        
        new_tags = ['Hosted Service']
        
        print '\n{}'.format('-' * section_break_count)
        print '- Prepare Hosted Service Items (Add tags: {})...'.format(', '.join(new_tags))
        
        items_to_prep = get_hosted_service_items(portal, items)
        
        for item_to_prep in items_to_prep:
            print '\n    {}'.format(format_hosted_item_info(item_to_prep))
            tags = item_to_prep.get('tags')
            for new_tag in new_tags:
                if new_tag not in tags:
                    tags.append(new_tag)
            # NOTE: have to pass new tags as string and not as a list
            resp = portal.update_item(item_to_prep['id'], {'tags':', '.join(tags)})
            if not resp:
                print '***ERROR encountered during "update_item".'
                total_success = False
                               
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


