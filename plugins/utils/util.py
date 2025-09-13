import shutil


def flatten_resources(root_module):
    return root_module["resources"] + sum(
        [
            flatten_resources(child)
            for child in root_module.get("child_modules", list())
        ],
        start=[],
    )


def extract_values_from_state(state_json):

    # when not initialized, this doesn't return anything useful, but also not an error
    # this is not an exceptional case in our usage, so no warning
    if len(state_json.keys()) == 1 and "format_version" in state_json:
        return None

    # handle the difference between showing a state and a plan by preprocessing the differences
    if "planned_values" in state_json:
        result = {
            key: value
            for key, value in state_json.items()
            if key
            in [
                "format_version",
                "terraform_version",
                "planned_values",
            ]
        }
        # renaming planned_values to values for filtering
        result["values"] = result.pop("planned_values")
    else:
        # no changes necessary
        result = state_json

    return result["values"]


def validate_bin_path(bin_path: str) -> None:
    if not shutil.which(bin_path):
        raise RuntimeError(
            "Path for Terraform binary '{0}' doesn't exist on this host - check the path and try again please.".format(
                bin_path
            )
        )
