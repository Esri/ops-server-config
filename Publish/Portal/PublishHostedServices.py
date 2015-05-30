#!/usr/bin/env python
import sys, os, time, json
#import traceback

sys.path.append(r'C:\GitHub\ops-server-config\SupportFiles')
sys.path.append(r'C:\GitHub\ops-server-config\Publish\Portal')

from portalpy import Portal, unpack, provision

import logging
logging.basicConfig()

def print_publish_info(service_pub_info):
    """
    Print results obtained from check_publshing_status function execution
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
    print "Id: " + str(itemID) + "\tTitle: '" + str(itemTitle) + "'   Type:" + str(itemType) + "   Owner: " + str(itemOwner)

def check_publishing_status(services_pub_info):
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
                status_resp = check_job_status(item_id,
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

def check_job_status(item_id, job_id, job_type, check_interval=10):
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

total_pub_success = False
total_pub_jobs_success = 0

portal_address = 'https://dev03118.esri.com/arcgis'
adminuser = 'admin'
password = 'H0neyBadger5'
file_type = 'serviceDefinition'
item_id = '5334a550a4c34f0facff2f442f136340'

portal = Portal(portal_address, adminuser, password)

item = portal.item(item_id)

print '\t- Publishing source item {} ({})...'.format(item_id, item['type'])
services_pub_info = portal.publish_item(file_type=file_type, item_id=item_id)

total_pub_jobs = len(services_pub_info)
print '\t- Publishing source item created {} publishing job(s).'.format(total_pub_jobs)

print '\t- Checking publishing job(s) status...'.format(item_id)
services_pub_info = check_publishing_status(services_pub_info)


for service_pub_info in services_pub_info:
    print_publish_info(service_pub_info)
    if service_pub_info['jobStatus'].lower() == 'completed':
        total_pub_jobs_success += 1

print '\n\t- {:0>3} out of {:0>3} job(s) were published successfully.'.format(
    total_pub_jobs_success,
    total_pub_jobs
)

print '\nDone.'





