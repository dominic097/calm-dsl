from .resource import ResourceAPI
from .connection import REQUEST


class OnboardingAPI(ResourceAPI):
    def __init__(self, connection):
        # Initialize with a custom resource type for onboarding
        # Since this is an NCM API, we'll override the base paths
        super().__init__(connection, resource_type="onboarding")

        # Override the base paths for NCM onboarding APIs
        self.api_base_path = "api/opsmgmt/v4/onboarding"

        # Define specific endpoint paths
        self.accounts_path = self.api_base_path + "/accounts"
        self.account_status_path = self.accounts_path + "/status/{}"

    def get_accounts(self, params=None):
        """
        Get onboarding accounts

        Args:
            params (dict, optional): Query parameters like passHomePcUuid=true

        Returns:
            tuple: (response, error) tuple
        """
        url = self.accounts_path

        PARAMETER_MAP = {True: "true", False: "false"}

        # Add query parameters if provided
        if params:
            query_params = []
            for key, value in params.items():
                if isinstance(value, bool):
                    value = PARAMETER_MAP.get(value, value)
                    query_params.append(f"{key}={value}")
                else:
                    query_params.append(f"{key}={value}")

            if query_params:
                url += "?" + "&".join(query_params)

        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def get_workflow_status(self, workflow_uuid):
        """
        Get account onboarding status

        Args:
            workflow_uuid (str): UUID of the workflow

        Returns:
            tuple: (response, error) tuple
        """
        url = self.account_status_path.format(workflow_uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)

    def get_account(self, account_uuid):
        """
        Get account details from onboarding API

        Args:
            account_uuid (str): UUID of the account

        Returns:
            tuple: (response, error) tuple
        """
        url = self.accounts_path + "/{}".format(account_uuid)
        return self.connection._call(url, verify=False, method=REQUEST.METHOD.GET)
