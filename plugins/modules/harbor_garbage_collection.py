#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Joshua Hügli <@joschi36>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: harbor_garbage_collection
author:
  - Aleksey Kuznetsov (@alekkuznetsov)
  - Joshua Hügli (@joschi36)
version_added: 0.1.0
short_description: Manages Harbor garbage collection settings
description:
  - Update Harbor garbage collection options over API.
options:
  schedule_cron:
    description:
    - Standard cron string.
    type: str
    required: true
  delete_untagged:
    description:
    - Whether to delete untagged artifacts.
    type: bool
    required: true
  state:
    description:
    - Desired state of the garbage collection settings.
    - Only V(present) is supported.
    type: str
    required: false
    default: present
    choices:
      - present
extends_documentation_fragment:
  - w1ndblow.harbor.api
'''

EXAMPLES = r'''
- name: Configure Harbor garbage collection
  w1ndblow.harbor.harbor_garbage_collection:
    api_url: https://localhost/api/v2.0
    api_username: admin
    api_password: Harbor12345
    schedule_cron: "0 0 0 * * *"
    delete_untagged: true
'''

import copy
import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.w1ndblow.harbor.plugins.module_utils.harbor_base import HarborBaseModule


class HarborGarbageCollectionModule(HarborBaseModule):
    def getGarbageCollection(self):
        gc_request = self.make_request(
            f'{self.api_url}/system/gc/schedule',
        )
        if gc_request['status'] == 200 and \
                gc_request['content-length'] == 0:
            return {}
        gc = gc_request['data']
        if gc.get('schedule', None):
            del gc['schedule']['next_scheduled_time']
        else:
            return {}
        if gc.get('job_parameters', None):
            job_parameter_string = json.loads(gc['job_parameters'])
        return {
            'parameters': {
                'delete_untagged': job_parameter_string.get(
                    'delete_untagged')
            },
            'schedule': gc['schedule']
        }

    def putGarbageCollection(self, payload):
        put_gc_request = self.make_request(
            f'{self.api_url}/system/gc/schedule',
            method='PUT',
            data=payload
        )
        if not put_gc_request['status'] == 200:
            self.module.fail_json(
                msg=self.requestParse(put_gc_request))

    def constructDesired(self, delete_untagged, schedule_cron):
        return {
            'parameters': {
                'delete_untagged': delete_untagged
            },
            'schedule': {
                'cron': schedule_cron,
                'type': 'Custom'
            }
        }

    @property
    def argspec(self):
        argument_spec = copy.deepcopy(self.COMMON_ARG_SPEC)
        argument_spec.update(
            schedule_cron=dict(type='str', required=True),
            delete_untagged=dict(type='bool', required=True),
            state=dict(default='present', choices=['present'])
        )
        return argument_spec

    def __init__(self):
        self.module = AnsibleModule(
            argument_spec=self.argspec,
            supports_check_mode=True
        )

        super().__init__()

        self.result = dict(
            changed=False
        )

        desired = self.constructDesired(
            self.module.params['delete_untagged'],
            self.module.params['schedule_cron'])
        before = self.getGarbageCollection()

        if desired != before:
            # Test change with checkmode
            if self.module.check_mode:
                self.result['changed'] = True
                self.result['diff'] = {
                    'before': json.dumps(before, indent=4),
                    'after': json.dumps(desired, indent=4),
                }

            # Apply change without checkmode
            else:
                self.putGarbageCollection(desired)

                after = self.getGarbageCollection()

                self.result['changed'] = True
                self.result['diff'] = {
                    'before': json.dumps(before, indent=4),
                    'after': json.dumps(after, indent=4),
                }

        self.module.exit_json(**self.result)


def main():
    HarborGarbageCollectionModule()


if __name__ == '__main__':
    main()
