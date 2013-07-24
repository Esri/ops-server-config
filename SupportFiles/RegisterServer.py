#==============================================================================
#Name:          RegisterServer.py
#Purpose:       
#
#Prerequisites: 
#
#History:       2013/02/25:   Initial code.
#
#==============================================================================
import sys, os, traceback

import urllib
import urllib2
import json

scriptName = sys.argv[0]

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------
if len(sys.argv) <> 8:
    print "\n" + scriptName + " <PortalFullyQualifiedDomainName>"+ \
			    " <PortalAdminUserName>" + \
			    " <PortalAdminPassword>" + \
			    " <ServerFullyQualifiedDomainName>" + \
			    " <ServerPort>" + \
			    " <ServerAdminUserName>" + \
                            " <ServerAdminPassword>"
    print "\nWhere:"
    print "\n\t<PortalFullyQualifiedDomainName> (required parameter) - the fully qualified domain name of the Portal."
    print "\n\t<PortalAdminUserName> (required parameter) - the portal administrator user name."
    print "\n\t<PortalAdminPassword> (required parameter) - the portal administrator password."   
    print "\n\t<ServerFullyQualifiedDomainName> (required parameter) - the fully qualified domain name of the ArcGIS Server being registered."
    print "\n\t<ServerPort> (required parameter) - the ArcGIS Server port number."
    print "\n\t<ServerAdminUserName> (required parameter) - ArcGIS Server site administrator user name."
    print "\n\t<ServerAdminPassword> (required parameter) - ArcGIS Server site administrator password."
    print
    sys.exit(1)

portalFQDN = sys.argv[1]
portalAdminUser = sys.argv[2]
portalAdminPass = sys.argv[3]

agsFQDN = sys.argv[4]
agsPort = sys.argv[5]
agsAdminUser = sys.argv[6]
agsAdminPass = sys.argv[7]

isHosted = "true"
serverType = "ArcGIS"


def genPortalToken(portalFQDN, adminUser, adminPass, expiration=60):
    #Re-usable function to get a token
    
    query_dict = {'username':   adminUser,
                  'password':   adminPass,
                  'expiration': str(expiration),
                  'client':     'referer',
		  'referer':	"https://{}/arcgis".format(portalFQDN)}
    
    query_string = urllib.urlencode(query_dict)
    url = "https://{}/arcgis/sharing/generateToken".format(portalFQDN)
    
    token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())
    
    if "token" not in token:
        print token
        return None
    else:
        # Return the token to the function which called for it
        return token['token']

def genAGSToken(server, port, adminUser, adminPass, expiration=60):
    #Re-usable function to get a token required for Admin changes
    
    query_dict = {'username':   adminUser,
                  'password':   adminPass,
                  'expiration': str(expiration),
                  'client':     'requestip'}
    
    query_string = urllib.urlencode(query_dict)
    url = "https://{}:{}/arcgis/admin/generateToken".format(server, port)
    
    token = json.loads(urllib.urlopen(url + "?f=json", query_string).read())
        
    if "token" not in token:
        print token
        return None
    else:
        # Return the token to the function which called for it
        return token['token']
	
try:
    success = True
    
    # -------------------------------------------------------------------------
    # Get Portal Token
    # -------------------------------------------------------------------------
    print "\n-Generating Portal for ArcGIS token..."
    portalToken = genPortalToken(portalFQDN, portalAdminUser, portalAdminPass)
    if portalToken is not None:
	success = True
	print "\tDone."
    else:
	success = False

    # -------------------------------------------------------------------------
    # Get Server Token
    # -------------------------------------------------------------------------
    if success:
	print "\n-Generating ArcGIS for Server token..."
	agsServerName = agsFQDN.split(".")[0]
	agsToken = genAGSToken(agsServerName, agsPort, agsAdminUser, agsAdminPass)
	if agsToken is not None:
	    success = True
	    print "\tDone."
	else:
	    success = False
	    
    # -------------------------------------------------------------------------
    # Register server with Portal
    # -------------------------------------------------------------------------
    if success:
	print "\n-Registering ArcGIS Server site {} with Portal for ArcGIS {}...".format(agsFQDN, portalFQDN)
	
	url_p1 = "https://{}/arcgis/sharing/portals/self/servers/register?".format(portalFQDN)
	url_p2 = "name={}:{}&url=https://{}/arcgis&adminUrl=https://{}:{}/arcgis".format(agsFQDN, agsPort, agsFQDN, agsFQDN, agsPort)
	url_p3 = "&isHosted={}&serverType={}&f=json&token={}".format(isHosted, serverType, portalToken)
	
	url = url_p1 + url_p2 + url_p3
	
	status = json.loads(urllib2.urlopen(url, ' ').read())
	
	if "success" in status:
	    success = True
	    print "\tDone."
	    # Get properties from the Registration request
	    serverID = status["serverId"]
	    secretKey = status["secretKey"]
	    
	else:
	    success = False
	    print "\n***Error***:"
	    print status
	    print "\nURL string used in REST request:"
	    print url + "\n"

    # -------------------------------------------------------------------------
    # Update ArcGIS Server site security configuration
    # (i.e. update to use Portal users/roles)
    # -------------------------------------------------------------------------	    
    if success:
	print "\n-Update security configuration..."

	## "Build" config update syntax
	#portalUrl = "https://{}/arcgis".format(portalFQDN)
	#portalMode = "ARCGIS_PORTAL_FEDERATION"
	#   
	#portalPropDict = {"portalUrl":portalUrl.encode('ascii'), "portalSecretKey": secretKey.encode('ascii'), \
	#		  "portalMode": portalMode.encode('ascii'), "token": portalToken.encode('ascii')}
	#
	#authenticationTier = "ARCGIS_PORTAL"
	#updateDict = {"authenticationTier":authenticationTier, "portalProperties":portalPropDict}
	#   
	## Update security configuration
	#query_string = urllib.urlencode(updateDict)
	#url = "https://{}:{}/arcgis/admin/security/config/update?f=json&token={}".format(agsFQDN, agsPort, agsToken)
	#status = json.loads(urllib.urlopen(url + "&securityConfig=", query_string).read())

	# "Build" config update syntax
	portalUrl = "https://{}/arcgis".format(portalFQDN)
	privatePortalUrl = "https://{}:7443/arcgis".format(portalFQDN)
	portalMode = "ARCGIS_PORTAL_FEDERATION"
	serverUrl = "https://{}/arcgis".format(agsFQDN)
    
	portalPropDict = {"portalUrl":portalUrl.encode('ascii'), "privatePortalUrl": privatePortalUrl.encode('ascii'), \
			"portalSecretKey": secretKey.encode('ascii'), \
			"portalMode": portalMode.encode('ascii'), "serverId": serverID.encode('ascii'), \
			"serverUrl": serverUrl.encode('ascii'), "token": portalToken.encode('ascii')}
	
	authenticationTier = "ARCGIS_PORTAL"
	updateDict = {"authenticationTier":authenticationTier, "portalProperties":portalPropDict}
    
	# Update security configuration
	query_string = urllib.urlencode(updateDict)
	url = "https://{}:{}/arcgis/admin/security/config/update?f=json&token={}".format(agsFQDN, agsPort, agsToken)
	status = json.loads(urllib.urlopen(url + "&securityConfig=", query_string).read())
	
	if status["status"] == "success":
	    success = True
	    print "\tDone."
	else:
	    success = False
	    print "\n***Error***:"
	    print status
	    print "\nURL string used in REST request:"
	    print url + "\n"
    
except:
    
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
    if success:
        print "\nRegistration of ArcGIS Server with Portal was completed successfully.\n"
        sys.exit(0)
    else:
        print "\nERROR: Registration of ArcGIS Server with Portal was _NOT_ completed successfully.\n"
        sys.exit(1)
    