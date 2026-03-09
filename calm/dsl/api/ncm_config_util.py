from calm.dsl.config import get_context
from calm.dsl.config.constants import CONFIG


def is_nc_enabled_by_config():
    """
    This helper returns whether NC is enabled for a setup
    """
    context = get_context()
    nc_server_config = context.get_nc_server_config()
    return nc_server_config.get(CONFIG.NC_SERVER.ENABLED, False)


def is_ncm_enabled_by_config():
    """
    This helper returns whether NCM is enabled for a setup (defined in a config file)
    """
    context = get_context()
    ncm_server_config = context.get_ncm_server_config()
    return ncm_server_config.get(CONFIG.NCM_SERVER.NCM_ENABLED, False)
