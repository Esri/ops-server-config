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
#Name:          ListServicesInSDFiles.py
#           
#Purpose:       Write service names referenced in SD files to file.
#
#==============================================================================
import sys
import os
import traceback
import datetime
import ast
import copy
import json
import subprocess
import tempfile

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(sys.argv[0])), 'SupportFiles'))

from walkingDirTrees import listFiles
from GetSDFiles import extractFromSDFile

scriptName = os.path.basename(sys.argv[0])
exitErrCode = 1
sectionBreak = '=' * 175
sectionBreak1 = '-' * 175
sevenZipExePath = r'C:\Program Files\7-Zip\7z.exe'
out_f = None

# Create temporary extract folder
extract_folder = tempfile.mkdtemp()
    
def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) <> 3:
        
        print '\n' + scriptName + ' <SDFile_Root_Folder> <Output_File>'
    
        print '\nWhere:'
        print '\n\t<SDFile_Root_Folder> (required): folder containing the SD files.'
        print '\n\t<Output_File> (required): path and name of file where service names will be written.'
        return None
    
    else:
        
        # Set variables from parameter values
        sd_root_folder = sys.argv[1]
        output_file = sys.argv[2]
        
        if not os.path.isdir(sd_root_folder):
            print '\nERROR: Specified <SDFile_Root_Folder> path {} does not exist' \
                ' or is not a directory. Exiting script.\n'.format(sd_root_folder)
            return None
        
        if os.path.exists(output_file):
            print '\nERROR: Specified <Output_File> file {} already exists. ' \
                'Exiting script.\n'.format(output_file)
            return None
        
    return sd_root_folder, output_file

def _format_servicename(folder_name, service_name, service_type):
    
    full_service_name = '{}.{}'.format(service_name, service_type)
    if len(folder_name) > 0:
        full_service_name = '{}/{}'.format(folder_name, full_service_name)
    
    return full_service_name

def get_servicename_from_sdfile(sd_file):
    ''' Return folder/servicename.servicetype from service defintion file'''

    # Extract service configuration json file from compressed .sd file
    extract_file = 'serviceconfiguration.json'
    json_file = os.path.join(extract_folder, extract_file)
    extractFromSDFile(sd_file, extract_folder, extract_file)
        
    # Extract service information from the service config json file
    os.chdir(extract_folder)
    service_config = json.load(open(extract_file))
    folder_name = service_config['folderName']
    service_name = service_config['service']['serviceName']
    service_type = service_config['service']['type']
    
    return _format_servicename(folder_name, service_name, service_type)

def main():

    total_success = True

    # Before executing rest of script, lets check if 7-zip exe exists
    if not os.path.exists(sevenZipExePath):
        print 'ERROR: File path set by "sevenZipExePath" variable (' + \
            sevenZipExePath + ') does not exist. Exiting script.'
        sys.exit(exitErrCode)
        
    # Get script parameters
    results = check_args()
    if not results:
        sys.exit(exitErrCode)
    sd_root_folder, output_file = results
    
    try:            
        write_list = []
        
        sd_files = listFiles(sd_root_folder, '*.sd')
        
        for sd_file in sd_files:
            full_service_name = get_servicename_from_sdfile(sd_file)
            write_list.append(full_service_name)
        
        write_list.sort()
        
        if len(write_list) > 0:
            out_f = open(output_file, 'w')
            for write_str in write_list:
                out_f.write('{}\n'.format(write_str))
            
        print '\n\nDone. Output written to file: {}\n'.format(output_file)
        
    except:
        total_success = False
        
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
        if out_f:
            out_f.close()
            
        if total_success:
            sys.exit(0)
        else:
            sys.exit(exitErrCode)
        
        
if __name__ == "__main__":
    main()
