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
rem #==============================================================================
rem # Name:          InstallIIS.bat
rem #
rem # Purpose:       Installs IIS, .NET framework 3.5 and configures certain
rem #                aspects of the IIS configuration.
rem #
rem #==============================================================================
title Internet Information Server ^(IIS^) Installer

set ops_scriptName=%0

REM ---------------------------------------------------------------------
REM Set user specified variables
REM ---------------------------------------------------------------------
Call InstallSettings.bat
set sectionBreak=========================================================================

REM ---------------------------------------------------------------------
REM Check if command prompt is running in elevated permissions mode
REM (i.e. "run as administrator)
REM ---------------------------------------------------------------------
echo.
echo --Checking if Windows Command window is running as administrator
echo   by querying LOCAL SERVICE user registry entries...
echo.
reg query HKU\S-1-5-19
if "%ERRORLEVEL%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR:
    echo **  You are _NOT_ running Windows Command window
    echo **  in elevated administrator mode ^(i.e., the CMD.exe
    echo **  must be "Run as administrator"^).
    echo **  Exiting %ops_scriptName%
    echo **********************************************************
    echo.
    goto end
)
cls

REM ---------------------------------------------------------------------
REM Check if user "installed" configuration script in correct location
REM ---------------------------------------------------------------------
echo.
echo --Checking if installation scripts are installed in the correct location...

set ops_ScriptRootName=ops-server-config
set ops_ScriptRoot=C:\%ops_ScriptRootName%\

echo %~dp0 | find /I "%ops_ScriptRoot%"

if "%ERRORLEVEL%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR:
    echo **  The '%ops_ScriptRootName%' folder is not installed in
    echo **  the correct location. It should be located at:
    echo **  %ops_ScriptRoot%
    echo **  Exiting  %ops_scriptName%.
    echo **********************************************************
    echo.
    goto end
)
cls

:start
REM ---------------------------------------------------------------------
REM Start Block
REM ---------------------------------------------------------------------
echo *************************************************************************
echo *           Internet Information Server ^(IIS^) Installer               *
echo *************************************************************************
echo. This script:
echo.   - Installs IIS.
echo.   - Installs .Net Framework 3.5
echo.   - Sets the IIS default document
echo.   - Adds additional IIS MIME types required by Ops Server components.
echo.
echo 1. Install
echo. 
echo 0. Quit
echo.
 
set /p choice="Enter the number of your choice: "

if "%choice%"=="1" (
    goto Install
)
if "%choice%"=="0" exit
echo Invalid choice: %choice%
echo.
pause
cls
goto start

:Install
REM ---------------------------------------------------------------------
REM Install Software
REM ---------------------------------------------------------------------
echo.
echo Start at:
date /T
time /T
echo.
echo %sectionBreak%
echo Install IIS and other prerequisites for ArcGIS Web Adaptor for IIS
echo.
Call %~dp0WebAdaptorIIS\InstallWebAdaptorPrerequisites.bat
PING 127.0.0.1 -n 3 > nul


REM ---------------------------------------------------------------------
REM Open Server Manager so users who have a domain certicate server
REM can create a domain certificate and bind to https
REM ---------------------------------------------------------------------
echo.
echo %sectionBreak%
echo Create domain certificate (applies only to those users who
echo have a domain certificate server and want to use a domain
echo certificate with Portal for ArcGIS/ArcGIS Server) and bind to https
echo.
Call %~dp0WebAdaptorIIS\CreateCertificate.bat
goto end

:end
echo.
echo Execution of  %ops_scriptName% script completed.
date /T
time /T
echo.
pause
REM exit