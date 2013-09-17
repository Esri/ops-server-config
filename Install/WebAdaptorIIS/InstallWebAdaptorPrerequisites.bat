REM =====================================================================
REM Install Web Adpator Prerequisites
REM =====================================================================
REM NOTE: These prerequisites must be installed before ArcGIS Server

REM ---------------------------------------------------------------------
REM Install IIS Role and .Net Framework Feature
REM ---------------------------------------------------------------------
Call %~dp0SupportFiles\InstallRolesAndFeatures.bat

REM ---------------------------------------------------------------------
REM Set the IIS default document
REM ---------------------------------------------------------------------
Call %~dp0SupportFiles\SetIISDefaultDocument.bat

REM ---------------------------------------------------------------------
REM Modify IIS as needed for Ops Server
REM ---------------------------------------------------------------------
REM Add additional MIME types
Call %~dp0SupportFiles\AddIISMimeTypes.bat
PING 127.0.0.1 -n 3 > nul