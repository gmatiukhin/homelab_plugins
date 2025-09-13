import dataclasses
import os


@dataclasses.dataclass(init=False)
class Config:
    """foobar"""

    project_paths: list = []
    search_child_modules: bool = True
    use_node_groups: bool = True
    group_overrides: dict = {}
    host_overrides: dict = {}

    def __init__(self, cfg) -> None:
        project_paths = cfg.get("project_path", os.getcwd())

        self.project_paths = (
            project_paths if isinstance(project_paths, list) else [project_paths]
        )

        self.search_child_modules = cfg.get("search_child_modules", True)
        self.use_node_groups = cfg.get("use_per_node_groups", True)
        self.group_overrides = cfg.get("group_overrides", dict())
        self.host_overrides = cfg.get("host_overrides", dict())
