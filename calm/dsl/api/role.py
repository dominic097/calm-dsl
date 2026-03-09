from calm.dsl.api.iam_v4_resource import IAMV4ResourceAPI


class RoleAPI(IAMV4ResourceAPI):
    _NAME_FIELD = "displayName"

    def __init__(self, connection):
        super().__init__(connection, resource_type="roles")

    def get_name_uuid_map(self, limit: int = None) -> dict:
        """
        Returns a map of role names to their UUIDs.
        Args:
            limit: Optional limit on the number of roles to return.
                  If None, all roles will be returned.
        Returns:
            A dictionary mapping role names to their UUIDs.
            structure: {name: [uuid1, uuid2, ...]}
        """
        return super()._get_name_uuid_map(name_field=self._NAME_FIELD, limit=limit)

    def get_uuid_name_map(self, limit: int = None) -> dict:
        """
        Returns a map of role UUIDs to their names.
        Args:
            limit: Optional limit on the number of roles to return.
                   If None, all roles will be returned.
        Returns:
            A dictionary mapping role UUIDs to their names.
            structure: {uuid: name}
        """
        return super()._get_uuid_name_map(name_field=self._NAME_FIELD, limit=limit)
