REM =====================================================================
REM Create Certificate
REM =====================================================================
REM This script launches the ServerManager.msc interface

echo.
echo %sectionBreak%
echo Create domain certificate and bind to https port 443 using IIS Manager
echo.
echo When the "Server Manager" interface opens, perform the following^:
echo.
echo 1. Navigate to Server Manager ^> Roles ^> Web Server ^(IIS^)
echo             ^> Internet Information Services ^(IIS^) Manager
echo.
echo 2. From the Connections panel, click on the server node and then
echo             double-click on "Server Certificates" ^(in IIS group^).
echo.
echo 3. From the "Actions" panel, click "Create Domain Certificate".
echo.
echo 4. On the "Distinguished Name Properties" dialog enter...
echo.
echo      Common name^:        %ops_agsFQDN%
echo      Organization^:       Esri, Inc.
echo      Organization unit^:  Development
echo      City^/locality^:      Redlands
echo      State^/province^:     CA
echo      Country^/region^:     US
echo.
echo      Then click "Next" button.
echo.
echo 5. On the "Online Certificaion Authority" dialog...
echo.
echo    ^- Click "Select", click the "ESRI Enterprise Root" certificate
echo       authority and click "OK".
echo.
echo    ^- Within the "Friendly name" textbox enter "%ops_agsFQDN% Esri Ent Root CA".
echo.
echo    ^- Click "Finish".
echo.
echo 6. Now you will bind the certificate to https port 443...
echo.
echo    ^- From the "Connections" panel, navigate to Sites ^> Default Web Site
echo.
echo    ^- From the "Actions" panel, click "Bindings".
echo.
echo    ^- On the "Site Bindings" dialog, click "Add",
echo       select "https" in "Type" dropdown, select the certificate you made above
echo       in the "SSL certificate" dropdown and then click "OK".
echo       On the "Site Bindings" dialog, click "Close".
echo.
echo 7. Now close the "Server Manager" interface, click File ^> Exit.
echo.
echo.

%SystemRoot%\system32\ServerManager.msc
PING 127.0.0.1 -n 3 > nul
