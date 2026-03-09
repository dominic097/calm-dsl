from calm.dsl.api.connection import NCMultiConnection
from calm.dsl.constants import RESOURCE


class TestNCMultiConnection:
    """
    Test cases for NCMultiConnection class.
    """

    def test_nc_multi_connection(self):
        """
        Tests the NCMultiConnection class initialization and API type retrieval.
        """
        nc_multi_connection = NCMultiConnection(
            "test.host", 443, "nc-dev-test.ntnx.com"
        )

        # PC connection
        pc_connection = nc_multi_connection.get_connection_by_api_type(
            RESOURCE.API_TYPE.PC_API
        )
        assert pc_connection.host == "test.host"
        assert pc_connection.port == 443
        assert pc_connection == nc_multi_connection.pc_connection

        # NCM connection
        ncm_connection = nc_multi_connection.get_connection_by_api_type(
            RESOURCE.API_TYPE.CALM_API
        )
        assert ncm_connection.host == "ncm.services.nc-dev-test.ntnx.com"
        assert ncm_connection.port == ""
        assert ncm_connection == nc_multi_connection.ncm_connection

        # DM connection
        dm_connection = nc_multi_connection.get_connection_by_api_type(
            RESOURCE.API_TYPE.DM_API
        )
        assert dm_connection.host == "dm.services.nc-dev-test.ntnx.com"
        assert dm_connection.port == ""
        assert dm_connection == nc_multi_connection.dm_connection

        # IAM connection
        iam_connection = nc_multi_connection.get_connection_by_api_type(
            RESOURCE.API_TYPE.IAM_AUTHN_API
        )
        assert iam_connection.host == "iam.services.nc-dev-test.ntnx.com"
        assert iam_connection.port == ""
        assert iam_connection == nc_multi_connection.iam_connection
