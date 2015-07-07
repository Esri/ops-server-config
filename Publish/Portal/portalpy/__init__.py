#------------------------------------------------------------------------------
# Copyright 2014 Esri
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

""" The portalpy module for working with the ArcGIS Online API."""

__version__ = '1.0a8'

import collections
import copy
import gzip
import httplib
import imghdr
import json
import logging
import mimetools
import mimetypes
import os
import re
import tempfile
import unicodedata
import urllib
import urllib2
import urlparse
import UserDict

from calendar import timegm
from cStringIO import StringIO
from itertools import groupby
from operator import itemgetter

URL_BASED_ITEM_TYPES = frozenset(['Feature Service', 'Map Service',
                                  'Image Service', 'Web Mapping Application','WMS','WMTS', 'Geodata Service',
                                  'Globe Service','Geometry Service', 'Geocoding Service',
                                  'Network Analysis Service', 'Geoprocessing Service','Mobile Application',
                                  'Document Link', 'KML', 'Workflow Manager Service'])

TEXT_BASED_ITEM_TYPES = frozenset(['Web Map', 'Feature Service', 'Map Service',
                                   'Image Service', 'Feature Collection', 'Feature Collection Template',
                                   'Web Mapping Application', 'Mobile Application', 'Symbol Set', 'Color Set',
                                   'Windows Viewer Configuration', 'Operation View'])

FILE_BASED_ITEM_TYPES = frozenset(['Code Attachment', 'Shapefile', 'CSV',
                                   'Service Definition', 'Map Document', 'Map Package', 'Tile Package',
                                   'Explorer Map', 'Globe Document', 'Scene Document', 'Published Map',
                                   'Map Template', 'Windows Mobile Package', 'Layer', 'Layer Package',
                                   'Explorer Layer', 'Geoprocessing Package', 'Geoprocessing Sample',
                                   'Locator Package', 'Workflow Manager Package', 'Code Sample',
                                   'Desktop Application Template', 'Desktop Add In', 'Explorer Add In',
                                   'CityEngine Web Scene', 'Windows Viewer Add In', 'Operations Dashboard Add In',
                                   'Microsoft Word', 'Microsoft Powerpoint', 'Microsoft PowerPoint', 'Microsoft Excel', 'PDF',
                                   'Image', 'Visio Document', 'ArcPad Package', 'Web Scene',
                                   'Pro Map', 'CAD Drawing', 'iWork Keynote', 'iWork Pages', 'iWork Numbers',
                                   'Basemap Package', 'Project Package', 'Task File', 'Layout',
                                   'Rule Package', 'Desktop Application', 'Project Template',
                                   'Mobile Basemap Package', 'Desktop style']) #'KML'

RELATIONSHIP_TYPES = frozenset(['Map2Service', 'WMA2Code',
                                'Map2FeatureCollection', 'MobileApp2Code', 'Service2Data',
                                'Service2Service', 'Map2AppConfig', 'Item2Attachment',
                                'Item2Report', 'Listed2Provisioned'])

RELATIONSHIP_DIRECTIONS = frozenset(['forward', 'reverse'])

URL_ITEM_FILTER = ' OR '.join(['type:"%s"' % t for t in URL_BASED_ITEM_TYPES]) \
                  + ' -type:"Web Map" -type:"Map Package"'

WEB_ITEM_FILTER = '((type:"service" -type:"globe" -type:"geodata") OR ' \
                  + 'type:"KML" OR type:"WMS" OR type:"Web Map" OR ' \
                  + 'type:"web mapping application" OR (type:"feature collection" ' \
                  + '-type:"Feature Collection Template") OR ' \
                  + 'type:"mobile application")'
WEBMAP_ITEM_FILTER = 'type:"Web Map" -type:"Web Mapping Application"'
EXCLUDE_BASEMAP_FILTER = ' -tags:basemap'

OPVIEW_ITEM_FILTER = 'type:"Operation View"' #EL, added 6/10/2013

_log = logging.getLogger(__name__)

class Portal(object):
    """ An object representing a connection to a single portal (via URL)."""

    aggregate_functions = {
        'sum': lambda x: sum(result for result in x),
        'avg': lambda x: sum(result for result in x) / len(x),
        'count': lambda x: len(x),
        'min': lambda x: min(result for result in x),
        'max': lambda x: max(result for result in x),
        'first': lambda x: x[0],
        'last': lambda x: x[-1]
    }

    def __init__(self, url, username=None, password=None, key_file=None,
                 cert_file=None, expiration=160, referer=None, proxy_host=None,
                 proxy_port=None, connection=None, workdir=tempfile.gettempdir()):
        """ The Portal constructor. Requires URL and optionally username/password."""
        self.url = url
        if url:
            normalized_url = normalize_url(self.url)
            if not normalized_url[-1] == '/':
                normalized_url += '/'
            self.resturl = normalized_url + 'sharing/rest/'
            self.hostname = parse_hostname(url)
        self.workdir = workdir

        # Setup the instance members
        self._basepostdata = { 'f': 'json' }
        self._version = None
        self._properties = None
        self._logged_in_user = None
        self._resources = None
        self._languages = None
        self._regions = None
        self._is_pre_162 = False
        self._is_pre_21 = False

        # Setup a cache for user item links, so we don't need to comb through
        # folders every time we need it
        self._user_item_links_cache = LRUCache(num_entries=100)

        # If a connection was passed in, use it, otherwise setup the
        # connection (use all SSL until portal informs us otherwise)
        if connection:
            _log.debug('Using existing connection to: ' + \
                       parse_hostname(connection.baseurl))
            self.con = connection
        if not connection:
            _log.debug('Connecting to portal: ' + self.hostname)
            self.con = ArcGISConnection(self.resturl, username, password,
                                        key_file, cert_file, expiration, True,
                                        referer, proxy_host, proxy_port)

        # Store the logged in user information. It's useful.
        if self.is_logged_in():
            self._logged_in_user = self.user(username)

        # Cache the version and properties information
        self.reinitialize()

    def _postdata(self):
        if self._basepostdata:
            # Return a defensive copy
            return copy.deepcopy(self._basepostdata)
        return None

    def login(self, username, password, expiration=60):
        """ Logs into the portal using username/password. """
        newtoken = self.con.login(username, password, expiration)
        if newtoken:
            self._logged_in_user = self.user(username)
        return newtoken

    def logout(self):
        """ Logs out of the portal. """
        self.con.logout()

    def is_logged_in(self):
        """ Returns true if logged into the portal. """
        return self.con.is_logged_in()

    def logged_in_user(self):
        """ Returns the logging in user (JSON object). """
        if self._logged_in_user:
            # Return a defensive copy
            return copy.deepcopy(self._logged_in_user)
        return None

    def generate_token(self, username, password, expiration=60):
        """ Generates and returns a new token, but doesn't re-login. """
        return self.con.generate_token(username, password, expiration)

    def reinitialize(self):
        """ Caches the portal version and properties. """
        self.version(True)
        self.properties(True)

    def version(self, force=False):
        """ Returns the portal version (using cache unless force=True). """

        # If we've never retrieved the version before, or the caller is
        # forcing a check of the server, then check the server
        if not self._version or force:
            resp = self.con.post('', self._postdata())
            if not resp:
                old_resturl = normalize_url(self.url) + 'sharing/'
                resp = self.con.post(old_resturl, self._postdata(), ssl=True)
                if resp:
                    _log.warn('Portal is pre-1.6.2; some things may not work')
                    self._is_pre_162 = True
                    self._is_pre_21 = True
                    self.resturl = old_resturl
                    self.con.baseurl = old_resturl
            else:
                version = resp.get('currentVersion')
                if version == '1.6.2' or version == '2.0':
                    _log.warn('Portal is pre-2.1; some features not supported')
                    self._is_pre_21 = True
            if resp:
                self._version = resp.get('currentVersion')

        return self._version

    def properties(self, force=False):
        """ Returns the portal properties (using cache unless force=True). """

        # If we've never retrieved the properties before, or the caller is
        # forcing a check of the server, then check the server
        if not self._properties or force:
            path = 'accounts/self' if self._is_pre_162 else 'portals/self'
            resp = self.con.post(path, self._postdata(), ssl=True)
            if resp:
                self._properties = resp
                self.con.all_ssl = self.is_all_ssl()

        # Return a defensive copy
        return copy.deepcopy(self._properties)

    def set_properties(self, properties, clear_empty_fields=False):
        """ Sets the portal properties. """
        postdata = self._postdata()
        postdata.update(properties)
        postdata.update({ 'clearEmptyFields': str(clear_empty_fields).lower() })
        resp = self.con.post('portals/self/update', postdata)
        if resp and resp.get('success'):
            self.properties(force=True)  #recache local properties

    def update_property(self, name, value):
        """ Updates a single portal property. """
        self.update_properties({name: value})

    def update_properties(self, props):
        """ Updates multiple portal properties. """
        all_props = self.properties()
        all_props.update(props)
        self.set_properties(all_props)

    def is_public(self):
        """ Returns true if this portal allows anonymous access. """
        return not self._properties.get('access') == 'private'

    def is_all_ssl(self):
        """ Returns true if this portal requires SSL. """

        # If properties aren't set yet, return true (assume SSL until the
        # properties tell us otherwise)
        if not self._properties:
            return True

        # If access property doesnt exist, will correctly return false
        return self._properties.get('allSSL')

    def is_multitenant(self):
        """ Returns true if this portal is multitenant. """
        return self._properties['portalMode'] == 'multitenant'

    def is_arcgisonline(self):
        """ Returns true if this portal is ArcGIS Online. """
        return self._properties['portalName'] == 'ArcGIS Online' \
            and self.is_multitenant()

    def is_subscription(self):
        """ Returns true if this portal is an ArcGIS Online subscription. """
        return bool(self._properties.get('urlKey'))

    def is_org(self):
        """ Returns true if this portal is an organization. """
        return bool(self._properties.get('id'))

    def _is_searching_public(self, scope):
        if scope == 'public':
            return True
        elif scope == 'org':
            return False
        elif scope == 'default' or scope is None:
            # By default orgs won't search public
            return False if self.is_org() else True
        else:
            raise PortalError('Unknown scope "' + scope + '". Supported ' \
                              + 'values are "public", "org", and "default"')

    def languages(self, force=False):
        """ Returns the portal languages (using cache unless force=True). """

        # If we've never retrieved the languages before, or the caller is
        # forcing a check of the server, then check the server
        if not self._languages or force:
            self._languages = self.con.post('portals/languages',
                                            self._postdata())

        # Return a defensive copy
        return copy.deepcopy(self._languages)

    def regions(self, force=False):
        """ Returns the portal regions (using cache unless force=True). """

        # If we've never retrieved the regions before, or the caller is
        # forcing a check of the server, then check the server
        if not self._regions or force:
            self._regions = self.con.post('portals/regions', self._postdata())

        # Return a defensive copy
        return copy.deepcopy(self._regions)

    # TODO Add auto-paging
    def resources(self, force=False):
        """ Returns the portal resources (using cache unless force=True). """

        # If we've never retrieved the resources before, or the caller is
        # forcing a check of the server, then check the server
        if not self._resources or force:
            self._resources = self.con.post('portals/self/resources',
                                            self._postdata())

        # Return a defensive copy
        return copy.deepcopy(self._resources)

    def resource(self, key):
        """ Returns the resource for a given key. """
        return self.con.get('portals/self/resources/' + key, try_json=False)

    def resourced(self, key, filename=None, dir=None):
        """ Downloads the resource for a given key. """
        if not filename:
            filename = key
        if not dir:
            dir = self.workdir
        filepath = os.path.join(dir, filename)
        self.con.download('portals/self/resources/' + key, filepath)
        return filepath

    def add_resource(self, key, text='', data=None):
        """ Adds a new resource to the portal. """
        postdata = self._postdata()
        postdata['key'] = key
        postdata['text'] = text
        files = []
        if data:
            if _is_http_url(data):
                data = urllib.urlretrieve(data)[0]
            files.append(('file', data, os.path.basename(data)))
        resp = self.con.post('portals/self/addresource', postdata, files)
        if resp:
            return resp.get('success')

    def remove_resource(self, key):
        """ Removes the resource for a given key. """
        postdata = self._postdata()
        postdata['key'] = key
        resp = self.con.post('portals/self/removeresource', postdata)
        if resp:
            return resp.get('success')

    def info(self):
        """ Returns a PortalInfo object describing this portal. """
        username = None
        userrole = None
        if self.is_logged_in():
            username = self.logged_in_user()['username']
            userrole = self.logged_in_user()['role']
        return PortalInfo(self.hostname, self.url, self._properties,
                          self._version, username, userrole)

    # Used to invite users to an online organization (subscription).
    # The invitations parameter is a list of invitations. An
    # invitation is a dictionary with the following required keys:
    # email, role, and the following optional keys: username, fullname
    def invite(self, invitations, email_subject, email_html):
        """ Invites users to an an online subscription. """
        postdata = self._postdata()
        postdata['invitationList'] = {'invitations': invitations}
        postdata['subject'] = email_subject
        postdata['html'] = email_html
        resp = self.con.post('portals/self/invite', postdata)
        if resp and resp.get('success'):
            return resp['notInvited']

    def invitations(self, properties=None):
        """ Returns invitations to an online subscription. """
        if properties is None:
            properties = []
        resp = self._invitations_page(1, 100)
        results = self._extract(resp['invitations'], properties)
        nextstart = int(resp['nextStart'])
        while nextstart > 0:
            resp = self._invitations_page(nextstart, 100)
            results.extend(self._extract(resp['invitations'], properties))
            nextstart = int(resp['nextStart'])
        return results

    def _invitations_page(self, start, num):
        postdata = self._postdata()
        postdata.update({ 'start': start, 'num': num })
        return self.con.post('portals/self/invitations', postdata)

    def accept(self, invitation_id):
        """ Accepts an invitation to the organization. """
        postdata = self._postdata()
        postdata['invitationId'] = invitation_id
        resp = self.con.post('community/invitations/' + invitation_id \
                             + '/accept', postdata)
        if resp:
            return resp.get('success')

    # Used to signup a new user to an on-premises portal.
    def signup(self, username, password, fullname, email):
        """ Signs up users to an instance of Portal for ArcGIS. """
        if self.is_arcgisonline():
            raise PortalError('Signup is not supported on ArcGIS Online')

        postdata = self._postdata()
        postdata['username'] = username
        postdata['password'] = password
        postdata['fullname'] = fullname
        postdata['email'] = email
        resp = self.con.post('community/signUp', postdata, ssl=True)
        if resp:
            return resp.get('success')

    def item(self, id):
        """ Returns the item for the specified item id. """
        return self.con.post('content/items/' + id, self._postdata())

    def item_data(self, id, return_json=False):
        """ Returns the item data for the specified item id. """
        return self.con.get('content/items/' + id + '/data', try_json=return_json)

    def item_datad(self, id, dir=None, filename=None):
        """ Downloads the item data for the specified item id, returns file path. """
        dataurlpath = 'content/items/' + id + '/data'
        if not filename:
            filename = self.item(id).get('name')
            if not filename:
                filename = 'data'
        if not dir:
            dir = self.workdir
        filepath = os.path.join(dir, filename)
        self.con.download(dataurlpath, filepath)
        return filepath

    def item_thumbnail(self, id):
        """ Returns the item thumbnail for the specified item id. """
        thumbnail_file = self.item(id).get('thumbnail')
        if thumbnail_file:
            thumbnail_url_path = 'content/items/' + id + '/info/' + thumbnail_file
            if thumbnail_url_path:
                return self.con.get(thumbnail_url_path, try_json=False)

    def item_thumbnaild(self, id, dir=None, thumbnail_file=None):
        """ Downloads the item thumbnail for the specified item id, returns file path. """
        if not thumbnail_file:
            thumbnail_file = self.item(id).get('thumbnail')

        # Only proceed if a thumbnail exists
        if thumbnail_file:
            thumbnail_url_path = 'content/items/' + id + '/info/' + thumbnail_file
            if thumbnail_url_path:
                if not dir:
                    dir = self.workdir
                file_name = os.path.split(thumbnail_file)[1]
                if len(file_name) > 50: #If > 50 chars, truncate to last 30 chars
                    file_name = file_name[-30:]
                file_path = os.path.join(dir, file_name)
                self.con.download(thumbnail_url_path, file_path)
                return file_path

    def item_metadata(self, id):
        """ Returns the item metadata for the specified item id. """
        metadataurlpath = 'content/items/' + id + '/info/metadata/metadata.xml'
        try:
            return self.con.get(metadataurlpath, try_json=False)

        # If the get operation returns a 400 HTTP Error then the metadata simply
        # doesn't exist, let's just return None in this case
        except urllib2.HTTPError as e:
            if e.code == 400 or e.code == 500:
                return None
            else:
                raise e

    def item_metadatad(self, id, dir=None):
        """ Downloads the item metadata for the specified item id, returns file path. """
        metadataurlpath = 'content/items/' + id + '/info/metadata/metadata.xml'
        if not dir:
            dir = self.workdir
        filepath = os.path.join(dir, 'metadata.xml')
        try:
            self.con.download(metadataurlpath, filepath)
            return filepath

        # If the get operation returns a 400 HTTP/IO Error then the metadata
        # simply doesn't exist, let's just return None in this case
        except urllib2.HTTPError as e:
            if e.code == 400 or e.code == 500:
                return None
            else:
                raise e

    def search(self, properties=None, q=None, bbox=None, group_fields=None,
               sort_field='', sort_order='asc', num=1000, scope='default'):
        """ Searches portal items. Supports sorting, aggregation, and auto-paging. """
        return self._search(self._search_page, properties, q, bbox, group_fields,
                            sort_field, sort_order, num, scope)

    def _search(self, search_func, properties, q, bbox, group_fields,
                sort_field, sort_order, num, scope):

        # If user is attempting to search public and hasn't specified a query
        # then throw an error
        is_searching_public = self._is_searching_public(scope)
        if is_searching_public and not q:
            raise PortalError('q parameter is required when searching ' \
                              + 'with public scope')

        # If the user is searching within the org, verify that either we can
        # get the org's account id. If we can't, it's likely a private portal
        # and the user is not logged in... then we throw an error
        if not is_searching_public:
            accountid = self._properties.get('id')
            if accountid and q:
                q += ' accountid:' + accountid
            elif accountid:
                q = 'accountid:' + accountid
            else:
                raise PortalError('Cannot search this portal at the org scope. ' \
                                  + 'Either attemping to search www.arcgis.com ' \
                                  + 'or a private subscirption/portal anonymously')

        # Parse the properties into the property names and aggregate functions.
        # Then validate the inputs (e.g. make sure aggregate functions are
        # supported, that propertie are valid)
        if properties is None:
            properties = []
        prop_names, func_names = self._parse_properties(properties)
        self._validate_properties(properties, func_names, group_fields)

        # Prepare for searching
        prop_names_nodups = list(set(prop_names))
        sort_field_name = ''
        if sort_field:
            sort_field_name = self._parse_properties([sort_field])[0][0]

        # Execute the search and get back the results
        count = 0
        resp = search_func(q, bbox, 1, min(num, 100), sort_field_name, sort_order)
        results = self._extract(resp['results'], prop_names_nodups)
        count += int(resp['num'])
        nextstart = int(resp['nextStart'])
        while count < num and nextstart > 0:
            resp = search_func(q, bbox, nextstart, min(num - count, 100),
                               sort_field_name, sort_order)
            results.extend(self._extract(resp['results'], prop_names_nodups))
            count += int(resp['num'])
            nextstart = int(resp['nextStart'])

        # If group fields were specified, aggregate the results (and sort, if
        # sort field was specified)
        if group_fields:
            results = self._groupby_and_sort(results, group_fields, prop_names,
                                             func_names, sort_field, sort_order)
        return results

    def _groupby_and_sort(self, results, group_fields, prop_names, func_names,
                          sort_field, sort_order):

        # Sort, then use standard Python groupby function to group the results
        aggregated_results = []
        if group_fields:
            sorted_results = self._multikeysort(results, group_fields)
            keyfunc = self._multikeygroupby_keyfunc(group_fields)
            for k, group in groupby(sorted_results, keyfunc):
                group_results = list(group)

                # Loop over all of the properties and aggregate those properties
                # where aggregate functions were specified. Where they weren't,
                # just take the value from the first row (they should all be the
                # same because that property must have been a group field/key)
                aggregated_result = dict()
                for i, prop_name in enumerate(prop_names):
                    func_name = func_names[i]
                    if func_name:
                        prop_name_aggr = func_name + '(' + prop_name + ')'
                        prop_values = unpack(
                            self._extract(group_results, [prop_name]))
                        aggregated_result[prop_name_aggr] = \
                            self.aggregate_functions[func_name](prop_values)
                    else:
                        aggregated_result[prop_name] = group_results[0][prop_name]

                # Append the aggregated result to the list of aggregated
                # results (our final return value)
                aggregated_results.append(aggregated_result)

        # If a sort field was specified, sort and return the results.
        if sort_field:
            if not sort_order:
                sort_order = 'asc'
            return sorted(aggregated_results or results,
                          key=itemgetter(sort_field),
                          reverse=(sort_order.lower() == 'desc'))

        return aggregated_results

    # Parse the properties into the property names and function names
    # using regular expressions, look for <w1> or <w1>(<w2>)
    def _parse_properties(self, properties):
        property_names = []
        property_funcs = []
        for property in properties:
            pattern = r'\s*(?P<w1>\w+)?\s*(\()?\s*(?P<w2>\w+)?\s*(\))?\s*(.*)'
            m = re.match(pattern, property)
            group_count = len(filter(None, m.groups()))
            if group_count is 1:
                property_funcs.append(None)
                property_names.append(m.group('w1'))
            elif group_count is 4:
                property_func_name = m.group('w1')
                if not property_func_name in self.aggregate_functions:
                    raise PortalError('Unknown aggregate function \''
                                      + property_func_name + '\'')
                property_funcs.append(property_func_name)
                property_names.append(m.group('w2'))
            else:
                raise PortalError('Invalid property: ' + property)
        return property_names, property_funcs

    def _validate_properties(self, properties, func_names, group_fields):
        if group_fields:
            for i, property in enumerate(properties):
                func_name = func_names[i]
                if not func_name and not property in group_fields:
                    raise PortalError('Property ' + property + ' does not ' \
                                      + 'have an aggregation function, nor is ' \
                                      + 'it specified in group_fields')
                if func_name and not func_name in self.aggregate_functions:
                    raise PortalError('Unsupported aggregate function \'' \
                                      + func_name + '\'')
        else:
            if len(filter(None, func_names)) > 0:
                raise PortalError('Aggregator functions are only supported ' \
                                  + 'when group_fields is specified')

    def _multikeysort(self, results, properties):
        comparers = [ ((itemgetter(col[1:].strip()), -1) if col.startswith('-')
                       else (itemgetter(col.strip()), 1)) for col in properties]
        def comparer(left, right):
            for fn, mult in comparers:
                result = cmp(fn(left), fn(right))
                if result:
                    return mult * result
            else:
                return 0
        return sorted(results, cmp=comparer)

    def _multikeygroupby_keyfunc(self, group_fields):
        def get_keys(result, group_fields=group_fields):
            keys = []
            for group_field in group_fields:
                keys.append(result[group_field])
            return tuple(keys)
        return get_keys

    def _search_page(self, q=None, bbox=None, start=1, num=10, sortfield='', sortorder='asc'):
        _log.info('Searching items (q=' + str(q) + ', bbox=' + str(bbox) \
                  + ', start=' + str(start) + ', num=' + str(num) + ')')
        postdata = self._postdata()
        postdata.update({ 'q': q or '', 'bbox': bbox or '', 'start': start, 'num': num,
                          'sortField': sortfield, 'sortOrder': sortorder })
        return self.con.post('search', postdata)

    def webmap(self, id):
        """ Returns a WebMap object for the specified item id """
        return WebMap(id, self.item_data(id), self.con.ensure_ascii)

    def webmaps(self, q=None, bbox=None, sort_field='', sort_order='asc',
                num=1000, scope='default', include_basemaps=False,
                ignore_errors=True):
        """ Search portal items for webmaps, returning WebMap objects """

        # Build the search query
        search_q = WEBMAP_ITEM_FILTER
        if include_basemaps:
            search_q += ' ' + EXCLUDE_BASEMAP_FILTER
        if q:
            search_q += ' ' + q

        # Search for the corresponding webmaps (return IDs only)
        webmap_items = self.search(['id'], search_q, bbox,
                                   sort_field=sort_field,
                                   sort_order=sort_order,
                                   num=num,
                                   scope=scope)
        webmap_ids = unpack(webmap_items)

        # Build and return an array of WebMap objects
        if webmap_ids:
            webmaps = []
            for webmap_id in webmap_ids:
                try:
                    webmap = self.webmap(webmap_id)
                    webmaps.append(webmap)
                except Exception as e:
                    if not ignore_errors:
                        raise e
                    else:
                        _log.warning(e)
            return webmaps

    def basemaps(self, properties=None, q=None):
        """ Returns portal basemaps. """
        if not 'basemapGalleryGroupQuery' in self.properties():
            raise PortalError('Unable to access portal basemaps')
        group_q = self.properties().get('basemapGalleryGroupQuery')
        if group_q:
            item_q = WEBMAP_ITEM_FILTER
            if q:
                item_q += ' AND ' + q
            return self._gallery_items(group_q, properties, item_q)

    def color_sets(self, properties=None, q=None):
        """ Returns portal color sets. """
        if not 'colorSetsGroupQuery' in self.properties():
            raise PortalError('Unable to access portal color sets')
        group_q = self.properties().get('colorSetsGroupQuery')
        if group_q:
            item_q = 'type:"Color Sets"'
            if q:
                item_q += ' AND ' + q
            return self._gallery_items(group_q, properties, item_q)

    def featured_items(self, properties=None, q=None):
        """ Returns portal featured items. """
        if not 'featuredItemsGroupQuery' in self.properties():
            raise PortalError('Unable to access portal featured items')
        group_q = self.properties().get('featuredItemsGroupQuery')
        if group_q:
            return self._gallery_items(group_q, properties, q)

    def featured_items_homepage(self, properties=None, q=None):
        """ Returns portal items featured on the home page. """
        if not 'homePageFeaturedContent' in self.properties():
            raise PortalError('Unable to access portal featured items ' \
                              + '(home page)')
        group_q = self.properties().get('homePageFeaturedContent')
        if group_q:
            return self._gallery_items(group_q, properties, q)

    def feature_collection_templates(self, properties=None, q=None):
        """ Returns portal feature collection (layer) templates. """
        if not 'layerTemplatesGroupQuery' in self.properties():
            raise PortalError('Unable to access portal feature collection ' \
                              + 'templates')
        group_q = self.properties().get('layerTemplatesGroupQuery')
        if group_q:
            item_q = 'type:"Feature Collection Template"'
            if q:
                item_q += ' AND ' + q
            return self._gallery_items(group_q, properties, item_q)

    def symbol_sets(self, properties=None, q=None):
        """ Returns portal symbol sets. """
        if not 'symbolSetsGroupQuery' in self.properties():
            raise PortalError('Unable to access portal symbol sets')
        group_q = self.properties().get('symbolSetsGroupQuery')
        if group_q:
            item_q = 'type:"Symbol Sets"'
            if q:
                item_q += ' AND ' + q
            return self._gallery_items(group_q, properties, item_q)

    def gallery_templates(self, properties=None, q=None):
        """ Returns portal gallery templates. """
        if not 'galleryTemplatesGroupQuery' in self.properties():
            raise PortalError('Unable to access portal gallery templates')
        group_q = self.properties().get('galleryTemplatesGroupQuery')
        if group_q:
            item_q = 'type:"Web Mapping Application"'
            if q:
                item_q += ' AND ' + q
            return self._gallery_items(group_q, properties, item_q)

    def webmap_templates(self, properties=None, q=None):
        """ Returns portal web (mapping) application templates. """
        if not 'templatesGroupQuery' in self.properties():
            raise PortalError('Unable to access portal web map templates')
        group_q = self.properties().get('templatesGroupQuery')
        if group_q:
            item_q = 'type:"Web Mapping Application"'
            if q:
                item_q += ' AND ' + q
            return self._gallery_items(group_q, properties, item_q)

    def _gallery_items(self, group_q, properties, item_filter):
        group_results = self.groups(['id'], group_q, scope='public')
        if group_results:
            group_id = group_results[0]['id']
            item_q = 'group:' + group_id
            if item_filter:
                item_q += ' AND ' + item_filter
            return self.search(properties, item_q, scope='public')

    def add_item(self, item, data=None, thumbnail=None, metadata=None,
                 owner=None, folder=None):
        """ Adds an item, optionally with data, metadata, and/or thumbnail. """

        # Add the item properties to the post data
        postdata = self._postdata()
        postdata.update(unicode_to_ascii(item))

        # Build the files list (tuples)
        files = []
        if data:
            if _is_http_url(data):
                data = urllib.urlretrieve(data)[0]
            files.append(('file', data, os.path.basename(data)))
        if metadata:
            if _is_http_url(metadata):
                metadata = urllib.urlretrieve(metadata)[0]
            files.append(('metadata', metadata, 'metadata.xml'))
        if thumbnail:
            if _is_http_url(thumbnail):
                thumbnail = urllib.urlretrieve(thumbnail)[0]
                file_ext = os.path.splitext(thumbnail)[1]
                if not file_ext:
                    file_ext = imghdr.what(thumbnail)
                    if file_ext in ('gif', 'png', 'jpeg'):
                        new_thumbnail = thumbnail + '.' + file_ext
                        os.rename(thumbnail, new_thumbnail)
                        thumbnail = new_thumbnail
            files.append(('thumbnail', thumbnail, os.path.basename(thumbnail)))

        # If owner isn't specified, use the logged in user
        if not owner:
            owner = self.logged_in_user()['username']

        # Setup the item path, including the folder, and post to it
        path = 'content/users/' + owner
        if folder:
            path += '/' + folder
        path += '/addItem'
        resp = self.con.post(path, postdata, files)
        if resp and resp.get('success'):
            return resp['id']

    def update_item(self, id, item=None, data=None, metadata=None, thumbnail=None):
        """ Updates an item's properties, data, metadata, and/or thumbnail. """

        if not (item or data or metadata or thumbnail):
            _log.info('Update item called without anything to update')
            return None

        if item is None:
            item = {}

        # Build the link
        path = self.user_item_link(id, item.get('owner'), path_only=True) \
               + '/update'

        # Setup the postdata, including the item (if specified)
        postdata = self._postdata()
        if item:
            postdata.update(unicode_to_ascii(item))
            keys_to_delete = ['id', 'owner', 'thumbnail', 'size', 'numComments',
                              'numRatings', 'avgRating', 'numViews' ]
            for key in keys_to_delete:
                if key in postdata:
                    del postdata[key]

        # Build the files list (tuples)
        files = []
        if data:
            if _is_http_url(data):
                data = urllib.urlretrieve(data)[0]
            files.append(('file', data, os.path.basename(data)))
        if metadata:
            if _is_http_url(metadata):
                metadata = urllib.urlretrieve(metadata)[0]
            files.append(('metadata', metadata, 'metadata.xml'))
        if thumbnail:
            if _is_http_url(thumbnail):
                thumbnail = urllib.urlretrieve(thumbnail)[0]
                file_ext = os.path.splitext(thumbnail)[1]
                if not file_ext:
                    file_ext = imghdr.what(thumbnail)
                    if file_ext in ('gif', 'png', 'jpeg'):
                        new_thumbnail = thumbnail + '.' + file_ext
                        os.rename(thumbnail, new_thumbnail)
                        thumbnail = new_thumbnail
            files.append(('thumbnail', thumbnail, os.path.basename(thumbnail)))

        resp = self.con.post(path, postdata, files)
        if resp:
            return resp.get('success')

    def publish_item(self, file_type, item_id):
        """
        Publishes a hosted service based on an existing service definition item.
        """
        # FOR FUTURE USE - Information about future parameters
        #
        # Publishes a hosted service based on an existing source item.
        # Publishers can create feature services as well as tiled map
        # services.
        # Feature services can be created using input files of type csv,
        # shapefile, serviceDefinition, featureCollection, and
        # fileGeodatabase.
        # 
        # Inputs:
        #    file_type - Item type.
        #               Values: serviceDefinition | shapefile | csv |
        #               tilePackage | featureService | featureCollection |
        #               fileGeodata
        #    publish_parameters - object describing the service to be created
        #                        as part of the publish operation. Only
        #                        required for CSV, Shapefiles, feature
        #                        collection, and file geodatabase.
        #    item_id - The ID of the item to be published.
        #    text - The text in the file to be published. This ONLY applies
        #           to CSV files.
        #    file_path - The file to be uploaded.
        #    output_type - Only used when a feature service is published as a
        #                 tile service.

        # FOR FUTURE USE
        # _allowed_types = ['serviceDefinition', 'shapefile', 'csv',
        #                   'tilePackage', 'featureService',
        #                   'featureCollection', 'fileGeodatabase']
        #
        _allowed_types = ['serviceDefinition']
        
        if file_type.lower() not in [t.lower() for t in _allowed_types]:
            raise PortalError('Unsupported file type: {}'.format(file_type))
       
        # Setup the postdata
        postdata = self._postdata()
        
        # Set parameters
        # NOTE: request parameters are: itemId, file, text, fileType,
        # publishParameters, outputType, and overwrite
        params = {'fileType': file_type}
        if item_id is not None:
            params['itemId'] = item_id
        else:
            # TEMPORARY USE
            raise PortalError('Parameter "item_id" must contain non-None value.')
        
        # FOR FUTURE USE
        # if publish_parameters is not None:
        #     params['publishParameters'] = publish_parameters            
        # if text is not None and file_type.lower() == 'csv':
        #     params['text'] = text
        
        postdata.update(unicode_to_ascii(params))

        # Setup the REST path and post to it
        owner = self.logged_in_user()['username']
        path = 'content/users/' + owner
        # if folder:
        #     path += '/' + folder
        path += '/publish'
        resp = self.con.post(path, postdata)
        if resp:
            return resp.get('services')

    def job_status(self, item_id, job_id=None, job_type=None):
        """
           Inquire about status when publishing an item, adding an item in
           async mode, or adding with a multipart upload. "Partial" is
           available for Add Item Multipart, when only a part is uploaded
           and the item is not committed.

           Input:
              job_type The type of asynchronous job for which the status has
                      to be checked. Default is none, which check the
                      item's status.  This parameter is optional unless
                      used with the operations listed below.
                      Values: publish, generateFeatures, export,
                              and createService
              job_id - The job ID returned during publish, generateFeatures,
                      export, and createService calls.
        """
        # Setup the postdata
        postdata = self._postdata()
        
        params = {}
        if job_type is not None:
            params['jobType'] = job_type
        if job_id is not None:
            params["jobId"] = job_id
            
        postdata.update(unicode_to_ascii(params))
        path = 'content/users/{}/items/{}/status'.format(self.item(item_id)['owner'], item_id)
        return self.con.post(path, postdata)

    def update_webmap(self, webmap):
        """ Updates the specific webmap in the portal. """
        return self.update_item(webmap.id, {'text': webmap.data})

    def delete_item(self, id, owner=None):
        """ Deletes a single item from the portal. """
        path = self.user_item_link(id, owner, path_only=True) + '/delete'
        resp = self.con.post(path, self._postdata())
        if resp:
            return resp.get('success')

    def share_item(self, item_id, group_ids, org=False, everyone=False):
        """ Shares an single item within the portal with groups, the org, and/or everyone. """
        group_ids = unpack(group_ids, 'id')
        postdata = self._postdata()
        postdata['everyone'] = str(everyone).lower()
        postdata['org'] = str(org).lower()
        postdata['groups'] = ','.join(group_ids) if group_ids else ''
        return self.con.post('content/items/' + item_id + '/share', postdata)

    def unshare_item(self, item_id, group_ids):
        """ Unshares a single item within the portal . """
        group_ids = unpack(group_ids, 'id')
        postdata = self._postdata()
        postdata['groups'] = ','.join(group_ids) if group_ids else ''
        return self.con.post('content/items/' + item_id + '/unshare', postdata)

    def reassign_item(self, id, target_owner, target_folder=None):
        """ Reassigns a single item within the portal. """
        user_item_link = self.user_item_link(id, path_only=True)
        postdata = self._postdata()
        postdata['targetUsername'] = target_owner
        postdata['targetFoldername'] = target_folder if target_folder else '/'
        return self.con.post(user_item_link + '/reassign', postdata)

    def share_items(self, owner, item_ids, group_ids=None, org=False,
                    everyone=False):
        """ Shares items with groups, the org, and/or everyone. """
        item_ids = unpack(item_ids, 'id')
        group_ids = unpack(group_ids, 'id')
        postdata = self._postdata()
        postdata['everyone'] = str(everyone).lower()
        postdata['org'] = str(org).lower()
        postdata['groups'] = ','.join(group_ids) if group_ids else ''
        postdata['items'] = ','.join(item_ids)
        return self.con.post('content/users/' + owner + '/shareItems',
                             postdata)

    def unshare_items(self, owner, item_ids, group_ids):
        """ Unshares items with groups. """
        item_ids = unpack(item_ids, 'id')
        group_ids = unpack(group_ids, 'id')
        postdata = self._postdata()
        postdata.update({'groups': ','.join(group_ids),
                         'items': ','.join(item_ids)})
        return self.con.post('content/users/' + owner + '/unshareItems', postdata)

    def delete_items(self, owner, item_ids):
        """ Deletes items from the portal. """
        item_ids = unpack(item_ids, 'id')
        postdata = self._postdata()
        postdata['items'] = ','.join(item_ids)
        return self.con.post('content/users/' + owner + '/deleteItems', postdata)

    def folders(self, owner):
        """ Returns the specified user's folders. """
        resp = self.con.post('content/users/' + owner, self._postdata())
        if resp and 'folders' in resp:
            return resp['folders']
        else:
            return []

    def create_folder(self, owner, title):
        """ Creates a folder for the given user with given title. """
        postdata = self._postdata()
        postdata['title'] =  title
        resp = self.con.post('content/users/' + owner + '/createFolder',
                             postdata)
        if resp and resp.get('success'):
            return resp['folder']


    def delete_folder(self, owner, folder_id):
        """ Deletes a specific user folder. """
        path = '/content/users/' + owner + '/' + folder_id + '/delete'
        resp = self.con.post(path, self._postdata())
        if resp:
            return resp.get('success')

    def related_items(self, id, types=RELATIONSHIP_TYPES,
                      directions=frozenset(['forward'])):
        """ Returns items related to the specified item. """
        if not set(types) <= RELATIONSHIP_TYPES:
            raise PortalError('Unsupported relationship types: ' \
                              + str(types))
        if not set(directions) <= RELATIONSHIP_DIRECTIONS:
            raise PortalError('Unsupported directions: ' + str(directions))
        related_items = []
        for rel_type in types:
            for direction in directions:
                postdata = self._postdata()
                postdata['relationshipType'] = rel_type
                postdata['direction'] = direction
                resp = self.con.post('content/items/' + id + '/relatedItems',
                                     postdata)
                for related_item in resp['relatedItems']:
                    related_items.append((related_item, rel_type, direction))
        return related_items

    def add_relationship(self, owner, origin_id, dest_id, rel_type, folder=None):
        """ Adds a relationship between two items. """
        if not rel_type in RELATIONSHIP_TYPES:
            raise PortalError('Unsupported relationship type: ' + rel_type)
        postdata = self._postdata()
        postdata['originItemId'] = origin_id
        postdata['destinationItemId'] = dest_id
        postdata['relationshipType'] = rel_type
        path = 'content/users/' + owner
        if folder:
            path += '/' + folder
        path += '/addRelationship'
        resp = self.con.post(path, postdata)
        if resp:
            return resp.get('success')

    def delete_relationship(self, owner, origin_id, dest_id, rel_type,
                            folder=None):
        """ Deletes a relationship between two items. """
        if not rel_type in RELATIONSHIP_TYPES:
            raise PortalError('Unsupported relationship type: ' + rel_type)
        postdata = self._postdata()
        postdata['originItemId'] = origin_id
        postdata['destinationItemId'] = dest_id
        postdata['relationshipType'] = rel_type
        path = 'content/users/' + owner
        if folder:
            path += '/' + folder
        path += '/deleteRelationship'
        resp = self.con.post(path, postdata)
        if resp:
            return resp.get('success')

    def group(self, id):
        """ Returns the group for the specified group id. """
        return self.con.post('community/groups/' + id, self._postdata())

    def groups(self, properties=None, q=None, group_fields=None, sort_field='',
               sort_order='asc', num=1000, scope='default'):
        """ Searches portal groups. Supports sorting, aggregation, and auto-paging. """
        return self._search(self._groups_page, properties, q, None, group_fields,
                            sort_field, sort_order, num, scope)

    def _groups_page(self, q=None, bbox=None, start=1, num=10, sortfield='',
                     sortorder='asc'):
        _log.info('Searching groups (q=' + str(q) + ', start=' + str(start) \
                  + ', num=' + str(num) + ')')
        postdata = self._postdata()
        postdata.update({ 'q': q, 'start': start, 'num': num,
                          'sortField': sortfield, 'sortOrder': sortorder })
        return self.con.post('community/groups', postdata)

    def group_thumbnail(self, id):
        """ Returns the group thumbnail for the specified group id. """
        thumbnail_file = self.group(id).get('thumbnail')
        if thumbnail_file:
            thumbnail_url_path = 'community/groups/' + id + '/info/' + thumbnail_file
            if thumbnail_url_path:
                return self.con.get(thumbnail_url_path, try_json=False)

    def group_thumbnaild(self, id, dir=None, thumbnail_file=None):
        """ Downloads the group thumbnail for the specified group id, returns file path. """
        if not thumbnail_file:
            thumbnail_file = self.group(id).get('thumbnail')

        # Only proceed if a thumbnail exists
        if thumbnail_file:
            thumbnail_url_path = 'community/groups/' + id + '/info/' + thumbnail_file
            if thumbnail_url_path:
                if not dir:
                    dir = self.workdir
                file_path = os.path.join(dir, thumbnail_file)
                self.con.download(thumbnail_url_path, file_path)
                return file_path

    def group_members(self, id):
        """ Returns members of the specified group. """
        return self.con.post('community/groups/' + id + '/users',
                             self._postdata())
    
    def group_items(self, id):
        """ Returns the items shared with the specified group id. """
        return self.con.post('content/groups/' + id, self._postdata())['items']

    def create_group(self, group, thumbnail=None):
        """ Creates a group, optionally with a thumbnail. """

        postdata = self._postdata()
        postdata.update(unicode_to_ascii(group))

        # Build the files list (tuples)
        files = []
        if thumbnail:
            if _is_http_url(thumbnail):
                thumbnail = urllib.urlretrieve(thumbnail)[0]
                file_ext = os.path.splitext(thumbnail)[1]
                if not file_ext:
                    file_ext = imghdr.what(thumbnail)
                    if file_ext in ('gif', 'png', 'jpeg'):
                        new_thumbnail = thumbnail + '.' + file_ext
                        os.rename(thumbnail, new_thumbnail)
                        thumbnail = new_thumbnail
            files.append(('thumbnail', thumbnail, os.path.basename(thumbnail)))

        # Send the POST request, and return the id from the response
        resp = self.con.post('community/createGroup', postdata, files)
        if resp and resp.get('success'):
            return resp['group']['id']

    def update_group(self, id, properties=None, thumbnail=None):
        """ Updates a group's properties. """
        postdata = self._postdata()
        if properties:
            postdata.update(properties)

        files = []
        if thumbnail:
            if _is_http_url(thumbnail):
                thumbnail = urllib.urlretrieve(thumbnail)[0]
                file_ext = os.path.splitext(thumbnail)[1]
                if not file_ext:
                    file_ext = imghdr.what(thumbnail)
                    if file_ext in ('gif', 'png', 'jpeg'):
                        new_thumbnail = thumbnail + '.' + file_ext
                        os.rename(thumbnail, new_thumbnail)
                        thumbnail = new_thumbnail
            files.append(('thumbnail', thumbnail, os.path.basename(thumbnail)))

        resp = self.con.post('community/groups/' + id + '/update', postdata, files)
        if resp:
            return resp.get('success')

    def reassign_group(self, id, target_owner):
        """ Reassigns a group to another owner. """
        postdata = self._postdata()
        postdata['targetUsername'] = target_owner
        resp = self.con.post('community/groups/' + id + '/reassign', postdata)
        if resp:
            return resp.get('success')

    def delete_group(self, id):
        """ Deletes a group. """
        # TODO: considering removing it from the list of featured groups?
        resp = self.con.post('community/groups/' + id + '/delete',
                             self._postdata())
        if resp:
            return resp.get('success')

    def leave_group(self, id):
        """ Removes the logged in user from the specified group. """
        resp = self.con.post('community/groups/' + id + '/leave',
                             self._postdata())
        if resp:
            return resp.get('success')

    def user(self, username):
        """ Returns the user for the specified username. """
        return self.con.post('community/users/' + username, self._postdata())

    def user_item(self, id, owner=None, folder_id=None):
        """ Returns a tuple of the item properties, item sharing, and folder id. """

        # EL commented 6/7/2013: having issues where the id exists in the cache,
        # but the URL to the item is incorrect; for example, the item is located
        # in a folder, but the folder_id is None.
        
        ## First check the cache, and if we have the link, try it
        #if id in self._user_item_links_cache:
        #    user_item_link = self._user_item_links_cache[id]
        #    resp = self.con.post(user_item_link, self._postdata())
        #    if resp and not resp.get('error'):
        #        return resp['item'], resp['sharing'], folder_id
        
        # If we haven't cached the link, or the cached link no longer works,
        # proceed with trying the more manual approach. Start with getting the
        # owner, if not provided as input.
        if not owner:
            item = self.item(id)
            if not item:
                raise PortalError('Invalid item id: ' + id)
            owner = item['owner']

        # TODO supress warnings when searching

        # If a folder was provided, use it to find the item
        basepath = 'content/users/' + owner + '/'
        if folder_id:
            path = basepath + folder_id + '/items/' + id
            resp = self.con.post(path, self._postdata())
            if resp and not resp.get('error'):
                self._user_item_links_cache[id] = path
                return resp['item'], resp['sharing'], folder_id

        # Otherwise, first try the root folder
        path = basepath + 'items/' + id
        resp = self.con.post(path, self._postdata())
        if resp and not 'error' in resp:
            self._user_item_links_cache[id] = path
            return resp['item'], resp['sharing'], folder_id

        # If the item wasnt in root folder, try other folders
        folders = self.folders(owner)
        for folder in folders:
            path = basepath + folder['id'] + '/items/' + id
            resp = self.con.post(path, self._postdata())
            if resp and not resp.get('error'):
                self._user_item_links_cache[id] = path
                return resp['item'], resp['sharing'], folder['id']

        return None, None, None

    def user_item_link(self, id, owner=None, folder_id=None, path_only=False):
        """ Returns the user link to an item (includes folder if appropriate). """

        # The call to user_item will use the cache, and will validate the link
        item, item_sharing, folder_id = self.user_item(id, owner, folder_id)

        if item:
            link = ''
            if not path_only:
                link += self.con.baseurl
                if self.is_all_ssl():
                    link = link.replace('http://', 'https')
            link += 'content/users/' + item['owner'] + '/'
            if not folder_id:
                return link + 'items/' + id
            else:
                return link + folder_id + '/items/' + id
            
    def org_users(self, properties=None, group_fields=None, sort_field='',
                  sort_order='asc', num=1000):
        """ Returns all users within the portal organization. """

        # Parse the properties into the property names and aggregate functions.
        # Then validate the inputs (e.g. make sure aggregate functions are
        # supported, that propertie are valid)
        if properties is None:
            properties = []
        prop_names, func_names = self._parse_properties(properties)
        self._validate_properties(properties, func_names, group_fields)

        # Prepare for searching
        prop_names_nodups = list(set(prop_names))

        # Execute the search and get back the results
        count = 0
        resp = self._org_users_page(1, min(num, 100))
        resp_users = resp.get('users')
        results = self._extract(resp_users, prop_names_nodups)
        count += int(resp['num'])
        nextstart = int(resp['nextStart'])
        while count < num and nextstart > 0:
            resp = self._org_users_page(nextstart, min(num - count, 100))
            resp_users = resp.get('users')
            results.extend(self._extract(resp_users, prop_names_nodups))
            count += int(resp['num'])
            nextstart = int(resp['nextStart'])

        # If group fields were specified, aggregate the results (and sort, if
        # sort field was specified)
        if group_fields or sort_field:
            results = self._groupby_and_sort(results, group_fields, prop_names,
                                             func_names, sort_field, sort_order)
        return results

    def _org_users_page(self, start=1, num=10):
        _log.info('Retrieving org users (start=' + str(start) \
                  + ', num=' + str(num) + ')')
        postdata = self._postdata()
        postdata['start'] = start
        postdata['num'] = num
        return self.con.post('portals/self/users', postdata)

    def users(self, properties=None, q=None, group_fields=None, sort_field='',
              sort_order='asc', num=1000, scope='default'):
        """ Searches portal users. Supports sorting, aggregation, and auto-paging. """

        # If user is attempting to search public and hasn't specified a query
        # then throw an error
        is_searching_public = self._is_searching_public(scope)
        if is_searching_public and not q:
            raise PortalError('q parameter is required when searching ' \
                              + 'with public scope')

        # If the user is searching within the org, verify that either we can
        # get the org's account id. If we can't, it's likely a private portal
        # and the user is not logged in... then we throw an error
        if not is_searching_public:
            accountid = self._properties.get('id')
            if accountid and q:
                q += ' accountid:' + accountid
            elif accountid:
                q = 'accountid:' + accountid
            else:
                raise PortalError('Cannot search this portal at the org scope. ' \
                                  + 'Either attemping to search www.arcgis.com ' \
                                  + 'or a private subscirption/portal anonymously')

        # Parse the properties into the property names and aggregate functions.
        # Then validate the inputs (e.g. make sure aggregate functions are
        # supported, that propertie are valid)
        if properties is None:
            properties = []
        prop_names, func_names = self._parse_properties(properties)
        self._validate_properties(properties, func_names, group_fields)

        # Prepare for searching
        prop_names_nodups = list(set(prop_names))
        sort_field_name = ''
        if sort_field:
            sort_field_name = self._parse_properties([sort_field])[0][0]

        # Execute the search and get back the results
        count = 0
        resp = self._users_page(q, 1, min(num, 100), sort_field_name, sort_order)
        resp_users = resp.get('results')
        results = self._extract(resp_users, prop_names_nodups)
        count += int(resp['num'])
        nextstart = int(resp['nextStart'])
        while count < num and nextstart > 0:
            resp = self._users_page(q, nextstart, min(num - count, 100),
                                    sort_field_name, sort_order)
            resp_users = resp.get('results')
            results.extend(self._extract(resp_users, prop_names_nodups))
            count += int(resp['num'])
            nextstart = int(resp['nextStart'])

        # If group fields were specified, aggregate the results (and sort, if
        # sort field was specified)
        if group_fields:
            results = self._groupby_and_sort(results, group_fields, prop_names,
                                             func_names, sort_field, sort_order)
        return results

    def _users_page(self, q=None, start=1, num=10, sortfield='', sortorder='asc'):
        _log.info('Searching users (q=' + str(q) + ', start=' + str(start) \
                  + ', num=' + str(num) + ')')
        postdata = self._postdata()
        postdata.update({ 'q': q, 'start': start, 'num': num,
                          'sortField': sortfield, 'sortOrder': sortorder })
        return self.con.post('community/users', postdata)

    def user_contents(self, username):
        """ Returns a tuple of root items and a dictionary of folder items."""
        resp = self.con.post('content/users/' + username, self._postdata())
        root_items = resp['items']
        folders = []
        for folder in resp['folders']:
            resp = self.con.post('content/users/' + username + '/' \
                                 + folder['id'], self._postdata())
            folders.append((folder['id'], folder['title'], resp['items']))
        return root_items, folders

    def user_invitations(self, username):
        """ Returns all of a user's invitations. """
        invitations_url = 'community/users/' + username + '/invitations'
        invitations = self.con.post(invitations_url, self._postdata())
        return invitations['userInvitations']

    def accept_user_invitation(self, username, invitation_id):
        """ Accepts a specific user invitation. """
        invitations_url = 'community/users/' + username + '/invitations'
        accept_url = invitations_url + '/' + invitation_id + '/accept'
        self.con.post(accept_url, self._postdata())

    def user_notifications(self, username):
        """ Returns all of a user's notifications. """
        notifications_url = 'community/users/' + username + '/notifications'
        notifications = self.con.post(notifications_url, self._postdata())
        return notifications['notifications']

    def delete_notification(self, username, notification_id):
        """ Deletes a specific user notification. """
        notifications_url = 'community/users/' + username + '/notifications'
        delete_url = notifications_url +'/' + notification_id + '/delete'
        self.con.post(delete_url, self._postdata())

    def update_user(self, username, properties):
        """ Updates a user's properties."""
        postdata = self._postdata()
        postdata.update(properties)
        resp = self.con.post('community/users/' + username + '/update',
                             postdata, ssl=True)
        if resp:
            return resp.get('success')

    def update_user_role(self, username, role):
        """ Updates a user's role."""
        postdata = self._postdata()
        postdata.update({'user': username, 'role': role})
        resp = self.con.post('portals/self/updateuserrole', postdata, ssl=True)
        if resp:
            return resp.get('success')

    def reset_user(self, username, password, new_password=None,
                   new_security_question=None, new_security_answer=None):
        """ Resets a user's password, security question, and/or security answer."""
        postdata = self._postdata()
        postdata['password'] = password
        if new_password:
            postdata['newPassword'] = new_password
        if new_security_question:
            postdata['newSecurityQuestionIdx'] = new_security_question
        if new_security_answer:
            postdata['newSecurityAnswer'] = new_security_answer
        resp = self.con.post('community/users/' + username + '/reset',
                             postdata,ssl=True)
        if resp:
            return resp.get('success')

    def delete_user(self, username, cascade=False, reassign_to=None):
        """ Deletes a user from the portal, optionally deleting or reassigning groups and items."""

        # If we're cascading, handle items and groups
        if cascade:
            # Reassign or delete the user's items
            items = self.search(['id'], 'owner:' + username)
            if items:
                if reassign_to:
                    for item in items:
                        self.reassign_item(item['id'], reassign_to)
                else:
                    self.delete_items(username, items)
            # Reassign or delete the user's groups
            groups = self.groups(['id'], 'owner:' + username)
            if groups:
                for group in groups:
                    if reassign_to:
                        self.reassign_group(group['id'], reassign_to)
                    else:
                        self.delete_group(group['id'])

        # Delete the user
        resp = self.con.post('community/users/' + username + '/delete',
                             self._postdata())
        if resp:
            return resp.get('success')

    def invite_group_users(self, user_names, group_ids,
                           role='group_member', expiration=10080):
        """ Invites users to groups."""

        user_names = unpack(user_names, 'username')
        group_ids = unpack(group_ids, 'id')

        # Send out the invitations
        for group_id in group_ids:
            postdata = self._postdata()
            postdata['users'] = ','.join(user_names)
            postdata['role'] = role
            postdata['expiration'] = expiration
            resp = self.con.post('community/groups/' + group_id + '/invite',
                                 postdata)
            if not resp or not resp.get('success'):
                raise PortalError('Error inviting ' + str(user_names) \
                                  + ' to group ' + str(group_id))

    def add_group_users(self, user_names, group_ids):
        """ Adds users to groups. Supported on 2.1 or newer portals.  """

        if self._is_pre_21:
            _log.warning('The auto_accept option is not supported in ' \
                         + 'pre-2.0 portals')
            return

        user_names = unpack(user_names, 'username')
        group_ids = unpack(group_ids, 'id')

        # Remove the users to each group
        retval = dict()
        for group_id in group_ids:
            postdata = self._postdata()
            postdata['users'] = ','.join(user_names)
            resp = self.con.post('community/groups/' + group_id + '/addUsers',
                                 postdata)
            retval[group_id] = resp
        return retval

    def remove_group_users(self, user_names, group_ids):
        """ Remove users from groups. Supported on 2.1 or newer portals. """

        user_names = unpack(user_names, 'username')
        group_ids = unpack(group_ids, 'id')

        # Remove the users to each group
        retval = dict()
        for group_id in group_ids:
            postdata = self._postdata()
            postdata['users'] = ','.join(user_names)
            resp = self.con.post('community/groups/' + group_id + '/removeUsers',
                                 postdata)
            retval[group_id] = resp
        return retval

    def _extract(self, results, props=None):
        if not props or len(props) == 0:
            return results
        newresults = []
        for result in results:
            newresult = dict((p, result[p]) for p in props if p in result)
            newresults.append(newresult)
        return newresults

    def operationview(self, id):
        """ Returns an OperationView object for the specified item id """
        return OperationView(id, self.item_data(id), self.con.ensure_ascii)

    def operationviews(self, q=None, bbox=None, sort_field='', sort_order='asc',
                num=1000, scope='default', ignore_errors=True):
        """ Search portal items for operation views, returning OperationView objects """
        
        # Build the search query
        search_q = OPVIEW_ITEM_FILTER
        if q:
            search_q += ' ' + q

        # Search for the corresponding webmaps (return IDs only)
        opview_items = self.search(['id'], search_q, bbox,
                                   sort_field=sort_field,
                                   sort_order=sort_order,
                                   num=num,
                                   scope=scope)
        opview_ids = unpack(opview_items)

        # Build and return an array of WebMap objects
        if opview_ids:
            opviews = []
            for opview_id in opview_ids:
                try:
                    opview = self.operationview(opview_id)
                    opviews.append(opview)
                except Exception as e:
                    if not ignore_errors:
                        raise e
                    else:
                        _log.warning(e)
            return opviews

    def update_operationview(self, operationview):
        """ Updates the specific operationview in the portal. """
        return self.update_item(operationview.id, {'text': operationview.data})
     
class ArcGISConnection(object):
    """ A class users to manage connection to ArcGIS services (Portal and Server). """

    def __init__(self, baseurl, username=None, password=None, key_file=None,
                 cert_file=None, expiration=60, all_ssl=False, referer=None,
                 proxy_host=None, proxy_port=None, ensure_ascii=True):
        """ The ArcGISConnection constructor. Requires URL and optionally username/password. """

        self.baseurl = normalize_url(baseurl)
        self.key_file = key_file
        self.cert_file = cert_file
        self.all_ssl = all_ssl
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.ensure_ascii = ensure_ascii
        self.token = None

        # Setup the referer and user agent
        if not referer:
            import socket
            ip = socket.gethostbyname(socket.gethostname())
            referer = socket.gethostbyaddr(ip)[0]
        self._referer = referer
        self._useragent = 'PortalPy/' + __version__

        # Login if credentials were provided
        if username and password:
            self.login(username, password, expiration)
        elif username or password:
            _log.warning('Both username and password required for login')

    def generate_token(self, username, password, expiration=60):
        """ Generates and returns a new token, but doesn't re-login. """
        postdata = { 'username': username, 'password': password,
                     'client': 'referer', 'referer': self._referer,
                     'expiration': expiration, 'f': 'json' }
        resp = self.post('generateToken', postdata, ssl=True)
        if resp:
            return resp.get('token')

    def login(self, username, password, expiration=60):
        """ Logs into the portal using username/password. """
        newtoken = self.generate_token(username, password, expiration)
        if newtoken:
            self.token = newtoken
            self._username = username
            self._password = password
            self._expiration = expiration
        return newtoken

    def relogin(self, expiration=None):
        """ Re-authenticates with the portal using the same username/password. """
        if not expiration:
            expiration = self._expiration
        return self.login(self._username, self._password, expiration)

    def logout(self):
        """ Logs out of the portal. """
        self.token = None

    def is_logged_in(self):
        """ Returns true if logged into the portal. """
        return self.token is not None

    def get(self, path, ssl=False, compress=True, try_json=True, is_retry=False):
        """ Returns result of an HTTP GET. Handles token timeout and all SSL mode."""
        url = path
        if not path.startswith('http://') and not path.startswith('https://'):
            url = self.baseurl + path
        if ssl or self.all_ssl:
            url = url.replace('http://', 'https://')

        # Add the token if logged in
        if self.is_logged_in():
            url = self._url_add_token(url, self.token)

        _log.debug('REQUEST (get): ' + url)

        try:
            # Send the request and read the response
            headers = [('Referer', self._referer),
                       ('User-Agent', self._useragent)]
            if compress:
                headers.append(('Accept-encoding', 'gzip'))
            opener = urllib2.build_opener()
            opener.addheaders = headers
            resp = opener.open(url)
            if resp.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(resp.read())
                f = gzip.GzipFile(fileobj=buf)
                resp_data = f.read()
            else:
                resp_data = resp.read()

            # If we're not trying to parse to JSON, return response as is
            if not try_json:
                return resp_data

            try:
                resp_json = json.loads(resp_data)

                # Convert to ascii if directed to do so
                if self.ensure_ascii:
                    resp_json = unicode_to_ascii(resp_json)

                # Check for errors, and handle the case where the token timed
                # out during use (and simply needs to be re-generated)
                try:
                    if resp_json.get('error', None):
                        errorcode = resp_json['error']['code']
                        if errorcode == 498 and not is_retry:
                            _log.info('Token expired during get request, ' \
                                      + 'fetching a new token and retrying')
                            newtoken = self.relogin()
                            newpath = self._url_add_token(path, newtoken)
                            return self.get(newpath, ssl, compress, try_json, is_retry=True)
                        elif errorcode == 498:
                            raise PortalError('Invalid token')
                        self._handle_json_error(resp_json['error'])
                        return None
                except AttributeError:
                    # Top-level JSON object isnt a dict, so can't have an error
                    pass

                # If the JSON parsed correctly and there are no errors,
                # return the JSON
                return resp_json

            # If we couldnt parse the response to JSON, return it as is
            except ValueError:
                return resp

        # If we got an HTTPError when making the request check to see if it's
        # related to token timeout, in which case, regenerate a token
        except urllib2.HTTPError as e:
            if e.code == 498 and not is_retry:
                _log.info('Token expired during get request, fetching a new ' \
                          + 'token and retrying')
                self.logout()
                newtoken = self.relogin()
                newpath = self._url_add_token(path, newtoken)
                return self.get(newpath, ssl, try_json, is_retry=True)
            elif e.code == 498:
                raise PortalError('Invalid token')
            else:
                raise e

    def download(self, path, filepath, ssl=False, is_retry=False):
        """ Downloads result of an HTTP GET. Handles token timeout and all SSL mode."""
        url = path
        if not path.startswith('http://') and not path.startswith('https://'):
            url = self.baseurl + path
        if ssl or self.all_ssl:
            url = url.replace('http://', 'https://')

        # Add the token if logged in
        if self.is_logged_in():
            url = self._url_add_token(url, self.token)

        _log.debug('REQUEST (download): ' + url + ', to ' + filepath)

        # Send the request, and handle the case where the token has
        # timed out (relogin and try again)
        try:
            # TODO handle PKI
            opener = _StrictURLopener()
            opener.addheaders = [('Referer', self._referer),
                                 ('User-Agent', self._useragent)]
            opener.retrieve(url, filepath)
        except urllib2.HTTPError as e:
            if e.code == 498 and not is_retry:
                _log.info('Token expired during download request, fetching a ' \
                          + 'new token and retrying')
                self.logout()
                newtoken = self.relogin()
                newpath = self._url_add_token(path, newtoken)
                self.download(newpath, filepath, ssl, is_retry=True)
            elif e.code == 498:
                raise PortalError('Invalid token')
            else:
                raise e

    def _url_add_token(self, url, token):

        # Parse the URL and query string
        urlparts = urlparse.urlparse(url)
        qs_list = urlparse.parse_qsl(urlparts.query)

        # Update the token query string parameter
        replaced_token = False
        new_qs_list = []
        for qs_param in qs_list:
            if qs_param[0] == 'token':
                qs_param = ('token', token)
                replaced_token = True
            new_qs_list.append(qs_param)
        if not replaced_token:
            new_qs_list.append(('token', token))

        # Rebuild the URL from parts and return it
        return urlparse.urlunparse((urlparts.scheme, urlparts.netloc,
                                    urlparts.path, urlparts.params,
                                    urllib.urlencode(new_qs_list),
                                    urlparts.fragment))

    # TODO Handle HTTPError (?)
    def post(self, path, postdata=None, files=None, ssl=False, compress=True,
             is_retry=False):
        """ Returns result of an HTTP POST. Supports Multipart requests."""
        url = path
        if not path.startswith('http://') and not path.startswith('https://'):
            url = self.baseurl + path
        if ssl or self.all_ssl:
            url = url.replace('http://', 'https://')

        # Add the token if logged in
        if self.is_logged_in():
            postdata['token'] = self.token

        if _log.isEnabledFor(logging.DEBUG):
            msg = 'REQUEST: ' + url + ', ' + str(postdata)
            if files:
                msg += ', files=' + str(files)
            _log.debug(msg)

        # If there are files present, send a multipart request
        if files:
            parsed_url = urlparse.urlparse(url)
            resp_data = self._postmultipart(parsed_url.netloc,
                                            str(parsed_url.path),
                                            postdata,
                                            files,
                                            parsed_url.scheme == 'https')

        # Otherwise send a normal HTTP POST request
        else:
            encoded_postdata = None
            if postdata:
                encoded_postdata = urllib.urlencode(postdata)
            headers = [('Referer', self._referer),
                       ('User-Agent', self._useragent)]
            if compress:
                headers.append(('Accept-encoding', 'gzip'))
            opener = urllib2.build_opener()
            opener.addheaders = headers
            resp = opener.open(url, data=encoded_postdata)
            if resp.info().get('Content-Encoding') == 'gzip':
                buf = StringIO(resp.read())
                f = gzip.GzipFile(fileobj=buf)
                resp_data = f.read()
            else:
                resp_data = resp.read()

        # Parse the response into JSON
        if _log.isEnabledFor(logging.DEBUG):
            _log.debug('RESPONSE: ' + url + ', ' + unicode_to_ascii(resp_data))
        resp_json = json.loads(resp_data)

        # Convert to ascii if directed to do so
        if self.ensure_ascii:
            resp_json = unicode_to_ascii(resp_json)

        # Check for errors, and handle the case where the token timed out
        # during use (and simply needs to be re-generated)
        try:
            if resp_json.get('error', None):
                errorcode = resp_json['error']['code']
                if errorcode == 498 and not is_retry:
                    _log.info('Token expired during post request, fetching a new '
                              + 'token and retrying')
                    self.logout()
                    newtoken = self.relogin()
                    postdata['token'] = newtoken
                    return self.post(path, postdata, files, ssl, compress,
                                     is_retry=True)
                elif errorcode == 498:
                    raise PortalError('Invalid token')
                self._handle_json_error(resp_json['error'])
                return None
        except AttributeError:
            # Top-level JSON object isnt a dict, so can't have an error
            pass

        return resp_json

    def _postmultipart(self, host, selector, fields, files, ssl):
        boundary, body = self._encode_multipart_formdata(fields, files)
        headers = {
        'User-Agent': self._useragent,
        'Referer': self._referer,
        'Content-Type': 'multipart/form-data; boundary=%s' % boundary
        }
        if self.proxy_host:
            if ssl:
                h = httplib.HTTPSConnection(self.proxy_host, self.proxy_port,
                                            key_file=self.key_file,
                                            cert_file=self.cert_file)
                h.request('POST', 'https://' + host + selector, body, headers)
            else:
                h = httplib.HTTPConnection(self.proxy_host, self.proxy_port)
                h.request('POST', 'http://' + host + selector, body, headers)
        else:
            if ssl:
                h = httplib.HTTPSConnection(host, key_file=self.key_file,
                                            cert_file=self.cert_file)
                h.request('POST', selector, body, headers)
            else:
                h = httplib.HTTPConnection(host)
                h.request('POST', selector, body, headers)
        return h.getresponse().read()

    def _encode_multipart_formdata(self, fields, files):
        boundary = mimetools.choose_boundary()
        buf = StringIO()
        for (key, value) in fields.iteritems():
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"' % key)
            buf.write('\r\n\r\n' + _tostr(value) + '\r\n')
        for (key, filepath, filename) in files:
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename))
            buf.write('Content-Type: %s\r\n' % (self._get_content_type(filename)))
            file = open(filepath, "rb")
            try:
                buf.write('\r\n' + file.read() + '\r\n')
            finally:
                file.close()
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        return boundary, buf

    def _get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def _handle_json_error(self, error):
        _log.error(error.get('message', 'Unknown Error'))
        for errordetail in error['details']:
            _log.error(errordetail)

class PortalInfo(object):
    """ An object describing the portal. Supports printable string representation."""
    _org_str = 'Name: {0}\nID: {1}\nURL Key: {2}\nDescription: {3}\n' \
               + 'Culture: {4}\nAccess: {5}\nAll SSL: {6}\n' \
               + 'Supports Hosted Services: {7}\nAvailable Credits: {8}\n' \
               + 'Static Images URL: {9}\n'

    _portal_str = 'Portal Name: {0}\nPortal Hostname: {1}\n' \
                  + 'Portal URL (specified): {2}\n' \
                  + 'Portal URL (normalized): {3}\nPortal Mode: {4}\n' \
                  + 'Portal Version: {5}\n'

    _user_str = 'Logged In As: {0}\nRole: {1}\nUse Case: {2}\n'

    _seperator_str = '---------------------------\n'

    def __init__(self, hostname, url, properties, version, loggedinuser,
                 loggedinrole):
        """ The PortalInfo constructor."""
        self.hostname = hostname
        self.url = url
        self.properties = properties
        self.version = version
        self.loggedinuser = loggedinuser
        self.loggedinrole = loggedinrole

    def __str__(self):
        str = self._org_str.format(
            self._proptostr('name'), self._proptostr('id'), self._proptostr('urlKey'),
            self._proptostr('description'), self._proptostr('culture'),
            self._proptostr('access'), self._proptostr('allSSL'),
            self._proptostr('supportsHostedServices'),
            self._proptostr('availableCredits'),self._proptostr('staticImagesUrl'))
        str += self._seperator_str
        str += self._portal_str.format(
            self._proptostr('portalName'), self.hostname, self.url,
            normalize_url(self.url), self._proptostr('portalMode'), self.version)
        str += self._seperator_str
        str += self._user_str.format(
            self.loggedinuser, self.loggedinrole,self._usecasestr())
        return str

    def _proptostr(self, propname):
        return self.properties[propname] if propname in self.properties else 'N/A'

    def _usecasestr(self):
        mode = self.properties['portalMode']
        isorg = 'urlKey' in self.properties
        isloggedin = bool(self.loggedinuser)

        if mode == 'singletenant' and isloggedin:
            return 'Authenticated Portal User'
        elif mode == 'singletenant':
            return 'Anonymous Portal User'
        elif mode == 'multitenant' and isorg and isloggedin:
            return 'Authenticated Organizational User'
        elif mode == 'multitenant' and isorg:
            return 'Anonmyous Organizational User'
        elif mode == 'multitenant' and isloggedin:
            return 'Authenticated Non-Organizational User'
        elif mode == 'multitenant':
            return 'Anonmyous Non-Organizational User'
        else:
            return 'Unknown'

class WebMap(object):
    """ A Web Map object with utility functions based on Web Map JSON."""

    def __init__(self, id, data, ensure_ascii=True):
        """ The WebMap constructor. Takes a Web Map item's id and data as input."""
        self.id = id
        self.data = data
        self.ensure_ascii = ensure_ascii
        self._data_json = None
        self.json()

    def json(self):
        """ Returns the Web Map definition as JSON."""
        if self.data:
            if not self._data_json:
                try:
                    self._data_json = json.loads(self.data)
                    if not self._data_json:
                        raise PortalError('WebMap "' + self.id + '" has no data')
                    if self.ensure_ascii:
                        self._data_json = unicode_to_ascii(self._data_json)
                except:
                    raise PortalError('WebMap "' + self.id + '" has invalid data')
            return copy.deepcopy(self._data_json)
        else:
            raise PortalError('WebMap "' + self.id + '" has no data')

    def version(self):
        """ Returns the Web Map's version."""
        json = self.json()
        if 'version' in json:
            return json['version']
        raise PortalError('Web map has no version attribute')

    def layers(self):
        """ Returns all layers in the Web Map (including basemap and operational)."""
        layers = self.operational_layers()
        layers.append(self.basemap()['baseMapLayers'])
        return layers

    def operational_layers(self):
        """ Returns the Web Map's operational layers."""
        return self.json()['operationalLayers']

    def basemap(self):
        """ Returns the Web Map's basemap."""
        return self.json()['baseMap']

    def urls(self, layers=True, basemap=False, normalize=False):
        """ Returns the URLs referenced in the Web Map."""
        urls = []
        json = self.json()
        if layers:
            for layer in json['operationalLayers']:
                if 'url' in layer:
                    url = layer['url']
                    if normalize:
                        url = normalize_url(url)
                    urls.append(url)
        if basemap:
            for layer in json['baseMap']['baseMapLayers']:
                if 'url' in layer:
                    url = layer['url']
                    if normalize:
                        url = normalize_url(url)
                    urls.append(url)
        return urls

    def item_ids(self):
        """ Returns the item ids referenced in the Web Map."""
        item_ids = []
        for layer in self.json()['operationalLayers']:
            if 'itemId' in layer:
                item_ids.append(layer['itemId'])
        return item_ids

    def feature_collections(self, schemas=None, return_empty=False):
        """ Returns the feature collections present in the Web Map."""
        feature_collections = []
        for layer in self.json()['operationalLayers']:
            if 'featureCollection' in layer:
                feature_collection = layer['featureCollection']
                has_features = False
                for feature_layer in feature_collection['layers']:
                    if self._has_features(feature_layer, schemas, return_empty):
                        has_features = True
                        break
                if has_features:
                    feature_collections.append(feature_collection)
        return feature_collections

    def feature_sets(self, schemas=None, return_empty=False):
        """ Returns the feature sets present in the Web Map."""
        feature_sets = []
        for layer in self.json()['operationalLayers']:
            if 'featureCollection' in layer:
                feature_collection = layer['featureCollection']
                for feature_layer in feature_collection['layers']:
                    if self._has_features(feature_layer, schemas, return_empty):
                        feature_sets.append(feature_layer['featureSet'])
        return feature_sets

    def features(self, schemas=None):
        """ Returns all features in the Web Map for a given geomerty type."""
        features = []
        for layer in self.json()['operationalLayers']:
            if 'featureCollection' in layer:
                feature_collection = layer['featureCollection']
                for feature_layer in feature_collection['layers']:
                    if self._has_features(feature_layer, schemas, False):
                        features.extend(feature_layer['featureSet']['features'])
        return features

    def _has_features(self, layer, schemas, return_empty):

        # Handle the empty case first
        if not return_empty and len(layer['featureSet']['features']) == 0:
            return False

        # Check the schemas, if one is provided
        if schemas and not layer['layerDefinition'] in schemas:
            return False

        return True

    def bookmarks(self):
        """ Returns all bookmarks referenced in the Web Map."""
        json = self.json()
        if 'bookmarks' in json:
            return json['bookmarks']
        return []

    def query_tasks(self):
        """ Returns all query tasks referenced in the Web Map."""
        json = self.json()
        if 'tasks' in json:
            tasks = json['tasks']
            if 'queryTasks' in tasks:
                return tasks['queryTasks']
        return []

    def presentation(self):
        """ Returns the referenced in the Web Map (if one exists)."""
        json = self.json()
        if 'presentation' in json:
            return json['presentation']

    def gadgets(self):
        """ Returns the gadgets referenced in the Web Map."""
        json = self.json()
        if 'widgets' in json:
            widgets = json['widgets']
            if 'gadgets' in widgets:
                return widgets['gadgets']
        return []

    def time_slider(self):
        """ Returns the time slider referenced in the Web Map (if one exists)."""
        json = self.json()
        if 'widgets' in json:
            widgets = json['widgets']
            if 'timeSlider' in widgets:
                return widgets['timeSlider']

    def info(self):
        """ Returns information about the Web Map in a dictionary form."""
        info = dict()
        info['id'] = self.id
        info['version'] = self.version()
        info['basemap'] = self.basemap()['title']

        # Start adding the counts for various web map components
        info['counts'] = dict()
        info['counts']['layers'] = len(self.layers())
        info['counts']['operational_layers'] = len(self.operational_layers())
        info['counts']['referened_layers'] = len(self.item_ids())
        info['counts']['feature_collections'] = len(self.feature_collections())
        info['counts']['feature_sets'] = len(self.feature_sets())
        info['counts']['features'] = len(self.features())
        info['counts']['bookmarks'] = len(self.bookmarks())
        info['counts']['gadgets'] = limpoen(self.gadgets())
        info['counts']['query_tasks'] = len(self.query_tasks())
        info['counts']['presentations'] = 1 if self.presentation() else 0
        info['counts']['time_sliders'] = 1 if self.presentation() else 0

        # Count the popups
        popup_count = 0
        layers = self.operational_layers()
        for layer in layers:
            if 'popupInfo' in layer:
                popup_count += len(layer['popupInfo'])
        info['counts']['popups'] = popup_count

        return info

class OperationView(object):
    """ An OperationView object with utility functions based on Operation View JSON."""

    def __init__(self, id, data, ensure_ascii=True):
        """ The OperationView constructor. Takes an Operation View item's id and data as input."""
        self.id = id
        self.data = data
        self.ensure_ascii = ensure_ascii
        self._data_json = None
        self.json()

    def json(self):
        """ Returns the Operation View definition as JSON."""
        if self.data:
            if not self._data_json:
                try:
                    self._data_json = json.loads(self.data)
                    if not self._data_json:
                        raise PortalError('OperationView "' + self.id + '" has no data')
                    if self.ensure_ascii:
                        self._data_json = unicode_to_ascii(self._data_json)
                except:
                    raise PortalError('OperationView "' + self.id + '" has invalid data')
            return copy.deepcopy(self._data_json)
        else:
            raise PortalError('OperationView "' + self.id + '" has no data')

    def version(self):
        """ Returns the Operation View's version."""
        json = self.json()
        if 'version' in json:
            return json['version']
        raise PortalError('Operation View has no version attribute')

    def widgets(self):
        """ Returns the widgets referenced in the Operation View."""
        json = self.json()
        if 'widgets' in json:
            return json['widgets']
        return []

    def map_widgets(self):
        """ Returns the map widgets referenced in the Operation View."""
        map_widgets = []
        for widget in self.widgets():
            if widget['type'].lower() == "mapwidget":
                map_widgets.append(widget)
        return map_widgets

    def standalone_ds_urls(self, normalize=False):
        """ Returns the URLs for standalone data sources referenced in the Operation View."""
        urls = []
        json = self.json()
        for standaloneDS in json['standaloneDataSources']:
            if 'url' in standaloneDS:
                url = standaloneDS['url']
                if normalize:
                    url = normalize_url(url)
                urls.append(url)
        return urls

    def standalone_ds_service_item_ids(self):
        """ Returns the service item id for standalone data sources referenced in the Operation View."""
        service_item_ids = []
        json = self.json()
        for standaloneDS in json['standaloneDataSources']:
            if 'serviceItemId' in standaloneDS:
                service_item_ids.append(standaloneDS['serviceItemId'])
        return service_item_ids
    
class PortalError(Exception):
    """ The PortalError object, which is raised for standard portal errors."""
    def __init__(self, value):
        """ The PortalError constructor."""
        self.value = value
    def __str__(self):
        return repr(self.value)

class _StrictURLopener(urllib.FancyURLopener):
    def http_error_default(self, url, fp, errcode, errmsg, headers):
        if errcode != 200:
            raise urllib2.HTTPError(url, errcode, errmsg, headers, fp)

def normalize_url(url, charset='utf-8'):
    """ Normalizes a URL. Based on http://code.google.com/p/url-normalize."""
    def _clean(string):
        string = unicode(urllib.unquote(string), 'utf-8', 'replace')
        return unicodedata.normalize('NFC', string).encode('utf-8')

    default_port = {
    'ftp': 21,
    'telnet': 23,
    'http': 80,
    'gopher': 70,
    'news': 119,
    'nntp': 119,
    'prospero': 191,
    'https': 443,
    'snews': 563,
    'snntp': 563,
    }
    if isinstance(url, unicode):
        url = url.encode(charset, 'ignore')

    # if there is no scheme use http as default scheme
    if url[0] not in ['/', '-'] and ':' not in url[:7]:
        url = 'http://' + url

    # shebang urls support
    url = url.replace('#!', '?_escaped_fragment_=')

    # splitting url to useful parts
    scheme, auth, path, query, fragment = urlparse.urlsplit(url.strip())
    (userinfo, host, port) = re.search('([^@]*@)?([^:]*):?(.*)', auth).groups()

    # Always provide the URI scheme in lowercase characters.
    scheme = scheme.lower()

    # Always provide the host, if any, in lowercase characters.
    host = host.lower()
    if host and host[-1] == '.':
        host = host[:-1]
    # take care about IDN domains
    host = host.decode(charset).encode('idna')  # IDN -> ACE

    # Only perform percent-encoding where it is essential.
    # Always use uppercase A-through-F characters when percent-encoding.
    # All portions of the URI must be utf-8 encoded NFC from Unicode strings
    path = urllib.quote(_clean(path), "~:/?#[]@!$&'()*+,;=")
    fragment = urllib.quote(_clean(fragment), "~")

    # note care must be taken to only encode & and = characters as values
    query = "&".join(["=".join([urllib.quote(_clean(t), "~:/?#[]@!$'()*+,;=") \
                                for t in q.split("=", 1)]) for q in query.split("&")])

    # Prevent dot-segments appearing in non-relative URI paths.
    if scheme in ["", "http", "https", "ftp", "file"]:
        output = []
        for part in path.split('/'):
            if part == "":
                if not output:
                    output.append(part)
            elif part == ".":
                pass
            elif part == "..":
                if len(output) > 1:
                    output.pop()
            else:
                output.append(part)
        if part in ["", ".", ".."]:
            output.append("")
        path = '/'.join(output)

    # For schemes that define a default authority, use an empty authority if
    # the default is desired.
    if userinfo in ["@", ":@"]:
        userinfo = ""

    # For schemes that define an empty path to be equivalent to a path of "/",
    # use "/".
    if path == "" and scheme in ["http", "https", "ftp", "file"]:
        path = "/"

    # For schemes that define a port, use an empty port if the default is
    # desired
    if port and scheme in default_port.keys():
        if port.isdigit():
            port = str(int(port))
            if int(port) == default_port[scheme]:
                port = ''

    # Put it all back together again
    auth = (userinfo or "") + host
    if port:
        auth += ":" + port
    if url.endswith("#") and query == "" and fragment == "":
        path += "#"
    return urlparse.urlunsplit((scheme, auth, path, query, fragment))

def parse_hostname(url, include_port=False):
    """ Parses the hostname out of a URL."""
    if url:
        parsed_url = urlparse.urlparse(normalize_url(url))
        return parsed_url.netloc if include_port else parsed_url.hostname

def _is_http_url(url):
    if url:
        return urlparse.urlparse(url).scheme in ['http', 'https']

def portal_time(dt):
    """ Turns a UTC datetime object into portal's date/time string format."""
    return '000000' + str(timegm(dt.timetuple()) * 1000)

def unpack(obj_or_seq, key=None, flatten=False):
    """ Turns a list of single item dicts in a list of the dict's values."""

    # The trivial case (passed in None, return None)
    if not obj_or_seq:
        return None

    # We assume it's a sequence
    new_list = []
    for obj in obj_or_seq:
        value = _unpack_obj(obj, key, flatten)
        new_list.extend(value)

    return new_list

def _unpack_obj(obj, key=None, flatten=False):
    try:
        if key:
            value = [obj.get(key)]
        else:
            value = obj.values()
    except AttributeError:
        value = [obj]

    # Flatten any lists if directed to do so
    if value and flatten:
        value = [item for sublist in value for item in sublist]

    return value

def unicode_to_ascii(data):
    """ Converts strings and collections of strings from unicode to ascii. """
    if isinstance(data, str):
        return _remove_non_ascii(data)
    if isinstance(data, unicode):
        return _remove_non_ascii(str(data.encode('utf8')))
    elif isinstance(data, collections.Mapping):
        return dict(map(unicode_to_ascii, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(unicode_to_ascii, data))
    else:
        return data

def _remove_non_ascii(s):
    return ''.join(i for i in s if ord(i) < 128)

def _tostr(obj):
    if not obj:
        return ''
    if isinstance(obj, list):
        return ', '.join(map(_tostr, obj))
    return str(obj)

class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
    def __init__(self, key, cert):
        urllib2.HTTPSHandler.__init__(self)
        self.key = key
        self.cert = cert

    def https_open(self, req):
        # Rather than pass in a reference to a connection class, we pass in
        # a reference to a function which, for all intents and purposes,
        # will behave as a constructor
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=300):
        return httplib.HTTPSConnection(host, key_file=self.key, cert_file=self.cert)

# Based on recipe 18.7 in O'Reilly's Python Cookbook:
# Caching Objects with a FIFO (or LRU) Pruning Strategy
class LRUCache(object, UserDict.DictMixin):
    def __init__(self, num_entries=100, dct=()):
        self.num_entries = num_entries
        self.dct = dict(dct)
        self.lst = []
    def __repr__(self):
        return '%r(%r%r)' % (
        self.__class__.__name__, self.num_entries, self.dct)
    def copy(self):
        return self.__class__(self.num_entries, self.dct)
    def keys(self):
        return list(self.lst)
    def __getitem__(self, key):
        if key in self.dct:
            self.lst.remove(key)
        else:
            raise KeyError
        self.lst.append(key)
        return self.dct[key]
    def __setitem__(self, key, value):
        dct = self.dct
        lst = self.lst
        if key in dct:
            lst.remove(key)
        dct[key] = value
        lst.append(key)
        if len(lst) > self.num_entries:
            del dct[lst.pop(0)]
    def __delitem__(self, key):
        self.dct.pop(key)
        self.lst.remove(key)

# This function is a workaround to deal with what's typically described as a
# problem with the web server closing a connection. This is problem
# experienced with www.arcgis.com (first encountered 12/13/2012). The problem
# and workaround is described here:
# http://bobrochel.blogspot.com/2010/11/bad-servers-chunked-encoding-and.html
def patch_http_response_read(func):
    def inner(*args):
        try:
            return func(*args)
        except httplib.IncompleteRead, e:
            return e.partial

    return inner
httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)
