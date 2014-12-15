#!/usr/bin/env python
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
#Name:          RemapIDsOnServices.py
#
#Purpose:       Replace portal ids stored on ArcGIS Server services with new ids
#
#Prerequisites: - ArcGIS Service must have already been published.
#               - Portal items must have already been published.
#
#==============================================================================
import sys, os, traceback, datetime, ast, copy, json, time
import urlparse
from portalpy import Portal

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

from AGSRestFunctions import getServiceList
from AGSRestFunctions import getServiceInfo
from AGSRestFunctions import editServiceInfo

scriptName = sys.argv[0]
exitErrCode = 1
debug = False
sectionBreak = '=' * 175
sectionBreak1 = '-' * 175

doUpdateService = True
doDeleteItems = True

def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) <> 6:
        
        print '\n' + scriptName + ' <Server_FullyQualifiedDomainName> <Server_Port> <User_Name> <Password> <Use_SSL: Yes|No>'
    
        print '\nWhere:'
        print '\n\t<Server_FullyQualifiedDomainName> (required): the fully qualified domain name of the ArcGIS Server/Portal for ArcGIS machine.'
        print '\n\t<Server_Port> (required): the port number of the ArcGIS Server (specify # if no port).'
        print '\n\t<User_Name> (required): ArcGIS Server/Portal for ArcGIS site administrator.'
        print '\n\t<Password> (required): Password for ArcGIS Server/Portal for ArcGIS site administrator user.'
        print '\n\t<Use_SSL: Yes|No> (required) Flag indicating if ArcGIS Server requires HTTPS.'
        return None
    
    else:
        
        # Set variables from parameter values
        server = sys.argv[1]
        port = sys.argv[2]
        adminuser = sys.argv[3]
        password = sys.argv[4]
        useSSL = sys.argv[5]
        
        if port.strip() == '#':
            port = None
        
        if useSSL.strip().lower() in ['yes', 'ye', 'y']:
            useSSL = True
        else:
            useSSL = False
        
    return server, port, adminuser, password, useSSL

def getPortalURLItems(portal):
    url_items = None
    
    # Get all portal items not owned by logged in portal user
    items = portal.search(['id','type','url','title','owner'], q='-owner:"' + \
                            portal.logged_in_user()['username'] + '"')
    
    if items:
        url_items = {}
        for item in items:
            url = item.get('url')
            if url:
                # Remove http/s protocol from url
                urlparts = urlparse.urlparse(url)
                url_items[url.replace('{}://'.format(urlparts.scheme), '')] = item.get('id')
    return url_items

def getServiceSearchString(service, servicePortalItem):
    # 'Build' search string
    replaceURLEndpointTypes = ['FeatureServer', 'NAServer', 'MobileServer', 'SchematicsServer']
    servicePortalItemType = servicePortalItem['type']
    serviceType = service.split('.')[1]
    serviceSearchElements = service.replace('//', '/').replace('.', '/').split('/')
    if serviceType <> servicePortalItemType:
        if servicePortalItemType in replaceURLEndpointTypes:
            # Replace last element
            serviceSearchElements[-1:] = [servicePortalItemType]
        else:
            # Append portal type
            serviceSearchElements.append(servicePortalItemType)
    serviceSearchStr = '/'.join(serviceSearchElements)

    return serviceSearchStr

def findPortalItemID(server, serviceSearchStr, url_items):
    new_id = None
    for item_url, item_id in url_items.iteritems():
        if item_url.lower().startswith(server.lower()):
            if item_url.lower().endswith(serviceSearchStr.lower()):
                new_id = item_id
    return new_id

def parseService(service):
    # Parse folder and service nameType
    folder = None
    serviceNameType = None
     
    parsedService = service.split('//')
    
    if len(parsedService) == 1:
        serviceNameType = parsedService[0]
    else:
        folder = parsedService[0]
        serviceNameType = parsedService[1]
        
    return folder, serviceNameType

def main():
    
    totalSuccess = True
    
    # -------------------------------------------------
    # Check arguments
    # -------------------------------------------------
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    server, port, adminuser, password, useSSL = results
    
    if debug:
        print server, port, adminuser, password, useSSL
    
    print
    print '=' * 100
    print ' Remap portal ids stored within ArcGIS Server services'
    print '=' * 100
    print
    
    try:
        # -------------------------------------------------
        # Get portal items with URLs
        # -------------------------------------------------
        if useSSL:
            protocol = 'https'
        else:
            protocol = 'http'
        
        # Create portal object
        portal_address = '{}://{}:7443/arcgis'.format(protocol, server)
        portal = Portal(portal_address, adminuser, password)
        if not portal:
            raise Exception('ERROR: Could not create "portal" object.')
        
        print '\n- Retrieving portal item information from portal...'
        portal_url_items = getPortalURLItems(portal)
        if not portal_url_items:
            raise Exception('ERROR: There are no URL portal items. Have you published the portal content?')
            
        # ------------------------------------------------- 
        # Get all services that exist on server
        # -------------------------------------------------
        print '\n- Retrieving list of ArcGIS Server services...'
        allServices = getServiceList(server, port, adminuser, password)
        
        # Remove certain services from collection
        excludeServices = ['SampleWorldCities.MapServer']
        services = [service for service in allServices if service not in excludeServices]
        if len(services) == 0:
            raise Exception('ERROR: There are no user published ArcGIS Server services. Have you published the ArcGIS Server services?')

        # -------------------------------------------------
        # Update portal item ids with service portal properties json
        # -------------------------------------------------
        portalItemIDsToDelete = []
        
        print '\n- Remap portal ids on each ArcGIS Server service...\n'
        
        totalNumIDsNotFound = 0
        
        for service in services:
            time.sleep(0.5)
            print '\t' + ('-' * 75)
            print '\tService: ' + service
            
            folder, serviceNameType = parseService(service)
            
            numIDsFoundForService = 0
            
            # Get the service info
            info = getServiceInfo(server, port, adminuser, password, folder, serviceNameType)
            
            # Get the service portal properties json and update the item ids
            print '\n\t- Retrieving information about associated portal items stored in the server JSON...'
            servicePortalPropsOrig = info.get('portalProperties')
            
            if not servicePortalPropsOrig:
                raise Exception('ERROR: The service ' + service + ' does not ' +
                    'have any portal properties ("portalProperties" JSON key/value). ' + 
                    'Did you federate the server?')
        
            if servicePortalPropsOrig:
                
                servicePortalProps = copy.deepcopy(servicePortalPropsOrig)
                servicePortalItemsOrig = servicePortalProps.get('portalItems')
                servicePortalItems = copy.deepcopy(servicePortalItemsOrig)
                
                if not servicePortalItems:
                    totalSuccess = False
                    print '\n\t**** ERROR: this service does not have any associated portal items.'
                    continue
                    
                if servicePortalItems:
                    print '\n\t- Associated portal items...'
                    for servicePortalItem in servicePortalItems:
                        
                        orig_id = servicePortalItem['itemID']
                        
                        # Get service search string
                        serviceSearchStr = getServiceSearchString(service, servicePortalItem)
                        print '\n\t   - ' + serviceSearchStr + ': original item id = ' + orig_id
                        
                        # Get new portal item id
                        new_id = findPortalItemID(server, serviceSearchStr, portal_url_items)
                        
                        if new_id:
                            if (new_id <> orig_id):
                                numIDsFoundForService = numIDsFoundForService + 1
                                servicePortalItem['itemID'] = new_id
                                portalItemIDsToDelete.append(orig_id)
                                print '\t\tFound new item id - ' + new_id
                            else:
                                print '\t\tItem IDs match, not processing.'
                        else:
                            print '\n\t**** WARNING: new item id not found.'
                    
                    servicePortalProps['portalItems'] = servicePortalItems
                    info['portalProperties'] = servicePortalProps
                    
                    if doUpdateService:
                        print '\n\n\t- Updating portal item information stored within service JSON (service will be restarted automatically)...'
                        
                        if numIDsFoundForService == 0:
                            print '\n\t**** WARNING: there were no new ids found for this service so there is no need to update the service JSON info.'
                            continue
                        
                        success, status = editServiceInfo(server, port, adminuser, password, folder, serviceNameType, info)
                        if success:
                            print '\t\tDone.'
                        else:
                            totalSuccess = False
                            print '**** ERROR: Update of service was not successful.'
                            print 'status: ' + str(status)
                
     
        if doDeleteItems:
            print
            #print '=' * 100
            print '\n\n-Deleting portal items that were remapped to original portal item...'
            
            if len(portalItemIDsToDelete) == 0:
                print '\n**** ERROR: No portal items to delete; which means there were no portal items '
                print '\t     owned by ' + portal.logged_in_user()['username'] + ' that were remapped to original portal item.\n'
            
            # Get list of all portal ids so we can verify that the portal item exists before we delete
            portal_items = portal.search(['id'])
            time.sleep(5)
            
            for portalItemID in portalItemIDsToDelete:
                time.sleep(2)
                itemFound = False
                print '  -Deleting id ' + portalItemID + '...'
                
                # Delete if item exists
                for portal_item in portal_items:
                    if portal_item['id'] == portalItemID:
                        itemFound = True
                        results = portal.delete_item(portalItemID, portal.logged_in_user()['username'])
                        if results:
                            print '\tDone.'
                        else:
                            totalSuccess = False
                            print '**** ERROR: Deletion of service was not successful.'
                if not itemFound:
                    print '\tItem ' + portalItemID + ' does not exist. Skipping...'
                    
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
        print
        print
        if totalSuccess:
            print "Remap of portal item ids on services was completed successfully."
            sys.exit(0)
        else:
            print "ERROR: Remap of portal item ids on services was _NOT_ completed successfully."
            sys.exit(1)
        
        
if __name__ == "__main__":
    main()
