@echo off
REM ---------------------------------------------------------------------
REM Create Ops Server distribution folder structure
REM ---------------------------------------------------------------------
set ops_rootPath=%1
set ops_rootInstallPath=%ops_rootPath%\OPSServerInstall

set ops_OpsTypes=DomOps Intel LandOps MaritimeOps EmergencyManagement

REM ---------------------------------------
REM Create Demo and Scripts folder
REM ---------------------------------------
set ops_demoScriptsRootPath=%ops_rootPath%\DemoAndScripts

mkdir %ops_demoScriptsRootPath%

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

set ops_SoftwareFolders=ArcGISDataStore ArcGISGeoEvent ArcGISServer Authorization_Files ChatServer Database Desktop GeoEventOpsServerConfig ^
MessageSimulator OpsDashboardUtility ops-server-config PortalForArcGIS WebAdaptorIIS
for %%d in (%ops_SoftwareFolders%) do (
   mkdir %ops_softwareRootPath%\%%d
)

REM ---------------------------------------
REM Created web apps related folders
REM ---------------------------------------
set ops_webappsRootPath=%ops_rootInstallPath%\WebApps

mkdir %ops_webappsRootPath%