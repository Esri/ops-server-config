

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
print supportFilesPath
sys.path.append(supportFilesPath)

import portalpy
import json
import urlparse
import types
import shutil
from datetime import datetime, timedelta
from portalpy import Portal, parse_hostname, portal_time, WebMap, normalize_url, unpack
from portalpy.provision import load_items, load_items_based_on_tags
from Utilities import findInFile, editFiles
import logging
import OpsServerConfig

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
    
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------   
    if len(sys.argv) < 5:
        print '\n' + scriptName + ' <PortalURL> <AdminUser> <AdminPassword> ' + \
                    '<ContentFolderPath> {UsersToPost} {OpsServerTypesToPost}'
        print '\nWhere:'
        print '\n\t<PortalURL> (required parameter): URL of Portal to post content (i.e. https://fully_qualified_domain_name/arcgis)'
        
        print '\n\t<AdminUser> (required parameter): Portal user that has administrator role.'
        
        print '\n\t<AdminPassword> (required parameter): Password for AdminUser.'
        
        print '\n\t<ContentFolderPath> (required parameter): Folder path containing portal content to post.'
        
        print '\n\t{UsersToPost} (optional parameter):'
        print '\t\t-By default, content for all users is posted'
        print '\t\t-Specify # placeholder character if you want to post content for all users and you are'
        print '\t\t   specifying {OpsServerTypesToPost} values'
        print '\t\t-To post content for only specific users specify comma delimited list of users, i.e. user1,user2,...'
        #print '\t\t   (to include spaces in this list surround with double-quotes, i.e. "user1, user2,...")'
        print '\t\t-To post content for ALL users except specific users, specify comma delimited '
        print '\t\t   list of users to exclude with "-" prefix, i.e. -user1,user2,...'
        #print '\t\t   (to include spaces in this list surround with double-quotes, i.e. "-user1, user2,...")'
        
        print '\n\t{OpsServerTypesToPost} (optional parameter):'
        print '\t\t-To post content for specific Ops Server types specify type value, i.e.'
        print '\t\t   ' + str(valid_ops_types)  + '; you can specify more then one type,'
        print '\t\t   i.e, Land,Maritime,...'
        #print '\t\t   (to include spaces in this list surround with double-quotes, i.e. "Land, Maritime,...")'
        
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
    
    ## Check if connection can be made to target portal
    ##result = val_portal_connection_props(target_portal_address, adminuser, adminpassword)
    
    # Check if specified content folder exists.
    if not val_arg_content_path(contentpath):
        print "Parameter <ContentFolderPath>: folder '" + contentpath + "' does not exist."
        sys.exit(1)
    
    # Check if specified users are valid
    users = val_arg_users(specified_users, contentpath)
    
    if DEBUG:
        print "Users to publish: " + str(users)
    
    
    # Check if specified ops server types are valid
    if specified_ops_types:
        results, specified_ops_types = val_arg_ops_types(specified_ops_types)
        if not results:
            print "Parameter {OpsServersToPost}: '" + str(specified_ops_types) + \
            "' does not contain valid value(s)."
            print "Valid {OpsServersToPost} values are: " + str(valid_ops_types)
            sys.exit(1)
    
    # Extract target ArcGIS Server hostname from target portal URL;
    # NOTE: this script assumes that the ArcGIS Server is installed
    # on the same machine as Portal for ArcGIS
    new_hostname =  parse_hostname(target_portal_address)
    hostname_map = {source_hostname: new_hostname}
        
    # Publish content to target portal
    publish_portal(target_portal_address, contentpath, adminuser, adminpassword, users, hostname_map, specified_ops_types)
    
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
def publish_portal(portaladdress,contentpath,adminuser,adminpassword, users, hostname_map, specified_ops_types):
    os.chdir(contentpath)
    
    
    
    portal_properties = json.load(open("portal_properties.json"))
    portaladmin = Portal(portaladdress, adminuser, adminpassword)
    
    print_script_header(portaladmin, portal_processing, users, specified_ops_types)

    # Create Portal log folder for this portal
    portalLogPath = os.path.join(contentpath, portalLogFolder, get_servername_from_url(portaladmin.url))
    makeFolder(portalLogPath)
    
    # ------------------------------------------------------------------------
    # Creating Users
    # ------------------------------------------------------------------------
    print titleBreak
    print "Creating users...\n"
    
    ## Create dictionary of users to post content for. The "userfile.txt"
    ## file contains user name and full name of user, i.e. userx,User X.
    ## Dictionary key is user name, dictionary value is password; in this
    ## case set the password the same as user name.
    #userfile = open(os.path.join(contentpath,'userfile.txt'),'r')
    #for line in userfile:
    #    username,fullname = line.split(',')
    #    users[username] = username
    #userfile.close()
    
    for username, password in users.iteritems():
       print "... " + str(username)
       publish_register_user(portaladmin,contentpath,username,password)
    
    # ------------------------------------------------------------------------
    # Create groups and add users to groups
    # ------------------------------------------------------------------------
    print "\n" + titleBreak
    print "Creating groups ...\n"
    
    for username, password in users.iteritems():
        portal = Portal(portaladdress, username, password)
        newGroups = publish_user_groups(portal,contentpath,username,password, users)
 
    # ------------------------------------------------------------------------
    # Publish Items and Update their sharing info
    # ------------------------------------------------------------------------
    print "\n" + titleBreak
    print "Publishing items and setting sharing ..."
    print titleBreak
    
    for username, password in users.iteritems():
        # ---------------------------------------
        # Sign into portal as the user
        # ---------------------------------------
        portal = Portal(portaladdress, username, password)
        
        # ---------------------------------------
        # Publish all the users' items
        # ---------------------------------------
        #NOTE: must execute with portal object signed in as item owner.
        newItems, origItemSourceIDs = publish_user_items(portal, contentpath, source_hostname, new_hostname, new_port, specified_ops_types)
        
        # Dump info about new items to JSON to use for resetting IDs of related items
        dump_newItem_info(newItems, origItemSourceIDs, os.path.join(portalLogPath, username))
        
        # ---------------------------------------
        # Reassign the users' items to the
        # appropriate user folder
        # ---------------------------------------
        #NOTE: must execute with portal object signed in as an admin.
        foldersFolder = os.path.join(contentpath, username)
        if os.path.exists(os.path.join(foldersFolder, "folders.json")):
            os.chdir(foldersFolder)
            foldersInfo = json.load(open('folders.json'))
            reassign_items(portaladmin, username, newItems, origItemSourceIDs, foldersInfo)
        
        # ---------------------------------------
        # Share the users' items with the
        # appropriate groups
        # ---------------------------------------
        #NOTE: must execute with portal object signed in as item owner.
        userItemsPath = os.path.join(contentpath, username, "items")
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
    
    #----------------------------------------------------------------
    # EL, 6/11/2013 - don't update the portal properties
    ##Portal Resources
    #publish_portal_resources(portaladmin,portal_properties)
    #
    ##Portal Updates
    #print "Portal property updates..."
    #resp = publish_portal_properties(portaladmin,portal_properties,source_portal_address,target_portal_address)  
    #


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
    
    
def reassign_items(portalAdmin, ownerName, newItems, origItemSourceIDs, foldersInfo):
    #portalAdmin - portal object that has admin permissions
    #ownerName - the new owner of the items; could be same owner.
    #newItems - info on the items that were added to portal
    #origItemSourceIDs - the original source ids of the newItems, order of ids must match
    #   order of newItems
    #foldersInfo - Json info about the users folders
    
    if foldersInfo is not None:
        
        print "Reassigning items to appropriate folder if applicable..."
        
        for x in range(0, len(origItemSourceIDs)):
            newItem = newItems[x]
            newID = newItem["id"]
            origID = origItemSourceIDs[x]
            
            # Get name of the folder for the item
            folderName = publish_get_folder_name_for_item(newItem, foldersInfo)
            
            # If for some reason the folder name could not determine, set the folderName to root "/"
            if folderName is None:
                folderName = "/"
                
            # Reassign item to folder
            portalAdmin.reassign_item(newID, ownerName, folderName)
    
def publish_register_user(portaladmin,contentpath,username,password):

    userfolder = os.path.join(contentpath + "/" + username)
    os.chdir(userfolder)
    
    # Get user properties from file
    userproperties = json.load(open("userinfo.json"))
    fullname = userproperties["fullName"]
    role = userproperties["role"]
    email = userproperties["email"]
    
    # Register user
    portaladmin.signup(username,password,fullname,email)
    
    # Modify user role
    portaladmin.update_user_role(username, role)

    # Update user properties on portal
    #MF finding a few 'preferredView' properties that are 'null'/None
    if userproperties['preferredView'] == 'null' or userproperties['preferredView'] == None:
        userproperties['preferredView'] = 'GIS' #MF use GIS as the default instead of Web
        portaladmin.update_user(username,userproperties)
        
    # Create any folders for this user
    userfolder = os.path.join(contentpath, username)
    os.chdir(userfolder)
    if os.path.exists('folders.json'):
        folderInfo = json.load(open('folders.json'))
        for folder in folderInfo:
            folderName = folder[1]
            print "...... creating folder '" + folderName + "'"
            portaladmin.create_folder(username, folderName)
            

#def tags_exist(find_tags, tags_to_search):
#    found = False
#    
#    # Create list of possible "OpsServer" type tag prefixes; i.e. in case someone didn't
#    # specify the correct prefix.
#    ops_type_flags = ["opsserver", "opsservers", "opserver", "opservers", "opssrver", "opssrvr"]
#    
#    # Convert find_tags to lower case and remove and leading/trailing spaces
#    find_tags_mod = [element.lower().strip() for element in list(find_tags)]
#    
#    # Convert tags_to_search to lower case and remove and leading/trailing spaces
#    tags_to_search_mod = [element.lower().strip() for element in list(tags_to_search)]
#    
#    # Loop through tags to search and look for the find tags
#    for search in tags_to_search_mod:
#        search = search.replace(" ","")
#        if search.find(":") > -1:
#            element1 = search.split(":")[0]
#            element2 = search.split(":")[1]
#            
#            if element1 in ops_type_flags:
#                if element2 in find_tags:
#                    found = True
#    
#    return found

def publish_user_items(portal, contentpath, old_hostname, new_hostname, new_port, specified_ops_types):
    ''' Publish all items for current user '''
    # Returns list of dictionaries of new items as well as a list of the
    # original item ids
    
    print "\n" + sectionBreak
    userName = portal.logged_in_user()["username"]
    print "Publishing items for user '" + userName + "'...\n"
    #print "specified_ops_types: " + str(specified_ops_types)
    itemfolder = os.path.join(contentpath,userName,"items")

    #EL this assumes that everything in the itemFolder is a folder
    #itemfolders = os.listdir(itemfolder)
    
    # ------------------------------------------------------------------------
    # Add items
    # ------------------------------------------------------------------------
    newitems, old_source_ids = load_items_based_on_tags(portal, itemfolder, specified_ops_types)

    return newitems, old_source_ids

#def publish_user_items(portal, contentpath, old_hostname, new_hostname, new_port, specified_ops_types):
#    ''' Publish all items for current user '''
#    # Returns list of dictionaries of new items as well as a list of the
#    # original item ids
#    
#    print "\n" + sectionBreak
#    userName = portal.logged_in_user()["username"]
#    print "Publishing items for user '" + userName + "'...\n"
#    itemfolder = os.path.join(contentpath,userName,"items")
#
#    #EL this assumes that everything in the itemFolder is a folder
#    itemfolders = os.listdir(itemfolder)
#    
#    # ------------------------------------------------------------------------
#    # Add items
#    # ------------------------------------------------------------------------
#    newitems_all = []
#    old_source_ids_all = []
#    
#    for item_folder_name in itemfolders:
#        load_item = False
#        item_folder_path = os.path.join(itemfolder, item_folder_name)
#        print "-------------------------------------------------"
#        print "item_folder_path: " + item_folder_path
#        
#        if not specified_ops_types:
#            load_item = True
#        
#        if specified_ops_types:
#            print "specified_ops_types: " + str(specified_ops_types)
#            
#            # Get the item's json file
#            os.chdir(item_folder_path)
#            item = json.load(open("item.json"))
#            tags = item.get("tags")
#            
#            print "item tags: " + str(tags)
#            #print "b4 function: specified_ops_types: " + str(specified_ops_types)
#            
#            load_item = tags_exist(specified_ops_types, tags)
#            print "found: " + str(load_item)
#            #print "after function: specified_ops_types: " + str(specified_ops_types)
#            #print "after function: tags: " + str(tags)
#        
#        if load_item:
#            
#            # Load the item contained in the specified item folder
#            newitems, old_source_ids = load_items(portal, item_folder_path)
#
#            # Append the lists of new items and the original source ids to lists
#            # containing all of the users items
#            newitems_all.extend(newitems)
#            old_source_ids_all.extend(old_source_ids)
#            
#    return newitems_all, old_source_ids_all

#def publish_user_items(portal, contentpath, old_hostname, new_hostname, new_port):
#    ''' Publish all items for current user '''
#    # Returns list of dictionaries of new items as well as a list of the
#    # original item ids
#    
#    print "\n" + sectionBreak
#    userName = portal.logged_in_user()["username"]
#    print "Publishing items for user '" + userName + "'...\n"
#    itemfolder = os.path.join(contentpath,userName,"items")
#
#    #EL this assumes that everything in the itemFolder is a folder
#    itemfolders = os.listdir(itemfolder)
#    
#    # ------------------------------------------------------------------------
#    # Add items
#    # ------------------------------------------------------------------------
#    newitems, old_source_ids = load_items(portal, itemfolder)
#
#    return newitems, old_source_ids

def publish_user_groups(portal,contentpath,username,password, users):
    #MF print portal.logged_in_user["username"]
    groupfolder = os.path.join(contentpath + "/" + username + "/groups")
    groupfolders = os.listdir(groupfolder)
    
    numTotalGroupFolders = len(groupfolders)
    if numTotalGroupFolders == 0:
        print "\nUser '" + username + "' does not own any groups."
    else:
        print "\nCreating " + str(numTotalGroupFolders) + " group(s) for user '" + username + "'..."
    
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
        
        print "... group " + str(group['title'])
        groupId = portal.create_group(group,group['thumbfile'])
        destGroupID_GroupName[groupId] = str(group['title']) #EL Track new group id and group name for later use
        
        print "...... adding users to group"
        if groupId:
            originGroupToDestGroups[oldGroupID] = groupId
            groups = []
            groups.append(groupId)
            
            # Check if users are in the list we added to the portal
            users_to_invite = []
            portal_users = users.keys()
            for u in group_users["users"]:
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

def val_arg_users(specified_users, contentpath):
    all_users = {}          # Contains all users in the userfile.txt file.
    values_to_use = {}      # Contains users that that will be published
    exclude_users_list = [] # Contains users that should be excluded from publishing
    include_users_list = []
    
    if not specified_users:
        specified_users = ""
    else:
        specified_users = specified_users.strip()
    
    # Create dictionary of users based on contents of userfile.txt file.
    # The "userfile.txt" file contains user name and full name of user,
    # i.e. userx,User X. Dictionary key is user name, dictionary value
    # is password; in this case set the password the same as user name.
    userfile = open(os.path.join(contentpath,'userfile.txt'),'r')
    for line in userfile:
        username,fullname = line.split(',')
        all_users[username] = username
    userfile.close()

    
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

#def val_portal_connection_props(portal_address, username, password):
#    portal_con = Portal(portal_address, username, password)
#    if portal_con:
#        print "portal con is valid"
#    else:
#        print "not valid"
#    #print str(portal_con.logged_in_user)

if __name__ == "__main__":
    main()
