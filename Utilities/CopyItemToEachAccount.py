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
#Name:          CopyItemToEachAccount.py
#
#Purpose:       Adds the specified item(s) to each portal account.
#
#               - If the item already exists in the user account (existence
#                 based on item title name, then existing item is updated).
#
#               - To exclude certain portal accounts from receiving the
#                 item, add the user account names to the "exlude_users"
#                 variable.
#
#==============================================================================
import sys
import os
import time
import traceback
import json
import tempfile
import shutil
sys.path.append(os.path.join(os.path.join(os.path.dirname(
                    os.path.dirname(sys.argv[0])), 'Publish'), 'Portal'))
from portalpy import Portal, provision
import PortalContentExtract

# Get script name
scriptName = sys.argv[0]

# Create list of users to exclude
exclude_users = ['admin', 
                'system_publisher',
                'DemoEManagement',
                'DemoIntelligence',
                'DemoLGovt',
                'DemoMilitary',
                'DemoNationalSecurity',
                'DemoParksGardens',
                'DemoSGovt',
                'DemoUtilities',
                'ReleasedEManagement',
                'ReleasedIntelligence',
                'ReleasedLGovt',
                'ReleasedMilitary',
                'ReleasedOpsServer',
                'ReleasedParksGardens',
                'ReleasedSGovt',
                'ReleasedUtilities',
                'TemplateIntelligence',
                'TemplateMilitary']

# Get currrent working directory
start_dir = os.getcwd()

# Set section break characteristics for print statements
sec_len = 75
sec_char = '-'

def check_args():
    # -----------------------------------------------------------------
    # Check arguments
    # -----------------------------------------------------------------
    if len(sys.argv) <> 5:
        print '\n' + scriptName + ' <PortalURL> <AdminUser> ' \
                    '<AdminUserPassword> <GUID{,GUID...}>'
        print '\nWhere:'
        print '\n\t<PortalURL> (required): URL of Portal ' \
                    '(i.e. https://fully_qualified_domain_name/arcgis)'
        print '\n\t<AdminUser> (required): Primary portal administrator user.'
        print '\n\t<AdminUserPassword> (required): Password for AdminUser.'
        print '\n\t<GUID{,GUID...}> (required): GUIDs of portal items to ' \
                    'add to other user accounts.'
        print '\n\nNOTE: The specified items will not be added to the following accounts:'
        print '\t{}\n'.format(exclude_users)
        return None
    else:
        # Set variables from parameter values
        portal_address = sys.argv[1]
        adminuser = sys.argv[2]
        password = sys.argv[3]
        guids = sys.argv[4]
        src_ids = [guid.strip() for guid in guids.split(',')]
        return portal_address, adminuser, password, src_ids

def validate_guids(portal, guids):
    invalid_guids = []
    for guid in guids:
        search_results = portal.search(q='id:{}'.format(guid))
        if len(search_results) == 0:
            invalid_guids.append(guid)
    return invalid_guids

def get_folder_name(portal, owner, folder_id):
    folder_name = None
    if folder_id:
        folders = portal.folders(owner)
        for folder in folders:
            if folder_id == folder['id']:
                folder_name = folder['title']
    return folder_name

def has_folder(portal, owner, folder_name):
    ''' Determines if folder already exists '''
    exists = False
    if folder_name:
        for folder in portal.folders(owner):
            if folder_name == folder['title']:
                exists = True
                break
    return exists

def main():
    output_root = None
    
    # Get script parameters
    results = check_args()
    if not results:
        sys.exit(0)
    portal_address, adminuser, password, src_ids = results
        
    try:        
        
        # Create portal connection object
        portal = Portal(portal_address, adminuser, password)
        
        # Check if any specified GUIDs do not exist
        invalid_guids = validate_guids(portal, src_ids)
        if len(invalid_guids) > 0:
            raise Exception(
                'ERROR: The following portal items do not exist: {}'.format(
                                                            invalid_guids))
        
        # Create list of users
        users = [org_user['username'] for org_user in portal.org_users()]
        target_users = [user for user in users if user not in exclude_users]
        
        # -----------------------------------------------------------------
        # Extract portal items
        # -----------------------------------------------------------------
        print '\n\n{}\nExtracting select portal items...\n{}\n'.format(
                                    sec_char * sec_len, sec_char * sec_len)
        
        # Create temporary extract folder in OS users' temp directory
        output_root = os.path.join(tempfile.gettempdir(), 
                                    os.path.basename(
                                    sys.argv[0]).split('.')[0] + '_Extract' )
        os.makedirs(output_root)
        
        print 'Extract folder: {}'.format(output_root)
        
        # Extract specified portal item(s)
        for src_id in src_ids:
            src_item = portal.item(src_id)
            os.chdir(output_root)
            print '- Extracting item {} "{}" ({}) user account {}...'.format(
                                    src_item['id'], src_item['title'],
                                    src_item['type'], src_item['owner'])
            PortalContentExtract.extract_item(
                                    portal, src_item['id'], 
                                    src_item['owner'])
        
        # Create list of paths to individual extracted portal item folders
        src_item_paths = [os.path.join(output_root, 
                                        src_id) for src_id in src_ids]
        
        # -----------------------------------------------------------------
        # Publish extracted portal items for each user
        # -----------------------------------------------------------------
        print '\n\n{}\nPublish extracted items to each portal' \
                    'user account...\n{}'.format(sec_char * sec_len,
                                                 sec_char * sec_len)
        print 'NOTE: not publishing to the following users:'
        print exclude_users
        
        for target_user in target_users:
            print '\n\nUser Account: {}'.format(target_user)
            
            # Get info about user folders
            target_user_folders = portal.folders(target_user)
            
            for src_item_path in src_item_paths:
                
                # Get info about the source item
                os.chdir(src_item_path)
                src_item_json = json.load(open('item.json'))
                item_title = src_item_json['title']
                item_type = src_item_json['type']
                item_id = src_item_json['id']
                item_owner = src_item_json['owner']
                item_folder_id = src_item_json['ownerFolder']
                
                # Create folder in user account for item
                item_folder_name = get_folder_name(portal, item_owner,
                                                   item_folder_id)
                if item_folder_name:
                    if not has_folder(portal, target_user, item_folder_name):
                        print 'Creating target folder "{}" in account ' \
                                '{}...'.format(item_folder_name, target_user)
                        portal.create_folder(target_user, item_folder_name)
                
                # Check if user already owns item
                user_items = portal.search(
                                q='owner:{} AND type:{} AND title:{}'.format(
                                target_user, item_type, item_title))
                
                # Add item if item does not exist in user account or 
                # update item if it already exists
                if len(user_items) == 0:
                    print '\n- Add item "{}" ({}) to user account {}...'.format(
                                        item_title, item_type,
                                        portal.logged_in_user()['username'])
                    item, orig_id = provision.load_item(portal, src_item_path)
                    
                    print '- Reassign item to user account {}, ' \
                                'folder "{}"...'.format(target_user,
                                                        item_folder_name)
                    portal.reassign_item(item.get('id'), target_user, item_folder_name)
                else:
                    for user_item in user_items:
                        if user_item['id'] <> item_id:
                            print '\n- Update existing item {} ' \
                                    '"{}" ({}) user account {}...'.format(
                                            user_item['id'], user_item['title'],
                                            user_item['type'], user_item['owner'])
                            item, orig_id = provision.load_item(
                                            portal, src_item_path, 
                                            user_item['id'])
                            
                            print '- Reassign item to user account {}, ' \
                                'folder "{}"...'.format(target_user,
                                                        item_folder_name)
                            portal.reassign_item(item.get('id'), target_user, item_folder_name)
                            
                        else:
                            print '*** No need to update item {}; ' \
                                    'user is owner of extracted item.'.format(
                                    user_item['id'])
        print '\n\nDone.'
        
    except:
        
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
        
        # Change directory to starting directory, otherwise the
        # delete will fail.
        os.chdir(start_dir)
        
        # Delete temp extracted folder/files
        if output_root:
            if os.path.exists(output_root):
                shutil.rmtree(output_root)

if __name__ == "__main__":
    main()
