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
#Name:          PortalContentDestroyer.py
#           
#Purpose:       Deletes all items, groups and users from portal except for
#               specified admin account
#
#==============================================================================

import portalpy
import os
import json
import shutil
from datetime import datetime, timedelta
from portalpy import Portal, parse_hostname, portal_time
import sys
import logging

logging.basicConfig()

# Do not delete the content for the following users
exclude_users = ['system_publisher']

sectionBreak = '================================================'


DEBUG = False

def val_user_response(value):
    do_continue = False
    valid_values = ['y', 'yes'] # specified values in lowercase
    if not value:
        value = ''
    value = value.lower().strip().replace(" ","")
    if value in valid_values:
        do_continue = True
    return do_continue

def printResponse(response):
    if response == True:
        print "\t\tSuccessful."
    else:
        print "\t\t*** Error deleting."

def val_arg_users(portal, specified_users):
    values_to_use = []
    exclude_users_list = [] # Contains users that should be excluded
    include_users_list = [] # Contains users that should be included
    
    if specified_users:
        specified_users = specified_users.strip()
    
    # get a list of all portal users
    all_users = portal.users()

    # if there are no specified users then return all users
    if specified_users is None:
        return all_users
    
    elif specified_users == "#":
        return all_users
    
    elif specified_users.find("-") == 0:
        # Return all the users that _aren't_ in the specified users list.
        values_to_use = list(all_users)
        exclude_users = specified_users.replace("-","",1)
        exclude_users_list = [element.lower().strip() for element in exclude_users.split(",")]

        for exclude_user in exclude_users_list:
            for user in all_users:
                if exclude_user.lower() == user['username'].lower():
                    values_to_use.remove(user)

        return values_to_use
    
    else:
        # Return all the users that _are_ in the specified users list
        include_users_list = [element.lower().strip() for element in specified_users.split(",")]

        for include_user in include_users_list:
            for user in all_users:
                if include_user.lower() == user['username'].lower():
                    if user not in values_to_use:
                        values_to_use.append(user)

        return values_to_use
    
def main():
    
    scriptName = sys.argv[0]
    specified_users = None
    
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------   
    if len(sys.argv) < 4:
        print '\n' + scriptName + ' <PortalURL> <AdminUser> <AdminPassword> {UsersToDelete}'

        print '\nWhere:'
        print '\n\t<PortalURL> (required parameter): URL of Portal to delete content (i.e. https://fully_qualified_domain_name/arcgis)'
        print '\n\t<AdminUser> (required parameter): Portal user that has administrator role.'
        print '\n\t<AdminPassword> (required parameter): Password for AdminUser.'
        print '\n\t{UsersToDelete} (optional):'
        print '\t\t-By default, all users are deleted.'
        print '\t\t-To delete only specific users, specify comma delimited list of users, i.e. user1,user2,...'
        print '\t\t-To delete ALL except specific users, specify comma delimited '
        print '\t\t   list of users not to delete using "-" prefix, i.e. -user1,user2,...'
        sys.exit(1)
    
    # Set variables from script parameters
    portal_address = sys.argv[1]
    adminuser = sys.argv[2]
    adminpassword = sys.argv[3]
    if len(sys.argv) > 4:
        specified_users = sys.argv[4]

    # Add specified user parameter value to exclude list.
    if adminuser not in exclude_users:
        exclude_users.append(adminuser)
            
    # Create portal object based on specified connection information
    portaladmin = Portal(portal_address, adminuser, adminpassword)
    portalProps = portaladmin.properties
    
    print sectionBreak
    print "Deleting Portal Content"
    print sectionBreak
    print "Portal: " + portaladmin.hostname
    print "Hardcoded users to exclude from delete: " + str(exclude_users)
    print "User specified users to include/exclude(-) from delete: " + str(specified_users)
    print
    
    print "WARNING: this script will delete all user content in the specified portal: "
    print portaladmin.url + "\n"
    user_response = raw_input("Do you want to continue? Enter 'y' to continue: ")
    
    if not val_user_response(user_response):
        print "Exiting script..."
        sys.exit(1)
    
    # get a list of users
    portal_users_to_del = val_arg_users(portaladmin, specified_users)
    
    # Remove excluded users from list of users to delete
    for user_to_del in portal_users_to_del:
        if user_to_del['username'].lower() in exclude_users:
            portal_users_to_del.remove(user_to_del)     
    
    if len(portal_users_to_del) == 0:
        print "\nWARNING: there are no users to delete. Exiting script."
        sys.exit(1)
    
    # remove their groups and items
    for user_dict in portal_users_to_del:
        current_user = user_dict['username']
        
        print sectionBreak
        print "User: \t" + current_user
        
        # Delete the user and all owned groups and content
        resp = portaladmin.delete_user(current_user, cascade=True)
        printResponse(resp)
            
    print "\nDONE: Finished deleting content from portal."
    
if __name__ == "__main__":
    main()
