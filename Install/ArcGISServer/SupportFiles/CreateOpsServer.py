#==============================================================================
#Name:          CreateOpsServer.py
#Purpose:       Creates ArcGIS Server site, creates and registers data stores,
#               and configures Java Script API.
#
#Prerequisites: ArcGIS Server must be installed and authorized before executing
#               this script.
#
#History:       2012:   Initial code.
#
#==============================================================================
import sys, os, time, traceback, platform

# Add ConfigureOpsServer\SupportFiles to sys path inorder to import
#   modules in subfolder
supportFilesPath = os.path.join(
    os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(sys.argv[0])))), "SupportFiles")

sys.path.append(supportFilesPath)

import OpsServerConfig
import PreConfigurationChecks
import CreateLocalDataStores
import CreateSite
import RegisterDataStores

preConfigChecks = True
createSite = True
createDataStores = True
registerDataStores = True

serverName = OpsServerConfig.serverName
sharedDSConfig = OpsServerConfig.sharedDataStoreConfig

scriptName = sys.argv[0]

# ---------------------------------------------------------------------
# Check arguments
# ---------------------------------------------------------------------   
if len(sys.argv) <> 6:
    print "\n" + scriptName + " <AGSServiceAccount> <AGSSiteUserName> " + \
                "<passWord> <DataDriveLetter> <CacheDriveLetter>"
    print "\nWhere:"
    print "\n\t<AGSServiceAccount> (required parameter): ArcGIS Server service account"
    print "\n\t<AGSSiteUserName> (required parameter): ArcGIS Server site administrator user name"
    print "\n\t<passWord> (required parameter): Password used for AGS site admin, and sde user"
    print "\n\t<DataDriveLetter> (required parameter): the drive letter where Ops Server data will be stored"
    print "\n\t<CacheDriveLetter> (required parameter): the drive letter where Ops Server cache files will be stored"
    print
    sys.exit(1)


agsServerAccount = sys.argv[1]
userName = sys.argv[2]
passWord = sys.argv[3]
dataDrive = sys.argv[4]
cacheDrive = sys.argv[5]

    
try:
    success = True
    
    # Perform pre-configuration checks
    if preConfigChecks:
        success = PreConfigurationChecks.PreConfigChecks(userName, passWord)
    
    if not success:
        
        print
        print "\t**************************"
        print "\tERROR:"
        print "\tPre-Configuration checks FAILED."
        print "\tExiting configuration process."
        print "\t**************************"
        print
        
    else:
        print
        print "\t**************************"
        print "\tPre-Configuration checks PASSED."
        print "\tContinuing with configuration..."
        print "\t**************************"
        print
        
        # Create ArcGIS Server Site
        if createSite:
            if success:
                success = CreateSite.createSite(userName, passWord,
                                                dataDrive, cacheDrive)
                
                if success:
                    success = CreateSite.createAGSConnFile(userName, passWord)
        
        # Create local data stores
        if createDataStores:
            if success:
                success = CreateLocalDataStores.createDataStores(
                                        agsServerAccount, passWord, dataDrive)
        
        # Register local data stores
        if registerDataStores:
            if success:
                success = RegisterDataStores.registerDataStores(
                                                sharedDSConfig, False,
                                                userName, passWord, dataDrive)
    
    
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
    if success:
        print "Configuration of Ops Server ArcGIS Server/Site completed successfully."
        sys.exit(0)
    else:
        print "ERROR: Configuration of Ops Server ArcGIS Server/Site was _NOT_ completed successfully."
        sys.exit(1)
