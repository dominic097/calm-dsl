import click
import json
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.builtins import Ref
from .task_commands import watch_task
from .constants import ERGON_TASK
from calm.dsl.config import get_context
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE
from calm.dsl.log import get_logging_handle

from .utils import get_name_query, highlight_text


LOG = get_logging_handle(__name__)


def get_groups(name, filter_by, limit, offset, quiet, out):
    """Get the groups, optionally filtered by a string"""

    client = get_api_client()

    res, err = client.user_group.list()

    if err:
        context = get_context()
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch groups from {}".format(pc_ip))
        return

    total_matches = len(res)
    if total_matches > limit:
        LOG.warning(
            "Displaying {} out of {} entities. Please use --limit and --offset option for more results.".format(
                limit, total_matches
            )
        )

    if out == "json":
        click.echo(json.dumps(res, indent=4, separators=(",", ": ")))
        return

    json_rows = res
    if not json_rows:
        click.echo(highlight_text("No group found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            click.echo(highlight_text(_row["name"]))
        return

    table = PrettyTable()
    table.field_names = ["NAME", "DISTINGUISHED NAME", "TYPE", "UUID", "IDP ID"]

    for _row in json_rows:
        table.add_row(
            [
                highlight_text(_row["name"]),
                highlight_text(_row.get("distinguishedName", "")),
                highlight_text(_row.get("groupType", "")),
                highlight_text(_row.get("extId", "")),
                highlight_text(_row.get("idpId", "")),
            ]
        )

    click.echo(table)


def create_group(name, directory_service, distinguished_name):
    """
    Creates LDAP user-group on pc using IAM v4 API.

    Args:
        name (str): Common name of the user group (required)
        directory_service (str): Directory service name (required)
        distinguished_name (str): Distinguished name of the user group (optional)

    V4 API Required Fields:
        - name: string
        - groupType: enum (LDAP, SAML) - defaulted to LDAP
        - idpId: string (UUID format) - resolved from directory service
        - distinguishedName: string <= 255 characters
    """

    client = get_api_client()

    # Validate required parameters
    if not name:
        LOG.error("Name is required")
        sys.exit(-1)

    if not directory_service:
        LOG.error("Directory service name is required")
        sys.exit(-1)

    cache_data = Cache.get_entity_data(
        entity_type=CACHE.ENTITY.DIRECTORY_SERVICE, name=directory_service
    )

    if cache_data:
        idp_id = cache_data.get("uuid")
        if not idp_id:
            LOG.error(
                "Directory service '{}' has no UUID in cache".format(directory_service)
            )
            sys.exit(
                "Directory service '{}' has no UUID in cache".format(directory_service)
            )
        LOG.info(
            "Resolved directory service '{}' to IDP ID: {}".format(
                directory_service, idp_id
            )
        )
    else:
        LOG.error(
            "Directory service '{}' not found in cache. "
            "Please run 'calm update cache' to sync directory services.".format(
                directory_service
            )
        )
        sys.exit("Directory service '{}' not found in cache.".format(directory_service))

    # Build IAM v4 API payload
    group_payload = {
        "groupType": "LDAP",
        "idpId": idp_id,
        "name": name,
        "distinguishedName": distinguished_name,
    }

    LOG.info("Creating LDAP user group '{}' with IDP ID '{}'".format(name, idp_id))
    LOG.debug(
        "Creating user group with payload: {}".format(
            json.dumps(group_payload, indent=2)
        )
    )

    # Create the user group using IAM v4 API
    res, err = client.user_group.create(group_payload)
    if err:
        LOG.error(
            "[{}] - {}".format(err.get("code", "ERROR"), err.get("error", str(err)))
        )
        sys.exit(
            "[{}] - {}".format(err.get("code", "ERROR"), err.get("error", str(err)))
        )

    res = res.json()

    # IAM v4 API returns data in 'data' field, not 'metadata'/'status'
    group_data = res.get("data", {})

    if not group_data:
        LOG.error("Failed to create user group - no data returned")
        sys.exit("Failed to create user group - no data returned")

    stdout_dict = {
        "name": group_data.get("name"),
        "uuid": group_data.get("extId"),
    }

    LOG.info("User group created successfully")
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))


def delete_group(group_names):
    """deletes user-group on pc"""

    client = get_api_client()

    deleted_group_uuids = []
    for name in group_names:
        group_ref = Ref.Group(name)
        res, err = client.user_group.delete(group_ref["uuid"])
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        deleted_group_uuids.append(group_ref["uuid"])
        LOG.info("Polling on user-group deletion task")
        res = res.json()
        task_state = watch_task(
            res["status"]["execution_context"]["task_uuid"], poll_interval=5
        )
        if task_state in ERGON_TASK.FAILURE_STATES:
            LOG.exception(
                "User-Group deletion task went to {} state".format(task_state)
            )
            sys.exit(-1)

    # Update user-groups in cache
    if deleted_group_uuids:
        LOG.info("Updating user-groups cache ...")
        for _group_uuid in deleted_group_uuids:
            Cache.delete_one(entity_type=CACHE.ENTITY.USER_GROUP, uuid=_group_uuid)
        LOG.info("[Done]")
