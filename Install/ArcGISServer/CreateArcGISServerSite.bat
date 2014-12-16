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
rem # Name:          CreateArcGISServerSite.bat
rem #
rem # Purpose:       Creates the ArcGIS Server site, Ops Server folders,
rem #                local/enterprise geodatabase data stores and registers
rem #                the data stores; also starts specific ArcGIS Server services
rem #                required by Ops Server.
rem #
rem # Prerequisites: ArcGIS Server must be installed (see InstallArcGISServer.bat)
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

REM ---------------------------------------------------------------------
REM Create ArcGIS Server site, create data stores, register data stores
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Create ArcGIS Server site, create data stores, and register data stores...
echo.
Call "%~dp0SupportFiles\CreateOpsServer.py" %ops_agsServiceAccount% ^
                %ops_userName% %ops_passWord% %ops_dataDrive% %ops_cacheDrive%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 6 > nul

REM ---------------------------------------------------------------------
REM Start geometry service
REM ---------------------------------------------------------------------
set ops_servicesList=Utilities//Geometry.GeometryServer,Utilities//PrintingTools.GPServer
echo.
echo %sectionBreak%
echo Start the following services^:
echo    %ops_servicesList%
echo.
Call "%~dp0..\..\Publish\Server\StartStopServices.py" %FQDN% ^
    6080 %ops_userName% %ops_passWord% no Start %ops_servicesList%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul