REM =====================================================================
REM Install ArcGIS Server and Authorize Software
REM =====================================================================
echo.
echo %sectionBreak%
echo Install ArcGIS Server

REM ---------------------------------------------------------------------
REM Install ArcGIS Server
REM ---------------------------------------------------------------------
echo.
echo --Installing ArcGIS Server...
msiexec /I %ops_softwareRoot%\ArcGISServer\setup.msi /qb ^
    USER_NAME=%ops_agsServiceAccount% PASSWORD=%ops_passWord% INSTALLDIR1=C:\Python27
    
REM ---------------------------------------------------------------------
REM "Install" PostgreSQL client libraries to ArcGIS Server bin folder
REM ---------------------------------------------------------------------
echo.
echo --Copying PostgreSQL client libraries to ArcGIS Server bin folder...
START /WAIT robocopy %ops_softwareRoot%\Database\PostgreSQL_9.2.2\Windows\64bit\ ^
    "C:\Program Files\ArcGIS\Server\bin" *.*


REM ---------------------------------------------------------------------
REM "Install" geometry library to PostgreSQL lib folder
REM ---------------------------------------------------------------------
echo.
echo --Copying geometry library to PostgreSQL lib folder...
START /WAIT robocopy "C:\Program Files\ArcGIS\Server\DatabaseSupport\PostgreSQL\9.2\Windows64" ^
    %ops_postgresqlInstallDIR%\lib"

REM ---------------------------------------------------------------------
REM Authorize ArcGIS Server Software
REM ---------------------------------------------------------------------
echo.
echo --Authorizing ArcGIS Server...
echo.

REM Determine which type of authorization file to use; if no files found then
REM SoftwareAuthorization.exe will prompt user to walk through the authoriation wizard.

if exist %ops_AuthFileRootAGS%\Server_Ent_Adv.ecp (
	set ops_AuthFile=%ops_AuthFileRootAGS%\Server_Ent_Adv.ecp
) else if exist %ops_AuthFileRootAGS%\Server_Ent_Adv.prvc (
	set ops_AuthFile=%ops_AuthFileRootAGS%\Server_Ent_Adv.prvc
) else (
	set ops_AuthFile=NO_AUTHORIZATION_FILE_PROMPT_USER_FOR_INPUT
)

echo   Will use the following file to authorize. If no file found, 
echo   Software Authorization wizard will walk user through process:
echo   %ops_AuthFile%
echo.

if %ops_AuthFile%==NO_AUTHORIZATION_FILE_PROMPT_USER_FOR_INPUT (
  echo   Prompting user for authorizing information...
  %ops_softwareAuthExePath% -S Ver 10.2
) else (
  %ops_softwareAuthExePath% -S Ver 10.2 -LIF %ops_AuthFile%
)
PING 127.0.0.1 -n 15 > nul

REM ---------------------------------------------------------------------
REM Shutdown ArcGIS Server service
REM ---------------------------------------------------------------------

REM 2013/080/08: No longer need to edit the rest-config.properties
REM Commented out the code to edit the file and start the
REM AGS windows service.
REM -----------
REM Stop ArcGIS Server service so we edit the rest file.
rem echo %sectionBreak%
rem set winServicename="ArcGIS Server"
rem echo.
rem echo Stopping the ArcGIS Server service so we can edit the REST file...
rem echo.
rem net stop %winServicename%
rem PING 127.0.0.1 -n 10 > nul



REM ---------------------------------------------------------------------
REM Install/configure JavaScript API and Configure REST Properties
REM ---------------------------------------------------------------------

REM 2013/080/08: No longer need to edit the rest-config.properties
REM Commented out the code to edit the file and start the
REM AGS windows service.
REM -----------
rem echo.
rem echo %sectionBreak%
rem echo Configure ArcGIS Server files...
rem echo.

REM Shouldn't need to install the JavaScript API since one is installed
REM with 10.2 portal
REM Install JavaScript
REM Call "%~dp0..\..\..\SupportFiles\InstallJavaScriptAPIs.py" ^
REM  "C:\inetpub\wwwroot" %ops_softwareRoot%\JavaScriptAPI
REM PING 127.0.0.1 -n 3 > nul

REM 2013/080/08: No longer need to edit the rest-config.properties;
REM these properties are set through the AGS Admin REST API
REM -----------
REM Modify ArcGIS Server REST properties file
REM Call "%~dp0SupportFiles\ConfigureAGSFiles.py"
REM PING 127.0.0.1 -n 3 > nul

REM 2013/080/08: No longer need to restart the ArcGIS Server
REM service since we don't need to edit the rest-config.properties
REM file.
REM -----------
REM Restart ArcGIS Service to refresh the rest-properties file which
REM was editing in the call to the ConfigureAGSFiles.py script.
rem set winServicename="ArcGIS Server"
rem echo.
rem echo %sectionBreak%
rem echo Start ArcGIS Server service...
rem echo.
rem net start %winServicename%
rem PING 127.0.0.1 -n 20 > nul
    
REM ---------------------------------------------------------------------
REM Create ArcGIS Server site, create data stores, register data stores
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Create ArcGIS Server site, create data stores, and register data stores...
echo.
Call "%~dp0SupportFiles\CreateOpsServer.py" %ops_agsServiceAccount% ^
                %ops_userName% %ops_passWord% %ops_dataDrive% %ops_cacheDrive%
                

REM Add delay
PING 127.0.0.1 -n 6 > nul
