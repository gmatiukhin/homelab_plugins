from enum import StrEnum


class HostType(StrEnum):
    VM = "proxmox_virtual_environment_vm"
    CT = "proxmox_virtual_environment_container"
