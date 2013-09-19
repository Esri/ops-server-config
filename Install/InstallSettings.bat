@echo off
REM ---------------------------------------------------------------------
REM Set User Editable Variables
REM ---------------------------------------------------------------------

REM This variable defines the fully qualified domain name (FQDN) of the
REM server that ArcGIS Server and Portal for ArcGIS are being installed.
REM *****
REM NOTE: specify ops_FQDN value in lowercase.
REM *****
set ops_FQDN=SET_FQDN_OF_SERVER

REM Root folder where software installers are located. This can be a logical
REM drive letter or a UNC path.
set ops_softwareRoot=SET_PATH_TO_SOFTWARE_FOLDER

REM This variable defines the account that will run the ArcGIS
REM Server service. It can be a local user account or a domain account.
REM If using a local account and the account does not exist it will be created
REM using the password set by the variable "ops_passWord".
REM If using a domain account, the account must already exist.
REM Specify domain account using the syntax "domain\user". If the local/domain
REM account already exists, then the variable "ops_passWord" must be set
REM to the accounts password.
set ops_agsServiceAccount=SET_AGS_ACCOUNT_NAME

REM This variable defines the user name for the ArcGIS Server
REM site administrator user.
set ops_userName=SET_ACCOUNT_USER_NAME

REM This varaible is used for the following passwords: PostgreSQL superuser,
REM PostgreSQL service account, ArcGIS Server service account, ArcGIS Server
REM site administrator, and the "sde" user password that owns the ops server
REM geodatabases.
set ops_passWord=SET_PASSWORD_HERE

REM Defines the drive where the ArcGIS Server site cache directory will
REM be created.
set ops_cacheDrive=c

REM Defines the drive where the Ops Server Data directory will be created.
set ops_dataDrive=c

REM Define which web browser to use for installation steps which require you
REM to work within a web browser. Have encountered issues with Internet Explorer;
REM recommend FireFox or Chrome (NOTE: have mostly tested with FireFox).
set ops_webBrowserExePath="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

REM Define which text editor to use for installation steps which require you
REM to work within a text editor.
set ops_textEditorExePath=C:\Windows\System32\notepad.exe

REM The variables below define which processes to execute.
set ops_install_jdk1_7=NO
set ops_install_jdk1_6=NO
set ops_install_rdbms=YES
set ops_install_server=YES
set ops_install_webadaptor=YES
set ops_register_ags=YES
set ops_install_portal=YES
set ops_create_portal_admin_account=YES
set ops_register_portal=YES
set ops_change_ags_security=YES
set ops_register_ags_https=YES
set ops_federate_ags=YES

REM ---------------------------------------------------------------------
REM END Set User Editable Variables
REM ---------------------------------------------------------------------