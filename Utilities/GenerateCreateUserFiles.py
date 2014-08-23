#!/usr/bin/env python
#==============================================================================
#Name:          GenerateCreateUserFiles.py
#
#Purpose:       Creates the input files used by the CreateUsers.bat file from
#               the portal content extracted by the PortalContentExtract.py
#               script.
#
#Prerequisites: - Portal items must have been extracted to disk.
#
#History:       2014/07/30:   Initial code.
#
#==============================================================================
import sys, os, traceback, json

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), 'SupportFiles'))

from Utilities import findFilePath

scriptName = sys.argv[0]
exitErrCode = 1
sectionBreak = '=' * 175
sectionBreak1 = '-' * 175

userinfo_file = 'userinfo.json'
account_password = 'MyPassword!' # Built-in account password
email_suffix = '@no_email_in_user_profile.org'
ent_filename = 'enterprise_users.txt'
builtin_filename = 'builtin_users.txt'
out_ent_f = None        # Enterprise account file object
out_builtin_f = None    # Built-in account file object
file_objects = [out_ent_f, out_builtin_f]

def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) <> 3:
        
        print '\n' + scriptName + ' <PortalContentFolder> <OutputFolder>'

        print '\nWhere:'
        print '\n\t<PortalContentFolder> (required): path to the folder containing the extracted portal content.'
        print '\n\t<OutputFolder> (required): path to the folder where the output user files ({}, {}) will be created.\n'.format(ent_filename, builtin_filename)
        return None
    
    else:
        
        # Set variables from parameter values
        content_folder = sys.argv[1]
        output_folder = sys.argv[2]
        
        # Verify that paths exist
        if not os.path.exists(content_folder):
            print '\nERROR: <PortalContentFolder> path {} does not exist.\n'.format(content_folder)
            sys.exit(exitErrCode)
        if not os.path.exists(output_folder):
            print '\nERROR: <OutputFolder> path {} does not exist.\n'.format(output_folder)
            sys.exit(exitErrCode)
        
    return content_folder, output_folder

def get_userinfo_files(portal_content_folder):
    userinfo_files = findFilePath(portal_content_folder, userinfo_file, returnFirst=False)
    return userinfo_files

def is_enterprise_account(userinfo):
    ''' Returns boolean indicating if account is an enterprise account '''
    
    #idp_username = userinfo.get('idpUsername')
    #print 'idp_username: {}'.format(idp_username)
    #if idp_username:
    #    if idp_username != 'null':
    #        print 'It''s not a null'
    return userinfo['username'].find('@') > -1

def create_account_recs(portal_content_folder):
    ent_accounts = []
    builtin_accounts = []
    
    userinfo_files = get_userinfo_files(portal_content_folder)
    
    for userinfo_file in userinfo_files:
        os.chdir(os.path.dirname(userinfo_file))
        userinfo = json.load(open(userinfo_file))
        
        login = userinfo['username']
        email = userinfo['email']
        name = userinfo['fullName']
        role = userinfo['role']
        description = str(userinfo['description']) # Optional
        idpusername = str(userinfo['idpUsername']) # Optional
        
        # Perform some extra processing
        if not email:
            email = login.split('@')[0] + email_suffix
        if description == 'None':
            description = ''
        if idpusername == 'null':
            idpusername = ''
        
        if is_enterprise_account(userinfo):
            account = [login, email, name, role, description, idpusername]
            ent_accounts.append('|'.join(account))
        else:
            account = [login, account_password, email, name, role, description]
            builtin_accounts.append('|'.join(account))
            
    return ent_accounts, builtin_accounts

def write_files(output_folder, ent_accounts, builtin_accounts):
    
    out_ent_file = output_folder + os.path.sep + ent_filename
    out_builtin_file = output_folder + os.path.sep + builtin_filename
    
    # Delete existing files
    if os.path.exists(out_ent_file):
        os.remove(out_ent_file)
    if os.path.exists(out_builtin_file):
        os.remove(out_builtin_file)
    
    # Write files
    if len(ent_accounts) > 0:
        out_ent_f = open(out_ent_file, 'w')
        for account in ent_accounts:
            out_ent_f.write('{}\n'.format(account))
        out_ent_f.close()
        
    if len(builtin_accounts) > 0:
        out_builtin_f = open(out_builtin_file, 'w')
        for account in builtin_accounts:
            out_builtin_f.write('{}\n'.format(account))
        out_builtin_f.close()
        
def main():
    
    totalSuccess = True
    out_ent_file = None
    out_builtin_file = None
    
    # -------------------------------------------------
    # Check arguments
    # -------------------------------------------------
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    
    # Get parameter values
    content_folder, output_folder = results
    
    try:
        print '\n- Assembling user account info from extracted portal content...'
        ent_accounts, builtin_accounts = create_account_recs(content_folder)
        
        print '\n- Writing user account info to output files...'
        write_files(output_folder, ent_accounts, builtin_accounts)
        
        print '\nDone.\n'
        
    except:
        totalSuccess = False
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
     
        # Concatenate information together concerning the error into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
     
        # Print Python error messages for use in Python / Python Window
        print
        print "***** ERROR ENCOUNTERED *****"
        print pymsg + "\n"
        
    finally:
        for file_object in file_objects:
            if hasattr(file_object, 'close'):
                file_object.close()
            
        if totalSuccess:
            sys.exit(0)
        else:
            sys.exit(exitErrCode)
   
if __name__ == "__main__":
    main()
