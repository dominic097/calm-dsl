from .resource import ResourceAPI
from .connection import REQUEST


class MultidomainAPI(ResourceAPI):
    def __init__(self, connection):
        # Initialize with a custom resource type for multidomain
        # Override the base paths for multidomain v4.0 APIs
        super().__init__(connection, resource_type="multidomain")

        # Override the base paths for multidomain APIs
        self.api_base_path = "api/multidomain/v4.0"

        # Define specific endpoint paths
        self.config_path = self.api_base_path + "/config"
        self.registered_domains_path = self.config_path + "/registered-domains"
        self.applications_path = self.config_path + "/applications"

    def get_registered_domains(self):
        """
        Get registered domains configuration

        Args:
            params (dict, optional): Query parameters

        Returns:
            tuple: (response, error) tuple
        """
        return self.connection._call(
            self.registered_domains_path, verify=False, method=REQUEST.METHOD.GET
        )

    def get_applications(self, ignore_error=False):
        """
        Get multidomain applications configuration

        Args:
            params (dict, optional): Query parameters for filtering/pagination
            ignore_error (bool): If True, errors will be returned instead of raised
            timeout (tuple): (connection timeout, read timeout)

        Returns:
            tuple: (response, error) tuple
        """
        return self.connection._call(
            self.applications_path,
            verify=False,
            method=REQUEST.METHOD.GET,
            ignore_error=ignore_error,
        )
