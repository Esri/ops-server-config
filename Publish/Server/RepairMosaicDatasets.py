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
#Name:          RepairMosaicDatasets.py
#           
#Purpose:       Updates paths referenced in non-reference mosaic datasets stored
#               in file geodatabases to point to the Ops Server being setup.
#
#==============================================================================
import os
import sys
import traceback
import arcpy

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
sys.path.append(os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles"))

from Utilities import findFolderPath

print_msg = True
total_success = True
script_name = os.path.basename(sys.argv[0])

def getFileGeodatabases(root_path):
    # Get list of all folders ending in ".gdb"
    gdbs = findFolderPath(root_path, "*.gdb", False)
    
    # Ensure that list only contains entries that are local geodatabase
    # (file geodatabase); just in case there happens to be a folder with ".gdb"
    # that is not a geodatabase
    gdbs[:] = [gdb for gdb in gdbs if
                  arcpy.Describe(gdb).workspaceType.upper() == "LOCALDATABASE"]

    return gdbs

def check_args():
    # ---------------------------------------------------------------------
    # Check arguments
    # ---------------------------------------------------------------------

    if len(sys.argv) <> 3:
        
        print '\n{} <RootFolderToSearch> <RemapPathsList>'.format(script_name)
    
        print '\nWhere:'
        print '\n\t<RootFolderToSearch> (required): the root folder path to search for mosaic datasets.'
        print '\n\t<RemapPathsList> (required): a list of the paths to remap. Include the current path stored '
        print '\t\tin the mosaic dataset and the path to which it will be changed. You can enter an'
        print '\t\tasterisk (*) as the original path if you wish to change all your paths.'
        print '\n\t\tPattern (surround in double-qoutes): [[original_path new_path];...]'
        print '\n\t\tExamples:'
        print '\t\t\t"C:\OriginalSource\Data D:\NewSource\Data"'
        print '\t\t\t"C:\OriginalSource1\Data D:\NewSource1\Data; C:\OriginalSource2\Data D:\NewSource2\Data"'
        print '\t\t\t"\\\\FileServer\OriginalSource\Data \\\\FileServer\NewSource\Data"'
        print '\n\tNOTE: script only repairs paths in file geodatabase non-reference mosaic datasets.'
        return None
    
    else:
        
        # Set variables from parameter values
        root_path = sys.argv[1]
        remap_paths = sys.argv[2]
        
    return root_path, remap_paths

def main():
    
    total_success = True
        
    # Check arguments
    results = check_args()
    if not results:
        sys.exit(0)
    root_path, remap_paths = results
        
    try:
        print '\n{}'.format('=' * 80)
        print 'Repair Mosaic Datasets'
        print '{}\n'.format('=' * 80)
        print '{:<15}{}'.format('Root folder:', root_path)
        print '{:<15}{}\n'.format('Remap paths:', remap_paths)
        
        print 'Searching {} looking for file geodatabases...'.format(root_path)
        gdbs = getFileGeodatabases(root_path)
        
        for gdb in gdbs:
    
            print '\n\n{}'.format('=' * 80)
            print 'Found file geodatabase: {}'.format(gdb)
            print '\tChecking for existence of non-referenced mosaic datasets...'
            
            # Get any mosaic datasets in geodatabase
            arcpy.env.workspace = gdb
            mosaic_datasets = arcpy.ListDatasets('*', 'Mosaic')
            
            # Modify list to contain only non-reference mosaic datasets
            mosaic_datasets[:] = [mosaic_dataset for mosaic_dataset in mosaic_datasets if not arcpy.Describe(mosaic_dataset).referenced]
            
            if len(mosaic_datasets) == 0:
                print '\tNone found.'
            else:
                print '\tFound {} non-referenced mosaic dataset(s)...'.format(len(mosaic_datasets))
            
            for mosaic_dataset in mosaic_datasets:
                print '\n\t{}'.format('-' * 70)
                print '\tRepairing paths in mosaic dataset {}...'.format(mosaic_dataset)
                results = arcpy.RepairMosaicDatasetPaths_management(mosaic_dataset, remap_paths)
                if results.maxSeverity == 2:
                    total_success = False
                print '\n{}'.format(results.getMessages())

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
        if total_success:
            print "\n\nDone. Review output for errors.\n"
            sys.exit(0)
        else:
            print "\n\nDone. ERROR(s) occurred during mosaic dataset repair.\n"
            sys.exit(1)
        
        
if __name__ == "__main__":
    main()