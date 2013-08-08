#!/usr/bin/env python
#==============================================================================
#Name:          SetServicesDirectoryProps.py
#Purpose:       Sets the paths of the ArcGIS API for JavaScript to use
#               locally hosted JavaScript API and map viewer
#                   
#Prerequisites: None
#
#History:       2013/08/08: E.L. - Initial code.
#
#==============================================================================
import sys, os, traceback
from AGSRestFunctions import getServicesDirectory
from AGSRestFunctions import editServicesDirectory

scriptName = os.path.basename(sys.argv[0])
exitSuccessCode = 0
exitErrCode = 1
debug = False

def main():
    totalSuccess = True
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    server_fqdn, port, user, password = results
    
    if debug:
        print 'Parameter values: ', server_fqdn, port, user, password
    
    try:
        
        # ---------------------------------------------------------------------
        # Get the current ArcGIS Server Services Directory properties
        # ---------------------------------------------------------------------
        
        # Obtain current services directory properties so that the
        # 'allowedOrigins' and 'jsapi.arcgis.sdk' are set to these same values
        # (REST request will fail with a 'java.lang.NullPointerException' if all the
        # properties are not specified in the 'edit' request)
        success, s_dir_props = getServicesDirectory(server_fqdn, port, user, password)
        if not success:
            raise Exception('ERROR: Encountered issue getting current ' +
                    'services directory properties: \n' + str(s_dir_props))
        
        # ---------------------------------------------------------------------
        # Create services directory property values
        # ---------------------------------------------------------------------
        print '\n- Setting services directory properties...\n'
        
        arcgis_com_map = 'https://{}/arcgis/home/webmap/viewer.html'.format(server_fqdn)
        arcgis_com_map_text = 'Portal Map Viewer'
        jsapi_arcgis = 'https://{}/arcgis/jsapi/jsapi/'.format(server_fqdn)
        jsapi_arcgis_css = 'https://{}/arcgis/home/js/dojo/dijit/themes/tundra/tundra.css'.format(server_fqdn)
        jsapi_arcgis_css2 = 'https://{}/arcgis/home/js/esri/css/esri.css'.format(server_fqdn)
        
        # NOTE: Because key for the services directory enabled/disabled is incorrectly
        # returned as 'enabled' instead of 'servicesDirEnabled', let's check for
        # both keys; checking for key 'servicesDirEnabled' in case this key
        # fixed.
        if s_dir_props.get('enabled'):
            services_dir_enabled = s_dir_props.get('enabled')
        elif s_dir_props.get('servicesDirEnabled'):
            services_dir_enabled = s_dir_props.get('servicesDirEnabled')
        else:
            services_dir_enabled= 'true'
        
        # Set the Services Directory properties
        success, response = editServicesDirectory(server_fqdn, port, user, password,
                            s_dir_props['allowedOrigins'], arcgis_com_map,
                            arcgis_com_map_text, jsapi_arcgis,
                            jsapi_arcgis_css, jsapi_arcgis_css2,
                            s_dir_props['jsapi.arcgis.sdk'], services_dir_enabled)
        if not success:
            raise Exception('ERROR: Encountered issue setting services ' +
                    'directory properties: \n' + str(response))

        # ---------------------------------------------------------------------
        # Get the updated set ArcGIS Server Services Directory properties and
        # display the new values
        # ---------------------------------------------------------------------
        success, s_dir_props = getServicesDirectory(server_fqdn, port, user, password)
        if not success:
            raise Exception('ERROR: Encountered issue getting updated ' +
                    'services directory properties: \n' + str(s_dir_props))
        
        props_not_altered = ['consoleLogging', 'logLevel', 'enabled',
                            'servicesDirEnabled', 'jsapi.arcgis.sdk',
                            'allowedOrigins']

        print '- Services directory property values after update...\n'
        print '{:<30}{:<90}'.format('Property', 'Value')
        print '-' * 100
        for key in s_dir_props:
            keyName = key
            if keyName in props_not_altered:
                keyName = keyName + '*'
            print '{:<30}{:<90}'.format(keyName, s_dir_props[key])
        print '\n* These properties are not altered.'
        
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
        exe_str = '\nExecution of ' + scriptName + ' completed '
        if totalSuccess:
            print exe_str + 'successfully.'
            sys.exit(exitSuccessCode)
        else:
            print 'ERROR: ' + exe_str + 'unsuccessfully.'
            sys.exit(exitErrCode)

def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) <> 5:
        
        print '\n' + scriptName + ' <AGS_FQDN> <Port> <AdminUser> <AdminPassword>'
    
        print '\nWhere:'
        print '\t<AGS_FQDN> (required parameter): the fully qualified domain name of the ArcGIS Server.'
        print '\n\t<Port> (required parameter): the port number of the ArcGIS Server (specify # if no port).'
        print '\n\t<AdminUser> (required parameter): ArcGIS Server site administrator.'
        print '\n\t<AdminPassword> (required parameter): Password for ArcGIS Server site administrator.'
        print '\nPurpose:'
        print '\tSets the paths of the ArcGIS API for JavaScript to use the'
        print '\tthe locally hosted JavaScript API and map viewer installed'
        print '\tduring the installation of Portal for ArcGIS.'
        print '\n\tNote(s):'
        print '\t- The properties set by this script can be examined using'
        print '\tthe following ArcGIS Server Admin REST API URL:'
        print '\thttps://server.domain/arcgis/admin/system/handlers/rest/servicesdirectory'
        print '\n\t- Script does not validate property values.'
        print '\n\t- Script is hardcode to set the JavaScript API URLs'
        print '\tusing https.'
        return None
    
    else:
        
        # Set variables from parameter values
        server_fqdn = sys.argv[1].lower()
        port = sys.argv[2]
        adminuser = sys.argv[3]
        password = sys.argv[4]
        
        if port.strip() == '#':
            port = None
            
    return server_fqdn, port, adminuser, password

if __name__ == "__main__":
    main()