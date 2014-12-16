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
rem # Name:          InstallWebAdaptorPrerequisites.bat
rem #
rem # Purpose:       Install Web Adpator Prerequisites: 
rem #                  - IIS Roles and IIS features
rem #                  - .Net framework 3.5
rem #                Also sets the IIS default document and adds additional MIME
rem #                  types needed for Ops Server applications to IIS.
rem #
rem #==============================================================================

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