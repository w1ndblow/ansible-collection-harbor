#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Joshua Hügli <@joschi36>
# GNU General Public License v3.0+ (see COPYING or \
# https://www.gnu.org/licenses/gpl-3.0.txt)
import copy
import json
from ansible_collections.swisstxt.harbor.plugins.module_utils.harbor_base import HarborBaseModule
from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = '''
---
self.module: harbor_project
author:
  - Joshua Hügli (@joschi36)
version_added: ""
short_description: Manage Harbor project
description:
  - Create, update and delete Harbor Configuration over API.
options:
  #TODO
extends_documentation_fragment:
  - swisstxt.harbor.api
'''


class HarborProjectModule(HarborBaseModule):
    @property
    def argspec(self):
        argument_spec = copy.deepcopy(self.COMMON_ARG_SPEC)
        argument_spec.update(
            name=dict(type='str', required=True),

            public=dict(type='bool', required=False),
            auto_scan=dict(type='bool', required=False),
            content_trust=dict(type='bool', required=False),

            quota_gb=dict(type='int', required=False),

            cache_registry=dict(type='str', required=False),

            state=dict(default='present', choices=[
                'present',
                'absent'])
        )
        return argument_spec

    def __init__(self):
        self.module = AnsibleModule(
            argument_spec=self.argspec,
            supports_check_mode=True,
        )

        super().__init__()

        self.result = dict(
            changed=False
        )

        existing_project = self.getProjectByName(self.module.params['name'])
        module_state = self.module.params['state']

        if existing_project and module_state == 'absent' and not \
                self.module.check_mode:
            del_request = self.make_request(
                    f'{self.api_url}/projects'
                    f'/{existing_project["project_id"]}',
                    method='DELETE')
            if del_request['status'] == 200:
                self.result['changed'] = True
                self.module.exit_json(**self.result)
            else:
                self.module.fail_json(msg=self.requestParse(
                        del_request))

        project_desired_metadata = {}
        if self.module.params['auto_scan'] is not None:
            project_desired_metadata['auto_scan'] = str(
                self.module.params['auto_scan']).lower()
        if self.module.params['content_trust'] is not None:
            project_desired_metadata['enable_content_trust'] = str(
                self.module.params['content_trust']).lower()
        if self.module.params['public'] is not None:
            project_desired_metadata['public'] = str(
                self.module.params['public']).lower()

        if existing_project:
            # Handle Quota
            if self.module.params['quota_gb'] is not None:
                quota_request = self.make_request(
                    f'{self.api_url}/quotas?reference_id'
                    f"={existing_project['project_id']}",
                    method='GET',
                )
                quota = quota_request['data'][0]
                actual_quota_size = quota['hard']['storage']
                desired_quota_size = self.quotaBits(
                            self.module.params['quota_gb'])
                if actual_quota_size != desired_quota_size:
                    quota_put_request = self.make_request(
                        f"{self.api_url}/quotas/{quota['id']}",
                        method='PUT',
                        data=json.dumps({
                            'hard': {
                                'storage': desired_quota_size
                             }}),
                    )
                    if quota_put_request['status'] == 200:
                        self.result['changed'] = True
                    elif quota_put_request['status'] == 400:
                        self.module.fail_json(
                            msg='Illegal format of quota update request..',
                            **self.result)
                    elif quota_put_request['status'] == 401:
                        self.module.fail_json(
                            msg='User need to log in first.', **self.result)
                    elif quota_put_request['status'] == 403:
                        self.module.fail_json(
                            msg='User does not have permission of admin role.',
                            **self.result)
                    elif quota_put_request['status'] == 500:
                        self.module.fail_json(
                            msg='Unexpected internal errors.',
                            **self.result)
                    else:
                        self.module.fail_json(
                            msg=f"""
                        Unknown HTTP status code: {quota_put_request['status']}
                        Body: {quota_put_request.text}
                        """)

            # Check & "calculate" desired configuration
            self.result['project'] = copy.deepcopy(existing_project)
            after_calculated = copy.deepcopy(existing_project)
            after_calculated['metadata'].update(project_desired_metadata)

            if existing_project == after_calculated:
                self.module.exit_json(**self.result)

            if self.module.check_mode:
                self.result['changed'] = True
                self.result['diff'] = {
                    'before': json.dumps(existing_project, indent=4),
                    'after': json.dumps(after_calculated, indent=4),
                }

            else:
                set_request = self.make_request(
                    f'{self.api_url}/projects'
                    f'/{existing_project["project_id"]}',
                    method='PUT',
                    data={
                        'metadata': project_desired_metadata
                    },
                )

                if not set_request['status'] == 200:
                    self.module.fail_json(
                        msg=self.requestParse(set_request), **self.result)

                after_request = self.make_request(
                    f'{self.api_url}/projects/'
                    f'{existing_project["project_id"]}',
                )
                self.result['project'] = copy.deepcopy(after_request)
                if existing_project != after_request:
                    self.result['changed'] = True
                    self.result['diff'] = {
                        'before': json.dumps(existing_project, indent=4),
                        'after': json.dumps(after_request, indent=4),
                    }

        else:
            if not self.module.check_mode:
                data = {
                    'project_name': self.module.params['name'],
                    'metadata': project_desired_metadata,
                }
                if self.module.params['quota_gb'] is not None:
                    data['storage_limit'] = self.quotaBits(
                        self.module.params['quota_gb'])

                if self.module.params['cache_registry'] is not None:
                    registry_request = self.make_request(
                        f'{self.api_url}/registries'
                        f'?q=name%3D{self.module.params['cache_registry']}',
                    )
                    try:
                        data['registry_id'] = registry_request[0]['id']
                    except (TypeError, ValueError):
                        self.module.fail_json(
                            msg='Registry not found',
                            **self.result)

                create_project_request = self.make_request(
                    self.api_url+'/projects',
                    method='POST',
                    data=data
                )
                if not create_project_request['status'] == 201:
                    self.module.fail_json(msg=self.requestParse(
                        create_project_request))

                after_request = self.make_request(
                    f'{self.api_url}/projects?page=1'
                    f'&page_size=1&name={self.module.params['name']}'
                )
                self.result['project'] = copy.deepcopy(after_request)
            self.result['changed'] = True

        self.module.exit_json(**self.result)


def main():
    HarborProjectModule()


if __name__ == '__main__':
    main()
