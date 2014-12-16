rem #------------------------------------------------------------------------------
rem # Copyright 2014 Esri
rem # Licensed under the Apache License, Version 2.0 (the "License");
rem # you may not use this file except in compliance with the License.
rem # You may obtain a copy of the License at
rem #
rem #   http://www.apache.org/licenses/LICENSE-2.0
rem #
rem # Unless required by applicable law or agreed to in writing, software
rem # distributed under the License is distributed on an "AS IS" BASIS,
rem # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
rem # See the License for the specific language governing permissions and
rem # limitations under the License.
rem #==============================================================================
rem # Name:          CreateCertificate.bat
rem #
rem # Purpose:       Enable SSL and bind the SSL certificate to web site that hosts
rem #                the web adaptor
rem #
rem # Prerequisites: IIS must be installed.
rem #
rem #==============================================================================
echo.
echo.
echo %sectionBreak%
echo  Enable SSL on your web server...
echo.
echo    To enable SSL on your web server you will need to:
echo      ^- Obtain a SSL certificate from a Certificate Authority or create a domain certificate.
echo      ^- Bind the certificate to the website that will host the ArcGIS Web Adaptor for IIS.
echo    See the instructions below.
echo.
echo. 
echo    When the "Internet Information Services ^(IIS^) Manager" interface opens, perform the following:
echo.
echo.
echo    1. From the Connections panel, click on the server node and then
echo             double-click on "Server Certificates" ^(in IIS group^).
echo.
echo.
echo    ^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-
echo    2. Create Certificate Authority certificate __OR__ domain certificate.
echo.
echo.
echo        ^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-
echo.       To create Certificate Authority certificate:
echo        ^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-
echo.
echo        For more detailed information see the following web page:
echo.
echo        http://www.sslshopper.com/article-installing-an-ssl-certificate-in-windows-server-2008-iis-7.0.html
echo.
echo.
echo            2a. From the "Actions" panel, click "Create Certificate Request".
echo.
echo.
echo            2b. On the "Distinguished Name Properties" dialog...
echo.
echo                ^- Enter...
echo.
echo                Common name:        %ops_FQDN%
echo                Organization:       "Specify your organization"
echo                Organization unit:  "Specify organization unit"
echo                City^/locality:      "Specify your city/locality" ^(no abbreviations^)
echo                State^/province:     "Specify your state/provice" ^(no abbreviations^)
echo                Country^/region:     "Specify your country/region"
echo.
echo                ^- Click "Next".
echo.
echo.
echo            2c. On the "Cryptographic Service Provider Properties" dialog...
echo.
echo                ^- Use the default "Cryptographic service provider"
echo                    ^(i.e. Microsoft RSA SChannel Cryptographic Provider^)
echo.
echo                ^- Select a minimum bit length of at least 2048 or higher.
echo.
echo                ^- Click "Next" button.
echo.
echo.
echo            2d. On the "File Name" dialog...
echo.
echo                ^- Specify a file name for the certificate request (CSR file).
echo.
echo                ^- Click "Finish".
echo.
echo.
echo            2e. Use the contents of the CSR file to obtain a certificate
echo                from a Certficate Authority.
echo.
echo.
echo            2f. When you have obtained the certificate from a Certficate
echo                Authority, install the certificate by clicking on
echo                "Complete Certficate Request".
echo.
echo.
echo.           2g. On the "Specify Certificate Authority Response" dialog...
echo.
echo                ^- Browse to the certificate file.
echo.
echo                ^- Within the "Friendly name" textbox enter a friendly name
echo                  such as "%ops_FQDN%".
echo.
echo.
echo            2h. Proceed to step #3.
echo.
echo.
echo        ^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-
echo.       To create domain certificate:
echo        ^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-
echo.
echo            2a. From the "Actions" panel, click "Create Domain Certificate".
echo.
echo.
echo            2b. On the "Distinguished Name Properties" dialog enter...
echo.
echo.
echo                Common name:        %ops_FQDN%
echo                Organization:       "Specify your organization"
echo                Organization unit:  "Specify organization unit"
echo                City^/locality:      "Specify your city/locality" ^(no abbreviations^)
echo                State^/province:     "Specify your state/provice" ^(no abbreviations^)
echo                Country^/region:     "Specify your country/region"
echo.
echo                Then click "Next" button.
echo.
echo.
echo            2c. On the "Online Certificaion Authority" dialog...
echo.
echo                ^- Click "Select", click the certificate authority and click "OK".
echo.
echo                ^- Within the "Friendly name" textbox enter a friendly name
echo                  such as "%ops_FQDN%".
echo.
echo                ^- Click "Finish".
echo.
echo.
echo            2d. Proceed to step #3.
echo.
echo.
echo    ^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-^-
echo.
echo    3. Bind the certificate to the web site that will host the web adaptor.
echo.
echo.
echo        3a. From the "Connections" panel, navigate to Sites ^> Default Web Site
echo.
echo.
echo        3b. From the "Actions" panel, click "Bindings".
echo.
echo.
echo        3c. On the "Site Bindings" dialog, click "Add"...
echo.
echo            ^- Select "https" in "Type" dropdown.
echo.
echo            ^- Select the SSL certificate in the "SSL certificate" dropdown.
echo.
echo            ^- Click "OK".
echo.
echo            ^- On the "Site Bindings" dialog, click "Close".
echo.
echo.
echo    4. Close the "Server Manager" interface; click File ^> Exit.
echo.
echo.

%windir%\system32\inetsrv\InetMgr.exe
PING 127.0.0.1 -n 3 > nul
