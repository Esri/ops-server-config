@echo off
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
rem #========================================================================
rem #
rem # Purpose: Create Ops Server distribution folder structure. 
rem #
rem # Usage: CreateOpsServerReleaseFolderStructure <path>
rem #
rem #========================================================================

set argc=0
for %%x in (%*) do Set /A argc+=1
if %argc% LSS 1 (goto PRINTUSAGE)

set ops_rootPath=%1
set ops_rootInstallPath=%ops_rootPath%\OPSServerInstall

set ops_OpsTypes=DomOps Intel LandOps MaritimeOps EmergencyManagement

REM ---------------------------------------
REM Create Demo and Scripts folder
REM ---------------------------------------
set ops_demoScriptsRootPath=%ops_rootPath%\DemoAndScripts

mkdir %ops_demoScriptsRootPath%

REM ---------------------------------------
REM Create Resources folder
REM ---------------------------------------
set ops_resourcesRootPath=%ops_rootPath%\Resources
set ops_ResourcesSubFolders=Videos

mkdir %ops_resourcesRootPath%

for %%d in (%ops_ResourcesSubFolders%) do (
   mkdir %ops_resourcesRootPath%\%%d
)

REM ---------------------------------------
REM Create Geoevent related "support" folders
REM ---------------------------------------
set ops_geoeventRootPath=%ops_rootInstallPath%\Geoevent
set ops_geoeventSubFolders=Data jar_files MessageSimulator MessageSimulator\Messages MessageSimulator\Messages\GeoEventSimulator
mkdir %ops_geoeventRootPath%
for %%d in (%ops_geoeventSubFolders%) do (
   mkdir %ops_geoeventRootPath%\%%d
)

REM ---------------------------------------
REM Create portal related folders
REM ---------------------------------------
set ops_portalRootPath=%ops_rootInstallPath%\Portal

mkdir %ops_portalRootPath%\PortalContent
for %%d in (%ops_OpsTypes%) do (
   mkdir %ops_portalRootPath%\PortalResources\%%d
)

REM ---------------------------------------
REM Create server related folders
REM ---------------------------------------
set ops_serverRootPath=%ops_rootInstallPath%\Server

set ops_ServerFolders=DistributionEntGDBs ServiceDefinitions Staging\Caches Staging\Data SupportFiles\Republishing
for %%d in (%ops_ServerFolders%) do (
   mkdir %ops_serverRootPath%\%%d
)

REM ---------------------------------------
REM Create software related folders
REM ---------------------------------------
set ops_softwareRootPath=%ops_rootInstallPath%\Software

set ops_SoftwareFolders=ArcGISDataStore ArcGISGeoEvent ArcGISServer Authorization_Files ChatServer Database Desktop ArcGISPro ^
MessageSimulator OpsDashboardUtility ops-server-config PortalForArcGIS WebAdaptorIIS
for %%d in (%ops_SoftwareFolders%) do (
   mkdir %ops_softwareRootPath%\%%d
)

REM ---------------------------------------
REM Created web apps related folders
REM ---------------------------------------
set ops_webappsRootPath=%ops_rootInstallPath%\WebApps

mkdir %ops_webappsRootPath%

@echo Done.

goto END

:PRINTUSAGE
@echo Usage: CreateOpsServerReleaseFolderStructure ^<path^>
@goto END

:END
