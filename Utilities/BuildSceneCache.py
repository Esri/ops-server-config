#!/usr/bin/env python
#------------------------------------------------------------------------------
# Copyright 2016 Esri
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
#Name:          BuildSceneCache.py
#           
#Purpose:       Builds scene cache for hosted scene services
#
#==============================================================================
# This tool assumes and works with an Arcgis for Portal federated with an
# ArcGIS for Server. A valid service needs to exist before you can generate
# the data cache for it.

# This script assumes the server and portal are on the same machine.

# Script based on sample script created by Tam B. It was modified so that all
# parameters are specified on the command line, and other changes May 21, 2016

# For Http calls
import httplib, urllib, json

# For system tools
import sys, time, ssl, os

# For reading passwords without echoing
import getpass

script_referrer="PYTHON-SCRIPT"

# Change cacheUpdateFreq value (in secs) below to change caching job polling interval
cacheJobStatusUpdateFreq = 10

scriptName = os.path.basename(sys.argv[0])
exitErrCode = 1

sectionBreak = '=' * 80
sectionBreak1 = '-' * 80

# This disables ssl certificate validation to allow self-signed certificates to work. 
# Note this is done so here since Python 2.7.9 and up started validating (and failing)
# self-signed certificates. Portals with self-signed certs should be used only for
# internal testing/validation.

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

def print_args():
    """ Print script arguments """

    if len(sys.argv) < 4:
        
        print '\n' + scriptName + ' <Server_FullyQualifiedDomainName> <User_Name> <Password> {SceneService{,SceneService...}}'
    
        print '\nWhere:'
        print '\n\t<Server_FullyQualifiedDomainName> (required): the fully qualified domain name of the ArcGIS Server machine.'
        print '\n\t<User_Name> (required): ArcGIS Server for ArcGIS site administrator.'
        print '\n\t<Password> (required): Password for ArcGIS Server for ArcGIS site administrator user.'
        print '\n\t{SceneService{,SceneService...}} (optional): list of scene ' \
              'services to build scene cache on.'
        return None
    
    else:
        
        # Set variables from parameter values
        serverName = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]

        selectedServiceNames = None
        if len(sys.argv) == 5:
            selectedServiceNames = sys.argv[4]
            selectedServiceNames = [scene_service.strip() for scene_service in selectedServiceNames.split(',')]

    return serverName, username, password, selectedServiceNames

# A function to generate a token given username, password and the adminURL.
def getToken(username, password, serverName, serverPort):
    # Token URL is typically http://server[:port]/arcgis/sharing/generateToken
    tokenURL = "/arcgis/sharing/generateToken"
    
    # URL-encode the token parameters
    expiration = 20160
    params = urllib.urlencode({'username': username, 'password': password, "Referer": script_referrer, 'client': 'referer', 'expiration': expiration, 'f': 'json'})
    
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", "Referer": script_referrer}
    
    # Connect to URL and post parameters
    httpConn = httplib.HTTPSConnection(serverName, serverPort)
    httpConn.request("POST", tokenURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Error while fetching tokens from admin URL. Please check the URL and try again."
        return
    else:
        data = response.read()
        httpConn.close()
        
        # Check that data returned is not an error object
        if not assertJsonSuccess(str(data)):            
            return
        
        # Extract the token from it
        token = json.loads(data)
        if 'token' in token and len(token['token']) >= 0:
            return token["token"]
        else:
            import pprint
            pp = pprint.PrettyPrinter(indent=2).pprint
            pp(data)
            return token
        
# A function that checks that the input JSON object is not an error object.  
def assertJsonSuccess(data):
    obj = json.loads(data)
    if 'status' in obj and obj['status'] == "error":
        print "Error: JSON object returns an error. " + str(obj)
        return False
    else:
        return True
    
# A function that returns the caching status message given the JobID 
def getJobStatusMessage(serverName, username, password, SceneCachingToolJobsURL, token, serverPort):    
    # get the rest response
    data = getJsonResponse(serverName, username, password, SceneCachingToolJobsURL, token, serverPort)

    # load to get the json structs
    obj = json.loads(data)
    # pretty print the response json...
    import pprint
    pp = pprint.PrettyPrinter(indent=2).pprint
    if 'jobStatus' in obj and (obj['jobStatus'] == "esriJobExecuting" or obj['jobStatus'] == "esriJobWaiting" or
                               obj['jobStatus'] == "esriJobCancelling" or obj['jobStatus'] == "esriJobDeleting" or
                               obj['jobStatus'] == "esriJobSubmitted"):              
        for message in obj['messages']:
            for key, value in message.iteritems():
                if (key == 'type'):
                    typevalue = str(value)
                else:
                    if (key == 'description'):
                        description = str(value)
            if (len(typevalue) >= 0 and len(description) >= 0):
                #print typevalue, description + '\n'
                print description
        return True
    else:        
        for message in obj['messages']:
            for key, value in message.iteritems():
                if (key == 'type'):
                    typevalue = str(value)
                else:
                    if (key == 'description'):
                        description = str(value)
            if (len(typevalue) >= 0 and len(description) >= 0):
                #print typevalue, description + '\n'
                print description
        return False

# A function that returns the rest message from an ArcGIS Server
def getJsonResponse(serverName, username, password, restResourceURL, token, serverPort):    
# set the header
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", "Referer": script_referrer}
    # get token if not supplied
    if token == "":
        token = getToken(username, password, serverName, 7443)
    if token == "":
        print "Could not generate a token with the username and password provided."
        return

    #now get the response message...    
    # params
    expiration = 20160
    params = urllib.urlencode({'token': token, 'username': username, 'password': password, "Referer": script_referrer, 'client': 'referer', 'expiration': expiration, 'f': 'json'})
    
    # Connect to URL and post parameters    
    httpConn = httplib.HTTPSConnection(serverName, serverPort)
    httpConn.request("POST", restResourceURL, params, headers)
    
    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print response.reason        
        return
    else:
        data = response.read()
        httpConn.close()
        return data

# A function that formats lists into a json array
def json_list(list, jsonObjName):
    lst = []
    for lyrid in list:
        d = {}
        d[str(jsonObjName)]=lyrid
        lst.append(d)
    return json.dumps(lst)

def append_to_rows(layernames, layerids, row):
  for name, layerid in zip(layernames, layerids):
    row.append(' : '.join([name, str(layerid)]))

def print_rows(rows):
  for row in rows:
    print row

def print_data(layernames, layerids):
  rows = []
  append_to_rows(layernames, layerids, rows)
  print_rows(rows)
  
# Defines the entry point into the script
def main(argv=None):

    exit_err_code = 1
    
    total_success = True
    
    # Print/get script arguments
    results = print_args()
    if not results:
        sys.exit(exit_err_code)
    serverName, username, password, selectedServiceNames = results
    
    # Get/generateToken a token from the sharing api of Portal. Use the secure (https) 7443 port.
    portalPort = 7443
    token = getToken(username, password, serverName, portalPort)
    #print token
    if token == "":
        print "Could not generate a token with the username and password provided."
        sys.exit(exit_err_code)
    else:
        if 'error' in token:
            for error in token['error']:
                if (str(error) == 'code' and error[0] != 200):
                    sys.exit(exit_err_code)

    print '\n{}'.format(sectionBreak)
    print 'Build Scene Service Cache'
    print sectionBreak
        
    # Get the list of (scene) services available from arcgis server
    serverPort = 6443
    HostedServiceEndpnt = '/arcgis/rest/services/Hosted'
    data = getJsonResponse(serverName, username, password, HostedServiceEndpnt, token, serverPort)    
    obj = json.loads(data)
    
    #service name comes in form of "Hosted/Buildings". Drop the folder name 'Hosted'
    sceneServicenames = []
    for service in obj['services']:
        for key, value in service.iteritems():
            if (key == 'name'):                
                if (value[:7] == 'Hosted/'):
                    name = str(value[7:])
                else:
                    name = str(value)
            if (key == 'type'):
                if (value == 'SceneServer'):
                    sceneServicenames.append(name)
    
    if len(sceneServicenames) == 0:
        print '\nWARNING: Server {} does not have any scene services. Exiting script.'.format(serviceName)
        sys.exit(0)

    if selectedServiceNames is None:
        selectedServiceNames = sceneServicenames

    # Validate if specified scene services exist
    invalidServiceNames = []
    for selectedServiceName in selectedServiceNames:
        if selectedServiceName not in sceneServicenames:
            invalidServiceNames.append(selectedServiceName)

    if len(invalidServiceNames) > 0:
        print '\nERROR: the following specified scene services do not exist:'
        print invalidServiceNames
        sys.exit(exit_err_code)
        
    if len(selectedServiceNames) > 0:
        print '\nList of scene services to cache:'
        for serviceName in selectedServiceNames:
            print serviceName
        
    for serviceName in selectedServiceNames:
        print '\n{}'.format(sectionBreak1)
        print serviceName
        print sectionBreak1
        
        # Todo: reject name if it doesn't match existing service
        service_url = 'https://{}/arcgis/rest/services/Hosted/{}/SceneServer'.format(serverName, serviceName)
        
        # For now, let's just comment out the code to retrieve, list, and
        # allow the user to specify which layers in the scene service to cache
        
        # # Get all layer id and names for serviceName provided by user and determine if cache is to be built only for specific layer/s (default is to build cache for all layers)     
        # ServiceEndpnt = '/arcgis/rest/services/Hosted/{}/SceneServer'.format(serviceName)
        # data = getJsonResponse(serverName, username, password, ServiceEndpnt, token, serverPort)    
        # obj = json.loads(data)
        # 
        # print ('Below are the list of layers available for caching as acquired from :' + '\n'
        #        'https://' + serverName + ServiceEndpnt + '?f=pjson' + '\n')
        # 
        # print ('If caching of a specific layer/s is desired just enter the layerID/s from the list below for the layer/s you are interested in caching.' + '\n'
        #        'Default (if set to -1 or is not specified) is to cache all layers.' + '\n')
        # 
        # print ('LayerName : LayerID')
        # 
        # layerids = []
        # layernames = []
        # for layers in obj['layers']:        
        #     for key, value in layers.iteritems():
        #         if (key == 'id'):                                
        #             layerids.append(int(value))
        #         if (key == 'name'):
        #             layernames.append(str(value))        
        # print_data(layernames, layerids)   
        # 
        # layerIDs = []
        # if (len(selectedServiceNames) == 1):
        #     layerIDs = raw_input("Enter the layer id(s) of the layer(s) you\'d like to cache separated by comma. (ex.'3,5,8')")
        # else:
        #     layerIDs = '-1'
        #     print 'Multiple services selected for caching. Selecting of individual layers to cache is disabled.'
        # 
        # if (str(layerIDs) == '-1' or len(str(layerIDs)) <= 0):
        #     layer = "{}"
        # else:        
        #     layerIDIntlist = [int(e) if e.isdigit() else e for e in layerIDs.split(',')]
        #     layerJson = json_list(layerIDIntlist, 'id')
        #     layer = '{"layers":%s}' % (layerJson)
        
        # Build cache for all layers
        layer = '{}'
        
        # Construct the parameters to submit to the 'Manage Scene cache' tool
        num_of_caching_service_instances = 2
        update_mode = 'RECREATE_ALL_NODES'
        returnZ = 'false'
        update_extent = 'DEFAULT'
        area_of_interest = ''
        params = urllib.urlencode({'token': token, 'f': 'json', 'service_url': service_url,
                                   'num_of_caching_service_instances' : num_of_caching_service_instances,
                                    'layer': layer, 'update_mode': update_mode, 'returnZ': returnZ,
                                    'update_extent': update_extent, 'area_of_interest': area_of_interest})
        
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", "Referer": script_referrer}

        # Format the GP service tool url
        SceneCachingToolURL = '/arcgis/rest/services/System/SceneCachingControllers/GPServer/Manage%20Scene%20Cache'
        submitJob = '{}/submitJob'.format(SceneCachingToolURL)
        # Connect to URL and post parameters (using https!)
        # Set the port to 6443 as it needs to be the https server port as portal communicates to server via a secure port
        # Note if federated server is running on a different machine than the portal, chanage the 'serverName' parameter below accordingly.
        
        httpConn = httplib.HTTPSConnection(serverName, serverPort)
        httpConn.request("POST", submitJob, params, headers)
        
        # Read response
        response = httpConn.getresponse()
        if (response.status != 200):
            httpConn.close()
            print response.reason        
            return
        else:
            data = response.read()
            httpConn.close()

            # Check that data returned is not an error object
            if not assertJsonSuccess(data):          
                print 'Error returned by operation. ' + data
            else:
                print 'Scene Caching Job Submitted successfully!'
                print 'Caching Job status updates every {} seconds...'.format(cacheJobStatusUpdateFreq)
         
                # Extract the jobID from it
                jobid = json.loads(data)            
                guidJobId = str(jobid['jobId'])
                print 'JobID: {}'.format(guidJobId)
                
                # get the job status from the tool..             
                SceneCachingToolJobsURL = '{}/jobs/{}'.format(SceneCachingToolURL, guidJobId)            
                # Check the status of the result object every n seconds until it stops execution..
                result = True
                while result == True:                
                    time.sleep(cacheJobStatusUpdateFreq)
                    result = getJobStatusMessage(serverName, username, password, SceneCachingToolJobsURL, token, serverPort)
                #return

    print '\n\nScript {} completed.\n'.format(scriptName)
    sys.exit(0)

# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
