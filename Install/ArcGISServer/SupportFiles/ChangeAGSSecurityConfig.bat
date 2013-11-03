REM =====================================================================
REM Change the ArcGIS Server Security Configuration
REM =====================================================================
REM We're changing from the default of "HTTP and HTTPS" to "HTTPS Only"
set ops_ChkErrLevelFile=%~dp0..\..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat
echo.
echo.
echo %sectionBreak%
echo Change the ArcGIS Server security configuration to "HTTPS Only"...
echo.
echo ^- When the web browser opens...
echo.
echo    1. Sign in to the "ArcGIS Server Administrator Directory"
echo       site as the ArcGIS Server site administrator.
echo.
echo       Username: %ops_userName%
echo       Password: %ops_passWord%
echo.
echo       NOTE: You will be redirected to the "Security/Config"  page.
echo.
echo.
echo    2. On the "Security/Config" page, click the "update" link.
echo.
echo.
echo    4. In the "Protocol" dropdown, select "HTTPS Only".
echo.
echo.
echo    5. Click "Update".
echo.
echo       NOTE: this may take a minute or two to complete
echo             because the web server has to be restarted.
echo.
echo.
echo    6. Sign out from the "ArcGIS Server Administrator Directory".
echo.
echo.      NOTE: if the sign out results in an error or does not sign out,
echo             just close the web browser.
echo.
echo.
echo    7. Close the web browser.
echo.
echo.
set execute=%ops_webBrowserExePath% http://%ops_FQDN%:6080/arcgis/admin/security/config
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%

echo.
echo Giving ArcGIS Server a few more seconds to restart...
echo.
PING 127.0.0.1 -n 30 > nul
