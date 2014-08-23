#!/usr/bin/env python
#==============================================================================
#Name:          CreateServiceList.py
#Purpose:       Creates file containing list of services owned or shared by a group
#               to use as service list file in StartStopServices.py script
#
#Prerequisites: - Portal items must have already been published.
#
#History:       2014/06/24:   Initial code.
#
#==============================================================================
import sys, os, traceback, datetime, ast, copy, json

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), 'Publish' + os.path.sep + 'Portal'))

from portalpy import Portal
import logging

scriptName = sys.argv[0]
exitErrCode = 1
sectionBreak = '=' * 175
sectionBreak1 = '-' * 175
print_prefix = '\t\t\t\t{}'

logging.basicConfig()

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
    print '{:<30}{:<35}{:<85}{:<25}'.format(item.get('type'), item.get('id'), '"{}"'.format(item.get('title')), item.get('owner'))

def print_webmap_info(item):
    print '\t\t{:<14}{:<35}{:<85}{:<25}'.format(item.get('type'), item.get('id'), '"{}"'.format(item.get('title')), item.get('owner'))

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

def get_opview_service_urls(portal, item):
    print_service_prefix = '\t\t\t\t{}'
    urls = []
    opview = portal.operationview(item['id'])
    
    # Get URLs for stand alone data sources referenced in the operations view
    standalone_ds_urls = opview.standalone_ds_urls()
    if standalone_ds_urls:
        print '\t\tStand alone datasources:'
    for url in standalone_ds_urls:
        urls.append(url)
        print print_service_prefix.format(url)
        
    # Get URLs for services referenced in all web maps in the operations view
    mapwidgets = opview.map_widgets()
    for mapwidget in mapwidgets:
        webmap_id = mapwidget['mapId']
        webmap_item = portal.item(webmap_id)
        print
        print_webmap_info(webmap_item)
        webmap_service_urls = get_webmap_service_urls(portal, webmap_item)
        for url in webmap_service_urls:
            urls.append(url)
            print print_service_prefix.format(url)
            
    return urls

def get_webapp_service_urls(portal, item):
    print_service_prefix = '\t\t\t\t{}'
    webmap_urls = []
    url = item.get('url')
    if url:
        
        # Commented out: web map apps which have "webmap" in app URL have the web map info
        # stored in the item data
        ## Process web apps that have "webmap" in app URL
        #search_str = '&webmap='
        #if url.find(search_str) > 0:
        #    print 'Has &webmap= in url'
        #    webmap_id = url.split('&webmap=')[1]
        #    if webmap_id:
        #        webmap_item = portal.item(webmap_id)
        #        if webmap_item:
        #            wm_urls = get_webmap_service_urls(portal, webmap_item)
        #            webmap_urls.extend(wm_urls)
            
        item_data = portal.item_data(item['id'], return_json=True)
        if item_data:
            if isinstance(item_data, dict):
                values = item_data.get('values')

                if values:
                    # Note 'webmap' key is a comma-delimited string of webmap ids
                    webmap = values.get('webmap')
                    if webmap:
                        webmap = webmap.replace(' ', '')
                        webmap_ids = webmap.split(',')
                        for webmap_id in webmap_ids:
                            webmap_item = portal.item(webmap_id)
                            print
                            print_webmap_info(webmap_item)
                            wm_urls = get_webmap_service_urls(portal, webmap_item)
                            for wm_url in wm_urls:
                                print print_service_prefix.format(wm_url)
                            
                            webmap_urls.extend(wm_urls)
            else:
                print '\n**** WARNING: can''t determine what data sources are referenced in this item.\n'
                
    return webmap_urls

def _remove_layer_number(url):
    ''' Remove layer number if exists at end of url '''
    
    search_strs = ['/FeatureServer', '/MapServer']
    for search_str in search_strs:
        if url.find(search_str) > 0:
            url = url.split(search_str)[0] + search_str
            break
    return url

def main():
    
    totalSuccess = True
    out_file = None
    
    # -------------------------------------------------
    # Check arguments
    # -------------------------------------------------
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    
    # Get parameter values
    portal_url, user, password, output_file, access_mode, owner, group = results
    
    try:
        
        # Create portal object
        portal = Portal(portal_url, user, password)
        
        if not portal:
            raise Exception('ERROR: Could not create "portal" object.')

        if not portal.logged_in_user():
            raise Exception('\nERROR: Could not sign in with specified credentials.')

        # Find portal items
        items = searchPortal(portal, owner, group)
        
        all_urls = []
        services = []
        
        type_mapping = {'FeatureServer':'MapServer', 'NAServer':'MapServer',
                        'MobileServer':'MapServer', 'SchematicsServer':'MapServer'}
        
        if items:
            
            for item in items:
                print '-' * 170
                    
                if 'Service' in item.get('typeKeywords'):
                    if not 'Service Definition' in item.get('typeKeywords'):
                        print_item_info2(item)
                        url = item.get('url')
                        all_urls.append(url)
                        print print_prefix.format(url)
        
                elif item.get('type') == 'Web Map':
                    print_item_info2(item)
                    urls = get_webmap_service_urls(portal, item)
                    for url in urls:
                        all_urls.append(url)
                        print print_prefix.format(url)
                        
                elif item.get('type') == 'Operation View':
                    print_item_info2(item)
                    urls = get_opview_service_urls(portal, item)
                    for url in urls:
                        all_urls.append(url)      
        
                elif item.get('type') == 'Web Mapping Application':
                    print_item_info2(item)
                    urls = get_webapp_service_urls(portal, item)
                    for url in urls:
                        all_urls.append(url)
                        
                else:
                    print_item_info2(item)
                    print '\tSkipping service search for this item type...'
                    
                    
            if all_urls:
                for url in all_urls:
                    url = _remove_layer_number(url)
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
