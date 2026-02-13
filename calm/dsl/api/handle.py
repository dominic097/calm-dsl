from calm.dsl.config import get_context
from calm.dsl.config.constants import CONFIG
from calm.dsl.constants import MULTICONNECT

from .connection import (
    LOG,
    get_connection_obj,
    get_pc_connection,
    get_ncm_connection,
    connection_manager,
    REQUEST,
    MultiConnection,
    NCMultiConnection,
)
from .blueprint import BlueprintAPI
from .endpoint import EndpointAPI
from .runbook import RunbookAPI
from .library_tasks import TaskLibraryApi
from .application import ApplicationAPI
from .project import ProjectAPI
from .environment import EnvironmentAPI
from .setting import AccountsAPI
from .marketplace import MarketPlaceAPI
from .app_icons import AppIconAPI
from .version import VersionAPI
from .showback import ShowbackAPI
from .user import UserAPI
from .user_group import UserGroupAPI
from .role import RoleAPI
from .directory_service import DirectoryServiceAPI
from .authorization_policy import AuthorizationPolicyAPI
from .app_protection_policy import AppProtectionPolicyAPI
from .job import JobAPI
from .tunnel import TunnelAPI
from .vm_recovery_point import VmRecoveryPointAPI
from .nutanix_task import TaskAPI
from .network_group import NetworkGroupAPI
from .resource_type import ResourceTypeAPI
from .policy_action_type import PolicyActionTypeAPI
from .policy_event import PolicyEventAPI
from .policy_attributes import PolicyAttributesAPI
from .policy import PolicyAPI
from .approval import ApprovalAPI
from .approval_request import ApprovalRequestAPI
from .provider import ProviderAPI
from .quotas import QuotasAPI
from .groups_api import MultiGroupsAPI
from .util import get_auth_info
from .global_variable import GlobalVariableApi
from .onboarding import OnboardingAPI
from .multidomain import MultidomainAPI
from .network_function_chains import NetworkFunctionChainsAPI


class ClientHandle:
    def __init__(self, connection):
        self.connection = connection

    def connect(self):
        self.connection.connect()

        # Note - add entity api classes here
        self.project = ProjectAPI(self.connection)
        self.environment = EnvironmentAPI(self.connection)
        self.blueprint = BlueprintAPI(self.connection)
        self.endpoint = EndpointAPI(self.connection)
        self.runbook = RunbookAPI(self.connection)
        self.task = TaskLibraryApi(self.connection)
        self.application = ApplicationAPI(self.connection)
        self.account = AccountsAPI(self.connection)
        self.market_place = MarketPlaceAPI(self.connection)
        self.app_icon = AppIconAPI(self.connection)
        self.version = VersionAPI(self.connection)
        self.showback = ShowbackAPI(self.connection)
        self.user = UserAPI(self.connection)
        self.user_group = UserGroupAPI(self.connection)
        self.role = RoleAPI(self.connection)
        self.directory_service = DirectoryServiceAPI(self.connection)
        self.authorization_policy = AuthorizationPolicyAPI(self.connection)
        self.environment = EnvironmentAPI(self.connection)
        self.app_protection_policy = AppProtectionPolicyAPI(self.connection)
        self.job = JobAPI(self.connection)
        self.tunnel = TunnelAPI(self.connection)
        self.vm_recovery_point = VmRecoveryPointAPI(self.connection)
        self.nutanix_task = TaskAPI(self.connection)
        self.network_group = NetworkGroupAPI(self.connection)
        self.resource_types = ResourceTypeAPI(self.connection)
        self.policy_action_types = PolicyActionTypeAPI(self.connection)
        self.policy_event = PolicyEventAPI(self.connection)
        self.policy_attributes = PolicyAttributesAPI(self.connection)
        self.policy = PolicyAPI(self.connection)
        self.approvals = ApprovalAPI(self.connection)
        self.approval_requests = ApprovalRequestAPI(self.connection)
        self.provider = ProviderAPI(self.connection)
        self.quotas = QuotasAPI(self.connection)
        self.groups = MultiGroupsAPI(self.connection)
        self.global_variable = GlobalVariableApi(self.connection)
        self.onboarding = OnboardingAPI(self.connection)
        self.multidomain = MultidomainAPI(self.connection)
        # TODO: making an alias for acp to maintain backward compatibility
        # on client's end
        self.acp = self.authorization_policy
        self.network_function_chains = NetworkFunctionChainsAPI(self.connection)


def get_client_handle_by_deployment(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
    nc_enabled=False,
    nc_host=None,
    nc_auth=None,
    ncm_enabled=False,
    ncm_host=None,
    ncm_port=None,
):
    """
    Returns object of ClientHandle class based on deployment type.
    """
    LOG.debug(
        "Creating client handle nc_enabled: {}, ncm_enabled: {}".format(
            nc_enabled, ncm_enabled
        )
    )
    if nc_enabled:
        return get_nc_multi_client_handle(
            host,
            port,
            nc_host,
            auth_type=auth_type,
            scheme=scheme,
            pc_auth=auth,
            nc_auth=nc_auth,
        )
    elif ncm_enabled:
        return get_multi_client_handle_obj(
            host, port, ncm_host, ncm_port, auth_type, scheme, auth
        )
    else:
        return get_client_handle_obj(host, port, auth_type, scheme, auth)


def get_client_handle_obj(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    """returns object of ClientHandle class"""

    connection = get_connection_obj(host, port, auth_type, scheme, auth)
    handle = ClientHandle(connection)
    handle.connect()
    return handle


def get_multi_client_handle_obj(
    host,
    port,
    ncm_host,
    ncm_port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    """returns object of ClientHandle class"""

    multi_connection = MultiConnection()
    setattr(
        multi_connection,
        MULTICONNECT.PC_OBJ,
        get_pc_connection(host, port, auth_type, scheme, auth),
    )
    setattr(
        multi_connection,
        MULTICONNECT.NCM_OBJ,
        get_ncm_connection(ncm_host, ncm_port, auth_type, scheme, auth),
    )

    handle = ClientHandle(multi_connection)
    handle.connect()
    return handle


def get_nc_multi_client_handle(
    host,
    port,
    nc_host,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    pc_auth=None,
    nc_auth=None,
):
    """
    Instantiates the NC multiclient client handle.
    """
    nc_mutli_connection = NCMultiConnection(
        host, port, nc_host, auth_type, scheme, pc_auth, nc_auth
    )
    handle = ClientHandle(nc_mutli_connection)
    handle.connect()
    return handle


_API_CLIENT_HANDLE = None


def update_api_client(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    pc_auth=None,
    nc_config={},
    ncm_config={},
    **kwargs,
):
    """updates global api client object (_API_CLIENT_HANDLE)"""

    global _API_CLIENT_HANDLE

    nc_enabled = nc_config.get(CONFIG.NC_SERVER.ENABLED, False)
    if nc_enabled:
        nc_host = nc_config.get(CONFIG.NC_SERVER.HOST, None)
        nc_username = nc_config.get(CONFIG.NC_SERVER.USERNAME, None)
        nc_password = nc_config.get(CONFIG.NC_SERVER.PASSWORD, None)

        client = _create_api_client_with_nc_connection(
            host, port, nc_host, auth_type, scheme, pc_auth, (nc_username, nc_password)
        )
    else:
        ncm_enabled = ncm_config.get(CONFIG.NCM_SERVER.NCM_ENABLED, False)
        ncm_host = ncm_config.get(CONFIG.NCM_SERVER.HOST, None)
        ncm_port = ncm_config.get(CONFIG.NCM_SERVER.PORT, None)

        client = _create_api_client_with_ncm_connection(
            host, port, auth_type, scheme, pc_auth, ncm_enabled, ncm_host, ncm_port
        )

    _API_CLIENT_HANDLE = client
    _API_CLIENT_HANDLE.connect()

    return _API_CLIENT_HANDLE


def _create_api_client_with_nc_connection(
    host,
    port,
    nc_host,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    pc_auth=None,
    nc_auth=None,
):

    nc_multi_connection = connection_manager.update_nc_multi_connection(
        host, port, nc_host, auth_type, scheme, pc_auth, nc_auth
    )
    return ClientHandle(nc_multi_connection)


def _create_api_client_with_ncm_connection(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
    ncm_enabled=False,
    ncm_host=None,
    ncm_port=None,
):
    multi_connection = MultiConnection()

    # If ncm is not enabled, use pc host and port for ncm
    # It will create ncm session pointing to PC
    if not ncm_enabled:
        ncm_host = host
        ncm_port = port

    setattr(
        multi_connection,
        MULTICONNECT.PC_OBJ,
        connection_manager.update_pc_connection(
            host, port, auth_type, scheme=scheme, auth=auth
        ),
    )

    setattr(
        multi_connection,
        MULTICONNECT.NCM_OBJ,
        connection_manager.update_ncm_connection(
            ncm_host, ncm_port, auth_type, scheme, auth
        ),
    )

    return ClientHandle(multi_connection)


def get_api_client():
    """returns global api client object (_API_CLIENT_HANDLE)"""

    global _API_CLIENT_HANDLE

    if not _API_CLIENT_HANDLE:
        context = get_context()
        server_config = context.get_server_config()

        pc_ip = server_config.get("pc_ip")
        pc_port = server_config.get("pc_port")
        api_key_location = server_config.get("api_key_location", None)
        cred = get_auth_info(api_key_location)
        username = cred.get("username")
        password = cred.get("password")

        update_api_client(
            host=pc_ip,
            port=pc_port,
            pc_auth=(username, password),
            nc_config=context.get_nc_server_config(),
            ncm_config=context.get_ncm_server_config(),
        )

    return _API_CLIENT_HANDLE


def reset_api_client_handle():
    """resets global api client object (_API_CLIENT_HANDLE)"""

    global _API_CLIENT_HANDLE
    _API_CLIENT_HANDLE = None
