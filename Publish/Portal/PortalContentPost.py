

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# MFportalcontent.py
# -------------------------------------------------------
# Various tools for copying Portal by either direct copy
# or through an intermediate file system by extract/post.
# -------------------------------------------------------
# v1.0 - 11/**/2012
# -------------------------------------------------------
# - 12/11/2012 - MF - Copy and modify from BC portalcontent.py.
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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
from portalpy import Portal, parse_hostname, portal_time, WebMap, normalize_url, unpack
from portalpy.provision import load_items, load_item
from Utilities import findInFile, editFiles
import logging
import OpsServerConfig
import copy

logging.basicConfig()

# For now hard-code the server name of the source ArcGIS Server machine
source_hostname = "afmcomstaging.esri.com"
#port = '6080' #Use 6080 or None
#new_hostname = "holistic35.esri.com"
new_hostname = ""
new_port = None #Use 6080 or None

hostname_map = {}

#port = '6080' #Use 6080 or None

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

# Store list of valid Ops Server type values
valid_ops_types = OpsServerConfig.valid_ops_types

def main():

    scriptName = sys.argv[0]

    specified_users = None
    specified_ops_types = None
    id_mapping_file = None
    
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------   
    if len(sys.argv) < 5:
        print '\n' + scriptName + ' <PortalURL> <AdminUser> <AdminPassword> ' + \
                    '<ContentFolderPath> {UsersToPost} {OpsServerTypesToPost} {IdMappingFile}'
        print '\nWhere:'
        print '\n\t<PortalURL> (required): URL of Portal to post content (i.e. https://fully_qualified_domain_name/arcgis)'
        
        print '\n\t<AdminUser> (required): Portal user that has administrator role.'
        
        print '\n\t<AdminPassword> (required): Password for AdminUser.'
        
        print '\n\t<ContentFolderPath> (required): Folder path containing portal content to post.'
        
        print '\n\t{UsersToPost} (optional):'
        print '\t\t-By default, content for all users is posted'
        print '\t\t-Specify # placeholder character if you want to post content for all users and you are'
        print '\t\t   specifying {OpsServerTypesToPost} values'
        print '\t\t-To post content for only specific users specify comma delimited list of users, i.e. user1,user2,...'
        #print '\t\t   (to include spaces in this list surround with double-quotes, i.e. "user1, user2,...")'
        print '\t\t-To post content for ALL users except specific users, specify comma delimited '
        print '\t\t   list of users to exclude with "-" prefix, i.e. -user1,user2,...'
        
        print '\n\t{OpsServerTypesToPost} (optional):'
        print '\t\t-To post content for specific Ops Server types specify type value, i.e.'
        print '\t\t   ' + str(valid_ops_types)  + '; you can specify more then one type,'
        print '\t\t   i.e, Land,Maritime,...'
        print '\t\t-Specify # placeholder character if you do not want to use this parameter by need'
        print '\t\t   to specify the {IdMappingFile} parameter value.'
        
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
        specified_ops_types = sys.argv[6]
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
        if specified_ops_types:
            print "specifiedOpsTypes: " + str(specified_ops_types)
        if id_mapping_file:
            print "id_mapping_file: " + str(id_mapping_file)
    
    ## Check if connection can be made to target portal
    ##result = val_portal_connection_props(target_portal_address, adminuser, adminpassword)
    
    # Check if specified content folder exists.
    if not val_arg_content_path(contentpath):
        print "Parameter <ContentFolderPath>: folder '" + contentpath + "' does not exist."
        sys.exit(1)
    
    # Check if specified users are valid
    users = val_arg_users(specified_users, contentpath)
    
    if DEBUG:
        print "Users to publish: " + str(users.keys())
    
    
    # Check if specified ops server types are valid
    if specified_ops_types == "#":
        specified_ops_types = None
    if specified_ops_types:
        results, specified_ops_types = val_arg_ops_types(specified_ops_types)
        if not results:
            print "Parameter {OpsServersToPost}: '" + str(specified_ops_types) + \
            "' does not contain valid value(s)."
            print "Valid {OpsServersToPost} values are: " + str(valid_ops_types)
            sys.exit(1)
    
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
    publish_portal(target_portal_address, contentpath, adminuser, adminpassword, users, hostname_map, specified_ops_types, id_mapping_file)
    
    os.chdir(contentpath) #TODO: EL, do we need this?
    
    print "\nDONE: Finished posting content to portal."

def print_script_header(portal, portal_processing, users, specified_ops_types):
    print titleBreak
    print "                               Portal Content " + portal_processing
    print titleBreak
    print "Processing type: \t\t\t" + portal_processing
    print "Portal URL: \t\t\t\t" + portal.url
    print "Signed in as: \t\t\t\t" + portal.logged_in_user()['username'] + " (Role: " + portal.logged_in_user()['role'] + ")"
    print "Posting content for users: \t\t" + str(users.keys())
    print "Posting items with 'OpsServer'"
    print "\ttags containing: \t\t" + str(specified_ops_types)

    
#POST
def publish_portal(portaladdress,contentpath,adminuser,adminpassword, users, hostname_map, specified_ops_types, id_mapping_file):
    os.chdir(contentpath)
    
    portal_properties = json.load(open("portal_properties.json"))
    portaladmin = Portal(portaladdress, adminuser, adminpassword)
    
    print_script_header(portaladmin, portal_processing, users, specified_ops_types)

    # Create Portal log folder for this portal
    portalLogPath = os.path.join(contentpath, portalLogFolder, get_servername_from_url(portaladmin.url))
    makeFolder(portalLogPath)
    
    # ------------------------------------------------------------------------
    # Create users
    # ------------------------------------------------------------------------
    print titleBreak
    print 'Create users...\n'
   
    # Only create users if this is not an online organization
    if portaladmin.properties()['id'] == '0123456789ABCDEF': # All portals have this id.
        for username, userinfo in users.iteritems():
           #print '   - Creating user "{}" if it does not exist...'.format(userinfo['target_username'])
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
    
    for username, userinfo in users.iteritems():
        portal = Portal(portaladdress, userinfo['target_username'], userinfo['target_password'])
        newGroups = publish_user_groups(portal, contentpath, userinfo, users)
 
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
        # Sign into portal as the user
        # ---------------------------------------
        portal = Portal(portaladdress, username, password)
        
        # ---------------------------------------
        # Publish all the users' items
        # ---------------------------------------
        #NOTE: must execute with portal object signed in as item owner.
        usercontentpath = os.path.join(contentpath, userfoldername)
        newItems, origItemSourceIDs = publish_user_items(portal, usercontentpath, source_hostname,
                                new_hostname, new_port, specified_ops_types, portaladmin, id_mapping_file)
        
        # Dump info about new items to JSON to use for resetting IDs of related items
        dump_newItem_info(newItems, origItemSourceIDs, os.path.join(portalLogPath, username))
        
        # ---------------------------------------
        # Share the users' items with the
        # appropriate groups
        # ---------------------------------------
        #NOTE: must execute with portal object signed in as item owner.
        userItemsPath = os.path.join(contentpath, userfoldername, "items")
        share_items(portal, userItemsPath, newItems, origItemSourceIDs, originGroupToDestGroups)
    
    
    # Dump info about all items (old, new ids) into json
    os.chdir(portalLogPath)
    json.dump(origIDToNewID, open('oldID_newID.json','w'))
    
    # ------------------------------------------------------------------------
    # Post add processing: Update URLs and item ids
    # ------------------------------------------------------------------------
    
    print "\n" + titleBreak
    print "Update URLs and Item IDs..."
    print titleBreak
    
    # Update the urls in URL based items
    print "\n" + sectionBreak
    print "Update the URLs in URL based items...\n"
    update_url_based_items(portaladmin, hostname_map)   
    
    print "\n" + sectionBreak
    print "Update URLs within item properties...\n"    
    update_items(portaladmin, hostname_map)
    
    # Update the urls and item ids in webmaps
    print "\n" + sectionBreak
    print "Update the URLs and item ids in webmaps...\n"
    update_webmaps(portaladmin, hostname_map, origIDToNewID)
    
    # Update the urls and item ids in operation views
    print "\n" + sectionBreak
    print "Update the URLs and item ids in operation views...\n"
    update_operationviews(portaladmin, hostname_map, origIDToNewID)
    
    # Update the item ids in URLs and with data
    print "\n" + sectionBreak
    print "Update the item ids in web app URLs and data...\n"
    update_webapps(portaladmin, origIDToNewID)   
    
    # Update the URLs in any CSV portal items
    print "\n" + sectionBreak
    print "Update the URLs in CSV portal items...\n"
    update_csv_items(portaladmin, hostname_map)
    
    # Share the items in the default web apps template and
    # default gallery template built-in group with the
    # 'OpsServer' user 'AFMI Web Application Templates' and
    # 'AFMI Gallery Templates'
    print "\n" + sectionBreak
    print "Share the items in the default web apps and gallery template groups..."
    share_templates(portaladdress, users['OpsServer']['target_username'], users['OpsServer']['target_password'])
    

def dump_newItem_info(newItems, origItemSourceIDs, userLogPath):
    # Used for resetting the various ids in 'related' items in target portal
    
    # newItems - object returned by provision.Load_items function
    # origItemSourceIDs - object returned by provision.Load_items function
    # userLogPath - folder to write JSON files
    
    # Set json file paths
    #oldID_JsonFile = "old_item_ids.json"
    #oldID_JSONPath = os.path.join(userLogPath, oldID_JsonFile)
    
    #newItems_JsonFile = "new_items.json"
    #newItems_JsonPath = os.path.join(userLogPath, newItems_JsonFile)
    
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
        
        #d2["oldID"] = oldID
        #d2["newID"] = newID
        #d2["type"] = itemType
        
        oldID_newItem.append(d)
        
        d_new_info = {"id": newID, "type": itemType, "owner": itemOwner}
        oldID_newID[oldID] = dict(d_new_info)
        
        #Also add to module level dictionary
        origIDToNewID[oldID] = dict(d_new_info)
        
    # Dump info out to JSON files
    #json.dump(origItemSourceIDs, open(oldID_JsonFile,'w'))
    #json.dump(newItems, open(newItems_JsonFile,'w'))
    json.dump(oldID_newItem, open(oldID_newItem_JsonFile,'w'))
    json.dump(oldID_newID, open(oldID_newID_JsonFile,'w'))
    
    #return oldID_newItem_JsonFile, newItems_JsonFile, oldID_JsonFile
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
            #MF #TODO: check if owner belongs to the groups being shared to??
            # swap stored group ids with portal group ids??
            old_group_ids = sharing['groups']
            #print "old_group_ids..."
            #print old_group_ids
            for g in old_group_ids:
                #print "g..."
                #print g
                if g in originGroupToDestGroups.keys():
                    # EL: I don't want to alter the originGroupToDestGroups
                    # dictionary object in case I need it later. Add group id (g)
                    # to new list
                    #old_group_ids.remove(g) 
                    #old_group_ids.append(originGroupToDestGroups[g])
                    new_group_id = originGroupToDestGroups[g]
                    new_group_ids.append(new_group_id)
                    new_group_names = destGroupID_GroupName[new_group_id] #EL used for display
            
            if len(new_group_ids) == 0:
                new_group_ids = None
            #print "new_group_ids..."
            #print new_group_ids
            # setup item access and sharing info
            
            print "\tSharing item " + str(newItem.get("title")) + \
                "[" + str(newItem.get("type")) + "] with: " + \
                sharing['access'] + ", " + str(new_group_names) + "..."
            
            #EL: I think the access that should be checked is the property
            # in the sharing json, not the item json (it might be the same?)
            #if item['access'].lower() == "public":
            #    everyone = True
            if sharing['access'].lower() == "public":
                everyone = True
            
            #EL TODO: should this function be located outside the if sharing statement...
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


def publish_user_items(portal, usercontentpath, old_hostname, new_hostname, new_port, specified_ops_types, portaladmin, id_mapping_file):
    ''' Publish all items for current user '''
    # Returns list of dictionaries of new items as well as a list of the
    # original item ids
    newitems, old_source_ids = [], []
    existing_portal_ids = []
    
    print "\n" + sectionBreak
    userName = portal.logged_in_user()["username"]
    print "Publishing items for user '" + userName + "'...\n"
    
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
        existing_portal_items = portaladmin.search()
        for existing_portal_item in existing_portal_items:
            existing_portal_ids.append(existing_portal_item['id'])
        

    item_dirs = os.listdir(os.path.join(usercontentpath,"items"))
    
    n = 1
    for item_dir in item_dirs:
        overwrite_id = None
        do_load_item = False
        
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
        
        # Determine if item should be loaded based on specified tags
        if not specified_ops_types:
            do_load_item = True
        else:
            os.chdir(os.path.join(usercontentpath,"items", item_dir))
            iteminfo = json.load(open('item.json'))
            item_tags = iteminfo.get('tags')
            do_load_item = tags_exist(specified_ops_types, item_tags)
            if not do_load_item:
                print "\t   -Skipping item. Item tags do not match user specified criteria."
            
        # Add/Update item
        if do_load_item:
            item, old_source_id = load_item(portal, os.path.join(usercontentpath,"items", item_dir), overwrite_id)
            newitems.append(item)
            old_source_ids.append(old_source_id)
        
            # Reassign item to correct folder
            if os.path.exists(os.path.join(usercontentpath, "folders.json")):
                os.chdir(usercontentpath)
                foldersInfo = json.load(open('folders.json'))
                folderName = publish_get_folder_name_for_item(item, foldersInfo)
    
                if folderName is not None:
                    portaladmin.reassign_item(item['id'], portal.logged_in_user()['username'], folderName)           
            
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
    groupsFailed = ["None"] #EL: TODO: later we append to this list, but why do we initialize
                            # list with one element with "None" string? Was this supposed to be
                            # groupsFailed = []
    for folder in groupfolders:
        groupcount = groupcount + 1
        oldGroupID = folder # EL was groupID = folder
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
        else:
            print "... group '" + str(group['title']) + "' already exists."
            
        destGroupID_GroupName[groupId] = str(group['title']) #EL Track new group id and group name for later use
        
        print "...... adding users to group"
        if groupId:
            originGroupToDestGroups[oldGroupID] = groupId
            groups = []
            groups.append(groupId)
            
            # Check if users are in the list we added to the portal
            users_to_invite = []
            portal_users = get_target_users(users)
            for u in map_group_users(group_users["users"], users):
                u = str(u) #MF dict keys are unicode, make them ascii
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
    #MF publish resources from disk
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
    #MF update portal properties from old host to new
    
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

def update_url_based_items(portal, hostname_map):
    '''Updates the URLs in URL based items'''
    
    if DEBUG:
        print 'Function: update_url_based_items...'
        print '\tvariable hostname_map: ' + str(hostname_map) + '\n'
        
    # ------------------------------------------------------------------------
    # Replace hostname in URLs for URL based items (services)
    # ------------------------------------------------------------------------
    # EL, 6/18/2013: the "URL_ITEM_FILTER" does not capture all items with URLs
    # such as web mapping application, so don't apply a filter
    #url_items = portal.search(['id','type','url','title','owner'], portalpy.URL_ITEM_FILTER)
    url_items = portal.search(['id','type','url','title','owner'])
    for item in url_items:
        url = item.get('url')
        
        if url:
            print_item_info(item)
            
            url = normalize_url(url)
            host = parse_hostname(url, include_port=True)
            if host in hostname_map:
                url = url.replace(host, hostname_map[host])
                portal.update_item(item['id'], {'url': url})

def update_items(portal, hostname_map):
    ''' Update server names in item properties '''
    
    jsonPropertiesToUpdate = ['description', 'snippet', 'accessInformation', 'licenseInfo']
    
    # Return all portal items
    items = portal.search()
    
    if not items:
        return

    for item in items:
        print_item_info(item)
        itemID = item.get('id')
        
        for jsonProperty in jsonPropertiesToUpdate:
            is_updated = False
            propertyValue = item.get(jsonProperty)
            if propertyValue:
                for host in hostname_map:
                    if propertyValue.find(host) > -1:
                        propertyValue = propertyValue.replace(host, hostname_map[host])
                        is_updated = True
        
                if is_updated:
                    portal.update_item(itemID, {jsonProperty: propertyValue})

def update_webmaps(portal, hostname_map, id_map):
    '''Update URLs and item ids in WebMaps'''
    
    if DEBUG:
        print 'Function: update_webmaps...'
        print '\tvariable hostname_map: ' + str(hostname_map)
        print '\tvariable id_map: ' + str(id_map) + '\n'
        
    # ------------------------------------------------------------------------
    # Replace hostname in URLs for Web Maps
    # ------------------------------------------------------------------------
    # 6/26/2013: Removed include_basemaps parameter; portalpy incorrectly
    # setting exclude tags (i.e. -tags:basemap) in search criteria so basemaps
    # were not being found.
    #webmaps = portal.webmaps(include_basemaps=True)
    webmaps = portal.webmaps()
    
    if not webmaps:
        return
    
    for webmap in webmaps:
        item, sharing, folder = portal.user_item(webmap.id)

        print_item_info(item)
        
        is_update = False
        
        for url in webmap.urls(layers=True, basemap=True):
            normalized_url = normalize_url(url)
            host = parse_hostname(normalized_url, include_port=True)
            if host in hostname_map:
                new_url = normalized_url.replace(host, hostname_map[host])
                webmap.data = webmap.data.replace(url, new_url)
                is_update = True
            
        for item_id in webmap.item_ids():
            if item_id in id_map:
                webmap.data = webmap.data.replace(item_id, id_map[item_id]["id"])
                is_update = True
            else:
                print "***ERROR: can't map item id '" + item_id + "' to new id."
        
        # Replace any other references to host names that may exist in the
        # webmap. Examples are feature collections; for example, you can have
        # renderers which have a URL to a portal symbol image or the author
        # of the webmap may have added fields which store URLs to resources.
        #
        # NOTE: this code block won't handle cases where the port number
        # is included in the URL; this is due to the fact that URLs can be
        # stored in any user defined keys so we can't explicitly 'pull' the
        # values for these keys.
        for host in hostname_map:
            if host in webmap.data:
                is_update = True
                webmap.data = webmap.data.replace(host, hostname_map[host])
                
        # If changes were made to URLs or item ids update the webmap
        if is_update:
            portal.update_webmap(webmap)

def update_operationviews(portal, hostname_map, id_map):
    '''Update URLs and item ids in OperationViews'''
    
    if DEBUG:
        print 'Function: update_operationviews...'
        print '\tvariable hostname_map: ' + str(hostname_map)
        print '\tvariable id_map: ' + str(id_map) + '\n'
        
    opviews = portal.operationviews()

    if not opviews:
        return
    
    for opview in opviews:
        item, sharing, folder = portal.user_item(opview.id)
        
        print_item_info(item)
    
        is_update = False
        
        # Replace MapID values in map widgets
        map_widgets = opview.map_widgets()
        for map_widget in map_widgets:
            map_id = map_widget['mapId']
            if map_id in id_map:
                opview.data = opview.data.replace(map_id, id_map[map_id]["id"])
                is_update = True
            else:
                print "***ERROR: can't map map id '" + map_id + "' to new id."
        
        # Replace service item id values in standalone data sources
        service_item_ids = opview.standalone_ds_service_item_ids()
        for service_item_id in service_item_ids:
            if service_item_id in id_map:
                opview.data = opview.data.replace(service_item_id, id_map[service_item_id]["id"])
                is_update = True
            else:
                print "***ERROR: can't map standalone data source service item id '" + service_item_id + "' to new id."               
        
        # Replace URL values in standalone data sources
        for url in opview.standalone_ds_urls():
           normalized_url = normalize_url(url)
           host = parse_hostname(normalized_url, include_port=True)
           if host in hostname_map:
               new_url = normalized_url.replace(host, hostname_map[host])
               opview.data = opview.data.replace(url, new_url)
               is_update = True       
        
        if is_update:
            portal.update_operationview(opview)

def update_webapps(portal, id_map):
    '''Update the item ids in web app URLs and data'''
    
    items = portal.search(['id','type','url','title','owner'])

    if not items:
        return
    
    for item in items:
        if item.get('type') == 'Web Mapping Application':
            is_update_url = False
            is_update_data = False
            
            new_url = None
            new_data = None
            
            print_item_info(item)
            
            url = item.get('url')
        
            # Update ids in url (replace any old ids with new ids)
            if url:
                for old_id in id_map:
                    if old_id in url:
                        url = url.replace(old_id, id_map[old_id]["id"])
                        item['url'] = url
                        is_update_url = True
             
            # Update the items' data (replace any old ids with new ids)
            item_data = portal.item_data(item.get('id'))
            
            if item_data:
                
                for old_id in id_map:
                    if old_id in item_data:
                        item_data = item_data.replace(old_id, id_map[old_id]["id"])
                        is_update_data = True
                
                if is_update_data:
                    item['text'] = item_data
                    
            if is_update_url or is_update_data:
                portal.update_item(item.get('id'), item)    

def update_csv_items(portal, hostname_map):
    ''' Update URLs in CSV portal items '''
    
    count = 0
    filePaths = []
    
    # Set query string for item search
    q = 'type:csv'
    
    # Perform search
    items = portal.search(['id','type','url','title','owner'], q)
    
    if not items:
        return
    
    for item in items:
        print_item_info(item)
        itemID = item.get('id')
        
        # Download file from portal
        filePath = portal.item_datad(itemID)
        filePaths.append(filePath)
        
        is_updated = False
        for host in hostname_map:
            if findInFile(filePath, host):
                editFiles([filePath], host, hostname_map[host])
                is_updated = True
            
        if is_updated:
            portal.update_item(itemID, None, filePath)
    
    # Delete the files that were downloaded.   
    if filePaths:
        for filePath in filePaths:
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

def val_arg_ops_types(specified_ops_types):
    
    is_valid = True
    values_to_use = []
    ops_type_all = "all"
    
    # Create copy of valid value list (so we can alter values) and convert to lower case
    valid_values = [element.lower().strip() for element in list(valid_ops_types)]
    
    # Convert user specified list of ops types to list and convert
    # to lower case and remove any leading or trailing "whitespace"
    # this handles cases where user entered spaces between
    # values i.e. "Land, Maritime".
    specified_values = [element.lower().strip() for element in specified_ops_types.split(",")]
    
    if DEBUG:
        print "specified_values: " + str(specified_values)

    # If user specified "all" then return list containing only this value
    if ops_type_all.lower() in specified_values:
        #values_to_use.append(ops_type_all.lower())
        values_to_use = list(valid_ops_types)
        #print "values_to_use:  " + str(values_to_use)
        return True, values_to_use
    
    # Check if user specified valid ops types
    for ops_type in specified_values:
        if ops_type not in valid_values:
            return False, values_to_use
        values_to_use.append(ops_type)
    
    # If the user has specified at least one valid value then add "all" to list
    # so that the load function will publish items that have the "all" to addition
    # to the items with the other tags specified.
    if len(values_to_use) > 0:
        values_to_use.append(ops_type_all)
        
    return is_valid, values_to_use

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
    
    ## Create dictionary of users based on contents of userfile.txt file.
    ## The "userfile.txt" file contains user name and full name of user,
    ## i.e. userx,User X. Dictionary key is user name, dictionary value
    ## is password; in this case set the password the same as user name.
    #userfile = open(os.path.join(contentpath,'userfile.txt'),'r')
    #lineOne = True
    #for line in userfile:
    #    # Skip the first line since it contains header info
    #    if lineOne:
    #        lineOne = False
    #        continue
    #    username,target_username,target_password = line.rstrip().split(',')
    #    all_users[username] = {'username': username,
    #                           'target_username': target_username,
    #                           'target_password': target_password}
    #userfile.close()
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

#def val_portal_connection_props(portal_address, username, password):
#    portal_con = Portal(portal_address, username, password)
#    if portal_con:
#        print "portal con is valid"
#    else:
#        print "not valid"
#    #print str(portal_con.logged_in_user)

if __name__ == "__main__":
    main()
