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
#Name:          CreateServiceList.py
#
#Purpose:       Creates file containing list of services owned or shared by a group
#               to use as service list file in StartStopServices.py script. Script
#               output can be used to QC issues with items.
#
#Prerequisites: Portal items must have already been published.
#
#==============================================================================
import sys
import os
import traceback
import datetime
import ast
import copy
import json

sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(sys.argv[0])), 'Publish' + os.path.sep + 'Portal'))
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(sys.argv[0])), 'SupportFiles'))


from portalpy import Portal
import logging
import urlparse
from AGSRestFunctions import getServicePortalProps
from AGSRestFunctions import getServiceList
from UrlChecker import checkUrl

scriptName = sys.argv[0]
exitErrCode = 1
sectionBreak = '=' * 175
sectionBreak1 = '-' * 175
print_prefix = '\t\t\t\t{}:{}'

logging.basicConfig()

service_portal_ids = None

do_url_checks = True
portal_netloc = None

def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) < 7:
        
        print '\n' + scriptName + ' <PortalURL> <User> <UserPassword> <OutputFile> <OVERWRITE|APPEND> <Owner> {GroupName}'

        print '\nWhere:'
        print '\n\t<PortalURL> (required): URL of Portal (i.e. https://fully_qualified_domain_name/arcgis)'
        print '\n\t<User> (required): Portal user to connect to portal with.'
        print '\n\t<UserPassword> (required): Password for portal user.'
        print '\n\t<OutputFile> (required): Path and name of file to write service names.'
        print '\n\t<OVERWRITE|APPEND> (required): Overwrite or append to existing file.'
        print '\n\t<Owner> (required): Owner of items or group.'
        print '\n\t{GroupName} (optional): Group name. Group names that contain spaces must be enclosed by double-quotes.\n'
        return None
    
    else:
        
        # Set variables from parameter values
        portal_url = sys.argv[1]
        user = sys.argv[2]
        password = sys.argv[3]
        output_file = sys.argv[4]
        access_mode = sys.argv[5]
        owner = sys.argv[6]
        group = None
        if len(sys.argv) == 8:
            group = sys.argv[7]
        
        if len(sys.argv) > 8:
            print '\nError: too many parameters. If you specify {group} and it contains spaces, the parameter value must be enclosed by double-quotes.\n'
            return None
        
        valid_access_modes = ['OVERWRITE', 'APPEND']
        if not access_mode.upper() in valid_access_modes:
            print '\nError: incorrect access mode "{}". Valid choices are {}\n'.format(access_mode, valid_access_modes)
            return None
        
        if access_mode.upper() == 'OVERWRITE':
            access_mode = 'w'
        else:
            access_mode = 'a'
    
    return portal_url, user, password, output_file, access_mode, owner, group

def searchPortal(portal, owner, group=None):
    # Search portal based on query
    all_items = None
    if not group:
        query = 'owner:{}'.format(owner)
        all_items = portal.search(q = query)
    else:
        all_items = []
        query = 'owner:{} AND title:{}'.format(owner, group)
        groups = portal.groups(q = query)
        for group in groups:
            group_items = portal.group_items(group['id'])
            if group_items:
                all_items.extend(group_items)
                
    return all_items

def print_item_info2(item):
    print '{:<30}{:<32}   {:<115}{:<25}'.format(item.get('type'), item.get('id'), '"{}"'.format(item.get('title')), item.get('owner'))

def print_webmap_info(item):
    print '{:<30}{:<14}{:<32}   {:<100}{:<25}'.format('', item.get('type'), item.get('id'), '"{}"'.format(item.get('title')), item.get('owner'))

def print_webmapapp_webmap_info(item):
    print '{:<16}{:<14}{:<32}   {:<115}{:<25}'.format('', item.get('type'), item.get('id'), '"{}"'.format(item.get('title')), item.get('owner'))
    
def print_opview_webmap_info(item):
    print '{:<16}{:<14}{:<32}   {:<115}{:<25}'.format('', item.get('type'), item.get('id'), '"{}"'.format(item.get('title')), item.get('owner'))
    
def get_webmap_service_urls(portal, item):
    
    urls = []
    webmap = portal.webmap(item['id'])
    
    op_layers = webmap.operational_layers()
    for layer in op_layers:
        url = layer.get('url')
        if url:
            urls.append(url)
        
    base_layers = webmap.basemap()['baseMapLayers']
    for layer in base_layers:
        url = layer.get('url')
        if url:
            urls.append(url)
    
    return urls

def get_opview_service_urls(portal, item, service_portal_ids):
    print_service_prefix = '\t\t\t\t{}'
    urls = []
    opview = portal.operationview(item['id'])
    
    # Get URLs for stand alone data sources referenced in the operations view
    standalone_ds_urls = opview.standalone_ds_urls()
    if standalone_ds_urls:
        print '\n\t\tStand alone datasources:'
    for url in standalone_ds_urls:
        urls.append(url)
        #print print_service_prefix.format(url)
        p_item_id = _get_item_id(url, service_portal_ids)
        print '\n{:<30}{:<14}{:<32}   {:<101}{:<25}'.format('','Service', str(p_item_id), str(_get_item_title(portal, p_item_id)), str(_get_item_owner(portal, p_item_id)))
        print '{:<30}{:<14}{:>32}   {:<100}'.format('','','URL:', url)
        if do_url_checks:
            _check_url(url)
         
    # Get URLs for services referenced in all web maps in the operations view
    mapwidgets = opview.map_widgets()
    for mapwidget in mapwidgets:
        print '\n'
        webmap_id = mapwidget['mapId']
        webmap_item = portal.item(webmap_id)
        
        #print_webmap_info(webmap_item)
        print_opview_webmap_info(webmap_item)
        webmap_service_urls = get_webmap_service_urls(portal, webmap_item)
        for url in webmap_service_urls:
            urls.append(url)
            #print print_service_prefix.format(url)
            p_item_id = _get_item_id(url, service_portal_ids)
            print '\n{:<30}{:<14}{:<32}   {:<101}{:<25}'.format('','Service', str(p_item_id), str(_get_item_title(portal, p_item_id)), str(_get_item_owner(portal, p_item_id)))
            print '{:<30}{:<14}{:>32}   {:<101}'.format('','','URL:', url)
            if do_url_checks:
                _check_url(url)
                                
    return urls

def get_webapp_service_urls(portal, item, service_portal_ids):

    print_service_prefix = '\t\t\t\t{}'
    webmap_urls = []
    
    if hasattr(item, 'get'):
        url = item.get('url')
    else:
        url = None
    
    if url:
            
        item_data = portal.item_data(item['id'], return_json=True)
        if item_data:
            if isinstance(item_data, dict):
                if hasattr(item_data, 'get'):
                    values = item_data.get('values')
                else:
                    values = None
                    print '\n**** WARNING: can''t determine what data sources are referenced in this item.\n'
                    
                if values:
                    # Note 'webmap' key is a comma-delimited string of webmap ids
                    if hasattr(values, 'get'):
                        webmap = values.get('webmap')
                    else:
                        webmap = None
                        print '\n**** WARNING: can''t determine what data sources are referenced in this item.\n'
                        
                    if webmap:
                        webmap = webmap.replace(' ', '')
                        webmap_ids = webmap.split(',')
                        for webmap_id in webmap_ids:
                            print '\n'
                            webmap_item = portal.item(webmap_id)
                            if webmap_item:
                                #print_webmap_info(webmap_item)
                                print_webmapapp_webmap_info(webmap_item)
                                wm_urls = get_webmap_service_urls(portal, webmap_item)
                                for wm_url in wm_urls:
                                    p_item_id = _get_item_id(wm_url, service_portal_ids)
                                    print '\n{:<30}{:<14}{:<32}   {:<101}{:<25}'.format('','Service', str(p_item_id), str(_get_item_title(portal, p_item_id)), str(_get_item_owner(portal, p_item_id)))
                                    print '{:<30}{:<14}{:>32}   {:<100}'.format('', '', 'URL:', wm_url)
                                    if do_url_checks:
                                        _check_url(wm_url)
                            
                                webmap_urls.extend(wm_urls)
            else:
                print '\n**** WARNING: can''t determine what data sources are referenced in this item.\n'
 
    return webmap_urls









def get_storymap_resources(portal, item, service_portal_ids):

    print_service_prefix = '\t\t\t\t{}'
    service_urls = []
    
    item_data = portal.item_data(item['id'], return_json=True)
    
    if item_data is None:
        return None
    
    if hasattr(item_data, 'get'):
        values = item_data.get('values')
    else:
        # values = None
        # print '\n**** WARNING: can''t determine what data sources are referenced in this item.\n'
        return None
        

    # ----------------------------
    # Get Web map information
    # ----------------------------
    webmap = values.get('webmap')
        
    if webmap:
        webmap = webmap.replace(' ', '')
        webmap_ids = webmap.split(',')
        for webmap_id in webmap_ids:
            print '\n'
            
            webmap_item = portal.item(webmap_id)
            if webmap_item:
                #print_webmap_info(webmap_item)
                print_webmapapp_webmap_info(webmap_item)
                wm_urls = get_webmap_service_urls(portal, webmap_item)
                for wm_url in wm_urls:
                    p_item_id = _get_item_id(wm_url, service_portal_ids)
                    print '\n{:<30}{:<14}{:<32}   {:<101}{:<25}'.format('','Service', str(p_item_id), str(_get_item_title(portal, p_item_id)), str(_get_item_owner(portal, p_item_id)))
                    print '{:<30}{:<14}{:>32}   {:<100}'.format('', '', 'URL:', wm_url)
                    if do_url_checks:
                        _check_url(wm_url)
            
                service_urls.extend(wm_urls)
            else:
                print '\nERROR: References web map item that does not exist: {}\n'.format(webmap_id)
                
    # ----------------------------
    # Get Story information
    # ----------------------------
    story_prop_keys = ['entries', 'sections']
    story = values.get('story')
    
    for story_prop_key in story_prop_keys:
        story_entries = story.get(story_prop_key)
        if story_entries:
            for story_entry in story_entries:
                media = story_entry.get('media')
                traverse_media_json(portal, media)
                            
    return service_urls

def traverse_media_json(portal, media):
    if media:
        for media_key in media.keys():
            media_resource = media[media_key]
            if isinstance(media_resource, dict):
                url = media_resource.get('url')
                if url:
                    guid = None
                    if url.find('?appid=') > -1:
                        guid = url.split('?appid=')[1]
                    if url.find('?webmap=') > -1:
                        guid = url.split('?webmap=')[1]
                    if url.find('?3dWebScene=') > -1:
                        guid = url.split('?3dWebScene=')[1]
                    if url.find('index.html#/') > -1:   # Operations Dashboard
                        guid = url.split('index.html#/')[1]
                    if url.find('?webscene=') > -1:
                        guid = url.split('?webscene=')[1]
                    if url.find('index.html?id=') > -1: #web app builder apps
                        guid = url.split('index.html?id=')[1]
                    if url.find('?bookId=') > -1:       # Briefing books
                        guid = url.split('?bookId=')[1]
                        
                    if guid:
                        print '\n{:<30}{:<14}{:<32}   {:<101}{:<25}'.format('',media_resource.get('type'), str(guid), str(_get_item_title(portal, guid)), str(_get_item_owner(portal, guid)))
                    else:
                        print '\n{:<30}{:<14}{:<32}   {:<101}{:<25}'.format('',media_resource.get('type'), None, None, None)
                        
                    print '{:<30}{:<14}{:>32}   {:<100}'.format('', '', 'URL:', url)
                    if do_url_checks:
                        _check_url(url)

def _remove_layer_number(url):
    ''' Remove layer number if exists at end of url '''
    
    search_strs = ['/FeatureServer', '/MapServer']
    for search_str in search_strs:
        if url.find(search_str) > 0:
            url = url.split(search_str)[0] + search_str
            break
    return url

def get_service_portal_ids(server, port, user, password):
    
    service_portal_ids = None
    
    # Get list of services on specified ArcGIS Server
    service_list = getServiceList(server, port, user, password)
    if len(service_list) > 0:
        service_portal_ids = {}
    
    # Get ids for all portal items assocatied with each AGS service
    for service in service_list:
        parsed_service = service.split('//')
        folder = None
        if len(parsed_service) == 1:
            service_name_type = parsed_service[0]
        else:
            folder = parsed_service[0]
            service_name_type = parsed_service[1]
        
        service_portal_prop = getServicePortalProps(server, port, user, password, folder, service_name_type)
        service_portal_items = service_portal_prop['portalItems']
        root_service = service.split('.')[0].replace('//', '/')
        
        for service_portal_item in service_portal_items:
            service_portal_ids['{}/{}'.format(root_service,
                service_portal_item['type'])] = service_portal_item['itemID'].encode('ascii')

    return service_portal_ids

def _get_item_id(url, service_portal_ids):
    for s in service_portal_ids:
        if url.find(s) > 0:
            return service_portal_ids[s]    

def _get_item_owner(portal, item_id):
    if item_id:
        item = _get_item(portal, item_id)
        if item:
            return item.get('owner')

def _get_item_title(portal, item_id):
    if item_id:
        item = _get_item(portal, item_id)
        if item:
            return item.get('title')

def _get_item(portal, item_id):
    if item_id:
        item = portal.item(item_id)
        return item

def _check_url(url):
    badUrl, code, message = checkUrl(url)
    if badUrl:
        print 'ERROR: URL issue - code: {}; message: {}; url: {}'.format(code, message, url)
    
    url_netloc = urlparse.urlparse(url).netloc.split(':')[0].lower()
    p_url_netloc = portal_netloc.split(':')[0].lower()
    
    if url_netloc != p_url_netloc:
        print 'WARNING: URL is external to AGS site: {}'.format(url)
        
def main():
    
    totalSuccess = True
    out_file = None
    
    # Check arguments
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    
    # Get parameter values
    portal_url, user, password, output_file, access_mode, owner, group = results
    global portal_netloc
    portal_netloc = urlparse.urlparse(portal_url).netloc
    
    try:
        
        # Create portal object
        portal = Portal(portal_url, user, password)
        
        if not portal:
            raise Exception('ERROR: Could not create "portal" object.')

        if not portal.logged_in_user():
            raise Exception('\nERROR: Could not sign in with specified credentials.')
        
        # Get portal items
        items = searchPortal(portal, owner, group)
        
        # Get portal item ids for all AGS services
        urlparts = urlparse.urlparse(portal_url)
        server = urlparts.hostname
        # NOTE: call to following function assumes AGS server is using
        # same username and password as portal
        service_portal_ids = get_service_portal_ids(server, 6443, user, password)
        
        all_urls = []
        services = []
        
        type_mapping = {'FeatureServer':'MapServer', 'NAServer':'MapServer',
                        'MobileServer':'MapServer', 'SchematicsServer':'MapServer'}
        
        if items:
            
            for item in items:
                
                # if item['id'] <> 'faef542a74e141398c05c43379a67004':
                #     continue
                
                print '-' * 200
                
                if 'Service' in item.get('typeKeywords'):
                    if not 'Service Definition' in item.get('typeKeywords'):
                        print_item_info2(item)
                        url = item.get('url')
                        all_urls.append(url)
                        p_item_id = _get_item_id(url, service_portal_ids)
                        print '\n\t\t{:<14}{:<32}   {:<115}{:<25}'.format('Service', str(p_item_id), str(_get_item_title(portal, p_item_id)), str(_get_item_owner(portal, p_item_id)))
                        print '\t\t{:<14}{:>32}   {:<115}'.format('','URL:',url)
                        if do_url_checks:
                            _check_url(url)
                        
                elif item.get('type') == 'Web Map':
                    print_item_info2(item)
                    urls = get_webmap_service_urls(portal, item)
                    for url in urls:
                        all_urls.append(url)
                        p_item_id = _get_item_id(url, service_portal_ids)
                        print '\n\t\t{:<14}{:<32}   {:<115}{:<25}'.format('Service', str(p_item_id), str(_get_item_title(portal, p_item_id)), str(_get_item_owner(portal, p_item_id)))
                        print '\t\t{:<14}{:>32}   {:<115}'.format('','URL:',url)
                        if do_url_checks:
                            _check_url(url)
                        
                elif item.get('type') == 'Operation View':
                    print_item_info2(item)
                    urls = get_opview_service_urls(portal, item, service_portal_ids)
                    for url in urls:
                        all_urls.append(url)      
        
                elif item.get('type') == 'Web Mapping Application':
                    print_item_info2(item)
                    
                    if 'Story Map' in item.get('typeKeywords'):
                        print '(Story Map)'
                        urls = get_storymap_resources(portal, item, service_portal_ids)
                        for url in urls:
                            all_urls.append(url)
                            
                    else:
                        urls = get_webapp_service_urls(portal, item, service_portal_ids)
                        for url in urls:
                            all_urls.append(url)
                        
                else:
                    print_item_info2(item)
                    print '\tSkipping service search for this item type...'
                    
                    
            if all_urls:
                for url in all_urls:
                    url = _remove_layer_number(url)
                    if url.find('/Hosted/') == -1:
                        for search_str, replace_str in type_mapping.iteritems():
                            if url.find('/' + search_str) > 0:
                                url = url.replace('/' + search_str, '/' + replace_str)
                    url = '.'.join(url.rsplit('/', 1))
                    #print 'url line 271: ' + url
                    if url.find('/rest/services/') > 0:
                        service = url.split('/rest/services/')[1]
                        if not service in services:
                            services.append(service)
        
        if len(services) > 0:
            services.sort()
            out_file = open(output_file, access_mode)
            print '\n\n{}'.format('=' * 60)
            print 'Summary of services referenced by items:\n'
            for service in services:
                out_file.write(service + '\n')
                print '\t{}'.format(service)
            print '\n\tNumber of services: {}'.format(len(services))
            print '\tService list written to file: {}'.format(output_file)
        else:
            print '\n***** ERROR: There are no services to write to file.'
        
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
        if hasattr(out_file, 'close'):
            out_file.close()
        if totalSuccess:
            sys.exit(0)
        else:
            sys.exit(1)
   
if __name__ == "__main__":
    main()
