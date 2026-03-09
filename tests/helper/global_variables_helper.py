def remove_global_variables_from_spec(known_json):
    """
    This helper function is used to remove the global variables from the known_json
    for versions less than 4.3.0

    Args:
        known_json (dict): The known_json dictionary
    Returns:
        None
    """
    known_json.pop("global_variable_reference_list", None)


def remove_global_variables_from_json_spec(spec_json):
    """Remove global_variable_reference_list anywhere in the blueprint spec."""

    def _remove(obj):
        if isinstance(obj, dict):
            obj.pop("global_variable_reference_list", None)
            for v in list(obj.values()):
                _remove(v)
        elif isinstance(obj, list):
            for item in obj:
                _remove(item)

    _remove(spec_json)
