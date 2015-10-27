#!/usr/bin/env python
#------------------------------------------------------------------------------
# Copyright 2015 Esri
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
#Name:          PublishHostedServices.py
#
#Purpose:       Publish hosted services from source items in the portal.
#
#==============================================================================
import sys
import os
import time
import traceback
from datetime import datetime
from portalpy import Portal
from portalpy import TEXT_BASED_ITEM_TYPES

import logging
logging.basicConfig()

SOURCE_ITEM_TYPES = frozenset(['Service Definition'])

def print_publish_info(service_pub_info):
    """
    Print results obtained from check_publshing_status function
    """
    s = service_pub_info
    e_flag = ''
    if s['jobStatus'].lower() == 'failed':
        e_flag = 'ERROR'
        
    #print '\n{:<8}{}'.format('', '-' * 100)
    print '\n{:<8}{:<17}{}'.format('', 'Job ID:', s.get('jobId'))
    print '{:<8}{:<17}{}'.format(e_flag, 'Job Status:', s.get('jobStatus'))
    print '{:<8}{:<17}{}'.format('', 'Job Message:', s.get('jobMessage'))
    print '{:<8}{:<17}{}'.format('', 'Serice URL:', s.get('serviceurl'))
    print '{:<8}{:<17}{}'.format('', 'Serice Type:', s.get('type'))
    print '{:<8}{:<17}{}'.format('', 'Service Item ID:', s.get('serviceItemId'))
     
def print_item_info(item):
    itemID = item.get('id')
    itemTitle = item.get('title')
    itemOwner = item.get('owner')
    itemType = item.get('type')
    print "Id: {:<34}Owner: {:<25}Type: {:<25}Title: {:50}".format(itemID,
                                                               itemOwner,
                                                               itemType,
                                                               itemTitle)

def check_publishing_status(portal, item_id, services_pub_info):
    """
    Checks status of jobs created by 'publish' REST API endpoint.
    Returns modified services_pub_info object with jobStatus
    and jobMessage key/value pairs with job status information.
    """
    if services_pub_info:
        for service_pub_info in services_pub_info:

            service_pub_info['jobStatus'] = None
            service_pub_info['jobMessage'] = None
            
            success = service_pub_info.get('success')
            if success is None:
                # Publishing didn't immedidately fail therefore a job was
                # created and started. Check publishing job status.
                status_resp = check_job_status(portal, item_id,
                                    service_pub_info.get('jobId'), 'publish')
                status = status_resp['status']
                service_pub_info['jobStatus'] = status
                service_pub_info['jobMessage'] = status_resp['statusMessage']
    
            else:
                # Publishing failed immediately because 'success' key
                # only exists in json if a failure occurs
                if not success:
                    service_pub_info['jobStatus'] = 'failed'
                    info = service_pub_info.get('error')
                    if info:
                        service_pub_info['jobMessage'] = info.get('message')
                        
    return services_pub_info

def check_job_status(portal, item_id, job_id, job_type, check_interval=10):
    """
    Checks job status.
    Continues to check status at the specified interval until job
    reaches 'failed' or 'completed' state.
    """
    status = ''
    while status not in ['failed', 'completed']:
        resp = portal.job_status(item_id, job_id, job_type)
        status = resp.get('status')
        time.sleep(check_interval)
    return resp

def find_orig_service_item_id(portal, new_service_item_id):
    orig_service_item_id = None
    new_service_item = portal.item(new_service_item_id)
    new_service_item_url = new_service_item.get('url')

    query = 'type:service'
    items = portal.search(q=query)
    for item in items:
        url = item.get('url')
        if url:
            if url.lower() == new_service_item_url.lower() and \
                    new_service_item_id <> item['id']:
                orig_service_item_id = item['id']
                break
    return orig_service_item_id

def find_orig_service_item_ids(portal, services_pub_info):
    """
    Finds matching service item for each new service.
    Returns modified services_pub_info object with new
    'origServiceItemId' key/value pair containing the
    matching item id.
    """
    for service_pub_info in services_pub_info:
        service_pub_info['origServiceItemId'] = None
        target_item_id = service_pub_info.get('serviceItemId')
        src_item_id = find_orig_service_item_id(portal, target_item_id)
        if src_item_id:
            service_pub_info['origServiceItemId'] = src_item_id
    
    return services_pub_info

def transfer_item_info(portal, src_item_id, target_item_id):
    """ Transfer item information from source item to target item """
    
    src_item = portal.item(src_item_id)
    src_item_metadata_path = portal.item_metadatad(src_item_id)
    src_item_thumbnail_path = portal.item_thumbnaild(src_item_id)
    
    # URL can't be updated on hosted service so remove the url key
    if 'url' in src_item:
        del src_item['url']
    
    resp = portal.update_item(target_item_id,
                              item=src_item,
                              metadata=src_item_metadata_path,
                              thumbnail=src_item_thumbnail_path)
    return resp

def transfer_item_data(portal, src_item_id, target_item_id):
    """ Transfer item data from source item to target item """
    
    resp = None
    
    src_item = portal.item(src_item_id)
    if src_item['type'] in TEXT_BASED_ITEM_TYPES:
        try:
            src_item_data = portal.item_data(src_item_id)
        except Exception as err:
            print('ERROR: Exception: transfer_item_data function could not ' \
                  'retrieve item data for item: "{} - {}"'.format(
                                str(src_item.get('id')),
                                str(src_item.get('title'))))
            src_item_data = None
        if src_item_data:
            resp = portal.update_item(target_item_id, {'text': src_item_data})
        return resp
            
def transfer_item_sharing(portal, src_item_id, target_item_id):
    """ Transfer item sharing information from source item to target item """
    everyone = False
    org = False
    
    src_item_props, src_item_sharing, src_folder_id = portal.user_item(
                                    src_item_id,
                                    portal.item(src_item_id)['owner'])

    if src_item_sharing['access'].lower() == 'public':
         everyone = True
         org = True
    elif src_item_sharing['access'].lower() == 'org':
         everyone = False
         org = True
     
    resp = portal.share_item(target_item_id,
                             src_item_sharing.get('groups'),
                             org,
                             everyone)
            
    return resp

def is_valid_source_item(portal, item_id):
    valid = False
    source_item_id = get_source_item_ids(portal, q='id:{}'.format(item_id))
    if len(source_item_id) > 0:
        valid = True
    return valid

def get_source_item_ids(portal, q=None):
    """
    Get source items to publish.
    Can pass in portal search function query (q).
    Returns ids only for valid source items.
    """
    source_item_ids = []
    items = portal.search(q=q)
    for item in items:
        if item['type'] in SOURCE_ITEM_TYPES:
            source_item_ids.append(item['id'])
    return source_item_ids

def print_args():
    """ Print script arguments """
    if len(sys.argv) < 4:
        print '\n' + os.path.basename(sys.argv[0]) + \
                    ' <PortalURL>' \
                    ' <AdminUser>' \
                    ' <AdminUserPassword>' \
                    ' {GUID{,GUID...}}'
        print '\nWhere:'
        print '\n\t<PortalURL> (required): URL of Portal ' \
                    '(i.e. https://fully_qualified_domain_name/arcgis)'
        print '\n\t<AdminUser> (required): Primary portal administrator user.'
        print '\n\t<AdminUserPassword> (required): Password for AdminUser.'
        print '\n\t{GUID{,GUID...}} (optional): GUIDs of source items to ' \
                    'publish'
        print '\tNOTE: Valid source item types: {}'.format(
                                    ', '.join(SOURCE_ITEM_TYPES))
        print '\tNOTE: If GUID arguement is not provided all valid source ' \
                    ' items are published.'
        return None
    else:
        # Set variables from parameter values
        portal_address = sys.argv[1]
        adminuser = sys.argv[2]
        password = sys.argv[3]
        guids = None
        if len(sys.argv) == 5:
            guids = sys.argv[4]
            guids = [guid.strip() for guid in guids.split(',')]
        return portal_address, adminuser, password, guids
    
def main():
    exit_err_code = 1
    
    # Print/get script arguments
    results = print_args()
    if not results:
        sys.exit(exit_err_code)
    portal_address, adminuser, password, item_ids = results
    
    total_success = True
    #total_pub_jobs_success = 0

    file_type = 'serviceDefinition'

    #total_pub_success = False
    #total_transfer_success = False
    #do_continue = False
    
    print '=' * 150
    print 'Publish Hosted Services'
    print '=' * 150
    
    try:
        
        # Create portal connection
        portal = Portal(portal_address, adminuser, password)
        
        # Get ids of the source items to publish
        valid_items = True
        if not item_ids:
            print '\n- Searching for valid source items to publish...'
            item_ids = get_source_item_ids(portal)
        else:
            print '\n- Validating specified source item guids...'
            for item_id in item_ids:
                if not is_valid_source_item(portal, item_id):
                    valid_items = False
                    print 'ERROR: Item with GUID {} does not exist or is not a valid source type.'.format(item_id)
        
        if not valid_items:
            print 'ERROR: At least one specified GUID is invalid. Stopping script execution.'
            sys.exit(exit_err_code)
    
        num_src_items = len(item_ids)
        startTime = datetime.now()
        
        # #temp during testing
        # exclude_guids = []
        # for exclude_guid in exclude_guids:
        #     if exclude_guid in item_ids:
        #         item_ids.remove(exclude_guid)
        
        print '\n- Will attempt to publish the following {} source item(s)...\n'.format(num_src_items)
        for item_id in item_ids:
            print_item_info(portal.item(item_id))
        
        # TODO: may want to prompt user if they want to continue at this point so
        # they can review the items before trying to publish
        
        print '\n- Publish the source items...'
        
        i = 0
        grand_total_pub_jobs = 0 #Total number of jobs needed to publish all source items
        grand_total_pub_jobs_succeed = 0
        grand_total_skipped_transfer = 0
        
        for item_id in item_ids:
            i += 1
            total_pub_jobs_success = 0
            
            item = portal.item(item_id)
            
            print '\n{}'.format('-' * 100)
            print '{} out of {}\n'.format(i, num_src_items)
            print_item_info(item)
            
            # ---------------------------------------------------------------------
            # Publish source item
            # ---------------------------------------------------------------------
            print '\t{}'.format('-' * 50)
            print '\t Publish source item'
            print '\t{}'.format('-' * 50)
            print '\t- Publishing source item {} ({})...'.format(item_id,
                                                                 item['type'])
            services_pub_info = portal.publish_item(file_type=file_type,
                                                    item_id=item_id)
            
            total_pub_jobs = len(services_pub_info)
            grand_total_pub_jobs += total_pub_jobs
            print '\t- Publishing source item created {} publishing job(s).'.format(
                                                    total_pub_jobs)
            
            # Check the status of each publishing job spawned by the source item
            print '\t- Checking publishing job(s) status...'.format(item_id)
            services_pub_info = check_publishing_status(
                                    portal, item_id, services_pub_info)
            
            # Get count of completed jobs
            for service_pub_info in services_pub_info:
                print_publish_info(service_pub_info)
                if service_pub_info['jobStatus'].lower() == 'completed':
                    total_pub_jobs_success += 1
                    grand_total_pub_jobs_succeed += 1
                    
            # Report success status of publishig jobs
            print '\n\t- {:0>3} out of {:0>3} publishing job(s) were completed successfully.'.format(
                total_pub_jobs_success,
                total_pub_jobs
            )
            print_str = '\t- All publishing jobs associated with source item ' + \
                        'were{0} published successfully. Will{0} continue with ' + \
                        'information transfer.'
            
            # Do not move on to transfer information process if all jobs
            # were not sucessfully completed.
            if total_pub_jobs_success == total_pub_jobs:
                print  print_str.format('')
            else:
                print print_str.format(' NOT')
                continue
            
            # ---------------------------------------------------------------------
            # Transfer characteristics of source item to new item
            # ---------------------------------------------------------------------
            print '\n\t{}'.format('-' * 50)
            print '\t Transfer item information to new service item(s)'
            print '\t{}'.format('-' * 50)
            
            # Verify that each new service has an 'original' service item
            #print '\t- Verifying that each new service has an original service item...'
            print '\t- Searching for original service item for each new service...'
            total_has_orig_src_item = 0 
            
            services_pub_info = find_orig_service_item_ids(portal,
                                                           services_pub_info)
            for service_pub_info in services_pub_info:
                origServiceItemId = service_pub_info.get('origServiceItemId')
                if  origServiceItemId:
                    total_has_orig_src_item += 1
                else:
                    print 'WARNING: New service item {} ({})'.format(
                                            service_pub_info.get('serviceItemId'),
                                            service_pub_info.get('serviceurl'))
                    print '       does not have an associated "original" source item.'.format('')
                    
            # if total_has_orig_src_item == total_pub_jobs:
            #     do_continue = True
            # else:
            #     do_continue = False
            #     print 'WARNING: All new service items do not have original ' + \
            #             'service items. Stopping script execution.'
            
            print '\t- Transfer information from original service item(s) if it exists...'
            
            for service_pub_info in services_pub_info:
                
                target_item_id = service_pub_info.get('serviceItemId')
                src_item_id = service_pub_info.get('origServiceItemId')
                
                print '\n\t\t{:<27}{}'.format('New Service Item Id:', target_item_id)
                print '\t\t{:<27}{}'.format('New Service Item URL:', service_pub_info.get('serviceurl'))
                print '\t\t{:<27}{}'.format('Original Service Item URL:', str(src_item_id))
                
                # If there is no original service item for new service don't
                # continue with the transfer information process
                if not src_item_id:
                    print 'Warning: Original service item with matching URL does not exist. Skipping transfer.'
                    grand_total_skipped_transfer += 1
                    break
                
                # ------------------------------------
                # Transfer item information
                # ------------------------------------
                print '\t\t- Transferring item info...'
                time.sleep(5)
                resp = transfer_item_info(portal, src_item_id, target_item_id)
                print '\t\t\t{}'.format(resp)
                
                # ------------------------------------
                # Transfer item data
                # ------------------------------------
                print '\t\t- Transferring item data...'
                time.sleep(5)
                resp = transfer_item_data(portal, src_item_id, target_item_id)
                print '\t\t\t{}'.format(resp)
                
                # ------------------------------------
                # Transfer item sharing properties
                # ------------------------------------
                print '\t\t- Transferring item sharing properties...'
                time.sleep(5)
                resp = transfer_item_sharing(portal, src_item_id, target_item_id)
                if resp:
                    if resp.get('notSharedWith'):
                        print '{:<8}Could not share with: {}'.format(
                                'WARNING', resp.get('notSharedWith'))
    
    except:
        total_success = False
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
     
        # Concatenate information together concerning the error 
        # into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + \
                "\nError Info:\n" + str(sys.exc_info()[1])
        
        # Print Python error messages for use in Python / Python Window
        print
        print "***** ERROR ENCOUNTERED *****"
        print pymsg + "\n"
        
    finally:
        endTime = datetime.now()
        print
        print '-' * 100
        print 'Summary'
        print '-' * 100
        print 'Total number of...'
        print 'Source items to publish: {}'.format(num_src_items)
        print 'Publishing jobs: {}'.format(grand_total_pub_jobs)
        print 'Publishing jobs completed: {}'.format(grand_total_pub_jobs_succeed)
        print 'Publishing jobs that failed: {}'.format(grand_total_pub_jobs - grand_total_pub_jobs_succeed)
        print 'Services where info transfer was skipped because "original" service item did not exist: {}'.format(grand_total_skipped_transfer)
        
        print '\nStart time: {}'.format(startTime)
        print 'End time: {}'.format(endTime)
    
        print '\nDone.'
        if total_success:
            sys.exit(0)
        else:
            sys.exit(exit_err_code)

if __name__ == "__main__":
    main()


