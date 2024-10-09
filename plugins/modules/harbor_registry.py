#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Joshua Hügli <@joschi36>
# GNU General Public License v3.0+ (see COPYING or \
# https://www.gnu.org/licenses/gpl-3.0.txt)

import copy
import json
from ansible.module_utils.basic import AnsibleModule
from module_utils.harbor_base import \
    HarborBaseModule

DOCUMENTATION = '''
---
module: harbor_registry
author:
  - Joshua Hügli (@joschi36)
version_added: ""
short_description: Manage Harbor registries
description:
  - Create, update and delete Harbor registries over API.
options:
  #TODO
extends_documentation_fragment:
  - swisstxt.harbor.api
'''


class HarborRegistryModule(HarborBaseModule):
    @property
    def argspec(self):
        argument_spec = copy.deepcopy(self.COMMON_ARG_SPEC)
        argument_spec.update(
            name=dict(type='str', required=True),
            type=dict(
                type='str',
                required=False,
                choices=[
                    'ali-acr',
                    'aws-ecr',
                    'azure-acr',
                    'docker-hub',
                    'docker-registry',
                    'gitlab',
                    'google-gcr',
                    'harbor',
                    'helm-hub',
                    'huawei-SWR',
                    'jfrog-artifactory',
                    'quay',
                    'tencent-tcr',
                    ]
            ),
            endpoint_url=dict(type='str', required=False),
            access_key=dict(type='str', required=False),
            access_secret=dict(type='str', required=False, no_log=True),
            insecure=dict(type='bool', required=False),

            state=dict(default='present', choices=[
                'present',
                'absent'])
        )
        return argument_spec

    def __init__(self):
        self.module = AnsibleModule(
            argument_spec=self.argspec,
            supports_check_mode=True,
            required_if=[
                ('state', 'present', ('type',
                                      'endpoint_url'))
            ],
        )

        super().__init__()

        self.result = dict(
            changed=False
        )

        existing_registry_request = self.make_request(
            f"{self.api_url}/registries?q=name%3D{self.module.params['name']}",
        )

        existing_registry = existing_registry_request['data']
        module_state = self.module.params['state']

        if existing_registry and module_state == 'absent':
            existing_registry = existing_registry[0]
            del_request = self.make_request(
                f'{self.api_url}/registries/{existing_registry["id"]}',
                method='DELETE',
                )
            if del_request['status'] == 200:
                self.result['changed'] = True
                self.module.exit_json(**self.result)
            else:
                self.module.fail_json(msg=self.requestParse(
                        del_request))

        desired_registry = {
            'name': self.module.params['name'],
            'credential': {}
        }
        if self.module.params['insecure'] is not None:
            desired_registry['insecure'] = self.module.params['insecure']
        if self.module.params['type'] is not None:
            desired_registry['type'] = self.module.params['type']
        if self.module.params['endpoint_url'] is not None:
            desired_registry['url'] = self.module.params['endpoint_url']
        if self.module.params['access_key'] is not None:
            desired_registry['credential']['access_key'] = self.module.params[
                'access_key']
            desired_registry['credential']['type'] = 'basic'
        if self.module.params['access_secret'] is not None:
            desired_registry['credential']['access_secret'] = \
                self.module.params['access_secret']
            desired_registry['credential']['type'] = 'basic'

        if existing_registry:
            existing_registry = existing_registry[0]

            # Check & "calculate" desired configuration
            self.result['registry'] = copy.deepcopy(existing_registry)
            after_calculated = copy.deepcopy(existing_registry)
            after_calculated.update(desired_registry)

            # Ignore secret as it isn't returned with API
            after_calculated['credential'].pop('access_secret', None)
            after_calculated.pop('update_time', None)
            existing_registry['credential'].pop('access_secret', None)
            existing_registry.pop('update_time', None)

            if existing_registry == after_calculated:
                self.module.exit_json(**self.result)

            if self.module.check_mode:
                self.result['changed'] = True
                self.result['diff'] = {
                    'before': json.dumps(existing_registry, indent=4),
                    'after': json.dumps(after_calculated, indent=4),
                }

            else:
                set_request = self.make_request(
                    f'{self.api_url}/registries/{existing_registry["id"]}',
                    method='PUT',
                    data=desired_registry,
                )

                if not set_request['status'] == 200:
                    self.module.fail_json(msg=self.requestParse(set_request))

                after_request = self.make_request(
                    f'{self.api_url}/registries/{existing_registry["id"]}',
                )
                after = after_request['data']
                after['credential'].pop('access_secret', None)
                after.pop('update_time', None)
                self.result['registry'] = copy.deepcopy(after)
                if existing_registry != after:
                    self.result['changed'] = True
                    self.result['diff'] = {
                        'before': json.dumps(existing_registry, indent=4),
                        'after': json.dumps(after, indent=4),
                    }

        else:
            if not self.module.check_mode:
                create_project_request = self.make_request(
                    self.api_url+'/registries',
                    method='POST',
                    data=desired_registry
                )
                if not create_project_request['status'] == 201:
                    self.module.fail_json(msg=self.requestParse(
                        create_project_request))

                after_request = self.make_request(
                    f"{self.api_url}/registries?q=name%3D{self.module.params[
                        'name']}",
                )
                self.result['registry'] = copy.deepcopy(after_request['data'])

            self.result['changed'] = True

        self.module.exit_json(**self.result)


def main():
    HarborRegistryModule()


if __name__ == '__main__':
    main()
