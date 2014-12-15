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
rem # Name:          IsInstalled_NETFramework4_5.bat
rem #
rem # Purpose:       Check if .NET Framework 4.5 is installed
rem #
rem # Comments:      See the following web page for more information:
rem #                http://msdn.microsoft.com/en-us/library/hh925568(v=vs.110).aspx
rem #
rem #                If the registery DWORD "Release" exists then .NET Framework 4.5 or
REM #                newer has been installed.
rem #==============================================================================

reg query "HKLM\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" /v Release
set ops_CheckErrLvl=%ERRORLEVEL%

if "%ops_CheckErrLvl%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR: Installation dependency has not been met.
    echo **         .NET Framework 4.5 is not installed.
    echo **
    echo **  Solution: Install .NET Framework 4.5; the installer can
    echo **         downloaded from http://microsoft.com
    echo **********************************************************
    echo.
)

