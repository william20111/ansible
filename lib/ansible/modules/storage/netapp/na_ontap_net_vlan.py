#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: na_ontap_net_vlan
short_description: Manage NetApp Ontap network vlan
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.6'
author: Chris Archibald (carchi@netapp.com), Kevin Hutton (khutton@netapp.com)
description:
- Create or Delete a network vlan
options:
  state:
    description:
    - Whether the specified network vlan should exist or not
    choices: ['present', 'absent']
    default: present
  parent_interface:
    description:
    - The interface that hosts the vlan interface.
    required: true
  vlanid:
    description:
    - The vlan id. Ranges from 1 to 4094.
    required: true
  node:
    description:
    - Node name of vlan interface.
  interface_name:
    description:
    - Name of vlan interface. The name must be of the format <parent-inteface>-<vlanid>
  gvrp_enabled:
    type: bool
    description:
    - GVRP is deprecated and this attribute is ignored in cluster mode.
'''

EXAMPLES = """
    - name: create vlan
      na_ontap_net_vlan:
        state=present
        vlanid=13
        node={{ vlan node }}
        parent_interface={{ vlan parent interface name }}
        username={{ netapp_username }}
        password={{ netapp_password }}
        hostname={{ netapp_hostname }}
"""

RETURN = """

"""

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapVlan(object):
    """
    Created, and destorys Net Vlans's
    """
    def __init__(self):
        """
        Initializes the NetAppOntapVlan function
        """
        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            parent_interface=dict(required=True, type='str'),
            vlanid=dict(required=True, type='str'),
            node=dict(required=True, type='str'),
            interface_name=dict(required=False, type='str'),
            gvrp_enabled=dict(required=False, type='bool', default=False),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.parent_interface = p['parent_interface']
        self.vlanid = p['vlanid']
        self.node = p['node']
        self.interface_name = p['interface_name']
        self.gvrp_enabled = p['gvrp_enabled']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module)
        return

    def create_vlan(self):
        """
        Creates a new vlan
        """
        vlan_obj = netapp_utils.zapi.NaElement("net-vlan-create")
        vlan_info = self.create_vlan_info()

        vlan_obj.add_child_elem(vlan_info)
        self.server.invoke_successfully(vlan_obj, True)

    def delete_vlan(self):
        """
        Deletes a vland
        """
        vlan_obj = netapp_utils.zapi.NaElement("net-vlan-delete")
        vlan_info = self.create_vlan_info()

        vlan_obj.add_child_elem(vlan_info)
        self.server.invoke_successfully(vlan_obj, True)

    def does_vlan_exist(self):
        """
        Checks to see if a vlan already exists or not
        :return: Returns True if the vlan exists, false if it dosn't
        """
        vlan_obj = netapp_utils.zapi.NaElement("net-vlan-get")
        vlan_obj.add_new_child("interface-name", self.parent_interface + "-" + self.vlanid)
        vlan_obj.add_new_child("node", self.node)
        try:
            result = self.server.invoke_successfully(vlan_obj, True)
            result.get_child_by_name("attributes").get_child_by_name("vlan-info").get_child_by_name("interface-name")
        except netapp_utils.zapi.NaApiError:
            return False
        return True

    def create_vlan_info(self):
        """
        Create a vlan_info object to be used in a create/delete
        :return:
        """
        vlan_info = netapp_utils.zapi.NaElement("vlan-info")

        #  set up the vlan_info object:
        vlan_info.add_new_child("parent-interface", self.parent_interface)
        vlan_info.add_new_child("vlanid", self.vlanid)
        #  add the optional line if they exist.
        if self.node:
            vlan_info.add_new_child("node", self.node)
        if self.interface_name:
            vlan_info.add_new_child("interface-name", self.interface_name)
        if self.gvrp_enabled:
            vlan_info.add_new_child("gvrp-enabled", 'true')
        else:
            vlan_info.add_new_child("gvrp-enabled", 'false')
        return vlan_info

    def apply(self):
        """
        check the option in the playbook to see what needs to be done
        :return:
        """
        changed = False
        result = None
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event("na_ontap_net_vlan", cserver)
        existing_vlan = self.does_vlan_exist()
        if existing_vlan:
            if self.state == 'absent':  # delete
                changed = True
        else:
            if self.state == 'present':  # create
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    self.create_vlan()
                elif self.state == 'absent':
                    self.delete_vlan()
        self.module.exit_json(changed=changed, meta=result)


def main():
    """
    Creates the NetApp Ontap vlan object, and runs the correct play task.
    """
    v = NetAppOntapVlan()
    v.apply()


if __name__ == '__main__':
    main()
