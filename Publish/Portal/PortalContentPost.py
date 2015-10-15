#------------------------------------------------------------------------------
# Copyright 2014 Esri
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
#Name:          PortalContentPost.py
#           
#Purpose:       Publishes portal content that was extracted with the
#               PortalContentExtract.py script.
#
#==============================================================================
import os, sys

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilesPath = os.path.join(
    os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles")
sys.path.append(supportFilesPath)

import portalpy
import json
import urlparse
import types
import shutil
from datetime import datetime, timedelta
from portalpy import Portal, parse_hostname, portal_time, WebMap, normalize_url, unpack, TEXT_BASED_ITEM_TYPES
from portalpy.provision import load_items, load_item
from Utilities import findInFile, editFiles
import logging
import copy
from Utilities import findFilePath

logging.basicConfig()

# For now hard-code the server name of the source ArcGIS Server machine
source_hostname = "my_source_portal.domain"
new_hostname = ""
new_port = None #Use 6080 or None

hostname_map = {}

DEBUG = False

titleBreak = "====================================================================================="
sectionBreak = "------------------------------------------------------------------------------------"
sectionBreak2 = "--------------------"
portal_processing = "POST"
portalLogFolder = "PortalPostLogs"
users = {}

#track stored IDs to new IDs when posting groups
originGroupToDestGroups = {}

#EL track new group id and the group name
destGroupID_GroupName = {}

# Store original item id and new item id
origIDToNewID = {}

def main():

    scriptName = sys.argv[0]

    specified_users = None
    #specified_ops_types = None
    specified_groups = None
    id_mapping_file = None
    
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------   
    if len(sys.argv) < 5:
        print '\n' + scriptName + ' <PortalURL> <AdminUser> <AdminPassword> ' + \
                    '<ContentFolderPath> {UsersToPost} {GroupsToPost} {IdMappingFile}'
        print '\nWhere:'
        print '\n\t<PortalURL> (required): URL of Portal to post content (i.e. https://fully_qualified_domain_name/arcgis)'
        
        print '\n\t<AdminUser> (required): Portal user that has administrator role.'
        
        print '\n\t<AdminPassword> (required): Password for AdminUser.'
        
        print '\n\t<ContentFolderPath> (required): Folder path containing portal content to post.'
        
        print '\n\t{UsersToPost} (optional):'
        print '\t\t-By default, content for all users is posted'
        print '\t\t-Specify # placeholder character if you want to post content for all users and you are'
        print '\t\t   specifying {GroupsToPost} values'
        print '\t\t-To post content for only specific users specify comma delimited list of users, i.e. user1,user2,...'
        print '\t\t-To post content for ALL users except specific users, specify comma delimited '
        print '\t\t   list of users to exclude with "-" prefix, i.e. -user1,user2,...'
        print '\t\t-NOTE: Users names must match the "SourceUserName" values in the <ContentFolderPath>\userfile.txt file.'
 
        print '\n\t{GroupsToPost} (optional):'
        print '\t\t-To post content shared with specific portal groups specify a pipe "|" delimited list of groups using the syntax "GroupOwner:GroupTitle|GroupOwner:GroupTitle|...".'
        print '\t\t-Specify # placeholder character if you do not want to use this parameter and need to specify the {IdMappingFile} parameter value.'
        print '\t\t-NOTE: GroupOwner and GroupTitle values are case sensitive.'
        print '\t\t-NOTE: Parameter value MUST be surrounded by double-quotes.'
        
        print '\n\t{IdMappingFile} (optional): JSON file containing mapping between source and target portal item ids.'
        print '\t\t-Provides "overwrite" capability. If IdMappingFile is specified, the script will'
        print '\t\t   update any item that already exists; items that do not exist will be added.'
        
        print '\n\tNOTES:'
        print '\t\t(1) To include spaces in any of the parameter lists, surround the list with double-quotes,'
        print '\t\t i.e., "value1, value2, ..."'
        
        print '\n\t\t(2) Replacement of portal item URLs:'
        print '\t\t\t-This script will replace the host names in URLs in service, webmap and operation view items; '
        print '\t\t\t the script is hardcoded to replace the source hostname "' + source_hostname + '" with the '
        print '\t\t\t hostname of the target portal server <PortalURL>; i.e., this script assumes that the target'
        print '\t\t\t ArcGIS Server is installed on the target portal machine.'
        sys.exit(1)
    
    
    # Set variables from script parameters
    target_portal_address = sys.argv[1]
    adminuser = sys.argv[2]
    adminpassword = sys.argv[3]
    contentpath = sys.argv[4]
    if len(sys.argv) > 5:
        specified_users = sys.argv[5]
    if len(sys.argv) > 6:
        specified_groups = sys.argv[6]
        specified_groups = [group.strip() for group in specified_groups.split('|')]
    if len(sys.argv) > 7:
        id_mapping_file = sys.argv[7]
    if len(sys.argv) > 8:
        print "You entered too many script parameters."
        sys.exit(1)
        
    if DEBUG:
        print "target_portal_address: " + str(target_portal_address)
        print "adminuser: " + str(adminuser)
        print "adminpassword: " + str(adminpassword)
        print "contentpath: " + str(contentpath)
        if specified_users:
            print "specifiedUsers: " + str(specified_users)
        if specified_groups:
            print "specifiedOpsTypes: " + str(specified_groups)
        if id_mapping_file:
            print "id_mapping_file: " + str(id_mapping_file)
    
    
    # Check if specified content folder exists.
    if not val_arg_content_path(contentpath):
        print "Parameter <ContentFolderPath>: folder '" + contentpath + "' does not exist."
        sys.exit(1)
    
    # Check if specified users are valid
    users = val_arg_users(specified_users, contentpath)
    
    if DEBUG:
        print "Users to publish: " + str(users.keys())
    
    # Check if specified id mapping file exists
    if id_mapping_file:
        if not os.path.exists(id_mapping_file):
            print "Parameter {IdMappingFile}: folder '" + id_mapping_file + "' does not exist."
    
    # Extract target ArcGIS Server hostname from target portal URL;
    # NOTE: this script assumes that the ArcGIS Server is installed
    # on the same machine as Portal for ArcGIS
    new_hostname =  parse_hostname(target_portal_address)
    hostname_map = {source_hostname: new_hostname}
        
    # Publish content to target portal
    publish_portal(target_portal_address, contentpath, adminuser, adminpassword, users, hostname_map, specified_groups, id_mapping_file)
    
    os.chdir(contentpath)
    
    

def print_script_header(portal, portal_processing, users, specified_groups):
    print titleBreak
    print "                               Portal Content " + portal_processing
    print titleBreak
    print "Processing type: \t\t\t" + portal_processing
    print "Portal URL: \t\t\t\t" + portal.url
    print "Signed in as: \t\t\t\t" + portal.logged_in_user()['username'] + " (Role: " + portal.logged_in_user()['role'] + ")"
    print "Posting content for users: \t\t" + str(users.keys())
    print "Posting items shared with the following groups:"
    print str(specified_groups)

    
#POST
def publish_portal(portaladdress,contentpath,adminuser,adminpassword, users, hostname_map, specified_groups, id_mapping_file):
    os.chdir(contentpath)
    
    portal_properties = json.load(open("portal_properties.json"))
    portaladmin = Portal(portaladdress, adminuser, adminpassword)
    
    print_script_header(portaladmin, portal_processing, users, specified_groups)

    # Create Portal log folder for this portal
    portalLogPath = os.path.join(contentpath, portalLogFolder, get_servername_from_url(portaladmin.url))
    makeFolder(portalLogPath)
    
    # ------------------------------------------------------------------------
    # Get info about the groups on disk to filter items based on group membership
    # ------------------------------------------------------------------------
    # Get the groups on disk
    grps_on_disk = get_groups_on_disk(contentpath)
    
    # Validate that each specified group is valid
    if specified_groups:
        invalid_specified_groups = []
        for specified_group in specified_groups:
            found = False
            for grp in grps_on_disk.itervalues():
                if specified_group == grp:
                    found = True
            if not found:
               invalid_specified_groups.append(specified_group)
               
        if len(invalid_specified_groups) > 0:
            print '\n***ERROR: the following specified groups do not exist; NOTE: group owner and group title must match exactly including case:\n'
            print invalid_specified_groups
            return
    
    # ------------------------------------------------------------------------
    # Create users
    # ------------------------------------------------------------------------
    print titleBreak
    print 'Create users...\n'
   
    # Only create users if this is not an online organization
    if portaladmin.properties()['id'] == '0123456789ABCDEF': # All portals have this id.
        for username, userinfo in users.iteritems():
           create_user(portaladmin, contentpath, userinfo)
    else:
        print '\tThis is an online organization. Users must already have been created.'

    # ------------------------------------------------------------------------
    # Create user folders
    # ------------------------------------------------------------------------
    print '\n'+ titleBreak
    print 'Create user folders...\n'
    
    for username, userinfo in users.iteritems():
       print '\nUser: ' + userinfo['target_username']
       create_user_folders(portaladmin, contentpath, userinfo)

    # ------------------------------------------------------------------------
    # Create groups and add users to groups
    # ------------------------------------------------------------------------
    print "\n" + titleBreak
    print "Creating groups ...\n"
    
    oldGrpID_newGrpID = {}
    for username, userinfo in users.iteritems():
        newGroups = publish_user_groups(portaladmin, contentpath, userinfo, users)
        
        for key,val in newGroups.iteritems():
            oldGrpID_newGrpID[key] = {'id': val}
    
    # ------------------------------------------------------------------------
    # Publish Items and Update their sharing info
    # ------------------------------------------------------------------------
    print "\n" + titleBreak
    print "Publishing items and setting sharing ..."
    print titleBreak
    
    for username, userinfo in users.iteritems():
        
        username = userinfo['target_username']
        password = userinfo['target_password']
        userfoldername = userinfo['username']
        
        # ---------------------------------------
        # Publish all the users' items
        # ---------------------------------------
        usercontentpath = os.path.join(contentpath, userfoldername)
        
        newItems, origItemSourceIDs = publish_user_items(portaladmin, username, usercontentpath, source_hostname,
                                new_hostname, new_port, specified_groups, id_mapping_file, grps_on_disk)
        
        # Dump info about new items to JSON to use for resetting IDs of related items
        dump_newItem_info(newItems, origItemSourceIDs, os.path.join(portalLogPath, username))
        
        # ---------------------------------------
        # Share the users' items with the
        # appropriate groups
        # ---------------------------------------
        userItemsPath = os.path.join(contentpath, userfoldername, "items")
        share_items(portaladmin, userItemsPath, newItems, origItemSourceIDs, originGroupToDestGroups)
    
    
    # Dump info about all items (old, new ids) into json
    os.chdir(portalLogPath)
    json.dump(origIDToNewID, open('oldID_newID.json','w'))
    json.dump(oldGrpID_newGrpID, open('oldGrpID_newGrpID.json', 'w'))

    # ------------------------------------------------------------------------
    # Post publishing processing: Update URLs and item ids
    # ------------------------------------------------------------------------
    print "\n" + titleBreak
    print "Update URLs and Item IDs..."
    print titleBreak + "\n"
    
    # Add the group ids to the dictionary of old/new ids
    origIDToNewID.update(oldGrpID_newGrpID)
    
    update_post_publish(portaladmin, hostname_map, origIDToNewID)

    # Comment out: this functionality is now available out of the box
    # # ------------------------------------------------------------------------
    # # Share items in default web apps template and default gallery
    # # ------------------------------------------------------------------------    
    # # Share the items in the default web apps template and
    # # default gallery template built-in group with the
    # # 'OpsServer' user 'AFMI Web Application Templates' and
    # # 'AFMI Gallery Templates'
    # print "\n" + sectionBreak
    # print "Share the items in the default web apps and gallery template groups..."
    # group_owner = 'OpsServer'
    # if users.get(group_owner):
    #     share_templates(portaladdress, users[group_owner]['target_username'], users[group_owner]['target_password'])
    # else:
    #     print "-Skipping...user {} was not created. Can perform same operation through portal 'Edit Settings'.".format(group_owner)

    print "\nDONE: Finished posting content to portal."
    
def get_groups_on_disk(contentpath):
    groups_on_disk_info = {}
    group_json_files = findFilePath(contentpath, 'group.json', returnFirst=False)
    for group_json_file in group_json_files:
        os.chdir(os.path.dirname(group_json_file))
        group_json = json.load(open('group.json'))
        groups_on_disk_info[group_json['id']] = '{}:{}'.format(group_json['owner'], group_json['title'])
        
    return groups_on_disk_info

    
    
def dump_newItem_info(newItems, origItemSourceIDs, userLogPath):
    # Used for resetting the various ids in 'related' items in target portal
    
    oldID_newItem_JsonFile = "oldID_newItem.json"
    oldID_newItem_JsonFilePath = os.path.join(userLogPath, oldID_newItem_JsonFile)
    
    oldID_newID_JsonFile = "oldID_newID.json"
    oldID_newID_JsonFilePath = os.path.join(userLogPath, oldID_newID_JsonFile)
    
    # Create user log folder
    makeFolder(userLogPath)
    os.chdir(userLogPath)
    
    # Create dictionary where key is old item id, value is dictionary containing info
    # about new item
    # {"oldID": {"newID": "new id value", "type": "type value, "owner": "owner value"}}
    oldID_newItem = []
    oldID_newID = {}
    for x in range(0, len(origItemSourceIDs)):
        d = {}
        d_new_info = {}
        
        newID = newItems[x]["id"]
        oldID = origItemSourceIDs[x]
        itemType = newItems[x]["type"]
        itemOwner = newItems[x]["owner"]
        
        d["oldID"] = oldID
        d["newItem"] = newItems[x]
        
        oldID_newItem.append(d)
        
        d_new_info = {"id": newID, "type": itemType, "owner": itemOwner}
        oldID_newID[oldID] = dict(d_new_info)
        
        #Also add to module level dictionary
        origIDToNewID[oldID] = dict(d_new_info)
        
    # Dump info out to JSON files
    json.dump(oldID_newItem, open(oldID_newItem_JsonFile,'w'))
    json.dump(oldID_newID, open(oldID_newID_JsonFile,'w'))

    return oldID_newID_JsonFilePath, oldID_newItem_JsonFilePath

def share_items(portal, userItemsPath, newItems, origItemSourceIDs, originGroupToDestGroups):
    #newItems - info on the items that were added to portal
    #origItemSourceIDs - the original source ids of the newItems, order of ids must match
    #   order of newItems

    print "Sharing items..."
    
    for x in range(0, len(origItemSourceIDs)):
        newItem = newItems[x]
        newID = newItem["id"]
        origID = origItemSourceIDs[x]

        itemIdfolder = os.path.join(userItemsPath,str(origID))
        
        if not os.path.exists(itemIdfolder):
            continue
        
        # Load sharing json file
        os.chdir(itemIdfolder)
        sharing = json.load(open('sharing.json'))
        
        new_group_ids = []
        new_group_names = []
        everyone = False
        org = False
        
        if sharing:
            #TODO: check if owner belongs to the groups being shared to??
            # swap stored group ids with portal group ids??
            old_group_ids = sharing['groups']
            for g in old_group_ids:
                if g in originGroupToDestGroups.keys():
                    new_group_id = originGroupToDestGroups[g]
                    new_group_ids.append(new_group_id)
                    new_group_names = destGroupID_GroupName[new_group_id] #EL used for display
            
            if len(new_group_ids) == 0:
                new_group_ids = None
            
            print "\tSharing item " + str(newItem.get("title")) + \
                "[" + str(newItem.get("type")) + "] with: " + \
                sharing['access'] + ", " + str(new_group_names) + "..."
            
            if sharing['access'].lower() == "public":
                everyone = True
                org = True
            elif sharing['access'].lower() == "org":
                everyone = False
                org = True
            
            #TODO: should this function be located outside the if sharing statement...
            resp = portal.share_item(newID, new_group_ids, org, everyone)

        else:
            pass # nothing to share??
        del sharing

def has_user(portaladmin, username):
    ''' Determines if portal already has username '''
    exists = False
    portal_usernames = []
    portal_users = portaladmin.org_users()
    for portal_user in portal_users:
        portal_usernames.append(portal_user['username'])
    
    if username in portal_usernames:
      exists = True
    
    return exists

def create_user(portaladmin,contentpath,userinfo):
    
    username = userinfo['target_username']
    password = userinfo['target_password']
    userfoldername = userinfo['username']

    user_exists = has_user(portaladmin, username)
    
    if not user_exists:
        print '   - Creating user {}...'.format(username)
        # Get user properties from file
        userfolder = os.path.join(contentpath, userfoldername)
        os.chdir(userfolder)
        userproperties = json.load(open("userinfo.json"))
        fullname = userproperties["fullName"]
        role = userproperties["role"]
        email = userproperties["email"]
        
        # Check for null email
        if not email:
            email = username + '@no_email_in_user_profile.org'

        # Create user
        portaladmin.signup(username,password,fullname,email)
        
        # Modify user role
        portaladmin.update_user_role(username, role)
    else:
        print '   - User {} already exists.'.format(username)

def has_folder(portaladmin, username, foldername):
    ''' Determines if folder already exists '''
    exists = False
    portal_folders = []
    for portal_folder in portaladmin.folders(username):
        portal_folders.append(portal_folder['title'])
    
    if foldername in portal_folders:
      exists = True
    
    return exists

def create_user_folders(portaladmin, contentpath, userinfo):
    ''' Create user folders '''
    
    if not os.path.exists(os.path.join(contentpath, userinfo['username'], 'folders.json')):
        print '   - No folders to create.'
    else:
        os.chdir(os.path.join(contentpath, userinfo['username']))
        folderinfo = json.load(open('folders.json'))
        for folder in folderinfo:
            foldername = folder[1]
            if not has_folder(portaladmin, userinfo['target_username'], foldername):
                print '   - Creating folder "{}"...'.format(foldername)
                portaladmin.create_folder(userinfo['target_username'], foldername)
            else:
                print '   - Folder "{}" already exists.'.format(foldername)

def publish_user_items(portal, username, usercontentpath, old_hostname, new_hostname, new_port, specified_groups, id_mapping_file, grps_on_disk):
    ''' Publish all items for current user '''
    # Returns list of dictionaries of new items as well as a list of the
    # original item ids
    newitems, old_source_ids = [], []
    existing_portal_ids = []
    
    print "\n" + sectionBreak
    print "Publishing items for user '" + username + "'...\n"
    
    # Load 'id mapping' file if specified. Since this supports overwrite
    # capability, let's also create a list of all current item ids to verify that item
    # actually exists.
    id_mapping = None
    if id_mapping_file:
        filefolder = os.path.dirname(id_mapping_file)
        filename = os.path.basename(id_mapping_file)
        os.chdir(filefolder)
        id_mapping = json.load(open(filename))
        
        # Create list of existing portal items
        existing_portal_items = portal.search()
        for existing_portal_item in existing_portal_items:
            existing_portal_ids.append(existing_portal_item['id'])
        

    item_dirs = os.listdir(os.path.join(usercontentpath,"items"))
    
    n = 1
    for item_dir in item_dirs:
        overwrite_id = None
        do_load_item = False
        foldername = None
        
        print "\n\tPublishing item {} ({}/{})...".format(item_dir, n, len(item_dirs))
        
        if id_mapping:
            overwrite_id = id_mapping.get(item_dir)['id']
            if overwrite_id:
                print "\t   -Item referenced in id mapping file. Checking if item exists in portal..."
                if overwrite_id in existing_portal_ids:
                    print "\t   -Item exists in portal. Will update item."
                else:
                    overwrite_id = None
                    print "*** WARNING: item referenced in id mapping file does NOT exist in portal. Will add new item instead of updating."
        
        
        # Determine if item should be loaded base on specified group parameters
        if not specified_groups:
            do_load_item = True
        else:
            os.chdir(os.path.join(usercontentpath,"items", item_dir))
            sharing_info = json.load(open('sharing.json'))
            item_groups = sharing_info.get('groups')
            for item_group in item_groups:
                grp_on_disk = grps_on_disk.get(item_group)
                if grp_on_disk:
                    for specified_group in specified_groups:
                        if specified_group == grp_on_disk:
                            do_load_item = True

            if not do_load_item:
                print "\t   -Skipping item. Item groups do not match user specified group criteria."       
        
        
        # Add/Update item
        if do_load_item:
            
            try:
                item, old_source_id = load_item(portal, os.path.join(usercontentpath,"items", item_dir), overwrite_id)
                newitems.append(item)
                old_source_ids.append(old_source_id)         
    
                # Reassign item to target owner and folder
                if os.path.exists(os.path.join(usercontentpath, "folders.json")):
                    os.chdir(usercontentpath)
                    foldersinfo = json.load(open('folders.json'))
                    foldername = publish_get_folder_name_for_item(item, foldersinfo)
                
                portal.reassign_item(item['id'], username, foldername)
                
            except Exception as err:
                print 'ERROR: Exception on adding/updating item: {}'.format(item_dir)
                
        n = n + 1

    return newitems, old_source_ids

def publish_user_groups(portal,contentpath, userinfo, users):
    
    username = userinfo['target_username']
    password = userinfo['target_password']
    userfoldername = userinfo['username']
    
    groupfolder = os.path.join(contentpath, userfoldername, 'groups')
    groupfolders = os.listdir(groupfolder)
    
    numTotalGroupFolders = len(groupfolders)
    if numTotalGroupFolders == 0:
        print "\nUser '{}' does not own any groups.".format(username)
    else:
        print "\nCreating '{}' group(s) for user '{}'...".format(str(numTotalGroupFolders), username)
    
    groupcount = 0
    groupsprocessed = 0
    groupsFailed = ["None"] #TODO: later we append to this list, but why do we initialize
                            # list with one element with "None" string? Was this supposed to be
                            # groupsFailed = []
    for folder in groupfolders:
        groupcount = groupcount + 1
        oldGroupID = folder #was groupID = folder
        groupidfolder = os.path.join(groupfolder, folder)
        os.chdir(groupidfolder)
        group = json.load(open("group.json"))
        group_users = json.load(open("group_users.json"))
        
        # Check if group to add already exists
        groupId = getGroupID(portal, username, str(group['title']))
        
        # Create group if it doesn't exist
        if not groupId:
            print "... group '" + str(group['title']) + "'"
            groupId = portal.create_group(group,group['thumbfile'])
            # Reassign group
            portal.reassign_group(groupId, username)
        else:
            print "... group '" + str(group['title']) + "' already exists."
            
        destGroupID_GroupName[groupId] = str(group['title']) #Track new group id and group name for later use
        
        print "...... adding users to group"
        if groupId:
            originGroupToDestGroups[oldGroupID] = groupId
            groups = []
            groups.append(groupId)
            
            # Check if users are in the list we added to the portal
            users_to_invite = []
            portal_users = get_target_users(users)
            for u in map_group_users(group_users["users"], users):
                u = str(u) #dict keys are unicode, make them ascii
                if u in portal_users:
                    users_to_invite.append(u)
            
            if len(users_to_invite) != 0:
                print "......... adding the following users: " + str(users_to_invite)
                results = portal.add_group_users(users_to_invite, groups)
            else:
                print "......... no users to add."
            groupsprocessed = groupsprocessed + 1
        else:
            groupsFailed.append(groupID) #TODO: we append to this list, but don't use it anywhere.
    os.chdir(groupfolder)
    
    return originGroupToDestGroups

def get_target_users(users):
    target_users = []
    for user, userinfo in users.iteritems():
        target_users.append(userinfo['target_username'])
    
    return target_users

def map_group_users(group_users, users):
    target_group_users = []
    for group_user in group_users:
        if group_user in users.keys():
            target_group_users.append(users[group_user]['target_username'])
    return target_group_users

def publish_portal_resources(portaladmin,portal_properties):
    #publish resources from disk
    portalID = portal_properties['id']
    resourcesJSON = json.load(open(os.path.join(contentpath,'resources.json')))
    resourcesList = resourcesJSON['resources']
    
    print "Posting resources"
    for rsc in resourcesList:
        key = rsc['key']
        if key != 'accountSettings':
            datafile = os.path.join(contentpath,key)
            resp = portaladmin.add_resource(portalID,key,datafile,None)
   
def publish_portal_properties(portaladmin,portal_properties,oldHostname,newHostname):
    #update portal properties from old host to new
    
    portalID = portal_properties['id']
    resp = portaladmin.publish_portal_properties(portalID,portal_properties,oldHostname,newHostname)
    if resp['success'] == True:
        print "Portal properties updated."
    else:
        print "Error updating portal properties"

def get_servername_from_url(url):
    '''Get servername from url'''
    p = urlparse.urlparse(url)
    return p.hostname

def publish_get_folder_name_for_item(item, folders):
    '''Return the folder name the specific item is in'''
    folderName = None
    
    ownerFolderID = item.get('ownerFolder') #Make sure to use .get, which will
                                            #return None if key does not exist.
    
    if ownerFolderID is not None and ownerFolderID <> 'null':
        # We now have the ID of the folder so examine the folder json
        # and determine the folder name for this folder ID
        
        # Example [["e1363455dd044ab384995218fe3386bb", "folder_1", [{"avgRating": 0.0,...
        # element 0 is folderID, element 1 is folder name
        for folder in folders:
            folderID = folder[0]
            if folderID == ownerFolderID:
                folderName = folder[1]
            
    return folderName

def update_post_publish(portal, hostname_map, id_map):
    '''Replace server name and update item IDs referenced in items'''

    # Return all portal items
    items = portal.search()
    
    for item in items:
        
        print_item_info(item)
        
        # Replace host name/item ids in item json properties
        update_item_properties(portal, item, hostname_map, id_map)
        
        # Replace host name/item ids in item "data"
        update_item_data(portal, item, hostname_map, id_map)

def update_item_properties(portal, item, hostname_map, id_map):
    '''Replace host name/item ids in item json properties'''
    
    jsonPropsToUpdate = ['description', 'snippet', 'accessInformation', 'licenseInfo', 'url']
    for jsonProp in jsonPropsToUpdate:
        is_updated = False
        propertyValue = item.get(jsonProp)
        if propertyValue:
            for host in hostname_map:
                search_str_list = [host, host.lower(), host.upper()]
                for search_str in search_str_list:
                    if propertyValue.find(search_str) > -1:
                        propertyValue = propertyValue.replace(search_str, hostname_map[host])
                        is_updated = True
    
            for item_id in id_map:
                search_str_list = [item_id, item_id.lower(), item_id.upper()]
                for search_str in search_str_list:
                    if propertyValue.find(search_str) > -1:
                        propertyValue = propertyValue.replace(search_str, id_map[item_id]["id"])
                        is_updated = True
            
            if is_updated:
                portal.update_item(item['id'], {jsonProp: propertyValue}) 

def update_item_data(portal, item, hostname_map, id_map):
    '''Replace host name/item ids in item data'''

    if item['type'] in TEXT_BASED_ITEM_TYPES:
        
        try:
            itemdata = portal.item_data(item['id'])
        except Exception as err:
            print('ERROR: Exception: update_item_data function could not get item data for item: "{}"'.format(str(item.get('title'))))
            itemdata = None
        
        if itemdata:
            
            is_updated = False
            
            for host in hostname_map:
                search_str_list = [host, host.lower(), host.upper()]
                for search_str in search_str_list:
                    if itemdata.find(search_str) > -1:
                        itemdata = itemdata.replace(search_str, hostname_map[host])
                        is_updated = True

            for item_id in id_map:
                search_str_list = [item_id, item_id.lower(), item_id.upper()]
                for search_str in search_str_list:
                    if itemdata.find(search_str) > -1:
                        itemdata = itemdata.replace(search_str, id_map[item_id]["id"])
                        is_updated = True
            
            if is_updated:
                portal.update_item(item['id'], {'text': itemdata})     

    if item['type'] == 'CSV':
        update_csv_item(portal, item, hostname_map)

def update_csv_item(portal, item, hostname_map):
    ''' Update URLs in CSV item '''
    
    # Download file from portal
    filePath = portal.item_datad(item['id'])
    
    # Determine if file has the search string and perform replace
    is_updated = False
    for host in hostname_map:
        search_str_list = [host, host.lower(), host.upper()]
        for search_str in search_str_list:
            if findInFile(filePath, search_str):
                editFiles([filePath], search_str, hostname_map[host])
                is_updated = True
    
    # Upload the updated file back to the portal item
    if is_updated:
        portal.update_item(item['id'], None, filePath)
    
    # Delete the downloaded file
    if os.path.exists(filePath):
        os.remove(filePath)
     
def print_item_info(item):
    itemID = item.get('id')
    itemTitle = item.get('title')
    itemOwner = item.get('owner')
    itemType = item.get('type')
    print "\tId: " + str(itemID) + "\tTitle: '" + str(itemTitle) + "' (" + str(itemType) + "), Owner: '" + str(itemOwner) + "'\n"
    
def makeFolder(folderPath):
    '''Create folder'''
    if not os.path.exists(folderPath):
        os.makedirs(folderPath)
    
def val_arg_content_path(contentpath):
    '''Validate the content path script argument parameter'''
    is_valid = False
    if os.path.exists(contentpath):
        if os.path.isdir(contentpath):
            is_valid = True
    return is_valid

def read_userfile(contentpath):
    # Create dictionary of users based on contents of userfile.txt file.
    # The "userfile.txt" file contains user name from source portal,
    # user name for target portal and the password for the target user name
    all_users = {}
    userfile = open(os.path.join(contentpath,'userfile.txt'),'r')
    lineOne = True
    for line in userfile:
        # Skip the header info line
        if lineOne:
            lineOne = False
            continue
        username,target_username,target_password = line.rstrip().split(',')
        
        all_users[username] = {'username': username,
                               'target_username': target_username,
                               'target_password': target_password}
    userfile.close()
    
    return all_users

def val_arg_users(specified_users, contentpath):
    values_to_use = {}      # Contains users that that will be published
    exclude_users_list = [] # Contains users that should be excluded from publishing
    include_users_list = []
    
    if not specified_users:
        specified_users = ""
    else:
        specified_users = specified_users.strip()
    
    all_users = read_userfile(contentpath)
    
    # if there are no specified users then we should post content for
    # all users so return dictionary of all users
    if len(specified_users) == 0:
        return all_users
    
    elif specified_users == "#":
        return all_users
    
    elif specified_users.find("-") == 0:
        values_to_use = all_users.copy()
        exclude_users = specified_users.replace("-","",1)
        exclude_users_list = [element.lower().strip() for element in exclude_users.split(",")]
        for exclude_user in exclude_users_list:
            for user in all_users:
                if exclude_user == user.lower():
                    # Remove the user from the dictionary
                    del values_to_use[user]
        return values_to_use      
    
    else:
        # keep the users that were specified
        include_users_list = [element.lower().strip() for element in specified_users.split(",")]
        for include_user in include_users_list:
            for user in all_users:
                if include_user == user.lower():
                    #add to dictionary
                    values_to_use[user] = all_users[user] 
        return values_to_use

def share_templates(portaladdress, username, password):
    
    # Create portal connection
    portal = Portal(portaladdress, username, password)
    
    print '\nShare web app templates with "AFMI Web Application Templates" group...'
    results = share_default_webapp_templates(portal, portal.logged_in_user()['username'], 'AFMI Web Application Templates')
    if results['success']:
        print '\tDone.'
    else:
        print 'ERROR: {}'.format(results['message'])
    
    print '\nShare web app templates with "AFMI Gallery Templates" group...'
    results = share_default_gallery_templates(portal, portal.logged_in_user()['username'], 'AFMI Gallery Templates')
    if results['success']:
        print '\tDone.'
    else:
        print 'ERROR: {}'.format(results['message'])    

def share_default_gallery_templates(portal, groupOwner, groupTitle):
    func_results = {'success': True}
    
    templateType = 'GALLERY'
    results = share_default_templates(portal, templateType, groupOwner, groupTitle)
    if not results['success']:
        func_results['success'] = results['success']
        func_results['message'] = results['message']
        
    return func_results

def share_default_webapp_templates(portal, groupOwner, groupTitle):
    func_results = {'success': True}
    
    templateType = 'WEBAPPS'
    results = share_default_templates(portal, templateType, groupOwner, groupTitle)
    if not results['success']:
        func_results['success'] = results['success']
        func_results['message'] = results['message']
        
    return func_results

def share_default_templates(portal, templateType, groupOwner, groupTitle):
    func_results = {'success': True}
    
    # Get a list of template ids for items shared with the "default" template group
    printStatement = '\t-Retrieving list of items in default {} group...'
    
    if templateType == 'WEBAPPS':
        
        templateTypeStr = 'web app templates'
        print printStatement.format(templateTypeStr)
        templateIDs = unpack(portal.webmap_templates(['id']))
        
    elif templateType == 'GALLERY':
        
        templateTypeStr = 'gallery templates'
        print printStatement.format(templateTypeStr)
        templateIDs = unpack(portal.gallery_templates(['id']))
        
    else:
        # Template type value is invalid
        func_results['success'] = False
        func_results['message'] = 'Invalid templateType value "{}"; must be WEBAPPS or GALLERY.'.format(templateType)
        return func_results
    
    if not templateIDs:
        func_results['success'] = False
        func_results['message'] = '{} portal property not set to use "Default" group.'.format(templateTypeStr.capitalize())
        return func_results
    
    # Get the group id for the group to share the template items
    groupID = getGroupID(portal, groupOwner, groupTitle)
    
    if not groupID:
        func_results['success'] = False
        func_results['message'] = 'Could not find group where owner = "{}" and title = "{}"'.format(groupOwner, groupTitle)
        return func_results
    
    # Share templates with group
    print '\t-Sharing web templates with group {} ({})...'.format(groupTitle, groupOwner)
    results = share_template_items(portal, templateIDs, [groupID])
    if not results['success']:
        func_results['success'] = False
        print results['message']
        
    return func_results

def getGroupID(portal, owner, title):
    # Return id for group owned by 'owner' with title = specified title
    groupID = None
    groups = portal.user(owner)['groups']
    if groups:
        for group in groups:
            if group['title'] == title:
                groupID = group['id']
        
    return groupID

def share_template_items(portal, item_ids, group_ids):
    func_results = {'success': True}
    errList = []
    for item_id in item_ids:
        results = portal.share_item(item_id, group_ids)
        if len(results['notSharedWith']) > 0:
            errList.append(results)
    
    if len(errList) > 0:
        func_results['success'] = False
        func_results['message'] = errList
        
    return func_results

def tags_exist(find_tags, tags_to_search):
    '''Determines if specific "OpsServer" values exist in list of tags'''
    found = False
    
    DEBUG = False
    
    # Create list of possible "OpsServer" type tag prefixes; i.e. in case someone didn't
    # specify the correct prefix.
    ops_type_flags = ["opsserver", "opsservers", "opserver", "opservers", "opssrver", "opssrvr"]
    
    # Convert find_tags to lower case and remove and leading/trailing spaces
    find_tags_mod = [element.lower().strip().encode("ascii") for element in list(find_tags)]
    
    # Convert tags_to_search to lower case and remove and leading/trailing spaces
    tags_to_search_mod = [element.lower().strip().encode("ascii") for element in list(tags_to_search)]
    
    if DEBUG:
        print "In tags_exist function: "
        print "\tfind_tags_mod: " + str(find_tags_mod)
        print "\ttags_to_search_mod: " + str(tags_to_search_mod)
        print "\tops_type_flags: " + str(ops_type_flags)
    
    # Loop through tags to search and look for the find tags
    for search in tags_to_search_mod:
        search = search.replace(" ","")
        
        if DEBUG:
            print "\tsearch: " + search
            
        if search.find(":") > -1:
            
            if DEBUG:
                print "\tI'm in the find : if statement"
                
            element1 = search.split(":")[0]
            element2 = search.split(":")[1]
            
            if DEBUG:
                print "\t\telement1: " + element1
                print "\t\telement2: " + element2
                
            if element1 in ops_type_flags:
                if element2 in find_tags_mod:
                    found = True
                    
    if DEBUG:
        print "\tfound: " + str(found)
        
    return found

if __name__ == "__main__":
    main()
