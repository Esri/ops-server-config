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

import random

from math import sqrt
from portalpy import unpack

def group_item_stats(portal, sample_size=100):
    results = portal.groups(['id'])
    group_ids = unpack(results)
    group_ids_sample = random.sample(group_ids, min(sample_size, len(group_ids)))

    # Find the item counts (max of sample_size groups)
    item_counts = []
    for index, group_id in enumerate(group_ids_sample):
        if index > sample_size:
            break
        item_count = len(portal.search(['id'], 'group:' + group_id))
        item_counts.append(item_count)

    # Calculate and return statistics
    if len(item_counts):
        mean = sum(item_counts) / len(item_counts)
        stdv = _stdv(item_counts, mean)
        return min(item_counts), mean, max(item_counts), stdv
    return 0, 0, 0, 0

def group_member_stats(portal, sample_size=100):
    results = portal.groups(['id'])
    group_ids = unpack(results)
    group_ids_sample = random.sample(group_ids, min(sample_size, len(group_ids)))

    # Find the member counts (max of sample_size groups)
    member_counts = []
    for index, group_id in enumerate(group_ids_sample):
        if index > sample_size:
            break
        group_members = portal.group_members(group_id)
        member_count = len(group_members['admins']) + len(group_members['users'])
        member_counts.append(member_count)

    # Calculate and return statistics
    if len(member_counts):
        mean = sum(member_counts) / len(member_counts)
        stdv = _stdv(member_counts, mean)
        return min(member_counts), mean, max(member_counts), stdv
    return 0, 0, 0, 0

def _stdv(values, mean):
    stdv = 0
    for value in values:
        stdv += (value - mean)**2
    stdv = sqrt(stdv / float(len(values) - 1))
    stdv = round(stdv, 2)
    return stdv

