
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# -------------------------------------------------------
# Wipes out all items, groups and users from portal and
# leaves only the adminuser account.
# -------------------------------------------------------
# v1.0 - 11/**/2012
# -------------------------------------------------------
# - 10/30/2012 - MF - Original
# - 06/13/2013 - EL - Modified to use portalpy v. 1.08a
#                   which has new cascade parameter which
#                   greatly simplifies deleting content
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++

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
