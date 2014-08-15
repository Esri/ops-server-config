@echo off
title Operations Server Installer

REM ---------------------------------------------------------------------
REM Set user specified variables
REM ---------------------------------------------------------------------
Call InstallSettings.bat

REM ---------------------------------------------------------------------
REM Set other variables
REM ---------------------------------------------------------------------
set ops_AGSVersion=10.3
set ops_PortalVersion=10.3

REM Define ArcGIS Data Store Path
REM NOTE: must have "\" at end of path
set ops_agsDataStoreDIR=C:\AGSDataStore\

REM Define PostgreSQL paths
set ops_postgresqlInstallDIR=C:\PostgreSQL\9.2
set ops_postgresqlDataDIR=%ops_postgresqlInstallDIR%\data

REM Define path to Esri SoftwareAuthorization.exe
set ops_softwareAuthExePath="C:\Program Files\Common Files\ArcGIS\bin\SoftwareAuthorization.exe"

REM Define path to ConfigureWebAdaptor.exe
set ops_ConfWebAdaptorExePath="C:\Program Files (x86)\Common Files\ArcGIS\WebAdaptor\IIS\Tools\ConfigureWebAdaptor.exe"

REM ---------------------------------------------------------------------
REM Set the names of ArcGIS Server Web Adaptor and Portal for ArcGIS Web Adaptor
set ops_WebAdaptor_AGS=ags
set ops_WebAdaptor_Portal=arcgis

set sectionBreak===================================================================================
set ops_tempInstallDir=C:\OpsServerInstallTemp
cls

REM ---------------------------------------------------------------------
REM Check if command prompt is running in elevated permissions mode
REM (i.e. "run as administrator)
REM ---------------------------------------------------------------------
echo.
echo --Checking if Windows Command window is running as administrator
echo   by querying LOCAL SERVICE user registry entries...
echo.
reg query HKU\S-1-5-19
if "%ERRORLEVEL%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR:
    echo **  You are _NOT_ running Windows Command window
    echo **  in elevated administrator mode ^(i.e., the CMD.exe
    echo **  must be "Run as administrator"^).
    echo **  Exiting InstallOpsServer.bat.
    echo **********************************************************
    echo.
    goto end
)
cls

REM ---------------------------------------------------------------------
REM Check if user "installed" configuration script in correct location
REM ---------------------------------------------------------------------
echo.
echo --Checking if installation scripts are installed in the correct location...

set ops_ScriptRootName=ops-server-config
set ops_ScriptRoot=C:\%ops_ScriptRootName%\

echo %~dp0 | find /I "%ops_ScriptRoot%"

if "%ERRORLEVEL%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR:
    echo **  The '%ops_ScriptRootName%' folder is not installed in
    echo **  the correct location. It should be located at:
    echo **  %ops_ScriptRoot%
    echo **  Exiting InstallOpsServer.bat.
    echo **********************************************************
    echo.
    goto end
)
cls

REM ---------------------------------------------------------------------
REM Check if Software Root path exists and you have access to the folder
REM ---------------------------------------------------------------------

echo.
echo --Checking if specified software root path '%ops_softwareRoot%' exists...

if not exist %ops_softwareRoot% (
    echo.
    echo **********************************************************
    echo **  ERROR:
    echo **  The software root path ^(variable 'ops_softwareRoot'^)
    echo **  '%ops_softwareRoot%'
    echo **  you have specified does not exist or your account does
    echo **  not have access to this location.
    echo **  Exiting InstallOpsServer.bat.
    echo **********************************************************
    echo.
    goto end
)
cls

echo.
echo --Checking if you have access to the software root path '%ops_softwareRoot%'...

dir %ops_softwareRoot%
if "%ERRORLEVEL%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR:
    echo **  Your account does not have access to the sofware root
    echo **  folder path '%ops_ScriptRoot%'
    echo **  Exiting InstallOpsServer.bat.
    echo **********************************************************
    echo.
    goto end
)
cls

REM ---------------------------------------------------------------------
REM Check software dependencies
REM ---------------------------------------------------------------------
REM Always call SetOverallErrorLevel.bat after running one of the "check"
REM batch files under the "Checks" folder.

REM Set error "flag" to initial "good" value of zero.
set ops_OverallErrLvl=0

REM Check if IIS is running/installed.
Call %~dp0..\SupportFiles\BatchFiles\Checks\IsInstalled_IIS.bat
Call %~dp0..\SupportFiles\BatchFiles\SetOverallErrorLevel.bat %ops_CheckErrLvl%

REM Check if .NET 3.5 is installed.
Call %~dp0..\SupportFiles\BatchFiles\Checks\IsInstalled_NETFramework3_5.bat
Call %~dp0..\SupportFiles\BatchFiles\SetOverallErrorLevel.bat %ops_CheckErrLvl%

REM Check if .NET 4.5 is installed
Call %~dp0..\SupportFiles\BatchFiles\Checks\IsInstalled_NETFramework4_5.bat
Call %~dp0..\SupportFiles\BatchFiles\SetOverallErrorLevel.bat %ops_CheckErrLvl%

REM Pause script execution if dependencies are not met.
Call %~dp0..\SupportFiles\BatchFiles\CheckErrorLevel.bat %ops_OverallErrLvl%

REM Clear screen
cls

:start
REM ---------------------------------------------------------------------
REM Start Block
REM ---------------------------------------------------------------------
echo *************************************************************************
echo *                    Operations Server Installation                     *
echo *************************************************************************
echo.
echo 1. Install
echo. 
echo 0. Quit
echo.
 
set /p choice="Enter the number of your choice: "

if "%choice%"=="1" (
    set opsServerInstallType=Install
    REM was having problems with the IIS check on some systems;
    REM for now, set variable to "NO" so that it does not run
    REM the check. Not critical to run the check, since we do tell
    REM users that they have to uninstall IIS if it is already installed.
    set ops_Check_IIS_Existence=NO
    set ops_Check_DriveExistence=YES
    goto ValidationBeforeExecution
)
if "%choice%"=="0" exit
echo Invalid choice: %choice%
echo.
pause
cls
goto start


:ValidationBeforeExecution
REM ---------------------------------------------------------------------
REM Validate before executing the rest of the installation process
REM ---------------------------------------------------------------------


REM -------------------------------------------
REM Check if IIS is running
REM -------------------------------------------
if "%ops_Check_IIS_Existence%"=="YES" (
    REM ERRORLEVEL values when using the following "sc query" statement...
    REM If IIS service exists and is running: 0
    REM If IIS service exists and is stopped: 1
    REM If IIS service does not exist       : 1

    echo.
    echo.
    echo --Checking if IIS Web Server is running on this machine...
    echo.

    sc query W3SVC | find "RUNNING"
    if "%ERRORLEVEL%"=="0" (
        echo.
        echo **********************************************************
        echo **  ERROR:
        echo **  You have choosen to install Portal on a machine where
        echo **  IIS Web Server is also running. Please stop the IIS service
        echo **  ^(i.e. World Wide Web Publishing Service^) and set the startup
        echo **  type to "Manual", or uninstall IIS Web Server.
        echo **  Exiting InstallOpsServer.bat.
        echo **********************************************************
        echo.
        goto end
    )
    echo  IIS Web Server is not running or is not installed.
    echo.

)

REM -------------------------------------------
REM Check drives specified in cache and data
REM drive variables exist.
REM -------------------------------------------
if "%ops_Check_DriveExistence%"=="YES" (

    REM More info about using 'EXIST' command to determine drive
    REM existance can be found at: http://support.microsoft.com/kb/65994.
    REM An alternate choice to determine drive existance is to use:
    REM WMIC logicaldisk get name | find /I "%ops_cacheDrive%:"
    REM Then check immediately afterward if "%ERRORLEVEL%"=="1",
    REM which means drive letter does not exist.
    
    echo.
    echo --Checking if specified cache drive '%ops_cacheDrive%' exists...
    
    if not exist %ops_cacheDrive%:\NUL (
        echo.
        echo **********************************************************
        echo **  ERROR:
        echo **  The cache drive you have specified '%ops_cacheDrive%'
        echo **  does not exist. Either the 'ops_cacheDrive' variable in
        echo **  the InstallOpsServer.bat file is set to an incorrect
        echo **  drive letter or the drive is not mounted.
        echo **  Exiting InstallOpsServer.bat.
        echo **********************************************************
        echo.
        goto end
    ) else (
        echo Cache drive '%ops_cacheDrive%' exists.
    )
    
    echo.
    echo --Checking if specified data drive '%ops_dataDrive%' exists...
    
    if not exist %ops_dataDrive%:\NUL (
        echo.
        echo **********************************************************
        echo **  ERROR:
        echo **  The data drive you have specified '%ops_dataDrive%'
        echo **  does not exist. Either the 'ops_dataDrive' variable in
        echo **  the InstallOpsServer.bat file is set to an incorrect
        echo **  drive letter or the drive is not mounted.
        echo **  Exiting InstallOpsServer.bat.
        echo **********************************************************
        echo.
        goto end
    ) else (
        echo Data drive '%ops_dataDrive%' exists.
    )

)

if "%opsServerInstallType%"=="Install" goto Install


:Install
REM ---------------------------------------------------------------------
REM Install Software
REM ---------------------------------------------------------------------
echo.
echo Installation of Ops Server starting...
date /T
time /T
echo.

REM Install Java JDK 1.7
if "%ops_install_jdk1_7%"=="YES" (
    echo.
    echo %sectionBreak%
    echo Install Java JDK 1.7...
    echo.
    echo --Installing...
    echo.
    %ops_softwareRoot%\JavaJDK\jdk-7u7-windows-x64.exe /s
    PING 127.0.0.1 -n 60 > nul
)

REM Install Java JDK 1.6
if "%ops_install_jdk1_6%"=="YES" (
    echo.
    echo %sectionBreak%
    echo Install Java JDK 1.6...
    echo.
    echo --Installing...
    echo.
    %ops_softwareRoot%\JavaJDK\jdk-6u38-windows-x64.exe /s
    PING 127.0.0.1 -n 60 > nul
)

REM Install RDBMS
if "%ops_install_rdbms%"=="YES" (
    Call %~dp0PostgreSQL\InstallPostgreSQL.bat
)

REM Install ArcGIS Server
if "%ops_install_server%"=="YES" (
    Call %~dp0ArcGISServer\InstallArcGISServer.bat
)

REM Create ArcGIS Server site and data stores
if "%ops_create_ags_site%"=="YES" (
    Call %~dp0ArcGISServer\CreateArcGISServerSite.bat
)

REM Install ArcGIS GeoEvent Processor Extension for ArcGIS Server
if "%ops_install_geoevent%"=="YES" (
    Call %~dp0GeoEvent\InstallGeoEvent.bat
)

REM Install Web Adaptor
if "%ops_install_webadaptor%"=="YES" (
    Call %~dp0WebAdaptorIIS\InstallWebAdaptor.bat
)

REM Change ArcGIS security config to "HTTPS Only"
if "%ops_change_ags_security%"=="YES" (
    Call %~dp0ArcGISServer\SupportFiles\ChangeAGSSecurityConfig.bat
)

REM Register ArcGIS Server with the web adaptor as HTTPS
if "%ops_register_ags_https%"=="YES" (
    Call %~dp0WebAdaptorIIS\RegisterAGSwithWebAdaptorHTTPS.bat
)

REM Install ArcGIS Data Store
if "%ops_install_ags_datastore%"=="YES" (
    Call %~dp0ArcGISDataStore\InstallAGSDataStore.bat
)

REM Create ArcGIS Data Store
if "%ops_create_ags_datastore%"=="YES" (
    Call %~dp0ArcGISDataStore\SupportFiles\CreateAGSDataStore.bat
)

REM Install Portal Related Software
if "%ops_install_portal%"=="YES" (
    Call %~dp0Portal\InstallPortal.bat
)

REM Create Operations Dashboard ClickOnce Application and deploy to portal folders
if "%ops_create_opsdashboard_installer%"=="YES" (
    Call %~dp0OpsDashboardUtility\CreateOneClickInstaller.bat
)

REM Create the portal primary administrator account
if "%ops_create_portal_admin_account%"=="YES" (
    Call %~dp0Portal\Portal\CreatePortalAdminAccount.bat
)

REM Register portal with the webadaptor
if "%ops_register_portal%"=="YES" (
    Call %~dp0WebAdaptorIIS\RegisterPortalwithWebAdaptor.bat
)

REM Federate ArcGIS Server site with portal, set hosted server,
REM set SSL properties, and reset Utility service URLs
if "%ops_federate_ags%"=="YES" (
    Call %~dp0ArcGISServer\SupportFiles\FederateAGS.bat
)

REM Configure GeoEvent Processor Extension for ArcGIS Server
if "%ops_configure_geoevent%"=="YES" (
    Call %~dp0GeoEvent\SupportFiles\ConfigureGeoEvent.bat
)

goto end

:end
REM ---------------------------------------------------------------------
REM End Block
REM ---------------------------------------------------------------------
echo.
echo.
echo %sectionBreak%
echo Clean Up...

REM ------------------------------------------
REM Remove temp install folder
REM ------------------------------------------
echo.
echo Removing temp OpsServer install folder if exists...

IF EXIST %ops_tempInstallDir% (
 rmdir /S /Q %ops_tempInstallDir%
)
echo.
echo.
echo Execution of InstallOpsServer.bat script completed.
date /T
time /T
echo.
pause
REM exit