#==============================================================================
#Name:          ConfigureAGSFiles.py
#Purpose:       
#
#Prerequisites: 
#
#History:       2012:   Initial code.
#
#==============================================================================
import sys, os, traceback, platform

# Add ConfigureOpsServer\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilesPath = os.path.join(
    os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0])))), "SupportFiles")

sys.path.append(supportFilesPath)

import ConfigureFiles
from Utilities import makePath

try:
    totalSuccess = True
    
    # "Create" path to rest properties file
    pathList = ["Program Files", "ArcGIS", "Server", "framework", \
                "runtime", "tomcat", "webapps", "arcgis#rest", "WEB-INF", \
                "classes", "resources", "rest-config.properties"]
    restConfFile = makePath("C", pathList)
    
    print "\n-Editing REST properties file " + restConfFile + "...\n"
    
    # Edit Rest properties file
    success = ConfigureFiles.editRestConfigFile(restConfFile)
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
        print "Configuration of ArcGIS Server files completed successfully."
        sys.exit(0)
    else:
        print "ERROR: Configuration of ArcGIS Server files was _NOT_ completed successfully."
        sys.exit(1)
    