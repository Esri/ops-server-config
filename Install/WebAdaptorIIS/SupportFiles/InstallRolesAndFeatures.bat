echo.
echo --Installing IIS and .Net Framework...
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




    
