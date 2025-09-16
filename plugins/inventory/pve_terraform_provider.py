import subprocess
import json

from ansible.config.manager import to_native
from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils.common import process

from ansible_collections.gmatiukhin.homelab_plugins.plugins.utils.config import Config
from ansible_collections.gmatiukhin.homelab_plugins.plugins.utils.types import HostType
import ansible_collections.gmatiukhin.homelab_plugins.plugins.utils.util as util

DOCUMENTATION = r"""
name: pve_terraform_provider
plugin_type: inventory
author:
  - Grigorii Matiukhin (@gmatiukhin)
short_description: Builds an inventory from Terraform state file using bpg/proxmox provider.
description:
  - Builds an inventory from specified state file.
  - To read state file command "terraform show" is used, thus requiring initialized working directory.
  - Does not support caching.
options:
  plugin:
    description:
      - The name of the Inventory Plugin.
      - This should always be C(gmatiukhin.homelab_plugins.pve_terraform_provider).
    required: true
    type: str
    choices: [ gmatiukhin.homelab_plugins.pve_terraform_provider ]
  project_path:
    description:
      - The path to the initialized Terraform directory with the .tfstate file.
      - If I(project_path) are not specified, Terraform will attempt to automatically find the state file in the current working directory.
      - Accepts a string or a list of paths for use with multiple Terraform projects.
    type: raw
  bridge_iface:
    description:
      - Bridge interface on the PVE host to which guests are connected.
      - Used to select the appropriate IP address.
    type: str
    required: true
  search_child_modules:
    description:
      - Whether to include hosts from Terraform child modules.
    type: bool
    default: true
  use_node_groups:
    description:
      - Whether to use PVE nodes as groups.
    type: bool
    default: true
  group_overrides:
    description:
      - Variable overrides for specific groups.
    type: raw
  host_overrides:
    description:
      - Variable overrides for specific hosts.
    type: raw
  exclude_hosts:
    description:
      - Don't add specific hosts to the inventory.
    type: raw
  exclude_groups:
    description:
      - Don't add hosts in specific groups to the inventory.
    type: raw
  extra_group:
    description:
      - Add all hosts to a specific group.
      - Can be excluded by I(exlclude_groups).
      - Accepts a string or a list of groups.
"""


class InventoryModule(BaseInventoryPlugin):
    NAME = "gmatiukhin.homelab_plugins.pve_terraform_provider"

    def __init__(self):
        super(InventoryModule, self).__init__()

        self.known_hosts = set()

    def parse(self, inventory, loader, path, cache=False):
        super(InventoryModule, self).parse(inventory, loader, path)

        cfg = self._read_config_data(path)
        cfg = Config(cfg)
        terraform_binary = process.get_bin_path("terraform", required=True)

        state_content = []

        for path in cfg.project_paths:
            try:
                state_json = json.loads(
                    subprocess.run(
                        [terraform_binary, "show", "--json"],
                        cwd=path,
                        check=True,
                        capture_output=True,
                    ).stdout.decode("utf-8")
                )
                values = util.extract_values_from_state(state_json)

                state_content.append(values)
            except ChildProcessError as e:
                raise AnsibleError(
                    "Error executing `terraform show`: %s" % to_native(e)
                )

        if state_content:
            self.create_inventory(inventory, state_content, cfg)

    def create_inventory(self, inventory, state_content, cfg: Config):
        for state in state_content:
            if state is None:
                continue
            resources = (
                state["root_module"]["resources"]
                if not cfg.search_child_modules
                else util.flatten_resources(state["root_module"])
            )

            for resource in resources:
                if resource["type"] == HostType.CT:
                    self._handle_container(inventory, resource, cfg)
                elif resource["type"] == HostType.VM:
                    self._handle_vm(inventory, resource, cfg)

    def _handle_container(self, inventory, ct, cfg: Config):
        values = ct["values"]
        # using the devices on the LAN side of the virtual router
        ni = next(
            filter(
                lambda x: x["bridge"] == cfg.bridge_iface,
                values["network_interface"],
            )
        )
        iface = ni["name"]
        ipv4 = values["ipv4"][iface]

        host = ct["name"]
        groups = values["tags"]
        node_name = values["node_name"]

        self._add(inventory, host, ipv4, groups, node_name, cfg, ct["type"])

    def _handle_vm(self, inventory, vm, cfg: Config):
        values = vm["values"]
        # using the devices on the LAN side of the virtual router
        ni = next(
            filter(
                lambda x: x["bridge"] == cfg.bridge_iface,
                values["network_device"],
            )
        )
        mac = ni["mac_address"]
        # grab the first appearance of the mac address in the full list
        idx = values["mac_addresses"].index(mac)
        # to then grab the corresponding iface
        # additionally, ifaces are all a list of one element
        ipv4 = values["ipv4_addresses"][idx][0]

        host = vm["name"]
        groups = values["tags"]
        node_name = values["node_name"]

        self._add(inventory, host, ipv4, groups, node_name, cfg, vm["type"])

    def _add(
        self,
        inventory,
        host,
        ipv4,
        groups,
        node_name,
        cfg: Config,
        host_type: str | HostType,
    ):
        groups = groups + cfg.extra_groups

        match host_type:
            case HostType.VM:
                groups.append("virtual_machines")
            case HostType.CT:
                groups.append("containers")

        if cfg.use_node_groups:
            self._add_group(inventory, node_name, cfg)

        for group in groups:
            self._add_group(inventory, group, cfg)
        self._add_host(inventory, host, groups, ipv4, cfg, host_type)

    def _add_group(self, inventory, group, cfg: Config):
        if group in cfg.exclude_groups:
            return

        inventory.add_group(group)

        for var, val in cfg.group_overrides.get(group, dict()).items():
            inventory.set_variable(group, var, val)

    def _add_host(
        self, inventory, host, groups, ipv4, cfg: Config, host_type: str | HostType
    ):
        if host in cfg.exclude_hosts:
            return

        if any([group in cfg.exclude_groups for group in groups]):
            return

        if host in self.known_hosts:
            raise AnsibleError("Found duplicate host: %s" % to_native(host))

        self.known_hosts.add(host)

        inventory.add_host(host)
        for group in groups:
            if group not in cfg.exclude_groups:
                inventory.add_child(group, host)
        inventory.set_variable(host, "ansible_host", ipv4)
        inventory.set_variable(host, "virtual_machine", host_type == HostType.VM)
        inventory.set_variable(host, "container", host_type == HostType.CT)

        for var, val in cfg.host_overrides.get(host, dict()).items():
            inventory.set_variable(host, var, val)
