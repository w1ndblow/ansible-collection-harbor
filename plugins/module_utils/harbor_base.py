# -*- coding: utf-8 -*-

# (c) 2021, Joshua Hügli <@joschi36>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import json

from ansible.module_utils.urls import fetch_url


class HarborBaseModule(object):
    COMMON_ARG_SPEC = dict(
        api_url=dict(type='str', required=True),
        api_username=dict(type='str', required=True),
        api_password=dict(type='str', required=True, no_log=True)
    )

    def __init__(self):
        self.api_url = self.module.params['api_url']
        self.auth = (
            self.module.params['api_username'],
            self.module.params['api_password']
        )
        self.module.params['url_username'] = self.module.params['api_username']
        self.module.params['url_password'] = self.module.params['api_password']

    def make_request(self, api_path, method='GET', data=None):
        response = {
            'status': None,
            'errors': None,
            'data': None,
            'content-length': 0
        }
        pass_string = '{}:{}'.format(
            self.module.params['api_username'],
            self.module.params['api_password']
        )
        encoded_str = base64.b64encode(
            pass_string.encode('utf-8')).decode('utf-8')
        headers = {
            'Authorization': 'Basic {}'.format(encoded_str),
            'Content-Type': 'application/json',
        }
        try:
            resp, info = fetch_url(
                self.module,
                url=api_path,
                method=method,
                headers=headers,
                data=json.dumps(data)
            )
            string_byte = resp.read()
            if string_byte:
                response['data'] = json.loads(string_byte.decode('utf-8'))
            response['status'] = info['status']
            response['errors'] = info.get('body', None)
            response['content-length'] = int(info.get('content-length', 0))
        except json.JSONDecodeError:
            self.module.fail_json(
                msg=f"""
                    Not json {string_byte} in response: {response}
                    """)
        except Exception as e:
            response['errors'] = e
        return response

    def getProjectByName(self, name):
        # if project don't harbor response status 200
        # with json 'null' data
        try:
            r = self.make_request(
                api_path=f'{self.api_url}/projects?name={name}',
                method='GET')
            project_list = r['data'] if r['data'] else []
        except Exception:
            self.module.fail_json(msg='Project request failed', **self.result)
            return False

        if not len(project_list):
            return None

        for project in project_list:
            if project['name'] == name:
                return project

        return None

    def quotaBits(self, gigabytes):
        # Convert quota from user input (GiB) to api (bits)
        bits = -1 if gigabytes == -1 else gigabytes * (1024 ** 3)
        return bits

    def requestParse(self, request):
        try:
            if request['data']:
                message = 'HTTP status code: {0}\nMessage: {1}'.format(
                    request['status'],
                    request['data'].get('errors', [])[0].get('message', ''))
            else:
                message = \
                    'Do not get message'
        except ValueError:
            message = \
                'Unknown Response\n' \
                f"HTTP status code: {request['status']}\n" \
                f"Body: {request['data']}"
        return message


if __name__ == '__main__':
    pass
