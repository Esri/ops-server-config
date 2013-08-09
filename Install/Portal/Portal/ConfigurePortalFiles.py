#==============================================================================
#Name:          ConfigurePortalFiles.py
#Purpose:       
#
#Prerequisites: 
#
#History:       2012:   Initial code.
#
#==============================================================================
import sys, os, time, traceback, platform


# Add "Root folder"\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilesPath = os.path.join(
    os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0])))), "SupportFiles")

sys.path.append(supportFilesPath)

import ConfigureFiles
from Utilities import makePath

configurePortalOptions = True

scriptName = sys.argv[0]

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------
if len(sys.argv) <> 2:
    print "\n" + scriptName + " <ArcGISServerFullyQualifiedDomainName>"
    print "\nWhere:"
    print "\n\t<ArcGISServerFullyQualifiedDomainName> (required parameter): " + \
    "the fully qualified domain name of the ArcGIS Server associated with this portal."
    print
    sys.exit(1)

agsFQDN = sys.argv[1]

webAppsRootPath = makePath("C", ["Program Files", "ArcGIS", "Portal", "webapps"])

try:
    totalSuccess = True
    
    # Edit Portal Option files (web app index.html, etc files.)
    if configurePortalOptions:
        success = ConfigureFiles.updatePortalOptions(webAppsRootPath, agsFQDN)
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
        print "Configuration of Portal files completed successfully.\n"
        sys.exit(0)
    else:
        print "ERROR: Configuration of Portal files was _NOT_ completed successfully.\n"
        sys.exit(1)
    