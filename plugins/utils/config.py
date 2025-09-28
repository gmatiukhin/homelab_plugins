from dataclasses import dataclass, field
from ansible.errors import AnsibleParserError
import os


@dataclass(init=False)
class Config:
    project_paths: list[str] = field(default_factory=list)
    bridge_iface: str = ""
    search_child_modules: bool = True
    use_node_groups: bool = True
    group_overrides: dict[str, dict[str, str]] = field(default_factory=dict)
    host_overrides: dict[str, dict[str, str]] = field(default_factory=dict)
    exclude_hosts: list[str] = field(default_factory=list)
    exclude_groups: list[str] = field(default_factory=list)
    extra_groups: list[str] = field(default_factory=list)
    dns_only: bool = False
    domain: str = ""

    def __init__(self, cfg) -> None:
        project_paths = cfg.get("project_path", os.getcwd())

        self.project_paths = (
            project_paths if isinstance(project_paths, list) else [project_paths]
        )

        self.bridge_iface = cfg.get("bridge_iface")
        self.search_child_modules = cfg.get("search_child_modules", True)
        self.use_node_groups = cfg.get("use_per_node_groups", True)
        self.group_overrides = cfg.get("group_overrides", dict())
        self.host_overrides = cfg.get("host_overrides", dict())
        self.exclude_hosts = cfg.get("exclude_hosts", list())
        self.exclude_groups = cfg.get("exclude_groups", list())

        extra_groups = cfg.get("extra_group", list())

        self.extra_groups = (
            extra_groups if isinstance(extra_groups, list) else [extra_groups]
        )
        self.dns_only = cfg.get("dns_only", False)
        self.domain = cfg.get("domain", "")

        if self.dns_only and not self.domain:
            raise AnsibleParserError(
                "Option 'domain' is required when 'dns_only' is true"
            )
