from unittest.mock import Mock
from calm.dsl.api.user_api_mapper import (
    get_idp_service_name,
    get_user_from_response,
    get_user_group_from_response,
)


def test_get_idp_service_name():
    """
    Tests the get_idp_service_name function (happy path).
    """
    client = Mock()
    test_idp_name = "Test IDP"
    client.directory_service.get.return_value = {"name": test_idp_name}, None
    assert get_idp_service_name(client, "test-idp-id") == test_idp_name


def test_get_idp_service_name_id_is_empty():
    """
    Tests the get_idp_service_name function with an empty ID.
    """
    client = Mock()
    assert get_idp_service_name(client, "") == ""


def test_get_idp_service_name_with_error():
    """
    Tests the get_idp_service_name function with an error in fetching the IDP service.
    """
    client = Mock()
    client.directory_service.get.return_value = None, {
        "code": "404",
        "message": "Not Found",
    }
    assert get_idp_service_name(client, "test-idp-id") == ""


def test_get_idp_service_name__name_not_present():
    """
    Tests the get_idp_service_name function when the name is not present in the response.
    """
    client = Mock()
    client.directory_service.get.return_value = {}, None
    assert get_idp_service_name(client, "test-idp-id") == ""


def test_get_user_from_response():
    """
    Tests the get_user_from_response function (happy path).
    """
    client = Mock()
    test_idp_name = "Test IDP"
    test_idp_id = "test-idp-id"
    client.directory_service.get.return_value = {"name": test_idp_name}, None

    entity = {
        "username": "test_user",
        "extId": "12345",
        "displayName": "Test User",
        "idpId": "test-idp-id",
        "userType": "local",
    }
    expected_result = {
        "name": "test_user",
        "uuid": "12345",
        "display_name": "Test User",
        "directory": get_idp_service_name(client, "test-idp-id"),
        "user_type": "local",
    }
    assert get_user_from_response(client, entity) == expected_result


def test_get_user_from_response_invalid_data():
    """
    Tests the get_user_from_response function with invalid data.
    """
    client = Mock()
    entity = {"username": None, "extId": "", "displayName": None, "idpId": ""}
    assert get_user_from_response(client, entity) == {}


def test_get_user_group_from_response():
    """
    Tests the get_user_group_from_response function (happy path).
    """
    client = Mock()
    test_idp_name = "Test IDP"
    test_idp_id = "test-idp-id"
    client.directory_service.get.return_value = {"name": test_idp_name}, None

    entity = {
        "distinguishedName": "test_group",
        "extId": "67890",
        "name": "Test Group",
        "idpId": "test-idp-id",
    }
    expected_result = {
        "name": "test_group",
        "uuid": "67890",
        "display_name": "Test Group",
        "directory": get_idp_service_name(client, "test-idp-id"),
    }
    assert get_user_group_from_response(client, entity) == expected_result


def test_get_user_group_from_response_invalid_data():
    """
    Tests the get_user_group_from_response function with invalid data.
    """
    client = Mock()
    # ext id is missing
    entity = {
        "distinguishedName": None,
    }
    assert get_user_group_from_response(client, entity) == {}
