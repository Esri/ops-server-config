@echo off
title Operations Server Installer

REM ---------------------------------------------------------------------
REM Set User Editable Variables
REM ---------------------------------------------------------------------

REM This variable defines the fully qualified domain name (FQDN) of the
REM server that ArcGIS Server and Portal for ArcGIS are being installed.
REM *****
REM NOTE: specify ops_FQDN value in lowercase.
REM *****
set ops_FQDN=SET_FQDN_OF_SERVER

REM Root folder where software installers are located. This can be a logical
REM drive letter or a UNC path.
set ops_softwareRoot=SET_PATH_TO_SOFTWARE_FOLDER

REM This variable defines the account that will run the ArcGIS
REM Server service. It can be a local user account or a domain account.
REM If using a local account and the account does not exist it will be created
REM using the password set by the variable "ops_passWord".
REM If using a domain account, the account must already exist.
REM Specify domain account using the syntax "domain\user". If the local/domain
REM account already exists, then the variable "ops_passWord" must be set
REM to the accounts password.
set ops_agsServiceAccount=SET_AGS_ACCOUNT_NAME

REM This variable defines the user name for the ArcGIS Server
REM site administrator user.
set ops_userName=SET_ACCOUNT_USER_NAME

REM This varaible is used for the following passwords: PostgreSQL superuser,
REM PostgreSQL service account, ArcGIS Server service account, ArcGIS Server
REM site administrator, and the "sde" user password that owns the ops server
REM geodatabases.
set ops_passWord=SET_PASSWORD_HERE

REM Defines the drive where the ArcGIS Server site cache directory will
REM be created.
set ops_cacheDrive=c

REM Defines the drive where the Ops Server Data directory will be created.
set ops_dataDrive=c

REM Define which web browser to use for installation steps which require you
REM to work within a web browser. Have encountered issues with Internet Explorer;
REM recommend FireFox or Chrome (NOTE: have mostly tested with FireFox).
set ops_webBrowserExePath="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

REM Define which text editor to use for installation steps which require you
REM to work within a text editor.
set ops_textEditorExePath=C:\Windows\System32\notepad.exe

REM The variables below define which processes to execute.
set ops_install_jdk1_7=NO
set ops_install_jdk1_6=NO
set ops_install_rdbms=YES
set ops_install_server=YES
set ops_install_webadaptor=YES
set ops_register_ags=YES
set ops_install_portal=YES
set ops_create_portal_admin_account=YES
set ops_register_portal=YES
set ops_change_ags_security=YES
set ops_register_ags_https=YES
set ops_federate_ags=YES

REM ---------------------------------------------------------------------
REM END Set User Editable Variables
REM ---------------------------------------------------------------------

REM Define PostgreSQL paths
set ops_postgresqlInstallDIR="C:\Program Files\PostgreSQL\9.2"
set ops_postgresqlDataDIR=%ops_postgresqlInstallDIR%\data

REM Define path to Esri SoftwareAuthorization.exe
set ops_softwareAuthExePath="C:\Program Files\Common Files\ArcGIS\bin\SoftwareAuthorization.exe"

REM Define root folder path to ArcGIS Server authorization files
set ops_AuthFileRootAGS=%ops_softwareRoot%\Authorization_Files\ArcGIS_Server\Advanced

REM Define root folder path to Portal for ArcGIS authorization files
set ops_AuthFileRootPortal=%ops_softwareRoot%\Authorization_Files\ArcGIS_Portal

REM Define path to ConfigureWebAdaptor.exe
set ops_ConfWebAdaptorExePath="C:\Program Files (x86)\Common Files\ArcGIS\WebAdaptor\IIS\Tools\ConfigureWebAdaptor.exe"

set sectionBreak=========================================================================
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

:start
REM ---------------------------------------------------------------------
REM Start Block
REM ---------------------------------------------------------------------
echo *************************************************************************
echo *                    Operations Server Installation                     *
echo *************************************************************************
echo.
REM Display prequisites and other important install notes stored in Notes.txt
REM to user.
type Notes.txt
echo.
echo *************************************************************************
echo.
echo 1. Install Ops Server.
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

REM Install Web Adaptor
if "%ops_install_webadaptor%"=="YES" (
    Call %~dp0WebAdaptorIIS\InstallWebAdaptor.bat
)

REM Register ArcGIS Server with the Web Adaptor
if "%ops_register_ags%"=="YES" (
    Call %~dp0WebAdaptorIIS\RegisterAGSwithWebAdaptor.bat
)

REM Install Portal Related Software
if "%ops_install_portal%"=="YES" (
    Call %~dp0Portal\InstallPortal.bat
)

echo.
echo.
echo Almost done...
date /T
time /T
echo.
echo.

REM Create the portal primary administrator account
if "%ops_create_portal_admin_account%"=="YES" (
    Call %~dp0Portal\Portal\CreatePortalAdminAccount.bat
)

REM Register portal with the webadaptor
if "%ops_register_portal%"=="YES" (
    Call %~dp0WebAdaptorIIS\RegisterPortalwithWebAdaptor.bat
)

REM Change ArcGIS security config to "HTTPS Only"
if "%ops_change_ags_security%"=="YES" (
    Call %~dp0ArcGISServer\SupportFiles\ChangeAGSSecurityConfig.bat
)

REM Re-register ArcGIS Server with the web adaptor because the
REM security config was changed to HTTPS.
if "%ops_register_ags_https%"=="YES" (
    Call Call %~dp0WebAdaptorIIS\RegisterAGSwithWebAdaptorHTTPS.bat
    
    REM should we delete the http web adaptor entry?
)

REM Federate ArcGIS Server site with portal; set hosted server
REM and set SSL properties.
if "%ops_federate_ags%"=="YES" (
    Call %~dp0ArcGISServer\SupportFiles\FederateAGS.bat
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
echo Installation of Ops Server completed.
date /T
time /T
echo.
pause
REM exit