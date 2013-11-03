REM =====================================================================
REM Install Portal Software
REM =====================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat
SET FQDN=%ops_FQDN%

REM ---------------------------------------------------------------------
REM Install Portal for ArcGIS
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Install Portal for ArcGIS
echo.
echo --Installing Portal for ArcGIS...
echo.
set execute=%ops_softwareRoot%\Portal\setup.exe /qb CONTENTDIR=C:\arcgisportal

echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul

REM ---------------------------------------------------------------------
REM Authorize Portal for ArcGIS
REM ---------------------------------------------------------------------
echo.
echo --Authorizing Portal for ArcGIS...
echo.
echo   Will use the following file to authorize. If no file found, 
echo   Software Authorization wizard will walk user through process:
echo   %ops_PortalAuthFile%
echo.
set execute=%ops_softwareAuthExePath% -S Ver %ops_PortalVersion%
if exist %ops_PortalAuthFile% (
    set execute=%execute% -LIF %ops_PortalAuthFile%
) else (
    echo   Prompting user for authorizing information...
)
echo.
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 15 > nul

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
 %FQDN% # %ops_userName% %ops_passWord% Yes
echo.
 