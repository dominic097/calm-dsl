import sys
import time

from calm.dsl.api import get_api_client
from calm.dsl.log import get_logging_handle
from calm.dsl.config import get_context
from calm.dsl.api.ncm_config_util import is_nc_enabled_by_config

LOG = get_logging_handle(__name__)


def get_variable_value_options(
    entity_type, entity_uuid, var_uuid, poll_interval=10, is_global=False
):
    """returns dynamic variable values and api exception if occured"""

    client = get_api_client()
    ENTITY_TYPE_TO_API_CLIENT_MAP = {
        "blueprint": client.blueprint,
        "runbook": client.runbook,
        "marketplace_item": client.market_place,
    }

    payload = {}
    if is_global:
        res, _ = client.global_variable.values(uuid=var_uuid, payload=payload)
    else:
        res, _ = ENTITY_TYPE_TO_API_CLIENT_MAP[entity_type].variable_values(
            uuid=entity_uuid, var_uuid=var_uuid, payload=payload
        )

    var_task_data = res.json()

    # req_id and trl_id are necessary
    payload = {
        "requestId": var_task_data["request_id"],
        "trlId": var_task_data["trl_id"],
    }
    # Poll till completion of epsilon task
    maxWait = 5 * 60
    count = 0
    while count < maxWait:
        if is_global:
            res, err = client.global_variable.values(uuid=var_uuid, payload=payload)
        else:
            res, err = ENTITY_TYPE_TO_API_CLIENT_MAP[entity_type].variable_values(
                uuid=entity_uuid, var_uuid=var_uuid, payload=payload
            )

        # If there is exception during variable api call, it would be silently ignored
        if err:
            return list(), err

        var_val_data = res.json()
        if var_val_data["state"] == "SUCCESS":
            return var_val_data["values"], None

        count += poll_interval
        time.sleep(poll_interval)

    LOG.error("Waited for 5 minutes for dynamic variable evaludation")
    sys.exit(-1)


def url_builder(resource):
    """builds url for the resource"""

    context = get_context()

    if is_nc_enabled_by_config():
        nc_server_config = context.get_nc_server_config()
        nc_host = nc_server_config.get("host", None)
        return "https://{}/services/self_service/{}".format(nc_host, resource)
    else:
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]
        pc_port = server_config["pc_port"]
        return "https://{}:{}/dm/self_service/{}".format(pc_ip, pc_port, resource)
