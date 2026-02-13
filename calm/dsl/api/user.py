from .iam_v4_resource import IAMV4ResourceAPI
from .connection import REQUEST


class UserAPI(IAMV4ResourceAPI):
    """
    Resource API for Users."""

    _NAME_FIELD = "username"
    UPDATE_STATE = "$actions/change-state"

    def __init__(self, connection):
        super().__init__(connection, resource_type="users")

    def create(self, payload):
        return self.connection._call(
            self.api_base_path,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )

    def get_name_uuid_map(self, limit: int = None) -> dict:
        """
        Returns a map of user names to their UUIDs.
        Args:
            limit: Optional limit on the number of users to return.
                   If None, all users will be returned.
        Returns:
            A dictionary mapping user names to their UUIDs.
            structure: {name: [uuid1, uuid2, ...]}
        """
        return super()._get_name_uuid_map(name_field=self._NAME_FIELD, limit=limit)

    def get_uuid_name_map(self, limit: int = None) -> dict:
        """
        Returns a map of user UUIDs to their names.
        Args:
            limit: Optional limit on the number of users to return.
                   If None, all users will be returned.
        Returns:
            A dictionary mapping user UUIDs to their names.
            structure: {uuid: name}
        """
        return super()._get_uuid_name_map(name_field=self._NAME_FIELD, limit=limit)

    def update_state(self, user_ext_id, state):
        """
        Update the state of a user using IAM v4 API.

        Args:
            user_ext_id: The external ID (UUID) of the user
            state: The state to set (e.g., "INACTIVE", "ACTIVE")

        Returns:
            Response from the API call

        API Reference:
            POST /api/iam/v4.0.b1/authn/users/{extId}/$actions/update-state
        """
        update_state_path = f"{self.api_base_path}/{user_ext_id}/{self.UPDATE_STATE}"
        payload = {"status": state}

        return self.connection._call(
            update_state_path,
            verify=False,
            request_json=payload,
            method=REQUEST.METHOD.POST,
        )
