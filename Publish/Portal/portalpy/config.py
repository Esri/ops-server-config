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

import logging

from portalpy import unpack, PortalError

_log = logging.getLogger(__name__)

def configure_portal(portal, name=None, desc=None):
    props = dict()
    if name:
        props['name'] = name
    if desc:
        props['description'] = desc
    if props:
        portal.update_properties(props)

def create_basemap_gallery_group(portal, title, desc=None, snippet=None,
                                 tags='Basemap', phone=None, access='org',
                                 invitation_only=True, thumbnail=None,
                                 copy=True, copy_filter=None):

    # If it's a single tenant portal change 'org' access to 'public' access
    if not portal.is_multitenant() and access == 'org':
        access = 'public'

    # Prepare the group object
    group = { 'title': title, 'tags': tags, 'access': access,
              'isinvitationonly': invitation_only }
    if desc:
        group['description'] = desc
    if snippet:
        group['snippet'] = snippet
    if phone:
        group['phone'] = phone

    # Create the group
    group_id = portal.create_group(group, thumbnail)
    if not group_id:
        raise PortalError('Unable to create basemap group: ' + title)

    # Share the contents of the current basemap group, if directed to do so
    if copy:
        old_group_id = _prop_to_group_id(portal, 'basemapGalleryGroupQuery')
        if old_group_id:
            item_query = 'group:' + old_group_id
            if copy_filter:
                item_query += ' ' + copy_filter
                item_ids = unpack(portal.search(['id'], item_query, scope='public'))
                for item_id in item_ids:
                    portal.share_item(item_id, [group_id])

    # Update the portal to use the new basemap gallery group
    portal.update_property('basemapGalleryGroupQuery', 'id:' + group_id)
    return group_id

def feature_groups(portal, group_ids, clear_existing=False):
    featured_groups = []
    group_ids = unpack(group_ids, 'id')

    # If we're not clearing all existing groups, get the current set of featured
    # groups and check to see which groups are already featured. If a group is
    # already featured, remove it from the list.
    if not clear_existing:
        featured_groups = portal.properties().get('featuredGroups')
        already_featured_ids = []
        if featured_groups:
            for featured_group in featured_groups:
                if featured_group['id'] in group_ids:
                    _log.info('Group ' + featured_group['id'] + ' is already featured')
                    already_featured_ids.append(featured_group['id'])
        group_ids = [id for id in group_ids if id not in already_featured_ids]

    # Add the featured group entries to the array of featured groups (requires
    # fetching owner and title from the portal)
    for id in group_ids:
        group = portal.group(id)
        featured_groups.append({'owner': group['owner'], 'id': id,
                                'title': group['title']})

    # Update the featured groups property
    if featured_groups:
        portal.update_property('featuredGroups', featured_groups)

def feature_groups_query(portal, q, clear_existing=False):

    # Query for the groups we want to feature
    groups = portal.groups(['owner', 'id', 'title'], q)

    # If we're not clearing all existing groups, get the current set of featured
    # groups and add them to this list of groups to featyre.
    if not clear_existing:
        featured_groups = portal.properties().get('featuredGroups')
        if featured_groups:
            group_ids = [group['id'] for group in groups]
            for featured_group in featured_groups:
                if featured_group['id'] not in group_ids:
                    groups.append(featured_group)

    # Update the featured groups property
    if groups:
        portal.update_property('featuredGroups', groups)

def clear_featured_groups(portal):
    portal.update_property('featuredGroups', [])

def feature_items(portal, item_ids, gallery=True, home_page=True,
                  clear_existing=False):
    item_ids = unpack(item_ids, 'id')

    # Clear existing featured items (if directed to)
    if clear_existing:
        clear_featured_items(portal, gallery, home_page)

    # Retrieve the IDs of the gallery groups to share with
    group_ids = _get_featured_group_ids(portal, gallery, home_page)

    # If there are gallery groups to share with, share each item with the
    # gallery group(s)
    if group_ids:
        for item_id in item_ids:
            portal.share_item(item_id, group_ids)

def feature_items_query(portal, q, gallery=True, home_page=True,
                        clear_existing=False):

    # Query for the items to feature
    items = portal.search(['id'], q)
    item_ids = unpack(items)

    # Call the feature_items function using with the query results
    return feature_items(portal, item_ids, gallery, home_page, clear_existing)

def clear_featured_items(portal, gallery=True, home_page=True):

    # Retrieve the IDs of the gallery groups to unshare with
    group_ids = _get_featured_group_ids(portal, gallery, home_page)

    # If there are gallery group(s) to unshare with, get the list of items in
    # those group(s) and then unshare each item from the gallery group(s)
    if group_ids:
        item_query = ' OR '.join('group:"%s"' % id for id in group_ids)
        items = portal.search(['id'], item_query)
        item_ids = unpack(items)
        for item_id in item_ids:
            portal.share_item(item_id, group_ids)

def _get_featured_group_ids(portal, gallery, home_page):
    prop_names = []
    if gallery:
        prop_names.append('featuredItemsGroupQuery')
    if home_page:
        prop_names.append('homePageFeaturedContent')
    return _props_to_group_ids(portal, prop_names)

def _props_to_group_ids(portal, prop_names):
    group_ids = []
    for prop_name in prop_names:
        group_id = _prop_to_group_id(portal, prop_name)
        if group_id:
            group_ids.append(group_id)
    return group_ids

def _prop_to_group_id(portal, prop_name):
    group_query = portal.properties().get(prop_name)
    if group_query:
        groups = portal.groups(['id'], group_query, scope='public')
        if groups:
            return groups[0]['id']

