@echo off
title Internet Information Server ^(IIS^) Installer

set ops_scriptName=%0

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
echo.   - Installs .Net Framework
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
goto end

:end
echo.
echo Execution of  %ops_scriptName% script completed.
date /T
time /T
echo.
pause
REM exit