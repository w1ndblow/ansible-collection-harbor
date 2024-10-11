# Harbor Collection
contain modules for config harbor instance

## Tested with Ansible

2.16.3

## External requirements



### Supported connections
all

## Included content

* harbor_config
* harbor_garbase_collection
* harbor_project_member
* harbor_project
* harbor_registry

## Using this collection



`ansible-galaxy  collection install  git+https://github.com/w1ndblow/ansible-collection-harbor.git,refactor --upgrade`



in role

```yaml
---
- name: test ansible module
  hosts: localhost
  tasks:
    - name: Create project
      swisstxt.harbor.harbor_project:
        api_password: Harbor12345
        api_url: http://localhost:8080/api/v2.0
        api_username: admin
        name: hello
        state: absent

```



## Contributing to this collection




## Release notes



## Roadmap

* add labels to repository 

## More information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Collections Checklist](https://github.com/ansible-collections/overview/blob/master/collection_requirements.rst)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
- [The Bullhorn (the Ansible Contributor newsletter)](https://us19.campaign-archive.com/home/?u=56d874e027110e35dea0e03c1&id=d6635f5420)
- [Changes impacting Contributors](https://github.com/ansible-collections/overview/issues/45)

## Licensing

GNU General Public License v3.0 or later.

See [LICENSE](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
