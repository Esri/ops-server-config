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
rem # Name:          InstallMessageSimulator.bat
rem #
rem # Purpose:       Install Message Simulator
rem #
rem #==============================================================================
set ops_ChkErrLevelFile=%~dp0..\..\SupportFiles\BatchFiles\CheckErrorLevel.bat

echo.
echo %sectionBreak%
echo Install Message Simulator

REM ---------------------------------------------------------------------
REM Copy Message Simulator files
REM ---------------------------------------------------------------------
set ops_destPath="C:\MessageSimulator"
echo.
echo.
echo --Copying Message Simulator folders/files...
echo.
set execute=START /WAIT robocopy %ops_softwareRoot%\MessageSimulator\ %ops_destPath% *.* /S
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL% ROBOCOPY
PING 127.0.0.1 -n 3 > nul

REM ---------------------------------------------------------------------
REM Create Windows Scheduled Task
REM ---------------------------------------------------------------------
set ops_taskName=MessageSimulator
echo.
echo.
echo --Create Windows Scheduled Task for Message Simulator...
echo.
REM /F switch will create the task even if it already exists.
REM
set execute=SCHTASKS /Create /XML %~dp0SupportFiles\MessageSimulatorTask.xml /TN %ops_taskName% /F
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul

echo.
echo.
echo --Disable the Message Simulator task...
echo.
set execute=SCHTASKS /Change /TN %ops_taskName% /DISABLE
echo %execute%
echo.
%execute%
Call %ops_ChkErrLevelFile% %ERRORLEVEL%
PING 127.0.0.1 -n 3 > nul