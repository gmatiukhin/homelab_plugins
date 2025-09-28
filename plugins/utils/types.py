from enum import StrEnum


class HostType(StrEnum):
    QEMU = "proxmox_virtual_environment_vm"
    LXC = "proxmox_virtual_environment_container"
