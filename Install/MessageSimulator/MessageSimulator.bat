@echo off
rem #------------------------------------------------------------------------------
rem # Copyright 2015 Esri
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
rem # Name:          MessageSimulator.bat
rem #
rem # Purpose:       Enables and run the OS Schechuled Task "MessageSimulator"
rem #
rem #==============================================================================
set ops_scriptName=MessageSimulator.bat
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

set ops_taskName=MessageSimulator

set sectionBreak===================================================================================

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
    echo **  Exiting %ops_scriptName%.
    echo **********************************************************
    echo.
    goto end
)
cls

echo.
echo %sectionBreak%
echo Run %ops_taskName% scheduled task

REM ---------------------------------------------------------------------
REM Enable Windows Scheduled Task
REM ---------------------------------------------------------------------
echo.
echo.
echo --Enable Windows Scheduled Task for %ops_taskName%...
echo.
set execute=SCHTASKS /Change /TN %ops_taskName% /ENABLE
echo %execute%
echo.
%execute%
set error=%ERRORLEVEL%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul

REM If enable failed end script
if "%error%"=="1" (
	goto end
)


REM ---------------------------------------------------------------------
REM Run Windows Scheduled Task
REM ---------------------------------------------------------------------
echo.
echo.
echo --Run the %ops_taskName% task...
echo.
set execute=SCHTASKS /Run /TN %ops_taskName%
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul

:end
REM ---------------------------------------------------------------------
REM End Block
REM ---------------------------------------------------------------------
@echo on