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

""" The portalpy provisioning package for working with the ArcGIS Online API."""

import copy
import csv
import json
import logging
import os
import shutil
import tempfile

from portalpy import TEXT_BASED_ITEM_TYPES, FILE_BASED_ITEM_TYPES, PortalError,\
                     unicode_to_ascii

ITEM_COPY_PROPERTIES = ['title', 'type', 'typekeywords', 'description', 'tags',
                        'snippet', 'extent', 'spatialreference', 'name',
                        'accessinformation', 'licenseinfo', 'culture', 'url', ]

GROUP_COPY_PROPERTIES = ['title', 'description', 'tags', 'snippet', 'phone',
                         'access', 'isInvitationOnly']

GROUP_EXTRACT_PROPERTIES = ['id'] + GROUP_COPY_PROPERTIES

clean_temp_files = True

_log = logging.getLogger(__name__)


def copy_items(items, source, target, target_user, target_folder=None,
               relationships=None, work_dir=tempfile.gettempdir()):
    """ Copy items from the source portal to the target portal."""
    if not target.is_logged_in():
        raise PortalError('Must be logged into target portal to copy')

    # Make sure the folder exists (or gets created) on the target portal
    target_folder_id = None
    if target_folder:
        target_folder_id = _get_or_create_folder(target, target_user,
                                                 target_folder)

    # Create a temporary folder to use for copying items.
    copy_dir = tempfile.mkdtemp(prefix='copy_items_',
                                dir=unicode_to_ascii(work_dir))
    try:
        # Copy the items
        copied_items = _copy_items(items, source, target, target_user,
                                   target_folder_id, None, copy_dir)

        # Copy the related items (if specified)
        if relationships:
            related_items = _copy_relationships(copied_items, source, target,
                                                target_user, target_folder_id, relationships,
                                                copy_dir)
            copied_items.update(related_items)

    finally:
        if clean_temp_files:
            shutil.rmtree(copy_dir)

    return copied_items

def copy_user_contents(source, source_user, target, target_user, ids=None,
                       relationships=None, work_dir=tempfile.gettempdir()):
    """ Copy a user's items from the source portal to the target portal."""
    if not source.is_logged_in():
        raise PortalError('Must be logged into source portal to copy a '\
                          + 'user\'s contents')
    if not target.is_logged_in():
        raise PortalError('Must be logged into target portal to copy a '\
                          + 'user\'s contents')

    # Get the user's content
    root_items, folders = source.user_contents(source_user)

    # Create a temporary folder to use for copying items.
    copy_dir = tempfile.mkdtemp(prefix='copy_user_content_',
                                dir=unicode_to_ascii(work_dir))
    try:
        # Copy the items in the root folder
        copied_items = _copy_items(root_items, source, target, target_user, None,
                                   ids, copy_dir)

        # Loop over all of the folders in the source portal, and get or create
        # the corresponding folder in the target portal
        for folder_id, folder_title, items in folders:
            target_folder_id = _get_or_create_folder(target, target_user, folder_title)
            copied_folder_items = _copy_items(items, source, target, target_user,
                                              target_folder_id, ids, copy_dir)
            copied_items.update(copied_folder_items)

        # Copy the related items (if specified)
        if relationships:
            related_items = _copy_relationships(copied_items, source, target,
                                                target_user, None, relationships, copy_dir)
            copied_items.update(related_items)

    finally:
        if clean_temp_files:
            shutil.rmtree(copy_dir)

    return copied_items

def _copy_items(items, source, target, target_user, target_folder_id, ids,
                copy_dir):
    copied_items = dict()
    for item in items:
        itemid = item['id']
        if not ids or itemid in ids:
            target_itemid = _copy_item(item, source, target, target_user,
                                       target_folder_id, None, copy_dir)[0]
            if target_itemid:
                copied_items[itemid] = target_itemid
    return copied_items

def _copy_item(item, source, target, target_user, target_folder_id,
               relationships, copy_dir):
    itemid = item['id']
    item_dir = os.path.join(copy_dir, itemid)
    os.makedirs(item_dir)
    try:

        # Create a new items with the subset of properties we want to
        # copy to the target portal
        target_item = _select_properties(item, ITEM_COPY_PROPERTIES)

        # If its a text-based item, then read the text and
        # add it to the request. Otherwise treat it as a
        # file-based item, download it and add to the request
        # as a file
        data_file = None
        if item['type'] in TEXT_BASED_ITEM_TYPES:
            text = source.item_data(itemid)
            if text and len(text) > 0:
                target_item['text'] = text
        elif item['type'] in FILE_BASED_ITEM_TYPES:
            data_file = source.item_datad(itemid, item_dir, item.get('name'))

        # Handle the thumbnail (if one exists)
        thumbnail_file = None
        if 'thumbnail' in item:
            thumbnail_file = source.item_thumbnaild(
                itemid, item_dir, unicode_to_ascii(item['thumbnail']))

        # Handle the metadata (if it exists)
        metadata_file = source.item_metadatad(itemid, item_dir)

        # Add the item to the target portal
        target_itemid = target.add_item(
            target_item, data_file, thumbnail_file, metadata_file,
            target_user, unicode_to_ascii(target_folder_id))
        if target_itemid:
            _log.info('Copied item ' + itemid + ' in source portal '
                      + 'to ' + target_itemid + ' in target portal')

            # We're returning a mapping of source id to target (dict).
            # But before we return, handle the related items (if specified)
            copied_items = dict({itemid: target_itemid})
            if relationships:
                related_items = _copy_relationships(copied_items, source,
                                                    target, target_user, target_folder_id,
                                                    relationships, copy_dir)
                copied_items.update(related_items)
            return target_itemid, copied_items

        else:
            _log.warning('Item ' + itemid + ' was not copied '\
                         + 'to target portal')

    # Just log IOErrors (includes HTTPErrors)
    except IOError as e:
        _log.warning('Item ' + itemid + ' was not copied to target portal ' \
                     + '(' + str(e) + ')')

    # Clean up the item directories as we go
    finally:
        if clean_temp_files:
            shutil.rmtree(item_dir)

    # Return an empty tuple, if for some reason the copy didn't happen
    return None, None

def _copy_relationships(items, source, target, target_user, target_folder_id,
                        relationships, work_dir):
    all_copied_rel_items = dict()
    for source_id, target_id in items.items():

        # Get the items related to source_id in the source portal
        related_items = source.related_items(source_id, relationships)
        for source_rel_item, rel_type, rel_direction in related_items:
            source_rel_id = source_rel_item['id']

            # See if it's already been copied to the target
            target_rel_id = items.get(source_rel_id)
            if not target_rel_id:

                # If not, then copy it to the target
                target_rel_id, copied_rel_items =\
                _copy_item(source_rel_item, source, target, target_user,
                           target_folder_id, relationships, work_dir)
                if copied_rel_items:
                    all_copied_rel_items.update(copied_rel_items)
                    items.update(copied_rel_items)

            # Add the relationship
            if target_rel_id:
                target.add_relationship(target_user, target_id, target_rel_id,
                                        rel_type)
            else:
                _log.warning('Unable to copy related item ' + source_rel_id\
                             + ' to target portal')

    return all_copied_rel_items

def _select_properties(properties, property_names):
    selected = dict()
    for property_name in property_names:
        property_value = properties.get(property_name)
        if property_value is not None:
            selected[property_name] = unicode_to_ascii(property_value)
    return selected

def _get_or_create_folder(portal, owner, folder_title):
    for folder in portal.folders(owner):
        if folder['title'] == folder_title:
            return folder['id']
    new_folder = portal.create_folder(owner, folder_title)
    if new_folder:
        return new_folder['id']

def copy_groups(groups, source, target, target_owner=None,
                work_dir=tempfile.gettempdir()):
    """ Copy group from the source portal to the target portal."""
    if not target.is_logged_in():
        raise PortalError('Must be logged into target portal to copy')

    # Create the temporary directory to use for copying groups (required
    # for thumbnails)
    copy_dir = tempfile.mkdtemp(prefix='copy_groups_', dir=work_dir)

    # Loop over each of the groups, copying one at a time
    copied_groups = dict()
    try:
        for group in groups:
            groupid = group['id']
            group_dir = os.path.join(copy_dir, groupid)
            os.makedirs(group_dir)

            # Create a new groups with the subset of properties we want to
            # copy to the target portal. Handle switching between org and
            # public access when going from an org in a multitenant portal
            # and a single tenant portal
            target_group = _select_properties(group, GROUP_COPY_PROPERTIES)
            if target_group['access'] == 'org'\
            and not target.is_multitenant():
                target_group['access'] = 'public'
            elif target_group['access'] == 'public'\
                 and not source.is_multitenant()\
                 and target.is_multitenant() and target.is_org():
                target_group['access'] = 'org'

            # Handle the thumbnail (if one exists)
            thumbnail_file = None
            if 'thumbnail' in group:
                thumbnail_file = source.group_thumbnaild(
                    groupid, group_dir, group['thumbnail'])

            # Create the group in the target portal
            target_groupid = target.create_group(target_group, thumbnail_file)

            # If the group was created successfully, handling reassigning
            # the group (if the target_owner is specified and it's
            # different from the logged in user of the target portal
            if target_groupid:
                target_username = target.logged_in_user()['username']
                if target_owner and (target_owner != target_username):
                    target.reassign_group(target_groupid, target_owner)
                    target.leave_group(target_groupid)
                copied_groups[groupid] = target_groupid
                _log.info('Copied group ' + groupid + ' in source portal '
                          + 'to ' + target_groupid + ' in target portal')
            else:
                _log.warning('Group ' + groupid + ' was not copied '\
                             + 'to target portal')

            # Clean up the group directories as we go
            if clean_temp_files:
                shutil.rmtree(group_dir)

    # Make sure we clean up the whole copy folder
    finally:
        if clean_temp_files:
            shutil.rmtree(copy_dir)

    return copied_groups

class JSONSerializer(object):
    """ A class for serializing users, groups, and items to JSON."""
    def __init__(self, data=True, metadata=True, thumbnails=True, indent=None):
        """ The JSONSerializer constructor. """
        self.data = data
        self.metadata = metadata
        self.thumbnails = thumbnails
        self.indent = indent

    def serialize_groups(self, groups, path, portal=None):
        """ Serialize groups to JSON. """
        base_dir = os.path.abspath(path)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        elif not os.path.isdir(base_dir):
            base_dir = os.path.dirname(base_dir)

        for group in groups:
            group_dir = os.path.join(base_dir, group['id'])
            if not os.path.exists(group_dir):
                os.makedirs(group_dir)

            # Write the thumbnail to a file (per the name specified in the item)
            if self.thumbnails:
                if not portal:
                    raise PortalError('The "portal" argument is required to  '\
                                      + 'download thumbnails')
                thumbnail = group.get('thumbnail')
                if thumbnail:
                    portal.item_thumbnaild(group['id'], group_dir, thumbnail)

            # Write the group itself to a file
            self.to_file(group, os.path.join(group_dir, 'group.json'))

    def serialize_items(self, items, path, portal=None):
        """ Serialize items to JSON. """
        base_dir = os.path.abspath(path)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        elif not os.path.isdir(base_dir):
            base_dir = os.path.dirname(base_dir)

        for item in items:
            item_dir = os.path.join(base_dir, item['id'])
            if not os.path.exists(item_dir):
                os.makedirs(item_dir)

            # Write the thumbnail to a file (per the name specified in the item)
            if self.thumbnails:
                if not portal:
                    raise PortalError('The "portal" argument is required to  '\
                                      + 'download thumbnails')
                thumbnail = item.get('thumbnail')
                if thumbnail:
                    portal.item_thumbnaild(item['id'], item_dir, thumbnail)

            # Handle the data
            if self.data:
                if not portal:
                    raise PortalError('The "portal" argument is required to  '\
                                      + 'download data')
                if item['type'] in TEXT_BASED_ITEM_TYPES:
                    text = portal.item_data(item['id'])
                    if text and len(text) > 0:
                        item['text'] = text
                elif item['type'] in FILE_BASED_ITEM_TYPES:
                    data_dir = os.path.join(item_dir, 'data')
                    if not os.path.exists(data_dir):
                        os.makedirs(data_dir)
                    portal.item_datad(item['id'], data_dir, item.get('name'))

            # Write the metadata to a file
            if self.metadata:
                if not portal:
                    raise PortalError('The "portal" argument is required to  '\
                                      + 'download metadata')
                portal.item_metadatad(item['id'], item_dir)

            # Write the item itself to a file (do this at the end, as the data
            # will get writen to the item if the item type is text)
            self.to_file(item, os.path.join(item_dir, 'item.json'))

    def to_file(self, data, path):
        with open(path, 'w') as outfile:
            json.dump(data, outfile, indent=self.indent)

class JSONDeserializer(object):
    """ A class for deserializing users, groups, and items from JSON."""
    def deserialize_groups(self, path):
        """ Deserialize groups from JSON. """
        groups = []
        group_reader = csv.DictReader(open(path, "rb"))
        for group in group_reader:
            groups.append(group)
        return groups

    def deserialize_items(self, path):
        """ Deserialize items from JSON. """
        items = []

        base_dir = os.path.abspath(path)
        if not os.path.exists(base_dir):
            _log.warn('Path being deserialized doesn\'t exist: ' + base_dir)
            return
        item_dirs = os.listdir(path)
        for item_dir in item_dirs:
            item_path = os.path.join(base_dir, item_dir, 'item.json')
            item = self.from_file(item_path)

            thumbnail_path = None
            thumbnail = item.get('thumbnail')
            if thumbnail:
                thumbnail_filename = os.path.basename(thumbnail)
                thumbnail_path = os.path.join(base_dir, item_dir, thumbnail_filename)

            data_path = None
            data_dir = os.path.join(base_dir, item_dir, 'data')
            
            if os.path.exists(data_dir):
                data_filename = item.get('name')
                if not data_filename:
                    data_filename = 'data'
                data_path = os.path.join(data_dir, data_filename)

            metadata_path = os.path.join(base_dir, item_dir, 'metadata.xml')
            if not os.path.exists(metadata_path):
                metadata_path = None

            items.append((item, thumbnail_path, data_path, metadata_path))

        return items

    def deserialize_item(self, path):
        """ Deserialize an item from JSON. """

        if not os.path.exists(path):
            _log.warn('Path being deserialized doesn\'t exist: ' + path)
            return
        
        item_path = os.path.join(path, 'item.json')
        item = self.from_file(item_path)

        thumbnail_path = None
        thumbnail = item.get('thumbnail')
        if thumbnail:
            thumbnail_filename = os.path.basename(thumbnail)
            thumbnail_path = os.path.join(path, thumbnail_filename)

        data_path = None
        data_dir = os.path.join(path, 'data')
        
        if os.path.exists(data_dir):
            data_filename = item.get('name')
            if not data_filename:
                data_filename = 'data'
            data_path = os.path.join(data_dir, data_filename)

        metadata_path = os.path.join(path, 'metadata.xml')
        if not os.path.exists(metadata_path):
            metadata_path = None

        return (item, thumbnail_path, data_path, metadata_path)

    def from_file(self, path):
        with open(path, 'r') as infile:
            return json.load(infile)

class CSVSerializer(object):
    """ A class for serializing users, groups, and items to CSV."""
    def __init__(self, data=True, metadata=True, thumbnails=True):
        """ The CSVSerializer constructor. """
        self.data = data
        self.metadata = metadata
        self.thumbnails = thumbnails

    def serialize_groups(self, groups, path, portal=None):
        """ Serialize groups to CSV. """
        groups_copy = copy.deepcopy(groups)
        field_names = GROUP_EXTRACT_PROPERTIES

        if self.thumbnails:
            if not portal:
                raise PortalError('The "portal" argument is required to  '\
                                  + 'download thumbnails')
            field_names.append('thumbnail')
            base_dir = os.path.dirname(path)
            for i, group in enumerate(groups):
                if 'thumbnail' in group:
                    group_dir = os.path.join(base_dir, group['id'])
                    thumbnail_path = portal.group_thumbnaild(
                        group['id'], group_dir, group['thumbnail'])
                    groups_copy[i]['thumbnail'] = os.path.relpath(
                        thumbnail_path, base_dir)

        group_writer = csv.DictWriter(open(path, "wb"), field_names)
        group_writer.writeheader()
        group_writer.writerows(groups_copy)

class CSVDeserializer(object):
    """ A class for deserializing users, groups and items from CSV."""
    def deserialize_groups(self, path):
        """ Deerialize groups from CSV. """
        groups = []
        if not os.path.isfile(path):
            raise PortalError('Specific path is not a file: ' + path)
        group_reader = csv.DictReader(open(path, "rb"))
        for group in group_reader:
            groups.append(group)
        return groups

    def deserialize_users(self, path):
        """ Deserialize users from CSV. """
        users = []
        if not os.path.isfile(path):
            raise PortalError('Specific path is not a file: ' + path)
        user_reader = csv.DictReader(open(path, "rb"))
        for user in user_reader:
            users.append(user)
        return users

_known_serializers = {'csv': CSVSerializer, 'json': JSONSerializer}
_known_deserializers = {'csv': CSVDeserializer, 'json': JSONDeserializer}

def _select_deserializer(f, cls, **kw):
    if not cls:
        cls = _known_deserializers.get(f)
    if not cls:
        raise PortalError('Unsupported format \'' + f + '\' for deserialization')
    return cls(**kw)

def _select_serializer(f, cls, **kw):
    if not cls:
        cls = _known_serializers.get(f)
    if not cls:
        raise PortalError('Unsupported format \'' + f + '\' for serialization')
    return cls(**kw)

def load_users(portal, path, f='json', cls=None, **kw):
    """ Load users stored on disk into the portal. """
    if portal.is_multitenant():
        raise PortalError('Loading users into a multi-tenant portal is not '
                          + 'supported at this time')

    # Deserialize the users, and then loop over them one at a time to
    # add them to the portal
    deserializer = _select_deserializer(f, cls, **kw)
    users = deserializer.deserialize_users(path)
    for user in users:

        # Remove any properties that have no entry
        for property in list(user.keys()):
            if user[property] is None:
                del user[property]

        # Signup users in the portal using the signup operation
        portal.signup(user['username'], user['password'],
                      user['fullname'], user.get('email'))

    return users

def load_groups(portal, path, f='json', cls=None, **kw):
    """ Load groups stored on disk into the portal. """
    groups, source_ids = [], []

    # Deserialize the groups, and then loop over them one at a time to
    # add them to the portal
    deserializer = _select_deserializer(f, cls, **kw)
    dgroups = deserializer.deserialize_groups(path)
    for dgroup in dgroups:

        # Pop out some important group properties, which shouldn't be included
        # in the group dict passed to the create_group function
        source_id = dgroup.pop('id', None)
        thumbnail = dgroup.pop('thumbnail', None)
        owner = dgroup.pop('owner', portal.logged_in_user()['username'])

        # Remove any properties that have no entry
        for property in list(dgroup.keys()):
            if dgroup[property] is None:
                del dgroup[property]

        # Create the group, returns the group id in portal
        #
        # TODO Consider duplicates (any case for updating)
        id = portal.create_group(dgroup, thumbnail)

        # If an ID was returned, add results to return objects
        if id:
            group = dict(id=id, owner=owner, **dgroup)
            groups.append(group)
            source_ids.append(source_id)

    return groups, source_ids

def load_items(portal, path, f='json', cls=None, **kw):
    """ Load items stored on disk into the portal. """
    items, source_ids = [], []

    # Deserialize the items, and then loop over them one at a time to
    # add them to the portal
    deserializer = _select_deserializer(f, cls, **kw)
    ditems = deserializer.deserialize_items(path)
    for ditem_tuple in ditems:
        ditem = ditem_tuple[0]
        thumbnail = ditem_tuple[1]
        data = ditem_tuple[2]
        metadata = ditem_tuple[3]

        # Pop out some important item properties, which shouldn't be included
        # in the item dict passed to the add_item function
        source_id = ditem.pop('id', None)
        ditem.pop('owner')
        ditem.pop('thumbnail')

        # Remove any properties that have no entry
        for property in list(ditem.keys()):
            if ditem[property] is None:
                del ditem[property]

        # Add the item, returns the item id in portal
        # TODO Consider duplicates (any case for updating)
        id = portal.add_item(ditem, data, thumbnail, metadata)

        # If an ID was returned, add results to return objects
        if id:
            item = dict(id=id, owner=portal.logged_in_user()['username'], **ditem)
            items.append(item)
            source_ids.append(source_id)

    return items, source_ids

def load_item(portal, path, overwrite_id=None, f='json', cls=None, **kw):
    """ Load item stored on disk into the portal.
        Pass existing item id (overwrite_id) if updating item;
        otherwise item is added.
    """

    # Deserialize the item, and add the item
    # or update an existing item
    deserializer = _select_deserializer(f, cls, **kw)
    ditem_tuple = deserializer.deserialize_item(path)
    
    ditem = ditem_tuple[0]
    thumbnail = ditem_tuple[1]
    data = ditem_tuple[2]
    metadata = ditem_tuple[3]

    # Pop out some important item properties, which shouldn't be included
    # in the item dict passed to the add_item function
    source_id = ditem.pop('id', None)
    ditem.pop('owner')
    ditem.pop('thumbnail')

    # Remove any properties that have no entry
    for property in list(ditem.keys()):
        if ditem[property] is None:
            del ditem[property]

    # Add/Update the item, returns the item id in portal
    if not overwrite_id:
        id = portal.add_item(ditem, data, thumbnail, metadata)
    else:
        portal.update_item(overwrite_id, ditem, data, metadata, thumbnail)
        id = overwrite_id

    # If an ID was returned, add results to return objects
    if id:
        item = dict(id=id, owner=portal.logged_in_user()['username'], **ditem)

    return item, source_id


def save_groups(portal, groups, path, f='json', cls=None, **kw):
    """ Save groups in the portal to disk. """
    serializer = _select_serializer(f, cls, **kw)
    serializer.serialize_groups(groups, path, portal)

def save_items(portal, items, path, f='json', cls=None, **kw):
    """ Save items in the portal to disk. """
    serializer = _select_serializer(f, cls, **kw)
    serializer.serialize_items(items, path, portal)
