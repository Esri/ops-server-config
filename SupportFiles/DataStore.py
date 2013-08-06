#!/usr/bin/env python
# Eric Linz 8/2/2013

import sys, os, traceback
from AGSRestFunctions import registerDataItem as _register
from AGSRestFunctions import unregisterDataItem as _unregister
from AGSRestFunctions import validateDataItem as _validateitem
from AGSRestFunctions import getDataItemInfo as _getdataiteminfo

# JSON keys
_itemkey                = 'item'
_pathkey                = 'path'
_typekey                = 'type'
_infokey                = 'info'
_conntypekey            = 'dataStoreConnectionType'
_clientpathkey          = 'clientPath'
_infopathkey            = 'path'
_hostnamekey            = 'hostName'
_managedkey             = 'isManaged'
_unregpathkey           = 'itemPath'
_serverdbconnstrkey     = 'connectionString'
_clientdbconnstrkey     = 'clientConnectionString'

# JSON values
_path_folder            = '/fileShares/'
_path_egdb              = '/enterpriseDatabases/'
_type_folder            = 'folder'
_type_egdb              = 'egdb'
_conntype_shared        = 'shared'
_conntype_replicated    = 'replicated'
_conntype_managed       = 'serverOnly'


_postgres_db_conn_template_str = "SERVER=serverReplaceStr;" + \
    "INSTANCE=sde:postgresql:serverReplaceStr;DBCLIENT=postgresql;" + \
    "DB_CONNECTION_PROPERTIES=serverReplaceStr;DATABASE=dbReplaceStr;USER=userReplaceStr;PASSWORD=" + \
    "passwordReplaceStr;VERSION=sde.DEFAULT;AUTHENTICATION_MODE=DBMS"
            
def create_postgresql_db_connection_str(dbservername, dbname, username, password):
    ''' Create PostgreSQL database connection string '''
    db_conn_str = _postgres_db_conn_template_str.replace('serverReplaceStr', dbservername)
    db_conn_str = db_conn_str.replace('dbReplaceStr', dbname)
    db_conn_str = db_conn_str.replace('userReplaceStr', username)
    db_conn_str = db_conn_str.replace('passwordReplaceStr', password)
    
    return db_conn_str

def create_shared_folder_item(name, publisher_folder_path, publisher_folder_hostname=None):
    '''Create shared folder data item.
    'publisher_folder_hostname' required if 'publisher_folder_path' is drive letter location.
    'Returns tuple of data item path and dictionary representing the data item.
    '''
    
    info = {_infopathkey: publisher_folder_path,
            _conntypekey: _conntype_shared}
    
    if publisher_folder_hostname:
            info[_hostnamekey] = publisher_folder_hostname
    
    item = {_pathkey: _path_folder + name,
            _typekey: _type_folder,
            _infokey: info}

    return item[_pathkey], {_itemkey: item}
    
def create_replicated_folder_item(name, publisher_folder_path, server_folder_path, publisher_folder_hostname=None):
    '''Create replicated folder data item.
    'publisher_folder_hostname' required if 'publisher_folder_path' is drive letter location.
    'Returns tuple of data item path and dictionary representing the data item.
    '''
    
    info = {_infopathkey: server_folder_path,
            _conntypekey: _conntype_replicated}
    
    if publisher_folder_hostname:
            info[_hostnamekey] = publisher_folder_hostname
            
    item = {_pathkey: _path_folder + name,
            _typekey: _type_folder,
            _clientpathkey: publisher_folder_path,
            _infokey: info}

    return item[_pathkey], {_itemkey: item}
    
def create_shared_entdb_item(name, publisher_db_conn):
    '''Create shared enterprise database data item.
    'Returns tuple of data item path and dictionary representing the data item.
    '''
    
    info = {_conntypekey: _conntype_shared,
            _managedkey: False,
            _serverdbconnstrkey: publisher_db_conn}
    
    item = {_pathkey: _path_egdb + name,
            _typekey: _type_egdb,
            _clientpathkey: None,
            _infokey: info}

    return item[_pathkey], {_itemkey: item}
    
def create_replicated_entdb_item(name, publisher_db_conn, server_db_conn):
    '''Create replicated enterprise database date item.
    'Returns tuple of data item path and dictionary representing the data item.
    '''
    
    info = {_conntypekey: _conntype_replicated,
            _managedkey: False,
            _clientdbconnstrkey: publisher_db_conn,
            _serverdbconnstrkey: server_db_conn}
    
    item = {_pathkey: _path_egdb + name,
            _typekey: _type_egdb,
            _clientpathkey: None,
            _infokey: info}

    return item[_pathkey], {_itemkey: item}
    
def create_managed_entdb_item(name, server_db_conn):
    '''Create managed enterprise database data item.
    'Returns tuple of data item path and dictionary representing the data item.
    '''
    
    info = {_conntypekey: _conntype_managed,
            _managedkey: True,
            _serverdbconnstrkey: server_db_conn}
    
    item = {_pathkey: _path_egdb + name,
            _typekey: _type_egdb,
            _clientpathkey: None,
            _infokey: info}

    return item[_pathkey], {_itemkey: item}

def register(server, port, user, password, item, token=None):
    '''Register a data item.
    'Returns tuple: success(True|False) and response.
    '''
    
    return _register(server, port, user, password, item, token)
    
def unregister(server, port, user, password, itempath, token=None):
    '''Unregister a data item.
    'Returns tuple: success(True|False) and response.
    '''
    
    item = {_unregpathkey: itempath}
    return _unregister(server, port, user, password, item, token)

def validateitem(server, port, user, password, item, token=None):
    '''Validate a data item.
    'Returns tuple: success(True|False) and response.
    '''
    
    return _validateitem(server, port, user, password, item, token)

def getitem(server, port, user, password, itempath, token=None):
    '''Get data item based on data item path.
    'Returns tuple: success(True|False) and dictionary of data item.
    '''
    
    return _getdataiteminfo(server, port, user, password, itempath, token)
