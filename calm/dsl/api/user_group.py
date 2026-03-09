from calm.dsl.api.iam_v4_resource import IAMV4ResourceAPI
from .connection import REQUEST


class UserGroupAPI(IAMV4ResourceAPI):
    """
    Resource API for User Groups.
    """

    _NAME_FIELD = "name"

    def __init__(self, connection):
        super().__init__(connection, resource_type="user-groups")

    def create(self, payload):
        return self.connection._call(
            self.api_base_path,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def get_name_uuid_map(self, limit: int = None) -> dict:
        """
        Returns a map of user group names to their UUIDs.
        Args:
            limit: Optional limit on the number of user groups to return.
                   If None, all user groups will be returned.
        Returns:
            A dictionary mapping user group names to their UUIDs.
            structure: {name: [uuid1, uuid2, ...]}
        """
        return super()._get_name_uuid_map(name_field=self._NAME_FIELD, limit=limit)

    def get_uuid_name_map(self, limit: int = None) -> dict:
        """
        Returns a map of user group UUIDs to their names.
        Args:
            limit: Optional limit on the number of user groups to return.
                   If None, all user groups will be returned.
        Returns:
            A dictionary mapping user group UUIDs to their names.
            structure: {uuid: name}
        """
        return super()._get_uuid_name_map(name_field=self._NAME_FIELD, limit=limit)
