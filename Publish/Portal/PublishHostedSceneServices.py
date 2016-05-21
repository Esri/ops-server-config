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
#Name:          PublishHostedSceneServices.py
#
#Purpose:       Publish hosted scene services from source items in the portal.
#
#==============================================================================
import sys
import os
import time
import traceback
from datetime import datetime
from portalpy import Portal
from portalpy import TEXT_BASED_ITEM_TYPES
import json

from PublishHostedServices import publish_source_item
from PublishHostedServices import print_item_info

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

from Utilities import findFilePath

import logging
logging.basicConfig()

SOURCE_ITEM_TYPES = frozenset(['Feature Service'])

file_type = 'featureService'
output_type ='sceneService'
scene_parmater_file_suffix = '_sceneserver.json'
    
def is_valid_source_item(portal, item_id):
    valid = False
    source_item_id = get_source_item_ids(portal, q='id:{}'.format(item_id))
    if len(source_item_id) > 0:
        valid = True
    return valid

def get_source_item_ids(portal, q=None):
    """
    Get ids of hosted feature services that have an associated scene service.
    Can pass in portal search function query (q).
    Returns ids only for valid source items.
    """
    source_item_ids = []
    
    scene_item_ids = get_scene_service_item_ids(portal)
    
    items = portal.search(q=q)
    for item in items:
        if item['type'] in 'Feature Service':
            if '/Hosted/' in item['url']:
                if 'Hosted Service' in item['typeKeywords']:
                    # if the service has been published the item
                    # will have 'Hosted Service' in typeKeywords
                    
                    # Check if the feature service has an associated
                    # scene service
                    feat_service_name = item['url'].split('/')[-2]
                    for scene_id in scene_item_ids:
                        scene_service_name = portal.item(scene_id)['url'].split('/')[-2]
                        if feat_service_name == scene_service_name:
                            if item['id'] not in source_item_ids:
                                source_item_ids.append(item['id'])
                                 
    return source_item_ids

def get_scene_service_item_ids(portal):
    item_ids = []
    items = portal.search(q='type:Scene Service')
    for item in items:
        item_ids.append(item['id'])

    return item_ids

def validate_scene_parameter_folder(portal, folder, source_item_ids):
    valid = True
    msg = None
    
    # Does path exist
    if not os.path.exists(folder):
        valid = False
        msg = 'ERROR: folder {} does not exist.'.format(folder)
        return valid, msg
    
    # Is path a folder
    if not os.path.isdir(folder):
        valid = False
        msg = 'ERROR: path {} is not a folder.'.format(folder)
        return valid, msg
    
    # Does folder contain any scene service parameter files
    scene_parameter_files = findFilePath(folder,
                                '*' + scene_parmater_file_suffix,
                                returnFirst=False)
    if len(scene_parameter_files) == 0:
        valid = False
        msg = 'ERROR: folder {} does not contain any scene service' \
              ' parameter files (i.e. {})'.format(folder,
                                            scene_parmater_file_suffix)
        return valid, msg
        
    # Check if folder contains a scene service parameter file
    # for each scene service being published
    #missing_files = []
    msg = 'ERROR: folder {} is missing scene service parameter files ' \
          'for the following scene services: '.format(folder)
    for item_id in source_item_ids:
        service_name = portal.item(item_id)['url'].split('/')[-2]
        scene_parameter_file = os.path.join(folder, service_name + scene_parmater_file_suffix)
        if scene_parameter_file not in scene_parameter_files:
            valid = False
            msg = msg + '\n' + service_name
    if not valid:
        return valid, msg
    
    return valid, msg
    
def print_args():
    """ Print script arguments """
    if len(sys.argv) < 5:
        print '\n' + os.path.basename(sys.argv[0]) + \
                    ' <PortalURL>' \
                    ' <AdminUser>' \
                    ' <AdminUserPassword>' \
                    ' <SceneServiceParameterFolder>' \
                    ' {GUID{,GUID...}}'
        print '\nWhere:'
        print '\n\t<PortalURL> (required): URL of Portal ' \
                    '(i.e. https://fully_qualified_domain_name/arcgis)'
        print '\n\t<AdminUser> (required): Primary portal administrator user.'
        print '\n\t<AdminUserPassword> (required): Password for AdminUser.'
        print '\n\t<SceneServiceParameterFolder> (required): folder containing the ' \
                    'scene service publishing parameter json files.'
        print '\n\t{GUID{,GUID...}} (optional): GUIDs of hosted feature services ' \
                    'associated with hosted scene services.'
        print '\tNOTE: Valid source item types: {}'.format(
                                    ', '.join(SOURCE_ITEM_TYPES))
        print '\tNOTE: If GUID argument is not provided all valid source ' \
                    'items are used to publish scene services.'
        return None
    else:
        # Set variables from parameter values
        portal_address = sys.argv[1]
        adminuser = sys.argv[2]
        password = sys.argv[3]
        scene_parameter_folder = sys.argv[4]
        guids = None
        if len(sys.argv) == 6:
            guids = sys.argv[5]
            guids = [guid.strip() for guid in guids.split(',')]
        return portal_address, adminuser, password, scene_parameter_folder, guids
    
def main():
    exit_err_code = 1
    
    # Print/get script arguments
    results = print_args()
    if not results:
        sys.exit(exit_err_code)
    portal_address, adminuser, password, scene_parameter_folder, item_ids = results
    
    total_success = True
    
    print '=' * 150
    print 'Publish Hosted Scene Services'
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
                    print 'ERROR: Item with GUID {} does not exist, ' + \
                        'is not a hosted feature service, or does not ' + \
                        'have an associated scene service'.format(item_id)
        
        if not valid_items:
            print 'ERROR: At least one specified GUID is invalid. Stopping script execution.'
            sys.exit(exit_err_code)
    
        print '\n- Validating scene server parameter folder {}...'.format(scene_parameter_folder)
        is_valid, msg = validate_scene_parameter_folder(portal, scene_parameter_folder, item_ids)
        if not is_valid:
            print msg
            sys.exit(exit_err_code)
        
        num_src_items = len(item_ids)
        startTime = datetime.now()
        
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
        
        os.chdir(scene_parameter_folder)
        
        for item_id in item_ids:
            i += 1
            
            item = portal.item(item_id)
            
            print '\n{}'.format('-' * 100)
            print '{} out of {}\n'.format(i, num_src_items)
            print_item_info(item)
            
            parameter_file = item['url'].split('/')[-2] + '_sceneserver.json'
            print 'Scene service publishing parameter file: {}'.format(parameter_file)
            
            publish_parameters = json.load(open(parameter_file))

            total_pub_jobs, total_pub_jobs_success, total_skipped_transfer = \
                publish_source_item(portal,
                                    item_id,
                                    file_type,
                                    publish_parameters=publish_parameters,
                                    output_type=output_type)
            grand_total_pub_jobs += total_pub_jobs
            grand_total_pub_jobs_succeed += total_pub_jobs_success

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

        if total_success:
            sys.exit(0)
        else:
            sys.exit(exit_err_code)

if __name__ == "__main__":
    main()


