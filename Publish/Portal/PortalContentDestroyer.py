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

def main():
    
    scriptName = sys.argv[0]
    
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------   
    if len(sys.argv) <> 4:
        print '\n' + scriptName + ' <PortalURL> <AdminUser> <AdminPassword>'

        print '\nWhere:'
        print '\n\t<PortalURL> (required parameter): URL of Portal to delete content (i.e. https://fully_qualified_domain_name/arcgis)'
        print '\n\t<AdminUser> (required parameter): Portal user that has administrator role.'
        print '\n\t<AdminPassword> (required parameter): Password for AdminUser.\n'
        sys.exit(1)
    
    # Set variables from script parameters
    portal_address = sys.argv[1]
    adminuser = sys.argv[2]
    adminpassword = sys.argv[3]

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
    print "Excluded users: " + str(exclude_users)
    print
    
    print "WARNING: this script will delete all user content in the specified portal: "
    print portaladmin.url + "\n"
    user_response = raw_input("Do you want to continue? Enter 'y' to continue: ")
    
    if not val_user_response(user_response):
        print "Exiting script..."
        sys.exit(1)
    
    # get a list of users
    portal_users = portaladmin.users()
    
    # Create list of users to delete
    portal_users_to_del = []
    for portal_user in portal_users:
        if portal_user['username'] not in exclude_users:
            portal_users_to_del.append(portal_user)    
    
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
