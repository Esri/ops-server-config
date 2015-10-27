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
#Name:          PortalContentExtract.py
#           
#Purpose:       Extracts users/groups/items from a portal to files on disk.
#
#==============================================================================

import portalpy
import os, sys
import json
import urlparse
import types
import shutil
from datetime import datetime, timedelta
from portalpy import Portal, parse_hostname, portal_time, WebMap
import logging
TEXT_BASED_ITEM_TYPES = portalpy.TEXT_BASED_ITEM_TYPES
FILE_BASED_ITEM_TYPES = portalpy.FILE_BASED_ITEM_TYPES

logging.basicConfig()

portal_processing = "EXTRACT"
titleBreak = "====================================================================================="
sectionBreak = "------------------------------------------------------------------------------------"
sectionBreak2 = "--------------------"

users = {}

#track stored IDs to new IDs when posting groups
originGroupToDestGroups = {}

def main():

    scriptName = sys.argv[0]
    specifiedUsers = ""
    
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------   
    if len(sys.argv) < 5:
        print "\n" + scriptName + " <PortalURL> <AdminUser> <AdminPassword> " + \
                    "<ExtractFolderPath> {UsersToExtract}"
        print "\nWhere:"
        print "\n\t<PortalURL> (required parameter): URL of Portal to extract content (i.e. https://my_portal.domain/arcgis)"
        print "\n\t<AdminUser> (required parameter): Portal user that has administrator role."
        print "\n\t<AdminPassword> (required parameter): Password for AdminUser."
        print "\n\t<ExtractFolderPath> (required parameter): Folder path where portal content is extracted."
        print "\n\t{UsersToExtract} (optional parameter):"
        print "\t\t-By default all users are extracted (except for 'admin', 'administrator', and 'system_publisher')"
        print "\t\t-To extract content for specific users specify comma delimited list of users, i.e. user1,user2,..."
        print "\t\t   (make sure there are no spaces within this list of users)"
        print "\t\t-To extract content for ALL users except specific users, specify comma delimited "
        print "\t\t   list of users to exclude with '-' prefix, i.e. -user1,user2,..."
        print "\t\t   (make sure there are no spaces within this list of users)"
        print
        sys.exit(1)
    
    
    source_portal_address = sys.argv[1]
    adminuser = sys.argv[2]
    adminpassword = sys.argv[3]
    contentpath = sys.argv[4]
    if len(sys.argv) == 6:
        specifiedUsers = sys.argv[5]
        
    print_script_header(source_portal_address, portal_processing)
    if not os.path.exists(contentpath):
        os.makedirs(contentpath)
    else:
        shutil.rmtree(contentpath)
    extract_portal(source_portal_address,contentpath,adminuser,adminpassword,specifiedUsers)
    os.chdir(contentpath)    
    
    print "\nDONE."

def print_script_header(source_portal_address, portal_processing):
    print titleBreak
    print "                           Portal Content Extract"
    print titleBreak
    print "Processing type: " + "\t" + portal_processing
    print "Source portal URL: " + "\t" + source_portal_address
    print
    print
    
# EXTRACT
def extract_portal(portaladdress,contentpath,adminuser,adminpassword, specifiedUsers):
    '''Extract Portal info and content for all specified users'''
    
    specifiedUsers = specifiedUsers.lower()
    excludeUsersList = []
    includeUsersList = []
    #if first character is a minus, then the "specifiedUsers" variable
    # contains a comma delimited string of the users to exclude from the extract
    if len(specifiedUsers) > 0:
        if specifiedUsers.find("-") == 0:
            specifiedUsers = specifiedUsers.replace("-","",1)
            excludeUsersList = specifiedUsers.split(",")
        else:
            includeUsersList = specifiedUsers.split(",")
    
    # Create root output folder if it doesn't exist.
    if not os.path.exists(contentpath):
            os.makedirs(contentpath)
    os.chdir(contentpath)
    
    #Make Admin connection to portal and retrieve portal info
    portaladmin = Portal(portaladdress, adminuser, adminpassword)
    

    # ------------------------------------------------------------------------
    # Extract Portal Properties
    # ------------------------------------------------------------------------
    portal_properties = portaladmin.properties()
    
    print "\n- Extracting portal info ..."
    json.dump(portal_properties, open('portal_properties.json','w'))
    
    #Get portal featured items
    
    # get a list of portal resources
    resources = portaladmin.resources(portal_properties['id'])
    json.dump(resources,open('resources.json','w'))
 
    # ------------------------------------------------------------------------
    # Extract users, groups and items
    # ------------------------------------------------------------------------       
    print "\n- Extracting users, groups and items ..."
    
    # Get list of users on the source portal
    usersList = []
    usersListAllNames = portaladmin.users()
    
    # Create list of users that we don't want to extract content for.
    # NOTE: specify user names in lowercase.
    userExcludeList = ["admin", "system_publisher", "administrator"]
    
    # If user has specified users to exclude from extract then add these
    # users to the exclude list
    if len(excludeUsersList) > 0:
        userExcludeList.extend(excludeUsersList)
    
    # Create output file to store username and fullname properties
    userfile = open(os.path.join(contentpath,'userfile.txt'),'w')
    
    # If only specific users should be extracted
    # then only keep those users in the user information dictionary
    if len(includeUsersList) > 0:
        for u in usersListAllNames:
            userName = u["username"]
            if userName.lower() in includeUsersList:
                usersList.append(u)
    else:
        usersList = usersListAllNames
    
    userfile.write("SourceUserName,TargetUserName,TargetPassword\n")
    
    for u in usersList:
        userName = u["username"]
        if userName.lower() not in userExcludeList:
            users[str(userName)] = None
            userfile.write(userName + "," + userName + ",MyDefault4Password!" + "\n")
    userfile.close()   
    
    for username in users.keys():
        # Create output folder if it doesn't exist
        extractpath = os.path.join(contentpath, username)
        if not os.path.exists(extractpath):
            os.makedirs(extractpath)
        
        print "\n" + sectionBreak
        print "Extracting content for user: " + username
        
        # Dump user info to json file
        userinfo = portaladmin.user(username)
        filepath = os.path.join(extractpath, 'userinfo.json')
        json.dump(userinfo, open(filepath,'w'))

        # Extract folders for user
        extract_folders(portaladmin, extractpath, username)
        
        # Extract items owned by user
        extract_items(portaladmin, extractpath, username)
    
        # Extract groups owned by user
        extract_groups_from_user_info(portaladmin, userinfo, extractpath)

def extract_folders(portal, extractpath, username):
    
    # Get info about root items and those contained in folders
    root_items, folder_items = portal.user_contents(username)
    
    # Extract folder info
    if len(folder_items) > 0:
        os.chdir(extractpath)
        # Dump folder info to json file
        json.dump(folder_items, open('folders.json','w'))
    
    
def extract_groups_from_user_info(portal, userinfo, extractpath):
    '''Extract groups from user info '''
    # Function created 5/21/2013 to replace "extract_groups" function.
    # Because the password is not the same as the user name, we can't
    # login as the individual user to extract all the groups that
    # are owned by a user (i.e. public and private). So to work around
    # this fact, we are extracting the groups from the user info object,
    # which do contain both public and private groups.
    
    grouppath = os.path.join(extractpath, "groups")
    if not os.path.exists(grouppath):
        os.makedirs(grouppath)
    
    # userinfo.json file contains the all the groups that the user
    # belongs to; so extract only those groups which are owned by the user.
    groups = []
    allgroups = userinfo["groups"]
    for x in allgroups:
        if x["owner"] == userinfo["username"]:
            groups.append(x)
        
    if len(groups) == 0:
        print "\n- Groups: No groups."
    else:
        print "\n- Groups:"
        for group in groups:
            groupidpath = os.path.join(grouppath, group["id"])
            os.makedirs(groupidpath)
            os.chdir(groupidpath)
            if group:
                thumbfile = portal.group_thumbnaild(group["id"],groupidpath)
                group = portal.group(group["id"])
                print "... group '" + str(group['title']) + "' to " + str(group['id'])
                #MF users = portal.group_users(group["id"])
                users = portal.group_members(group["id"])
                
                if thumbfile:
                    thumbfile = os.path.basename(thumbfile)
                group["thumbfile"] = thumbfile
                json.dump(group, open('group.json','w'))
                json.dump(users, open('group_users.json','w'))
    
def do_extract_item(portal, item_id):
    extract = True
    exclude_item_types = ["Code Attachment"]
    item = portal.item(item_id)
    if item['type'] in exclude_item_types:
        extract = False
    return extract

def extract_items(portal,extractpath, username):
    '''Extract all items to a folder for a logged in user'''        
    itempath = os.path.join(extractpath, "items")
    if not os.path.exists(itempath):
        os.makedirs(itempath)
    os.chdir(itempath)

    # Get info about root items and those contained in folders
    root_items, folder_items = portal.user_contents(username)

    print "\n- Items:"
    
    # Extract root items
    if len(root_items) > 0:
        print "   - Root items:"
        for item in root_items:
            print "...... item '{}' [type: {}] to folder '{}'".format(item['title'], item['type'], item['id'])
            if not do_extract_item(portal, item['id']):
                print "WARNING: Skipping extract of this item '{}' [type: {}]".format(item['title'], item['type'])
                continue
            extract_item(portal,item["id"],username,folder='')
            os.chdir(itempath)
    else:
        print "   - Root items: No items."
        
    
    # Extract items in folders
    if len(folder_items) > 0:
        print "\n   - Folder items:"
        
        # Extract the items in each folder
        for folder_id, folder_title, items in folder_items:
            if len(items) > 0:
                print "       Folder '" + folder_title + "'..."
                for item in items:
                    print "........ item '{}' [type: {}] to folder '{}'".format(item['title'], item['type'], item['id'])
                    if not do_extract_item(portal, item['id']):
                        print "WARNING: Skipping extract of this item '{}' [type: {}]".format(item['title'], item['type'])
                        continue
                    extract_item(portal,item["id"],username,folder=folder_id)
                    os.chdir(itempath)
            else:
                print "       Folder '" + folder_title + "': contains no items."
    else:
        print "\n   - Folder items: No folders."

def extract_item(portal,itemid,username,folder=''):
    '''Extract single item to disk for a logged in user'''
    itemidpath = os.path.join(os.path.abspath(os.curdir), itemid)
    os.makedirs(itemidpath)
    os.chdir(itemidpath)
    
    itemdata = None
    
    iteminfo = portal.item(itemid)
    
    # Handle the data
        
    if iteminfo['type'] in TEXT_BASED_ITEM_TYPES:
        text = portal.item_data(iteminfo['id'])
        if text and len(text) > 0:
            iteminfo['text'] = text
    elif iteminfo['type'] in FILE_BASED_ITEM_TYPES:
        data_dir = os.path.join(itemidpath, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        portal.item_datad(iteminfo['id'], data_dir, iteminfo.get('name'))
    
    thumbfile = portal.item_thumbnaild(itemid,itemidpath)
    
    #TODO check if the itemdata file exists?
    
    if thumbfile:
        thumbfile = os.path.basename(thumbfile)
        iteminfo["thumbfile"] = thumbfile #EL 6/27/2013
        # Reset the "thumbnail" value because the portalpy will truncate
        # the thumnailfile to 30 characters.
        iteminfo["thumbnail"] = "thumbnail/" + thumbfile
    
    json.dump(iteminfo, open('item.json','w'))

    sharinginfo = portal.user_item(itemid,username,folder)
    json.dump(sharinginfo[1], open('sharing.json','w'))

if __name__ == "__main__":
    main()
