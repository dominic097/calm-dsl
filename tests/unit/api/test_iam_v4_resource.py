from calm.dsl.api.iam_v4_resource import IAMV4ResourceAPI
from calm.dsl.api.connection import Connection

from unittest.mock import Mock, patch, MagicMock
import pytest

IS_NC_ENABLED_BY_CONFIG = "calm.dsl.api.ncm_config_util.is_nc_enabled_by_config"


class TestIAMV4ResourceAPI:
    def setup_method(self):
        """
        Set up the test environment for IAMV4ResourceAPI.
        """
        # Create a proper mock Connection with spec to pass isinstance checks
        self._connection = Mock(spec=Connection)
        self._connection.host = "mock-host"
        self._nc_connection = Mock()
        self._nc_connection.get_connection_by_api_type.return_value = self._connection

        # Patch the resolver to bypass connection type validation
        with patch(
            "calm.dsl.api.resource.APIConnectivityDetailsResolver"
        ) as mock_resolver_class:
            mock_resolver = mock_resolver_class.return_value
            mock_resolver.resolve.return_value = MagicMock(
                connection=self._connection, api_path="api/iam/v4.0/authn/users"
            )

            self._iam_resource = IAMV4ResourceAPI(self._nc_connection, "users")

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_get(self, mock_is_nc_enabled):
        """
        Test the get method of IAMV4ResourceAPI.
        """
        mock_is_nc_enabled.return_value = True
        item_id = "12345"

        mock_response = Mock()
        mock_response.json.return_value = {"data": {"id": item_id}}
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)

        entity, err = self._iam_resource.get(id=item_id)
        assert entity["id"] == item_id
        assert err is None

    def test_get_with_invalid_id(self):
        """
        Test the get method with an invalid ID.
        """

        with pytest.raises(ValueError, match="ID cannot be None or empty."):
            self._iam_resource.get(id=None)

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_get_with_error(self, mock_is_nc_enabled):
        """
        Test the get method when an error occurs.
        """
        mock_is_nc_enabled.return_value = True
        item_id = "12345"

        mock_response = Mock()
        mock_response.status_code = 404
        self._connection._call.return_value = (mock_response, {"error": "Not Found"})

        entity, err = self._iam_resource.get(id=item_id)
        assert entity is None
        assert err == {"error": "Not Found"}

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list(self, mock_is_nc_enabled):
        """
        Test the list method of IAMV4ResourceAPI.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"id": "12345"}, {"id": "67890"}]}
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)

        entities, err = self._iam_resource.list(
            page=1,
            limit=2,
            _filter="name eq 'John Doe'",
            order_by="name",
            select="name,extId",
            ignore_error=True,
        )
        assert len(entities) == 2
        assert entities[0]["id"] == "12345"
        assert entities[1]["id"] == "67890"
        assert err is None

        call_args = self._connection._call.call_args
        assert call_args is not None
        assert (
            call_args[0][0]
            == "api/iam/v4.0/authn/users?$page=1&$limit=2&$filter=name eq 'John Doe'&$orderby=name&$select=name,extId"
        )
        assert call_args[1] == {
            "verify": False,
            "method": "get",
            "ignore_error": True,
            "timeout": (5, 60),
        }

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list_with_a_few_query_params(self, mock_is_nc_enabled):
        """
        Test the list method of IAMV4ResourceAPI.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"id": "12345"}, {"id": "67890"}]}
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)

        entities, _ = self._iam_resource.list(page=1, limit=2, select="name,extId")
        assert len(entities) == 2
        assert entities[0]["id"] == "12345"
        assert entities[1]["id"] == "67890"

        call_args = self._connection._call.call_args
        assert call_args is not None
        assert (
            call_args[0][0]
            == "api/iam/v4.0/authn/users?$page=1&$limit=2&$select=name,extId"
        )
        assert call_args[1] == {
            "verify": False,
            "method": "get",
            "ignore_error": False,
            "timeout": (5, 60),
        }

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list_with_error(self, mock_is_nc_enabled):
        """
        Test the list method when an error occurs.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.status_code = 400
        self._connection._call.return_value = (mock_response, {"error": "Bad request"})

        entities, err = self._iam_resource.list(ignore_error=True)
        assert entities is None
        assert err == {"error": "Bad request"}

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list_with_error_not_ignored(self, mock_is_nc_enabled):
        """
        Test the list method when the response is empty.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.json.return_value = {"data": []}
        mock_response.status_code = 400
        self._connection._call.return_value = (mock_response, {"error": "Bad request"})

        with pytest.raises(Exception):
            self._iam_resource.list(ignore_error=False)

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list_invalid_page(self, mock_is_nc_enabled):
        """
        Test the list method with an invalid page number.
        """
        mock_is_nc_enabled.return_value = True

        with pytest.raises(ValueError, match="Page number cannot be negative."):
            self._iam_resource.list(page=-1)

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list_invalid_limit(self, mock_is_nc_enabled):
        """
        Test the list method with an invalid limit.
        """
        mock_is_nc_enabled.return_value = True

        with pytest.raises(ValueError, match="Limit must be between 1 and 100."):
            self._iam_resource.list(limit=0)

        with pytest.raises(ValueError, match="Limit must be between 1 and 100."):
            self._iam_resource.list(limit=2000)

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list_all(self, mock_is_nc_enabled):
        """
        Test the list_all method of IAMV4ResourceAPI.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.json.return_value = {"data": [{"id": "12345"}, {"id": "67890"}]}
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)

        entities, err = self._iam_resource.list_all(api_limit=10)
        assert len(entities) == 2
        assert entities[0]["id"] == "12345"
        assert entities[1]["id"] == "67890"
        assert err is None
        assert self._connection._call.call_count == 1

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list_with_total_results_defined(self, mock_is_nc_enabled):
        """
        Test the list all method of IAMV4ResourceAPI with total results defined.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.json = Mock(
            side_effect=[
                {
                    "data": [
                        {"id": "12345"},
                        {"id": "67890"},
                    ]
                },
                {
                    "data": [
                        {"id": "01234"},
                        {"id": "56789"},
                    ]
                },
                {
                    "data": [
                        {"id": "11111"},
                        {"id": "22222"},
                    ]
                },
            ]
        )
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)
        entities, _ = self._iam_resource.list_all(total_results=5, api_limit=2)

        assert len(entities) == 5
        assert entities[0]["id"] == "12345"
        assert entities[1]["id"] == "67890"
        assert entities[2]["id"] == "01234"
        assert entities[3]["id"] == "56789"
        assert entities[4]["id"] == "11111"
        assert self._connection._call.call_count == 3

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list_all_with_error(self, mock_is_nc_enabled):
        """
        Test the list_all method when an error occurs.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.status_code = 400
        self._connection._call.return_value = (mock_response, {"error": "Bad request"})

        entities, err = self._iam_resource.list_all(api_limit=10, ignore_error=True)
        assert entities is None
        assert err == {"error": "Bad request"}

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_list_all_with_error_not_ignored(self, mock_is_nc_enabled):
        """
        Test the list_all method when an error occurs and ignore_error is False.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.status_code = 400
        self._connection._call.return_value = (mock_response, {"error": "Bad request"})

        with pytest.raises(Exception):
            self._iam_resource.list_all(api_limit=10, ignore_error=False)

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_get_name_uuid_map(self, mock_is_nc_enabled):
        """
        Test the get_name_uuid_map method of IAMV4ResourceAPI.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"displayName": "user1", "extId": "12345"},
                {"displayName": "user2", "extId": "67890"},
                {"displayName": "user2", "extId": "01234"},
            ]
        }
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)

        name_uuid_map = self._iam_resource.get_name_uuid_map(name_field="displayName")
        assert name_uuid_map == {"user1": ["12345"], "user2": ["67890", "01234"]}

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"displayName": "user1", "extId": "12345"},
                {"displayName": "user2", "extId": "67890"},
                {"displayName": "user2", "extId": "01234"},
            ]
        }
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)

        name_uuid_map = self._iam_resource.get_name_uuid_map(
            name_field="displayName", limit=2
        )
        assert name_uuid_map == {
            "user1": ["12345"],
            "user2": [
                "67890",
            ],
        }

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_get_name_uuid_map_with_limit(self, mock_is_nc_enabled):
        """
        Test the get_name_uuid_map method of IAMV4ResourceAPI with a limit.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"displayName": "user1", "extId": "12345"},
                {"displayName": "user2", "extId": "67890"},
                {"displayName": "user2", "extId": "01234"},
            ]
        }
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)

        name_uuid_map = self._iam_resource.get_name_uuid_map(
            name_field="displayName", limit=2
        )
        assert name_uuid_map == {
            "user1": ["12345"],
            "user2": [
                "67890",
            ],
        }

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_get_uuid_name_map(self, mock_is_nc_enabled):
        """
        Test the get_uuid_name_map method of IAMV4ResourceAPI.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"displayName": "user1", "extId": "12345"},
                {"displayName": "user2", "extId": "67890"},
                {"displayName": "user2", "extId": "01234"},
            ]
        }
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)

        uuid_name_map = self._iam_resource.get_uuid_name_map(name_field="displayName")
        assert uuid_name_map == {
            "12345": "user1",
            "67890": "user2",
            "01234": "user2",
        }

    @patch(IS_NC_ENABLED_BY_CONFIG)
    def test_get_uuid_name_map_with_limit(self, mock_is_nc_enabled):
        """
        Test the get_uuid_name_map method of IAMV4ResourceAPI with a limit.
        """
        mock_is_nc_enabled.return_value = True

        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"displayName": "user1", "extId": "12345"},
                {"displayName": "user2", "extId": "67890"},
                {"displayName": "user2", "extId": "01234"},
            ]
        }
        mock_response.status_code = 200
        self._connection._call.return_value = (mock_response, None)

        uuid_name_map = self._iam_resource.get_uuid_name_map(
            name_field="displayName", limit=2
        )
        assert uuid_name_map == {
            "12345": "user1",
            "67890": "user2",
        }
