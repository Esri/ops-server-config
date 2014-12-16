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
rem # Name:          RestartPortal.bat
rem #
rem # Purpose:       Restarts (stop/start) Portal for ArcGIS 
rem #
rem # Prerequisites: Portal for ArcGIS must be installed.
rem #
rem #==============================================================================
set winServicename="Portal for ArcGIS"

echo.
echo %sectionBreak%
echo Restarting windows service %winServicename%...
echo.
net stop %winServicename%
PING 127.0.0.1 -n 10 > nul
net start %winServicename%
PING 127.0.0.1 -n 20 > nul
