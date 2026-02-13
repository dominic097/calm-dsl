# -*- coding: utf-8 -*-
"""
connection: Provides a HTTP client to make requests to calm

Example:

pc_ip = "<pc_ip>"
pc_port = 9440
client = get_connection(pc_ip, pc_port,
                        auth=("<pc_username>", "<pc_passwd>"))

"""

import traceback
import json
import urllib3
import sys

from requests import Session as Session
from requests_toolbelt import MultipartEncoder
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectTimeout
from urllib3.util.retry import Retry

from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context
from calm.dsl.constants import MULTICONNECT, RESOURCE
from calm.dsl.api.meta import SingletonMeta
from typing import Optional
from calm.dsl.api.ncm_config_util import is_nc_enabled_by_config

urllib3.disable_warnings()
LOG = get_logging_handle(__name__)


class REQUEST:
    """Request related constants"""

    class SCHEME:
        """
        Connection schemes
        """

        HTTP = "http"
        HTTPS = "https"

    class AUTH_TYPE:
        """
        Types of auth
        """

        NONE = "none"
        BASIC = "basic"
        JWT = "jwt"

    class METHOD:
        """
        Request methods
        """

        DELETE = "delete"
        GET = "get"
        POST = "post"
        PUT = "put"


def build_url(host, port, endpoint="", scheme=REQUEST.SCHEME.HTTPS):
    """Build url.

    Args:
        host (str): hostname/ip
        port (int): port of the service
        endpoint (str): url endpoint
        scheme (str): http/https/tcp/udp
    Returns:
    Raises:
    """
    url = "{scheme}://{host}".format(scheme=scheme, host=host)
    if port is not None:
        url += ":{port}".format(port=port)
    url += "/{endpoint}".format(endpoint=endpoint)
    return url


class Connection:
    def __init__(
        self,
        host,
        port,
        auth_type=REQUEST.AUTH_TYPE.BASIC,
        scheme=REQUEST.SCHEME.HTTPS,
        auth=None,
        pool_maxsize=20,
        pool_connections=20,
        pool_block=True,
        base_url="",
        response_processor=None,
        session_headers=None,
        **kwargs,
    ):
        """Generic client to connect to server.

        Args:
            host (str): Hostname/IP address
            port (int): Port to connect to
            pool_maxsize (int): The maximum number of connections in the pool
            pool_connections (int): The number of urllib3 connection pools
                                    to cache
            pool_block (bool): Whether the connection pool should block
                               for connections
            base_url (str): Base URL
            scheme (str): http scheme (http or https)
            response_processor (dict): response processor dict
            session_headers (dict): session headers dict
            auth_type (str): auth type that needs to be used by the client
            auth (tuple): authentication
        Returns:
        Raises:
        """
        self.base_url = base_url
        self.host = host
        self.port = port
        self.session_headers = session_headers or {}
        self._pool_maxsize = pool_maxsize
        self._pool_connections = pool_connections
        self._pool_block = pool_block
        self.session = None
        self.auth = auth
        self.scheme = scheme
        self.auth_type = auth_type
        self.response_processor = response_processor

    def connect(self):
        """Connect to api server, create http session pool.

        Args:
        Returns:
            api server session
        Raises:
        """

        context = get_context()
        connection_config = context.get_connection_config()
        if connection_config["retries_enabled"]:
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=[
                    "GET",
                    "PUT",
                    "DELETE",
                    "POST",
                ],
            )
            http_adapter = HTTPAdapter(
                pool_block=bool(self._pool_block),
                pool_connections=int(self._pool_connections),
                pool_maxsize=int(self._pool_maxsize),
                max_retries=retry_strategy,
            )

        else:
            http_adapter = HTTPAdapter(
                pool_block=bool(self._pool_block),
                pool_connections=int(self._pool_connections),
                pool_maxsize=int(self._pool_maxsize),
            )

        self.session = Session()
        if self.auth and self.auth_type == REQUEST.AUTH_TYPE.BASIC:
            self.session.auth = self.auth
        self.session.headers.update({"Content-Type": "application/json"})

        self.session.mount("http://", http_adapter)
        self.session.mount("https://", http_adapter)
        self.base_url = build_url(self.host, self.port, scheme=self.scheme)
        LOG.debug("{} session created".format(self.__class__.__name__))
        return self.session

    def close(self):
        """
        Close the session.

        Args:
            None
        Returns:
            None
        """
        self.session.close()

    def _call(
        self,
        endpoint,
        method=REQUEST.METHOD.POST,
        cookies=None,
        request_json=None,
        request_params=None,
        verify=True,
        headers=None,
        files=None,
        ignore_error=False,
        warning_msg="",
        **kwargs,
    ):
        """Private method for making http request to calm

        Args:
            endpoint (str): calm server endpoint
            method (str): calm server http method
            cookies (dict): cookies that need to be forwarded.
            request_json (dict): request data
            request_params (dict): request params
            timeout (touple): (connection timeout, read timeout)
        Returns:
            (tuple (requests.Response, dict)): Response
        """
        timeout = kwargs.get("timeout", None)
        if not timeout:
            context = get_context()
            connection_config = context.get_connection_config()
            timeout = (
                connection_config["connection_timeout"],
                connection_config["read_timeout"],
            )

        if request_params is None:
            request_params = {}

        request_json = request_json or {}
        LOG.debug(
            """Server Request- '{method}' at '{endpoint}' with body:
            '{body}'""".format(
                method=method, endpoint=endpoint, body=request_json
            )
        )
        res = None
        err = None
        try:
            res = None
            context = get_context()
            if context.get_nc_server_config().get("nc_enabled", False):
                url = build_url(
                    self.host, port=None, endpoint=endpoint, scheme=self.scheme
                )
            else:
                url = build_url(
                    self.host, self.port, endpoint=endpoint, scheme=self.scheme
                )
            LOG.debug("URL is: {}".format(url))
            base_headers = self.session.headers
            if headers:
                base_headers.update(headers)

            if method == REQUEST.METHOD.POST:
                if files is not None:
                    request_json.update(files)
                    m = MultipartEncoder(fields=request_json)
                    res = self.session.post(
                        url,
                        data=m,
                        verify=verify,
                        headers={"Content-Type": m.content_type},
                        timeout=timeout,
                    )
                else:
                    res = self.session.post(
                        url,
                        params=request_params,
                        data=json.dumps(request_json),
                        verify=verify,
                        headers=base_headers,
                        cookies=cookies,
                        timeout=timeout,
                    )
            elif method == REQUEST.METHOD.PUT:
                res = self.session.put(
                    url,
                    params=request_params,
                    data=json.dumps(request_json),
                    verify=verify,
                    headers=base_headers,
                    cookies=cookies,
                    timeout=timeout,
                )
            elif method == REQUEST.METHOD.GET:
                res = self.session.get(
                    url,
                    params=request_params or request_json,
                    verify=verify,
                    headers=base_headers,
                    cookies=cookies,
                    timeout=timeout,
                )
            elif method == REQUEST.METHOD.DELETE:
                res = self.session.delete(
                    url,
                    params=request_params,
                    data=json.dumps(request_json),
                    verify=verify,
                    headers=base_headers,
                    cookies=cookies,
                    timeout=timeout,
                )
            res.raise_for_status()
            if not url.endswith("/download"):
                if not res.ok:
                    LOG.debug("Server Response: {}".format(res.json()))
        except ConnectTimeout as cte:
            if hasattr(res, "json") and callable(getattr(res, "json")):
                try:
                    err_msg = res.json()
                except Exception:
                    err_msg = "{}".format(cte)
                    pass
            elif hasattr(res, "text"):
                err_msg = res.text
            else:
                err_msg = "{}".format(cte)
            status_code = res.status_code if hasattr(res, "status_code") else 500
            err = {"error": err_msg, "code": status_code}

            if ignore_error:
                return None, err

            LOG.error(
                "Could not establish connection to server at https://{}:{}.".format(
                    self.host, self.port
                )
            )
            LOG.debug("Error Response: {}".format(cte))
            sys.exit(-1)
        except Exception as ex:
            LOG.debug("Got traceback\n{}".format(traceback.format_exc()))
            if hasattr(res, "json") and callable(getattr(res, "json")):
                try:
                    err_msg = res.json()
                except Exception:
                    err_msg = "{}".format(ex)
                    pass
            elif hasattr(res, "text"):
                err_msg = res.text
            else:
                err_msg = "{}".format(ex)
            status_code = res.status_code if hasattr(res, "status_code") else 500
            err = {"error": err_msg, "code": status_code}

            if ignore_error:
                if warning_msg:
                    LOG.warning(warning_msg)
                return None, err

            LOG.error(
                "Oops! Something went wrong.\n{}".format(
                    json.dumps(err, indent=4, separators=(",", ": "))
                )
            )

        return res, err


class PcConnection(Connection):
    pass


class NcmConnection(Connection):
    pass


class MultiConnection:
    """
    Encapsulates all type of connection objects here.
    """

    def __init__(self):
        setattr(self, MULTICONNECT.PC_OBJ, None)
        setattr(self, MULTICONNECT.NCM_OBJ, None)

    def get_pc_object(self):
        return getattr(self, MULTICONNECT.PC_OBJ, None)

    def get_ncm_object(self):
        return getattr(self, MULTICONNECT.NCM_OBJ, None)

    @property
    def base_url(self):
        """
        Dynamically fetch the base_url based on the connection type.

        @property decorator:
            - Provides a consistent interface for accessing base_url, regardless of
              whether client.connection is a Connection or MultiConnection object.
            - Improves flexibility and reduces the risk of errors when switching connection types.
        """
        context = get_context()
        ncm_server_config = context.get_ncm_server_config()
        try:
            if ncm_server_config.get("ncm_enabled", False):
                return self.get_ncm_object().base_url
            else:
                return self.get_pc_object().base_url
        except:
            LOG.debug("client.connection object does not exist or has no base_url.")
        return None

    def connect(self):

        # Case for one host (single connection object)
        if isinstance(self, Connection):
            self.connect()
            return

        if isinstance(self.get_pc_object(), PcConnection):
            self.get_pc_object().connect()
        else:
            LOG.debug("PC connection is not present")

        if isinstance(self.get_ncm_object(), NcmConnection):
            self.get_ncm_object().connect()
        else:
            LOG.debug("NCM connection is not present")

    def close(self):
        if isinstance(self.get_pc_object(), PcConnection):
            self.get_pc_object().close()
        else:
            LOG.debug("PC connection is not present")

        if isinstance(self.get_ncm_object(), NcmConnection):
            self.get_ncm_object().close()
        else:
            LOG.debug("NCM connection is not present")


class NCMultiConnection:
    """
    NCMultiConnection holds the connections to NC setup, with the subdomain
    connections relevant to Calm DSL.
    """

    NC_PORT = ""

    def __init__(
        self,
        host,
        port,
        nc_host,
        auth_type=REQUEST.AUTH_TYPE.BASIC,
        scheme=REQUEST.SCHEME.HTTPS,
        pc_auth=None,
        nc_auth=None,
    ):
        self._pc_connection = Connection(host, port, auth_type, scheme, pc_auth)
        self._nc_connection = Connection(nc_host, None, auth_type, scheme, nc_auth)
        self._ncm_connection = Connection(
            f"{MULTICONNECT.NC_NCM_SUBDOMAIN}.{nc_host}",
            self.NC_PORT,
            auth_type,
            scheme,
            nc_auth,
        )
        self._dm_connection = Connection(
            f"{MULTICONNECT.NC_DM_SUBDOMAIN}.{nc_host}",
            self.NC_PORT,
            auth_type,
            scheme,
            nc_auth,
        )
        self._iam_connection = Connection(
            f"{MULTICONNECT.NC_IAM_SUBDOMAIN}.{nc_host}",
            self.NC_PORT,
            auth_type,
            scheme,
            nc_auth,
        )

        self._connection_map = {
            RESOURCE.API_TYPE.PC_API: self._pc_connection,
            RESOURCE.API_TYPE.NC_API: self._nc_connection,
            RESOURCE.API_TYPE.CALM_API: self._ncm_connection,
            RESOURCE.API_TYPE.DM_API: self._dm_connection,
            RESOURCE.API_TYPE.IAM_AUTHN_API: self._iam_connection,
            RESOURCE.API_TYPE.IAM_AUTHZ_API: self._iam_connection,
        }

    def get_connection_by_api_type(self, api_type: RESOURCE.API_TYPE) -> Connection:
        """
        Returns the connection object based on the API type.
        Args:
            api_type (RESOURCE.API_TYPE): The API type for which the connection is requested.
        Returns:
            Connection: The connection object corresponding to the provided API type
            (defaults to None if the connection is not found).
        """
        LOG.debug(f"Retrieving connection for API type: {api_type.name}")
        return self._connection_map.get(api_type)

    @property
    def base_url(self):
        """
        Dynamically fetch the base_url based on the connection type.

        @property decorator:
            - Provides a consistent interface for accessing base_url, regardless of
              whether client.connection is a Connection or MultiConnection object.
            - Improves flexibility and reduces the risk of errors when switching connection types.
        """
        try:
            if is_nc_enabled_by_config():
                return self.nc_connection.base_url
        except:
            LOG.debug("client.connection object does not exist or has no base_url.")
        return None

    @property
    def pc_connection(self) -> Connection:
        return self._pc_connection

    @property
    def nc_connection(self) -> Connection:
        return self._nc_connection

    @property
    def ncm_connection(self) -> Connection:
        return self._ncm_connection

    @property
    def dm_connection(self) -> Connection:
        return self._dm_connection

    @property
    def iam_connection(self) -> Connection:
        return self._iam_connection

    def connect(self):
        """
        Connects with all the connections in the NCMultiConnection.
        """
        LOG.debug("Connection NCMultiConnection")
        self._pc_connection.connect()
        self._nc_connection.connect()
        self._ncm_connection.connect()
        self._dm_connection.connect()
        self._iam_connection.connect()

    def close(self):
        """
        Closes all the connections in the NCMultiConnection.
        """
        LOG.debug("Closing NCMultiConnection")
        self._pc_connection.close()
        self._nc_connection.close()
        self._ncm_connection.close()
        self._dm_connection.close()
        self._iam_connection.close()


def get_connection_obj(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    """Returns object of Connection class"""

    return Connection(host, port, auth_type, scheme, auth)


def get_pc_connection(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    """Returns object of PcConnection class"""

    return PcConnection(host, port, auth_type, scheme, auth)


def get_ncm_connection(
    host,
    port,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    auth=None,
):
    """Returns object of NcmConnection class"""

    return NcmConnection(host, port, auth_type, scheme, auth)


def get_nc_connection_handle(
    host,
    port,
    nc_host,
    auth_type=REQUEST.AUTH_TYPE.BASIC,
    scheme=REQUEST.SCHEME.HTTPS,
    pc_auth=None,
    nc_auth=None,
):
    """Get NCMultiConnection handle.

    Args:
        host (str): Hostname/IP address
        port (int): Port to connect to
        nc_host (str): NC subdomain host
        auth_type (str): auth type that needs to be used by the client
        scheme (str): http scheme (http or https)
        pc_auth (tuple): PC authentication
        nc_auth (tuple): NC authentication
    Returns:
        NCMultiConnection handle
    """
    return NCMultiConnection(
        host,
        port,
        nc_host,
        auth_type=auth_type,
        scheme=scheme,
        pc_auth=pc_auth,
        nc_auth=nc_auth,
    )


class ConnectionManager(metaclass=SingletonMeta):
    """
    Manages the connections for PC, NCM, and NC MultiConnection.
    This class provides a unified interface to access and manage the connections
    for different API types, ensuring that the correct connection is used based on
    the API type requested.
    """

    def __init__(self):
        self._pc_connection = None
        self._ncm_connection = None
        self._nc_multi_connection = None

    def update_pc_connection(
        self,
        host,
        port,
        auth_type=REQUEST.AUTH_TYPE.BASIC,
        scheme=REQUEST.SCHEME.HTTPS,
        auth=None,
    ) -> PcConnection:
        """Updates the PC connection."""
        self._pc_connection = get_pc_connection(host, port, auth_type, scheme, auth)
        return self._pc_connection

    def update_ncm_connection(
        self,
        host,
        port,
        auth_type=REQUEST.AUTH_TYPE.BASIC,
        scheme=REQUEST.SCHEME.HTTPS,
        auth=None,
    ) -> NcmConnection:
        """Updates the NCM connection."""
        self._ncm_connection = get_ncm_connection(host, port, auth_type, scheme, auth)
        return self._ncm_connection

    def update_nc_multi_connection(
        self,
        host,
        port,
        nc_host,
        auth_type=REQUEST.AUTH_TYPE.BASIC,
        scheme=REQUEST.SCHEME.HTTPS,
        pc_auth=None,
        nc_auth=None,
    ) -> NCMultiConnection:
        """Updates the NCMultiConnection."""
        self._nc_multi_connection = get_nc_connection_handle(
            host, port, nc_host, auth_type, scheme, pc_auth, nc_auth
        )
        return self._nc_multi_connection

    @property
    def pc_connection(self) -> Optional[Connection]:
        """Gets the PC connection."""
        return self._pc_connection

    @property
    def ncm_connection(self) -> Optional[Connection]:
        """Gets the NCM connection."""
        return self._ncm_connection

    @property
    def nc_multi_connection(self) -> Optional[NCMultiConnection]:
        """Gets the NCMultiConnection."""
        return self._nc_multi_connection


connection_manager = ConnectionManager()
