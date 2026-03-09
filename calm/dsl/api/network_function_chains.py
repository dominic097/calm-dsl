from .resource import ResourceAPI
from .connection import REQUEST


class NetworkFunctionChainsAPI(ResourceAPI):
    def __init__(self, connection):
        super().__init__(
            connection, resource_type="network_function_chains", calm_api=False
        )

    def list(self, params={}, ignore_error=False):
        return self.connection._call(
            self.list_path,
            verify=False,
            request_json=params,
            method=REQUEST.METHOD.POST,
            ignore_error=ignore_error,
        )
