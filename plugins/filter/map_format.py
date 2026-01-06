from ansible.errors import AnsibleFilterError


def map_format(value, pattern):
    """
    The same jinja2 filter plugin, but fixed for map application:
        range(3) | map('string') | map('gmatiukhin.homelab_plugins.map_format', 'foo.%s') -> foo.0, foo.1, foo.2
    """
    try:
        return str(pattern) % value
    except (TypeError, ValueError) as e:
        raise AnsibleFilterError(
            f"map_format failed: {str(e)} (value type: {type(value)}, pattern: {pattern})"
        ) from e


class FilterModule(object):
    """Custom Jinja2 filters for the collection."""

    def filters(self):
        return {
            "map_format": map_format,
        }
