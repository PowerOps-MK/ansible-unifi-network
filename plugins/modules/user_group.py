#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2023, Mr PotatoHead <mrpotatohead@powerops.nl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: user_group
short_description: Adds or removes a usergroup to a Unifi Network.
description:
    - Adds or removes a usergroup to a Unifi Network via the REST API.
author:
  - Mr PotatoHead (@mrpotatohead)
version_added: "1.0.0"

options:
  state:
    description:
      - The name of the database to add/remove the user from.
    default: 'present'
    choices: ['present', 'absent']
    type: str
  name:
    description:
      - The name of the user to add or remove.
    required: true
    type: str
  qos_down:
    description:
      - The name of the user to add or remove.
    required: false
    type: int
  qos_up:
    description:
      - The list of members like ["8443", "8080"]
    required: false
    type: int
"""

EXAMPLES = r"""
- name: Test present usergroup
  unifi.network.user_group:
    state: present
    name: "API-UserGroup"
    qos_down: -1
    qos_up: -1

- name: Test absent usergroup
  unifi.network.user_group:
    state: absent
    name: "API-UserGroup"
"""

RETURN = r"""
changed:
    description: boolean if a resource is changed.
    type: bool
    returned: always
result:
    description: json parsed response from the server.
    type: str
    returned: always
"""

# Modules
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.unifi.network.plugins.module_utils.create_session import (
    authenticate,
)

# Parameters
site = "default"
resource = "usergroup"
api_url = f"https://localhost:8443/api/s/{site}/rest/{resource}"


# Functions
class UserGroup(object):
    def __init__(self, module):
        self._module = module
        self._resource = None
        self._session = authenticate(module)
        self.changed = False
        self.result = ""

        self._get_resource()

    def _get_resource(self):
        """Get existing resources from the REST API"""
        # try:
        resources = self._session.get(url=api_url, validate_certs=False)
        resources_dict = self._module.from_json(resources.read())["data"]

        for resource in resources_dict:
            if resource["name"] == self._module.params["name"]:
                self._resource = f"{api_url}/{resource['_id']}"

        # except BaseException:
        # self._module.fail_json(msg="Getting resources from API had failed")

    def absent(self):
        """Remove config if not present"""
        try:
            if self._resource is not None:
                response = self._session.delete(
                    url=self._resource,
                    validate_certs=False,
                )
                self.changed = True
                self.result = self._resource  # response.read()

            return self.changed, self.result
        except BaseException:
            self._module.fail_json(msg="Deleting of resource failed")

    def present(self):
        """Apply config if not present"""
        try:
            payload = {
                "name": self._module.params["name"],
                "group_type": self._module.params["qos_down"],
                "group_members": self._module.params["qos_up"],
            }

            if self._resource is not None:
                response = self._session.put(
                    url=self._resource,
                    validate_certs=False,
                    data=self._module.jsonify(payload),
                )
            else:
                response = self._session.post(
                    url=api_url,
                    validate_certs=False,
                    data=self._module.jsonify(payload),
                )

            self._changed = True
            self._result = response.read()
            return self._changed, self._result
        except BaseException:
            self._module.fail_json(msg="Failed to create the resource")


# Run basic Ansible function
def main():
    # AnsibleModule object with parameters for abstraction
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type="str", default="present", choices=["present", "absent"]),
            name=dict(type="str", required=True),
            qos_down=dict(type="int", required=False),
            qos_up=dict(type="int", required=False),
        ),
        supports_check_mode=True,
        required_if=(("state", "present", ["qos_down", "qos_up"]),),
    )

    # Create Class instance
    user_group = UserGroup(module)

    # Setup state mapping
    choice_map = {"present": user_group.present, "absent": user_group.absent}

    # If check mode, return the current state
    if module.check_mode:
        module.exit_json(changed=False)

    # Run function based on the passed state
    changed, result = choice_map.get(module.params["state"])()

    # Return message as output
    module.exit_json(changed=changed, meta=result)


if __name__ == "__main__":
    main()
