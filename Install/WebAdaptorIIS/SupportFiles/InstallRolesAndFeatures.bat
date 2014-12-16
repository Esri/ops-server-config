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
rem # Name:          InstallRolesAndFeatures.bat
rem #
rem # Purpose:       Enable IIS roles/features and .NET framework 3.5
rem #
rem #==============================================================================
echo.
echo --Installing IIS and .Net Framework 3.5...
echo.
START /WAIT DISM  /Online /Enable-Feature /FeatureName:IIS-WebServerRole /FeatureName:IIS-WebServer ^
     /FeatureName:IIS-CommonHttpFeatures /FeatureName:IIS-StaticContent /FeatureName:IIS-DefaultDocument ^
     /FeatureName:IIS-DirectoryBrowsing /FeatureName:IIS-HttpErrors /FeatureName:IIS-ApplicationDevelopment ^
     /FeatureName:IIS-ASPNET /FeatureName:IIS-NetFxExtensibility /FeatureName:IIS-ISAPIExtensions /FeatureName:IIS-ISAPIFilter ^
     /FeatureName:IIS-HealthAndDiagnostics /FeatureName:IIS-HttpLogging /FeatureName:IIS-RequestMonitor ^
     /FeatureName:IIS-Security /FeatureName:IIS-BasicAuthentication /FeatureName:IIS-WindowsAuthentication ^
     /FeatureName:IIS-ClientCertificateMappingAuthentication /FeatureName:IIS-RequestFiltering ^
     /FeatureName:IIS-Performance /FeatureName:IIS-HttpCompressionStatic /FeatureName:IIS-WebServerManagementTools ^
     /FeatureName:IIS-ManagementConsole /FeatureName:IIS-ManagementScriptingTools /FeatureName:IIS-ManagementService ^
     /FeatureName:IIS-IIS6ManagementCompatibility /FeatureName:IIS-Metabase /FeatureName:NetFx3




    
