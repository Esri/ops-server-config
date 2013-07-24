REM =====================================================================
REM Register ArcGIS Server with the Web Adpator for IIS
REM =====================================================================

set ops_portalPropsFile="C:\Program Files\ArcGIS\Portal\etc\portal-config.properties"
echo.
echo %sectionBreak%
echo Register Portal for ArcGIS with the Web Adaptor for IIS...

REM ---------------------------------------------------------------------
REM Open the portal config file in note pad so user can copy the
REM shared key to paste into the web adaptor web page
REM ---------------------------------------------------------------------
echo.
echo.
echo ^- When the portal config properties file opens in notepad...
echo.
echo   1. Copy the "security.shared.key" value ^(you will need
echo      this value in a following step^).
echo.
echo      NOTE: Copy this value to another notepad session in
echo            case the contents of the copy buffer is lost.
echo.
echo   2. Close notepad.
echo.
echo.
%ops_textEditorExePath% %ops_portalPropsFile%


REM ---------------------------------------------------------------------
REM Open brower to webadaptor portal page
REM ---------------------------------------------------------------------
echo ^- When web browser opens the ArcGIS Web Adaptor Portal page...
echo.
echo    NOTE: For Firefox you may receive "This Connection is Untrusted"
echo          warning. In this case, click "I Understand the Risks", then
echo          click "Add Exception"; on the "Add Security Exception"
echo          dialog, click "Confirm Security Exception".
echo.
echo  1. For the "Portal URL" type the URL to the machine
echo     hosting Portal for ArcGIS, i.e.,
echo.
echo     http://%ops_agsFQDN%^:7080
echo.
echo  2. For the "Shared Key", paste the "security.shared.key"
echo     value you copied from the portal config properties file.
echo.
echo  3. Click "Configure".
echo.
echo. 4. Copy the contents in the green status box on the
echo     configuration page ^(you will need these values
echo     in the following step^).
echo.
echo      NOTE: Copy these values to another notepad session in
echo            case the contents of the copy buffer is lost.
echo.
echo  5. Close the web browser.
echo.
echo.
%ops_webBrowserExePath% https://%ops_agsFQDN%/arcgis/webadaptor/portal

REM ---------------------------------------------------------------------
REM Open the portal config file in note pad so user can paste the
REM information copied from the web adaptor portal config page
REM ---------------------------------------------------------------------
echo ^- When the portal config properties file opens in notepad...
echo.
echo   1. Replace the following with the content you copied
echo      from the configuration page:
echo.
echo      webadaptor.url^=
echo      webadaptor.http.port^=
echo      webadaptor.https.port^=
echo      webadaptor.server.name=
echo.
echo      The above properties should now be identical to
echo      the content you copied from the configuration
echo      page.
echo.
echo   2. Save and close the portal-config.properties file.
echo.
echo.
%ops_textEditorExePath% %ops_portalPropsFile%

REM ---------------------------------------------------------------------
REM Stop/Start the portal service for the changes made above to take affect
REM ---------------------------------------------------------------------
Call %~dp0..\Portal\Portal\RestartPortal.bat


echo.
echo ---------------------
echo NOTE^:
echo The Web Adaptor is now configured for use with the machine
echo hosting Portal for ArcGIS. You'll now access portal through
echo the web adaptor URL, instead of port 7080, i.e.,
echo https://%ops_agsFQDN%/arcgis/home
echo ---------------------
echo.