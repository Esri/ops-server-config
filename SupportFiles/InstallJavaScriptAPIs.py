#==============================================================================
#Name:          InstallJavaScriptAPIs.py
#Purpose:       
#
#Prerequisites: 
#
#History:       2012:   Initial code.
#
#==============================================================================
import sys, os, traceback

import ConfigureFiles
from Utilities import findFilePath

scriptName = sys.argv[0]

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------
if len(sys.argv) <> 3:
    print "\n" + scriptName + " <JavaScriptAPIInstallRootFolderPath> <JavaScriptAPIZipFileFolderPath>"
    print "\nWhere:"
    print "\n\t<JavaScriptAPIInstallRootFolderPath> (required parameter): path to JavaScript API Install root folder Path"
    print "\n\t<JavaScriptAPIZipFileFolderPath> (required parameter): path to folder containing JavaScript API .zip files"
    print
    sys.exit(1)

jsAPIInstallRootPath = sys.argv[1]
jsAPIZipFileFolderPath = sys.argv[2]

if not os.path.exists(jsAPIInstallRootPath):
    print "\nError: specified <JavaScriptAPIInstallRootFolderPath> path " + jsAPIInstallRootPath + " does not exist."
    sys.exit(1)

if not os.path.exists(jsAPIZipFileFolderPath):
    print "\nError: specified <JavaScriptAPIZipFileFolderPath> path " + jsAPIZipFileFolderPath + " does not exist."
    sys.exit(1)


def getJavaScriptAPIVersion(jsAPIZipFile):
    # Return version number as string
    version = ""
    fileBaseName = os.path.basename(jsAPIZipFile)
    
    for x in fileBaseName.split("_"):
        if x.lower().find("v") == 0:
            version = str(float(x.lower().replace("v", "")) / 10)
    
    return version

try:
    totalSuccess = True
    
    print "\n-Install JavaScript APIs located in folder: " + jsAPIZipFileFolderPath
    
    # Get list of all the zip files in the JavaScript API folder
    jsZipFileList = findFilePath(jsAPIZipFileFolderPath, "*.zip", False)
    
    # Install and configure Java Script files
    for jsAPIZipFile in jsZipFileList:
        
        print "\n-Installing " + jsAPIZipFile + "...\n"
        
        # Determine JavaScript API version number
        jsAPIVersion = getJavaScriptAPIVersion(jsAPIZipFile)
        
        success = ConfigureFiles.installJS(jsAPIZipFile,
                                jsAPIInstallRootPath, jsAPIVersion)
        if not success:
            totalSuccess = success
    
            
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
    print
    print
    if totalSuccess:
        print "Install of JavaScript API files completed successfully.\n"
        sys.exit(0)
    else:
        print "ERROR: Install of JavaScript API files was _NOT_ completed successfully.\n"
        sys.exit(1)
    