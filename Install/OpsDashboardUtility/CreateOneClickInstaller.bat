REM =====================================================================
REM Create the Operations Dashboard One-click Installer
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo.
echo %sectionBreak%
echo Create the Operations Dashboard One-click Installer...
echo.
echo.

REM ---------------------------------------------------------------------
REM Create the folder to store the deployment files created by the 
REM Ops Dashboard Deployment Utility
REM ---------------------------------------------------------------------
set ops_outputFolder=%ops_tempInstallDir%\OpsDashboardUtilityOutput

echo --Creating the output folder %ops_outputFolder%...
echo.

set execute=mkdir %ops_outputFolder%

if not exist %ops_outputFolder% (
  echo %execute%
  echo.
  %execute%
  Call %ops_ChkErrLevelFile% %ERRORLEVEL%
)


REM ---------------------------------------------------------------------
REM Run the Operations Dashboard Deployment Utility
REM ---------------------------------------------------------------------
echo.
echo.
echo --Running the Operations Dashboard Deployment Utility...
echo.
echo.
echo   NOTE: When the "Importing a new private signature key" dialog is
echo         displayed, click "OK".
echo.
echo.
set execute=START /WAIT %ops_softwareRoot%\OpsDashboardUtility\OperationsDashboardUtility.exe ^
/outPut %ops_outputFolder% /url https://%ops_FQDN%/arcgis ^
/certpath %ops_softwareRoot%\OpsDashboardUtility\Certificate\DefenseSolutions.pfx ^
/password esripassword /CertType selfsigned /authentMode Token
echo %execute%
echo.
echo It will take a couple of minutes for the OperationsDashboardUtility.exe to complete.
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 8 > nul


REM -----------------------------------
REM Copy One-click installer
REM -----------------------------------
set ops_destPath="C:\Program Files\ArcGIS\Portal\webapps\docroot\opsdashboard"
echo.
echo.
echo --Copying Ops Dashboard One-click installer files to %ops_destPath%...
echo.
set execute=START /WAIT robocopy %ops_outputFolder%\opsdashboard %ops_destPath% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY


REM -----------------------------------
REM Copy help files
REM -----------------------------------
set ops_destPath="C:\Program Files\ArcGIS\Portal\webapps\docroot\help\en\operations-dashboard"
echo.
echo.
echo --Copying Ops Dashboard help filesOne-click to %ops_destPath%...
echo.
set execute=START /WAIT robocopy %ops_outputFolder%\operations-dashboard %ops_destPath% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY
