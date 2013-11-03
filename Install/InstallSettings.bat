@echo off
REM ---------------------------------------------------------------------
REM Set User Editable Variables
REM ---------------------------------------------------------------------

REM ---------------------------------------------------------------------
REM This variable defines the fully qualified domain name (FQDN) of the
REM server that ArcGIS Server and Portal for ArcGIS are being installed.
REM *****
REM NOTE: specify ops_FQDN value in lowercase.
REM *****
set ops_FQDN=SET_FQDN_OF_SERVER

REM ---------------------------------------------------------------------
REM Root folder where software installers are located. This can be a logical
REM drive letter or a UNC path. 
REM
REM This is the path to the OPSServerInstall\Software folder on your
REM external drive.
REM
REM NOTEs:
REM    - The path must not contain any spaces.
REM    - Path can be a local path (i.e. with drive letter) or a UNC path.
set ops_softwareRoot=SET_PATH_TO_SOFTWARE_FOLDER

REM ---------------------------------------------------------------------
REM This variable defines the account that will run the ArcGIS
REM Server service. It can be a local user account or a domain account.
REM If using a local account and the account does not exist it will be created
REM using the password set by the variable "ops_passWord".
REM If using a domain account, the account must already exist.
REM Specify domain account using the syntax "domain\user". If the local/domain
REM account already exists, then the variable "ops_passWord" must be set
REM to the accounts' password.
set ops_agsServiceAccount=AFMAGS

REM ---------------------------------------------------------------------
REM This variable defines the user name for the ArcGIS Server
REM site administrator user and the Portal's initial administrator account.
REM The password for this account is set by the 'ops_passWord' variable.
REM
REM NOTE: the most restrictive user name requirements are for the Portal
REM       initial administrator account, so set this variable to a valid
REM       value for the Portal initial administrator account user name.
REM 
REM       The user name can only contain the following ASCII characters:
REM       - Numbers 0 through 9
REM       - ASCII letters A through Z (upper case and lower case)
REM       - A dot (.)
set ops_userName=admin

REM ---------------------------------------------------------------------
REM This varaible is used for the following passwords: PostgreSQL superuser,
REM PostgreSQL service account, ArcGIS Server service account, ArcGIS Server
REM site administrator, Portal for ArcGIS initial administrator account, and the
REM "sde" user password that owns the ops server geodatabases.
REM
REM NOTE: the most restrictive password requirements are for the Portal
REM       initial administrator account, so set this variable to a valid
REM       value for the Portal initial administrator account password.
REM 
REM       The password can only contain the following ASCII characters:
REM       - Numbers 0 through 9
REM       - ASCII letters A through Z (upper case and lower case)
REM       - A dot (.)
set ops_passWord=SET_PASSWORD_HERE

REM ---------------------------------------------------------------------
REM Defines the drive where the ArcGIS Server site cache directory will
REM be created.
set ops_cacheDrive=c

REM ---------------------------------------------------------------------
REM Defines the drive where the Ops Server Data directory will be created.
set ops_dataDrive=c

REM ---------------------------------------------------------------------
REM This variable defines the path and name of the ArcGIS Server
REM (AGS) authorization file (*** license must be the Enterprise Advanced 
REM license ***) to use during the installation process.
REM
REM Examples:
REM    C:\AuthorizationFiles\ArcGISServer\Server_Ent_Adv.ecp
REM    C:\AuthorizationFiles\ArcGISServer\Server_Ent_Adv.prvc
REM NOTEs:
REM    - Variable value must be enclosed by double-quotes ("value") if path contains
REM      any spaces.
REM    - Path can be a local path (i.e. with drive letter) or a UNC path.
set ops_AGSAuthFile="SET_FILE_PATH"

REM ---------------------------------------------------------------------
REM This variable defines the path and name of the Portal for ArcGIS
REM authorization file to use during the installation process.
REM Examples:
REM    C:\AuthorizationFiles\Portal\Portal_100.ecp
REM    C:\AuthorizationFiles\Portal\Portal_100.prvc
REM NOTEs:
REM    - Variable value must be enclosed by double-quotes ("value") if path contains
REM      any spaces.
REM    - Path can be a local path (i.e. with drive letter) or a UNC path.
set ops_PortalAuthFile="SET_FILE_PATH"

REM ---------------------------------------------------------------------
REM Define which web browser to use for installation steps which require you
REM to work within a web browser. Have encountered issues with Internet Explorer;
REM recommend FireFox or Chrome.
set ops_webBrowserExePath="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

REM ---------------------------------------------------------------------
REM The variables below define which processes to execute.
REM Valid values are "YES" or "NO"

REM Install the rdbms (PostgreSQL)
set ops_install_rdbms=YES

REM Install and authorize ArcGIS Server 
set ops_install_server=YES

REM Create the ArcGIS Server site, create the SDE geodatabases, SDE connection files
set ops_create_ags_site=YES

REM Install GeoEvent Processor Extension for ArcGIS Server and copy various
REM Ops Server configured GeoEvent files. 
set ops_install_geoevent=YES

REM Install the ArcGIS WebAdaptor for IIS
set ops_install_webadaptor=YES

REM Change the ArcGIS Server security configuration to "HTTPS Only"
set ops_change_ags_security=YES

REM Register ArcGIS Server with the WebAdaptor (using https)
set ops_register_ags_https=YES

REM Install Portal for ArcGIS
set ops_install_portal=YES

REM Create Operations Dashboard ClickOnce Application and deploy to portal folders
set ops_create_opsdashboard_installer=YES

REM Create the Portal for ArcGIS initial administrator account
set ops_create_portal_admin_account=YES

REM Register Portal for ArcGIS Server with the WebAdaptor
set ops_register_portal=YES

REM Federate ArcGIS Server site with portal, set hosted server,
REM set SSL properties, and reset Utility service URLs
set ops_federate_ags=YES

REM Configure GeoEvent Processor Extension for ArcGIS Server - create new administrator
REM user, reset ArcGIS Server connection for registered data store
set ops_configure_geoevent=YES

REM ---------------------------------------------------------------------
REM END Set User Editable Variables
REM ---------------------------------------------------------------------