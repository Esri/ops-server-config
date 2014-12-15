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
rem # Name:          IsInstalled_IIS.bat
rem #
rem # Purpose:       Check if IIS is installed
rem #
rem # Comments:      See the following web page for more information:
rem #                http://msdn.microsoft.com/en-us/library/hh925568(v=vs.110).aspx
rem #==============================================================================

set serviceName=W3SVC
sc query %serviceName% | find "RUNNING"
set ops_CheckErrLvl=%ERRORLEVEL%

if "%ops_CheckErrLvl%"=="1" (
    echo.
    echo **********************************************************
    echo **  ERROR: Installation dependency has not been met.
    echo **         IIS is not enabled or the IIS service
    echo **         "World Wide Web Publishing Service" ^(%serviceName%^)
    echo **         is not running.
    echo **
    echo **  Solution:
    echo **         - If IIS is not installed run the InstallIIS.bat
    echo **           which will "enable" this OS "role".
    echo **         - If IIS is installed, but the windows service is
    echo **           not running, start the windows service.
    echo **********************************************************
    echo.
)

