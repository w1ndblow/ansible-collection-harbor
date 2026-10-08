#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Joshua Hügli <@joschi36>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: harbor_scan_all_schedule
author:
  - Joshua Hügli (@joschi36)
version_added: 0.1.0
short_description: Manages Harbor scan all schedule settings
description:
  - Update Harbor scan all schedule options over API.
options:
  schedule_cron:
    description:
    - Standard cron string.
    type: str
    required: true
  state:
    description:
    - Desired state of the scan all schedule.
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
- name: Configure Harbor scan all schedule
  w1ndblow.harbor.harbor_scan_all_schedule:
    api_url: https://localhost/api/v2.0
    api_username: admin
    api_password: Harbor12345
    schedule_cron: "0 0 0 * * *"
'''

import copy
import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.w1ndblow.harbor.plugins.module_utils.harbor_base import HarborBaseModule


class HarborScanAllScheduleModule(HarborBaseModule):
    def getSchedule(self):
        schedule_request = self.make_request(
            f'{self.api_url}/system/scanAll/schedule',
        )
        if schedule_request['status'] == 200 and \
                schedule_request['content-length'] == 0:
            return {}

        schedule = schedule_request['data']
        del schedule['schedule']['next_scheduled_time']
        return {
            'schedule': schedule['schedule']
        }

    def putSchedule(self, payload):
        put_schedule_request = self.make_request(
            f'{self.api_url}/system/scanAll/schedule',
            method='PUT',
            data=payload
        )
        if not put_schedule_request['status'] == 200:
            self.module.fail_json(
                msg=self.requestParse(put_schedule_request))

    def constructDesired(self, schedule_cron):
        return {
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

        desired = self.constructDesired(self.module.params['schedule_cron'])
        before = self.getSchedule()

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
                self.putSchedule(desired)

                after = self.getSchedule()

                self.result['changed'] = True
                self.result['diff'] = {
                    'before': json.dumps(before, indent=4),
                    'after': json.dumps(after, indent=4),
                }

        self.module.exit_json(**self.result)


def main():
    HarborScanAllScheduleModule()


if __name__ == '__main__':
    main()
