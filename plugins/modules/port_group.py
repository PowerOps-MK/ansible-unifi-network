#!/usr/bin/python

# (c) 2012, Elliott Foster <elliott@fourkitchens.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: port_group
short_description: Adds or removes a user from a MongoDB database
description:
    - Adds or removes a user from a MongoDB database.
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
  type:
    description:
      - The name of the user to add or remove.
    required: false
    type: str
  members:
    description:
      - The list of members like ["8443", "8080"]
    required: false
    type: list
    elements: str

author:
    - "Julien Thebault (@Lujeni)"
"""

EXAMPLES = r"""
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world
# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true
# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
"""

RETURN = r"""
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
"""

# Modules
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import Request

# Parameters
site = "default"
resource = "firewallgroup"
login_url = "https://localhost:8443/api/login"
api_url = f"https://localhost:8443/api/s/{site}/rest/{resource}"
username = "unifi"
password = "6VK8eK92ePP*dHR6"


# Functions
class FirewallGroup(object):
    def __init__(self, module):
        self._module = module
        self._authenticate()
        # self._get_resource()

    def _authenticate(self):
        """Authenticate to the REST API"""
        try:
            payload = {"username": username, "password": password}

            session = Request()  # pylint: disable=E0602
            session.post(
                url=login_url, validate_certs=False, data=self._module.jsonify(payload)
            )

            return session
        except BaseException:
            self._module.fail_json(msg="Authenication to API had failed")

    def _get_resource(self):
        """Get existing resources from the REST API"""
        try:
            # Authenticate to the REST API
            session = authenticate(self)

            resources = session.get(url=api_url, validate_certs=False)
            resources_dict = self._module.from_json(resources.read())["data"]

            for resource in resources_dict:
                if resource["name"] == self._module.params["name"]:
                    return f"{api_url}/{resource['_id']}"

        except BaseException as e:
            # self._module.fail_json(msg="Getting resources from API had failed")
            self._module.fail_json(msg=e)

    def present(self):
        """Apply config if not present"""
        try:
            # Initialize variables
            changed = False
            result = ""
            payload = {
                "name": self._module.params["name"],
                "group_type": self._module.params["type"],
                "group_members": self._module.params["members"],
            }

            # Authenticate to the REST API
            session = authenticate(self)

            # Put resource if exist, otherwise create
            existing_url = get_resource(self)
            if existing_url is not None:
                response = session.put(
                    url=existing_url,
                    validate_certs=False,
                    data=self._module.jsonify(payload),
                )
                changed = True
                result = response.read()
            else:
                response = session.post(
                    url=api_url,
                    validate_certs=False,
                    data=self._module.jsonify(payload),
                )
                changed = True
                result = response.read()

            return changed, result
        except BaseException:
            self._module.fail_json(msg="Creating of resource failed")

    def absent(self):
        """Remove config if not present"""
        try:
            # Initialize variables
            changed = False
            result = ""

            # Authenticate to the REST API
            session = authenticate(self)

            # Delete resource if exist
            existing_url = get_resource(self)
            if existing_url is not None:
                response = session.delete(url=existing_url, validate_certs=False)
                changed = True
                result = response.read()

            return changed, result
        except BaseException:
            self._module.fail_json(msg="Deleting of resource failed")


# Run basic Ansible function
def main():
    # AnsibleModule object with parameters for abstraction
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type="str", default="present", choices=["present", "absent"]),
            name=dict(type="str", required=True),
            type=dict(type="str", required=False),
            members=dict(type="list", elements="str", required=False),
        ),
        supports_check_mode=True,
        required_if=(("state", "present", ["type", "members"]),),
    )

    choice_map = {"present": present, "absent": absent}

    # if check mode, return the current state
    if module.check_mode:
        module.exit_json(changed=False)

    # Create Class instance
    firewall_group = FirewallGroup(module)

    # Run function based on the passed state
    # changed, result = choice_map.get(module.params["state"])(module)

    # Return message as output
    module.exit_json(changed=changed, meta=result)


if __name__ == "__main__":
    main()
