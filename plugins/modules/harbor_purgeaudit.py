#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Joshua Hügli <@joschi36>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''
---
module: harbor_purgeaudit
author:
  - Joshua Hügli (@joschi36)
version_added: 0.1.0
short_description: Manages Harbor purge audit settings
description:
  - Update Harbor purge audit options over API.
options:
  schedule_cron:
    description:
    - Standard cron string.
    type: str
    required: true
  audit_retention_hour:
    description:
    - Number of hours to retain audit logs.
    type: int
    required: true
  included_operations:
    description:
    - Operations to include in the purge.
    type: list
    elements: str
    required: true
    choices:
    - create
    - delete
    - pull
  state:
    description:
    - Desired state of the purge audit settings.
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
- name: Configure Harbor purge audit schedule
  w1ndblow.harbor.harbor_purgeaudit:
    api_url: https://localhost/api/v2.0
    api_username: admin
    api_password: Harbor12345
    schedule_cron: "0 0 0 * * *"
    audit_retention_hour: 168
    included_operations:
    - create
    - delete
    - pull
'''

import copy
import json

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.w1ndblow.harbor.plugins.module_utils.harbor_base import HarborBaseModule


class HarborPurgeAuditModule(HarborBaseModule):
    def getPurgeAudit(self):
        purgeaudit_request = self.make_request(
            f'{self.api_url}/system/purgeaudit/schedule',
        )
        if purgeaudit_request['status'] == 200 and \
                purgeaudit_request['content-length'] == 0:
            return {}

        purgeaudit = purgeaudit_request['data']
        del purgeaudit['schedule']['next_scheduled_time']
        job_parameters = json.loads(purgeaudit['job_parameters'])

        return {
            'parameters': {
                'audit_retention_hour': job_parameters['audit_retention_hour'],
                'dry_run': False,
                'include_operations': job_parameters['include_operations']
            },
            'schedule': purgeaudit['schedule']
        }

    def putPurgeAudit(self, payload):
        put_purgeaudit_request = self.make_request(
            f'{self.api_url}/system/purgeaudit/schedule',
            method='PUT',
            data=payload
        )
        if not put_purgeaudit_request['status'] == 200:
            self.module.fail_json(
                msg=self.requestParse(put_purgeaudit_request))

    def constructDesired(self, audit_retention_hour, include_operations,
                         schedule_cron):
        return {
            'parameters': {
                'audit_retention_hour': audit_retention_hour,
                'dry_run': False,
                'include_operations': ','.join(include_operations)
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
            audit_retention_hour=dict(type='int', required=True),
            included_operations=dict(
                type='list',
                elements='str',
                required=True,
                choices=['create', 'delete', 'pull']),
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
            self.module.params['audit_retention_hour'],
            self.module.params['included_operations'],
            self.module.params['schedule_cron'])
        before = self.getPurgeAudit()

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
                self.putPurgeAudit(desired)

                after = self.getPurgeAudit()

                self.result['changed'] = True
                self.result['diff'] = {
                    'before': json.dumps(before, indent=4),
                    'after': json.dumps(after, indent=4),
                }

        self.module.exit_json(**self.result)


def main():
    HarborPurgeAuditModule()


if __name__ == '__main__':
    main()
