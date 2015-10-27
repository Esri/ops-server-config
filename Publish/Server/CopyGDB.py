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
#Name:      CopyGDB.py
#
#Purpose:   Copy contents from one geodatabase to another
#
#==============================================================================
import arcpy
import sys, traceback, time, os

# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilePath = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0]))), "SupportFiles")
sys.path.append(supportFilePath)

from datetime import datetime
from UtilitiesArcPy import checkResults, copyGDBData

scriptName = sys.argv[0]

if len(sys.argv) <> 3:
    print "\n" + scriptName + " <SourceGeodatabase> <DestinationGeodatabase>"
    print "\nWhere:"
    print "\n\t<SourceGeodatabase> (required): path to the source geodatabase."
    print "\n\t<DestinationGeodatabase> (required): path to the destination geodatabase."
    print
    sys.exit(1)

srcPath = sys.argv[1]
destPath = sys.argv[2]

# ---------------------------------------------------------------------
# Check parameters
# ---------------------------------------------------------------------
goodParameters = True

# Check path parameter to make sure they exist

if not os.path.exists(srcPath):
    print "\nThe path specified for parameter <SourceGeodatabase>" + \
                " (" + srcPath + ") does not exist."
    goodParameters = False

if not os.path.exists(destPath):
    print "\nThe path specified for parameter <DestinationGeodatabase>" + \
                " (" + destPath + ") does not exist."
    goodParameters = False

# Exit script if parameters are not valid.
if not goodParameters:
    print "\nInvalid script parameters. Exiting " + scriptName + "."
    sys.exit(1)

printMsg = True
totalCopySuccess = True


try:
    
    # startTime = datetime.now()
    # print
    # print '{:<14}{:<100}'.format("Source:", srcPath)
    # print '{:<14}{:<100}'.format("Destination:", destPath)
    
    results = copyGDBData(srcPath, destPath)
    success = checkResults(results, printMsg)
    if not success:
        totalCopySuccess = success
        
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
    if totalCopySuccess:
        print "\nData copy was successful."
    else:
        print "\nERROR occurred during data copy."
        
    # print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("Start time:", startTime)
    # print '{:<14}{:%Y-%m-%d %H:%M:%S}'.format("End time:", datetime.now())

    if totalCopySuccess:
         sys.exit(0)
    else:
         sys.exit(1)

