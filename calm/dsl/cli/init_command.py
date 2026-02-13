from calm.dsl.db.table_config import ncm_server_config
import click
import os
import json
import sys

from copy import deepcopy

from distutils.version import LooseVersion as LV
from urllib.parse import urlparse

from calm.dsl.config import (
    get_context,
    set_dsl_config,
    get_default_config_file,
    get_default_db_file,
    get_default_local_dir,
    get_default_connection_config,
    get_default_log_config,
    init_context,
)
from calm.dsl.db import init_db_handle
from calm.dsl.api import (
    get_resource_api,
    get_client_handle_obj,
    get_multi_client_handle_obj,
    get_nc_multi_client_handle,
    reset_api_client_handle,
)
from calm.dsl.store import Cache
from calm.dsl.init import init_bp, init_runbook, init_provider
from calm.dsl.providers import get_provider_types
from calm.dsl.store import Version
from calm.dsl.constants import (
    MULTICONNECT,
    POLICY,
    STRATOS,
    DSL_CONFIG,
    CLOUD_PROVIDERS,
)
from calm.dsl.builtins import file_exists
from calm.dsl.api.util import (
    get_auth_info,
    is_ncm_enabled,
    fetch_host_port_from_url,
    is_nc_enabled,
    is_ncm_enabled,
)
from .main import init, set
from calm.dsl.log import get_logging_handle, CustomLogging
from calm.dsl.builtins.models.helper.common import get_home_pc_uuid

LOG = get_logging_handle(__name__)
DEFAULT_CONNECTION_CONFIG = get_default_connection_config()
DEFAULT_LOG_CONFIG = get_default_log_config()


@init.command("dsl")
@click.option(
    "--ip",
    "-i",
    envvar="CALM_DSL_PC_IP",
    default=None,
    help="Prism/Nutanix Central server IP or hostname",
)
@click.option(
    "--port",
    "-P",
    envvar="CALM_DSL_PC_PORT",
    default=None,
    help="Prism Central server port number (skip for Nutanix Central)",
)
@click.option(
    "--username",
    "-u",
    envvar="CALM_DSL_PC_USERNAME",
    default=None,
    help="Prism/Nutanix Central username",
)
@click.option(
    "--password",
    "-p",
    envvar="CALM_DSL_PC_PASSWORD",
    default=None,
    help="Prism/Nutanix Central password",
)
@click.option(
    "--db_file",
    "-d",
    "db_file",
    envvar="CALM_DSL_DB_LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to local database file",
)
@click.option(
    "--local_dir",
    "-ld",
    envvar="CALM_DSL_LOCAL_DIR_LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="Path to local directory for storing secrets",
)
@click.option(
    "--config",
    "-cf",
    "config_file",
    envvar="CALM_DSL_CONFIG_FILE_LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to config file to store dsl configuration",
)
@click.option(
    "--project",
    "-pj",
    "project_name",
    envvar="CALM_DSL_DEFAULT_PROJECT",
    help="Default project name used for entities",
)
@click.option(
    "--log_level",
    "-l",
    envvar="CALM_DSL_LOG_LEVEL",
    default=DEFAULT_LOG_CONFIG["level"],
    help="Default log level",
)
@click.option(
    "--retries-enabled/--retries-disabled",
    "-re/-rd",
    default=DEFAULT_CONNECTION_CONFIG["retries_enabled"],
    help="Retries enabled/disabled for api connections",
)
@click.option(
    "--connection-timeout",
    "-ct",
    type=int,
    default=DEFAULT_CONNECTION_CONFIG["connection_timeout"],
    help="Connection timeout for api connections",
)
@click.option(
    "--read-timeout",
    "-rt",
    type=int,
    default=DEFAULT_CONNECTION_CONFIG["read_timeout"],
    help="Read timeout for api connections",
)
@click.option(
    "--api-key",
    "-ak",
    "api_key_location",
    default=None,
    help="Path to api key file for authentication",
)
def initialize_engine(
    ip,
    port,
    username,
    password,
    project_name,
    db_file,
    local_dir,
    config_file,
    log_level,
    retries_enabled,
    connection_timeout,
    read_timeout,
    api_key_location,
):
    """
    \b
    Initializes the calm dsl engine.

    NOTE: Env variables(if available) will be used as defaults for configuration
        i.) CALM_DSL_PC_IP: Prism/Nutanix Central Host
        ii.) CALM_DSL_PC_PORT: Prism Central Port (skip for Nutanix Central)
        iii.) CALM_DSL_PC_USERNAME: Prism/Nutanix Central username
        iv.) CALM_DSL_PC_PASSWORD: Prism/Nutanix Central password
        v.) CALM_DSL_DEFAULT_PROJECT: Default project name
        x.) CALM_DSL_CONFIG_FILE_LOCATION: Default config file location where dsl config will be stored
        xi.) CALM_DSL_LOCAL_DIR_LOCATION: Default local directory location to store secrets
        xii.) CALM_DSL_DB_LOCATION: Default internal dsl db location

    """
    if api_key_location:
        api_key_location = os.path.expanduser(api_key_location)
        if not file_exists(api_key_location):
            LOG.error("{} not found".format(api_key_location))
            sys.exit(-1)

    set_server_details(
        ip=ip,
        port=port,
        pc_username=username,
        pc_password=password,
        project_name=project_name,
        db_file=db_file,
        local_dir=local_dir,
        config_file=config_file,
        log_level=log_level,
        retries_enabled=retries_enabled,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
        api_key_location=api_key_location,
    )
    init_db()
    sync_cache()

    click.echo("\nHINT: To get started, follow the 3 steps below:")
    click.echo("1. Initialize an example blueprint DSL: calm init bp")
    click.echo(
        "2. Add vm image details according to your use in generated HelloBlueprint/blueprint.py"
    )
    click.echo(
        "3. Create and validate the blueprint: calm create bp --file HelloBlueprint/blueprint.py"
    )
    click.echo(
        "4. Start an application using the blueprint: calm launch bp Hello --app_name HelloApp01 -i"
    )

    click.echo("\nKeep Calm and DSL On!\n")


def _fetch_cp_feature_status(client):
    """
    Fetch custom provider feature status
    """
    Obj = get_resource_api(
        "features/custom_provider/status", client.connection, calm_api=True
    )
    res, err = Obj.read()
    if err:
        click.echo("[Fail]")
        raise Exception("[{}] - {}".format(err["code"], err["error"]))

    result = json.loads(res.content)
    return result.get("status", {}).get("feature_status", {}).get("is_enabled", False)


def _fetch_ncm_decoupled_status(client):
    """
    Fetch NCM decoupled status

    Returns:
        ncm_enabled: bool
        host (str): PC-FQDN
        ncm_host (str): NCM-FQDN
        ncm_port (str): NCM PORT
    """

    ncm_url = None
    ncm_host = None
    ncm_port = None

    ncm_enabled, ncm_url = is_ncm_enabled(client)

    if ncm_enabled:
        LOG.info("Checking if NCM is enabled on Server")
        ncm_host, ncm_port = fetch_host_port_from_url(ncm_url)
        LOG.info("ENABLED")
        LOG.info("NCM-FQDN is: {}".format(ncm_host))

    return ncm_enabled, ncm_host, ncm_port


def set_server_details(
    ip,
    port,
    pc_username,
    pc_password,
    project_name,
    db_file,
    local_dir,
    config_file,
    log_level,
    retries_enabled,
    connection_timeout,
    read_timeout,
    api_key_location,
):

    LOG.info("Skip port for Nutanix Central, if provided it will be ignored")
    if not (ip and port and pc_username and pc_password and project_name):
        click.echo("Please provide Calm DSL settings:\n")

    host = ip or click.prompt("Prism/Nutanix Central Host", default="")

    if api_key_location:
        cred = get_auth_info(api_key_location)
        pc_username = cred.get("username")
        pc_password = cred.get("password")
        port = DSL_CONFIG.SAAS_PORT
    else:
        port = port or click.prompt("Port", default="9440")
        pc_username = pc_username or click.prompt("Username", default="admin")
        pc_password = pc_password or click.prompt(
            "Password", default="", hide_input=True
        )

    project_name = project_name or click.prompt(
        "Project", default=DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
    )

    nc_host, nc_username, nc_password = host, pc_username, pc_password

    # Do not prompt for init config variables, Take default values for init.ini file
    config_file = config_file or get_default_config_file()
    local_dir = local_dir or get_default_local_dir()
    db_file = db_file or get_default_db_file()

    if port == DSL_CONFIG.SAAS_PORT:
        if api_key_location:
            LOG.info("Authenticating with username: {}".format(pc_username))
        else:
            LOG.warning(DSL_CONFIG.SAAS_LOGIN_WARN)

    (
        client,
        nc_enabled,
        nc_host,
        ncm_enabled,
        ncm_host,
        ncm_port,
    ) = _resolve_client_with_context_update(
        host,
        port,
        pc_username,
        pc_password,
        nc_host,
        nc_username,
        nc_password,
    )

    if nc_enabled and ncm_enabled:
        get_home_pc_uuid(client)

    # NCM not deployed (neither NCM 1.5 nor NCM 2.0+)
    if not nc_enabled and not ncm_enabled:
        # check calm enablement status when NCM is not decoupled
        LOG.info("Checking if Calm is enabled on Server")
        Obj = get_resource_api("services/nucalm/status", client.connection)
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        result = json.loads(res.content)
        service_enablement_status = result["service_enablement_status"]
        LOG.info(service_enablement_status)

    res, err = client.version.get_calm_version()
    if err:
        LOG.error("Failed to get version")
        click.echo("[Fail]")
        sys.exit(err["error"])
    calm_version = res.content.decode("utf-8")

    # get policy status
    if LV(calm_version) >= LV(POLICY.MIN_SUPPORTED_VERSION):
        Obj = get_resource_api("features/policy", client.connection, calm_api=True)
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        policy_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("Policy enabled={}".format(policy_status))
    else:
        LOG.debug("Policy is not supported")
        policy_status = False

    # get approval policy status
    if LV(calm_version) >= LV(POLICY.APPROVAL_POLICY_MIN_SUPPORTED_VERSION):
        Obj = get_resource_api(
            "features/approval_policy", client.connection, calm_api=True
        )
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        approval_policy_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("Approval Policy enabled={}".format(approval_policy_status))
    else:
        LOG.debug("Approval Policy is not supported")
        approval_policy_status = False

    # get stratos status
    if LV(calm_version) >= LV(STRATOS.MIN_SUPPORTED_VERSION):
        Obj = get_resource_api(
            "features/stratos/status", client.connection, calm_api=True
        )
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        stratos_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("stratos enabled={}".format(stratos_status))
    else:
        LOG.debug("Stratos is not supported")
        stratos_status = False

    if LV(calm_version) >= LV(CLOUD_PROVIDERS.MIN_SUPPORTED_VERSION):
        cp_status = _fetch_cp_feature_status(client)
        LOG.info("CP enabled={}".format(cp_status))
    else:
        LOG.debug("Cloud Providers are not supported")
        cp_status = False

    if project_name != DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME:
        LOG.info("Verifying the project details")
        project_name_uuid_map = client.project.get_name_uuid_map(
            params={"filter": "name=={}".format(project_name)}
        )
        if not project_name_uuid_map:
            LOG.error("Project '{}' not found !!!".format(project_name))
            sys.exit(-1)
        LOG.info("Project '{}' verified successfully".format(project_name))

    if api_key_location:
        pc_username = DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
        pc_password = DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME

    # Writing configuration to file
    set_dsl_config(
        host=host,
        port=port,
        username=pc_username,
        password=pc_password,
        ncm_enabled=ncm_enabled,
        ncm_host=ncm_host,
        ncm_port=ncm_port,
        nc_enabled=nc_enabled,
        nc_host=nc_host,
        nc_username=nc_username,
        nc_password=nc_password,
        api_key_location=api_key_location or DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME,
        project_name=project_name,
        log_level=log_level,
        config_file=config_file,
        db_location=db_file,
        local_dir=local_dir,
        policy_status=policy_status,
        approval_policy_status=approval_policy_status,
        stratos_status=stratos_status,
        retries_enabled=retries_enabled,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
        cp_status=cp_status,
    )

    # Updating context for using latest config data
    LOG.info("Updating context for using latest config file data")
    # make sure to use get_context() to get the context object, instead of initializing it in multiple places
    # this will ensure that the context is initialized only once
    # TODO: we should use a singleton pattern for context initialization
    context = get_context()
    # Reset configuration to reload from the saved config file (especially important in NC mode where PC host is discovered)
    context.reset_configuration()

    # Reset global API client handle so it picks up the updated context with correct PC host
    # This is critical in NC mode where PC host is discovered and saved to config after initial client creation
    if nc_enabled:
        reset_api_client_handle()

    if log_level:
        CustomLogging.set_verbose_level(getattr(CustomLogging, log_level))


def init_db():
    LOG.info("Creating local database")
    init_db_handle()


def sync_cache():
    Cache.sync()


@init.command("bp")
@click.option("--name", "-n", "bp_name", default="Hello", help="Name of blueprint")
@click.option(
    "--dir_name", "-d", default=os.getcwd(), help="Directory path for the blueprint"
)
@click.option(
    "--type",
    "-t",
    "provider_type",
    type=click.Choice(get_provider_types()),
    default="AHV_VM",
    help="Provider type",
)
@click.option(
    "--bp_type",
    "-b",
    "blueprint_type",
    type=click.Choice(["SINGLE_VM", "MULTI_VM"]),
    default="MULTI_VM",
    help="Blueprint type",
)
def init_dsl_bp(bp_name, dir_name, provider_type, blueprint_type):
    """Creates a starting directory for blueprint"""

    if not bp_name.isidentifier():
        LOG.error("Blueprint name '{}' is not a valid identifier".format(bp_name))
        sys.exit(-1)

    init_bp(bp_name, dir_name, provider_type, blueprint_type)


@init.command("runbook", feature_min_version="3.0.0", experimental=True)
@click.option("--name", "-n", "runbook_name", default="Hello", help="Name of runbook")
@click.option(
    "--dir_name", "-d", default=os.getcwd(), help="Directory path for the runbook"
)
def init_dsl_runbook(runbook_name, dir_name):
    """Creates a starting directory for runbook"""

    if not runbook_name.isidentifier():
        LOG.error("Runbook name '{}' is not a valid identifier".format(runbook_name))
        sys.exit(-1)

    init_runbook(runbook_name, dir_name)


@init.command("provider", feature_min_version="4.0.0", experimental=True)
@click.option("--name", "-n", "provider_name", default="hello", help="Name of provider")
@click.option(
    "--dir_name", "-d", default=os.getcwd(), help="Directory path for the provider"
)
def init_dsl_provider(provider_name, dir_name):
    """
    Creates a starting file for provider
    """

    if not provider_name.isidentifier():
        LOG.error("Provider name '{}' is not a valid identifier".format(provider_name))
        sys.exit(-1)

    init_provider(provider_name, dir_name)


# @init.command("scheduler", feature_min_version="3.3.0", experimental=True)
# @click.option("--name", "-n", "job_name", default="Hello", help="Name of job")
# @click.option(
#     "--dir_name", "-d", default=os.getcwd(), help="Directory path for the scheduler"
# )
# def init_dsl_scheduler(job_name, dir_name):
#     """Creates a starting directory for runbook"""
#
#     if not job_name.isidentifier():
#         LOG.error("Job name '{}' is not a valid identifier".format(job_name))
#         sys.exit(-1)
#
#     init_scheduler(job_name, dir_name)


@set.command("config")
@click.option(
    "--ip",
    "-i",
    "host",
    envvar="PRISM_SERVER_IP",
    default=None,
    help="Prism/Nutanix Central server IP or hostname",
)
@click.option(
    "--port",
    "-P",
    envvar="PRISM_SERVER_PORT",
    default=None,
    help="Prism Central server port number(skip for Nutanix Central)",
)
@click.option(
    "--username",
    "-u",
    "pc_username",
    envvar="PRISM_USERNAME",
    default=None,
    help="Prism/Nutanix Central username",
)
@click.option(
    "--password",
    "-p",
    "pc_password",
    envvar="PRISM_PASSWORD",
    default=None,
    help="Prism/Nutanix Central password",
)
@click.option("--project", "-pj", "project_name", help="Project name for entity")
@click.option(
    "--db_file",
    "-d",
    "db_location",
    envvar="DATABASE_LOCATION",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path to local database file",
)
@click.option(
    "--local_dir",
    "-ld",
    envvar="LOCAL_DIR",
    default=None,
    type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True),
    help="Path to local directory for storing secrets",
)
@click.option("--log_level", "-l", default=None, help="Default log level")
@click.option(
    "--retries-enabled/--retries-disabled",
    "-re/-rd",
    default=None,
    help="Retries enabled/disabled",
)
@click.option(
    "--connection-timeout",
    "-ct",
    type=int,
    help="connection timeout",
)
@click.option(
    "--read-timeout",
    "-rt",
    type=int,
    help="read timeout",
)
@click.option(
    "--api-key",
    "-ak",
    "api_key_location",
    default=None,
    help="Path to api key file for authentication",
)
@click.argument("config_file", required=False)
def _set_config(
    host,
    port,
    pc_username,
    pc_password,
    project_name,
    db_location,
    log_level,
    config_file,
    local_dir,
    retries_enabled,
    connection_timeout,
    read_timeout,
    api_key_location,
):
    """writes the configuration to config files i.e. config.ini and init.ini

    \b
    Note: Cache will be updated if supplied host is different from configured host.
    """

    LOG.info("Skip port for Nutanix Central, if provided it will be ignored")

    # Fetching context object
    context = get_context()

    server_config = context.get_server_config()

    # Update cache if there is change in host ip
    update_cache = host != server_config["pc_ip"] if host else False
    host = host or server_config["pc_ip"]

    # Reading api key location and port from config if not provided
    api_key_location = api_key_location or server_config.get(
        "api_key_location", DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
    )

    # Resetting stored location of api key (for PC login case)
    if api_key_location != DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME:
        api_key_location = os.path.expanduser(api_key_location)
    else:
        api_key_location = None

    port = port or server_config["pc_port"]

    cred = get_auth_info(api_key_location)
    stored_username = cred.get("username")
    stored_password = cred.get("password")

    pc_username = pc_username or stored_username
    pc_password = pc_password or stored_password
    project_config = context.get_project_config()
    project_name = project_name or project_config.get("name")

    if port == DSL_CONFIG.SAAS_PORT:
        if api_key_location:
            LOG.info("Authenticating with username: {}".format(pc_username))
        else:
            LOG.warning(DSL_CONFIG.SAAS_LOGIN_WARN)

    nc_config = context.get_nc_server_config()

    nc_enabled = nc_config.get("enabled", False)
    nc_host = host or nc_config.get("host", "")
    nc_username = pc_username or nc_config.get("username", "")
    nc_password = pc_password or nc_config.get("password", "")

    nc_host, nc_username, nc_password = host, pc_username, pc_password

    (
        client,
        nc_enabled,
        nc_host,
        ncm_enabled,
        ncm_host,
        ncm_port,
    ) = _resolve_client_with_context_update(
        host,
        port,
        pc_username,
        pc_password,
        nc_host,
        nc_username,
        nc_password,
    )

    if nc_enabled and ncm_enabled:
        get_home_pc_uuid(client)

    # NCM not deployed (neither NCM 1.5 nor NCM 2.0+)
    if not nc_enabled and not ncm_enabled:
        # check calm enablement status when NCM is not decoupled
        LOG.info("Checking if Calm is enabled on Server")
        Obj = get_resource_api("services/nucalm/status", client.connection)
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))

        result = json.loads(res.content)
        service_enablement_status = result["service_enablement_status"]
        LOG.info(service_enablement_status)

    res, err = client.version.get_calm_version()
    if err:
        LOG.error("Failed to get version")
        click.echo("[Fail]")
        sys.exit(err["error"])
    calm_version = res.content.decode("utf-8")

    # get policy status
    if LV(calm_version) >= LV(POLICY.MIN_SUPPORTED_VERSION):
        Obj = get_resource_api("features/policy", client.connection, calm_api=True)
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        policy_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("Policy enabled={}".format(policy_status))
    else:
        LOG.debug("Policy is not supported")
        policy_status = False

    # get approval policy status
    if LV(calm_version) >= LV(POLICY.APPROVAL_POLICY_MIN_SUPPORTED_VERSION):
        Obj = get_resource_api(
            "features/approval_policy", client.connection, calm_api=True
        )
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        approval_policy_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("Approval Policy enabled={}".format(approval_policy_status))
    else:
        LOG.debug("Approval Policy is not supported")
        approval_policy_status = False

    # get stratos status
    if LV(calm_version) >= LV(STRATOS.MIN_SUPPORTED_VERSION):
        Obj = get_resource_api(
            "features/stratos/status", client.connection, calm_api=True
        )
        res, err = Obj.read()

        if err:
            click.echo("[Fail]")
            raise Exception("[{}] - {}".format(err["code"], err["error"]))
        result = json.loads(res.content)
        stratos_status = (
            result.get("status", {}).get("feature_status", {}).get("is_enabled", False)
        )
        LOG.info("stratos enabled={}".format(stratos_status))
    else:
        LOG.debug("Stratos is not supported")
        stratos_status = False

    if LV(calm_version) >= LV(CLOUD_PROVIDERS.MIN_SUPPORTED_VERSION):
        cp_status = _fetch_cp_feature_status(client)
        LOG.info("CP enabled={}".format(cp_status))
    else:
        LOG.debug("Cloud Providers are not supported")
        cp_status = False

    if project_name != DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME:
        LOG.info("Verifying the project details")
        project_name_uuid_map = client.project.get_name_uuid_map(
            params={"filter": "name=={}".format(project_name)}
        )
        if not project_name_uuid_map:
            LOG.error("Project '{}' not found !!!".format(project_name))
            sys.exit(-1)
        LOG.info("Project '{}' verified successfully".format(project_name))

    log_config = context.get_log_config()
    log_level = log_level or log_config.get("level") or "INFO"

    # Take init_configuration from user params or init file
    init_config = context.get_init_config()
    config_file = (
        config_file or context._CONFIG_FILE or init_config["CONFIG"]["location"]
    )
    db_location = db_location or init_config["DB"]["location"]
    local_dir = local_dir or init_config["LOCAL_DIR"]["location"]

    # Get connection config
    connection_config = context.get_connection_config()
    if retries_enabled is None:  # Not supplied in command
        retries_enabled = connection_config["retries_enabled"]
    connection_timeout = connection_timeout or connection_config["connection_timeout"]
    read_timeout = read_timeout or connection_config["read_timeout"]

    if api_key_location:
        pc_username = DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME
        pc_password = DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME

    # Set the dsl configuration
    set_dsl_config(
        host=host,
        port=port,
        username=pc_username,
        password=pc_password,
        ncm_enabled=ncm_enabled,
        ncm_host=ncm_host,
        ncm_port=ncm_port,
        nc_enabled=nc_enabled,
        nc_host=nc_host,
        nc_username=nc_username,
        nc_password=nc_password,
        api_key_location=api_key_location or DSL_CONFIG.EMPTY_CONFIG_ENTITY_NAME,
        project_name=project_name,
        db_location=db_location,
        log_level=log_level,
        local_dir=local_dir,
        config_file=config_file,
        policy_status=policy_status,
        approval_policy_status=approval_policy_status,
        stratos_status=stratos_status,
        retries_enabled=retries_enabled,
        connection_timeout=connection_timeout,
        read_timeout=read_timeout,
        cp_status=cp_status,
    )
    LOG.info("Configuration changed successfully")

    # Updating context for using latest config data
    # make sure to use get_context() to get the context object, instead of initializing it in multiple places
    # this will ensure that the context is initialized only once
    # TODO: we should use a singleton pattern for context initialization
    get_context()
    # Reset configuration to reload from the saved config file (especially important in NC mode where PC host is discovered)
    context.reset_configuration()

    # Reset global API client handle so it picks up the updated context with correct PC host
    # This is critical in NC mode where PC host is discovered and saved to config after initial client creation
    if nc_enabled:
        reset_api_client_handle()

    if update_cache:
        sync_cache()


def _resolve_client_with_context_update(
    host: str,
    port: str,
    pc_username: str,
    pc_password: str,
    nc_host: str,
    nc_username: str,
    nc_password: str,
):
    """
    Resolves the client and update the context with NC and NCM information.
    """
    client = None
    ncm_host = None
    ncm_port = None
    nc_enabled = False
    ncm_enabled = False

    context = get_context()
    context.update_pc_server_context(host, port, pc_username, pc_password)

    # Create a temporary client handle
    client = get_nc_multi_client_handle(
        host,
        port,
        nc_host,
        pc_auth=(pc_username, pc_password),
        nc_auth=(nc_username, nc_password),
    )

    # Check if given host is a NC host
    try:
        Obj = get_resource_api(
            "internal/healthz",
            client.connection.nc_connection,
            override_connection=True,
        )
        _, err = Obj.read(ignore_error=True)

        # successful hit to this api is only possible if NC is supplied as host
        nc_enabled = err is None

    except Exception:
        nc_enabled = False

    # If pc host is given, Retrieve NC host
    if not nc_enabled:
        # to avoid using old details from config
        context.update_nc_server_context(nc_enabled, nc_host, nc_username, nc_password)
        nc_enabled, nc_host = is_nc_enabled(client)

    # use NC FQDN if NCM comes with the NC
    if nc_enabled:
        # update the nc_server_config in DSL context to use it for the API routing
        context.update_nc_server_context(nc_enabled, nc_host, nc_username, nc_password)

        client = get_nc_multi_client_handle(
            host,
            port,
            nc_host,
            pc_auth=(pc_username, pc_password),
            nc_auth=(nc_username, nc_password),
        )

        ncm_host = MULTICONNECT.NC_NCM_SUBDOMAIN + "." + nc_host
        # update the ncm_server_config in DSL context to use it for the API routing
        ncm_enabled, _ = is_ncm_enabled(client)
        context.update_ncm_server_context(ncm_enabled, ncm_host, ncm_port)

    else:
        # disable nc_server_config in DSL context
        context.update_nc_server_context(nc_enabled, nc_host, nc_username, nc_password)

        # Get NCM-FQDN using temporary client handle
        client = get_client_handle_obj(host, port, auth=(pc_username, pc_password))
        ncm_enabled, ncm_host, ncm_port = _fetch_ncm_decoupled_status(client)

        if ncm_enabled:
            client = get_multi_client_handle_obj(
                host, port, ncm_host, ncm_port, auth=(pc_username, pc_password)
            )
        # update the ncm_server_config in DSL context to use it for the API routing
        context.update_ncm_server_context(ncm_enabled, ncm_host, ncm_port)

    return client, nc_enabled, nc_host, ncm_enabled, ncm_host, ncm_port
