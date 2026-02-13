from unittest import mock

from calm.dsl.api.ncm_config_util import (
    is_nc_enabled_by_config,
    is_ncm_enabled_by_config,
)


@mock.patch("calm.dsl.api.ncm_config_util.get_context")
def test_is_nc_enabled_by_config__nc_is_enabled(get_context_mock):
    get_context_mock.return_value.get_nc_server_config.return_value = {"enabled": True}
    assert is_nc_enabled_by_config() is True


@mock.patch("calm.dsl.api.ncm_config_util.get_context")
def test_is_nc_enabled_by_config__nc_is_disabled(get_context_mock):
    get_context_mock.return_value.get_nc_server_config.return_value = {"enabled": False}
    assert is_nc_enabled_by_config() is False


@mock.patch("calm.dsl.api.ncm_config_util.get_context")
def test_is_ncm_enabled_by_config__ncm_is_enabled(get_context_mock):
    get_context_mock.return_value.get_ncm_server_config.return_value = {
        "ncm_enabled": True
    }
    assert is_ncm_enabled_by_config() is True


@mock.patch("calm.dsl.api.ncm_config_util.get_context")
def test_is_ncm_enabled_by_config__ncm_is_disabled(get_context_mock):
    get_context_mock.return_value.get_ncm_server_config.return_value = {
        "ncm_enabled": False
    }
    assert is_ncm_enabled_by_config() is False
