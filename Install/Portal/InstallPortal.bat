REM =====================================================================
REM Install Portal Software
REM =====================================================================

SET FQDN=%ops_FQDN%

REM ---------------------------------------------------------------------
REM Install Portal for ArcGIS
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Install Portal for ArcGIS
echo.
echo --Installing Portal for ArcGIS...
msiexec /I %ops_softwareRoot%\Portal\setup.msi /qb CONTENTDIR=C:\arcgisportal
PING 127.0.0.1 -n 3 > nul

REM ---------------------------------------------------------------------
REM Authorize Portal for ArcGIS
REM ---------------------------------------------------------------------
echo.
echo --Authorizing Portal for ArcGIS...
echo.

REM Determine which type of authorization file to use; if no files found then
REM SoftwareAuthorization.exe will prompt user to walk through the authoriation wizard.

if exist %ops_AuthFileRootPortal%\Portal_100.ecp (
	set ops_AuthFile=%ops_AuthFileRootPortal%\Portal_100.ecp
) else if exist %ops_AuthFileRootPortal%\Portal_100.prvc (
	set ops_AuthFile=%ops_AuthFileRootPortal%\Portal_100.prvc
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
REM Configure portal files
REM ---------------------------------------------------------------------
REM echo.
rem echo %sectionBreak%
rem echo Configure Portal files...
rem echo.
rem echo Don't think we need to do this anymore with 10.2 portal.
rem echo Commented call to "%~dp0Portal\ConfigurePortalFiles.py"
REM Call "%~dp0Portal\ConfigurePortalFiles.py" %FQDN%
REM PING 127.0.0.1 -n 3 > nul
rem echo.

REM ---------------------------------------------------------------------
REM Configure ArcGIS Server Services Directory properties to point to
REM locally hosted ArcGIS for JavaScript API
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Configure ArcGIS Server Services Directory to point to
echo locally hosted ArcGIS for JavaScript API...
echo.
Call "%~dp0..\..\SupportFiles\SetServicesDirectoryProps.py" ^
 %FQDN% # %ops_userName% %ops_passWord% No
echo.
 