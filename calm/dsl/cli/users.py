import click
import json
import sys
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.builtins import Ref
from calm.dsl.store import Cache
from calm.dsl.constants import CACHE, USER
from calm.dsl.log import get_logging_handle

from .utils import get_name_query, highlight_text
from .task_commands import watch_task
from .constants import ERGON_TASK


LOG = get_logging_handle(__name__)


def get_users(name, filter_by, limit, offset, quiet, out):
    """Get the users, optionally filtered by a string"""

    client = get_api_client()

    # TODO: Explore on ways to add filter by name and filter by status for v4 API

    res, err = client.user.list_all(select=USER.ALL_ATTRIBUTES, ignore_error=False)

    if err:
        ContextObj = get_context()
        server_config = ContextObj.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch users from {}".format(pc_ip))
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
        click.echo(highlight_text("No user found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            click.echo(highlight_text(_row["username"]))
        return

    table = PrettyTable()
    table.field_names = ["NAME", "DISPLAY NAME", "TYPE", "STATE", "UUID"]

    for _row in json_rows:

        table.add_row(
            [
                highlight_text(_row["username"]),
                highlight_text(_row.get("displayName", "")),
                highlight_text(_row.get("userType", "")),
                highlight_text(_row.get("status", "")),
                highlight_text(_row.get("extId", "")),
            ]
        )

    click.echo(table)


def create_user(
    name,
    first_name,
    last_name,
    display_name="",
    password=None,
    directory_service=None,
    user_type="LOCAL",
):
    """
    Create a user using IAM v4 API

    Args:
        name: Username (user principal name)
        first_name (REQUIRED in v4 API): User's first name
        last_name (REQUIRED in v4 API): User's last name
        display_name (Optional): User's display name  if not provided, first name will be used
        password: User's password (REQUIRED for LOCAL/SERVICE_ACCOUNT users)
        directory_service: Directory service name (required for LDAP/SAML)
        user_type: User type (LDAP, LOCAL, SERVICE_ACCOUNT, SAML, EXTERNAL)

    V4 API Required Fields:
        - username: string [1..255 chars], pattern: ^[^<>;'()&+%\/\\"`]*$
        - firstName: string (REQUIRED)
        - lastName: string (REQUIRED)
        - password: string (REQUIRED for LOCAL/SERVICE_ACCOUNT users)
        - userType: enum (SERVICE_ACCOUNT, LDAP, EXTERNAL, LOCAL, SAML)
    """
    client = get_api_client()

    user_name_uuid_map = client.user.get_name_uuid_map(limit=1000)

    if user_name_uuid_map.get(name):
        LOG.error("User with name {} already exists".format(name))
        sys.exit("User with name {} already exists".format(name))

    # display name can't be empty in api payload
    if not display_name:
        display_name = name

    # Build v4 payload with REQUIRED fields
    user_payload = {
        "username": name,
        "firstName": first_name,
        "lastName": last_name,
        "userType": user_type,
        "displayName": display_name,
    }

    # Password is REQUIRED for LOCAL and SERVICE_ACCOUNT users
    if user_type in ["LOCAL", "SERVICE_ACCOUNT"]:
        if not password:
            LOG.error("Password is required for user type '{}'".format(user_type))
            sys.exit("Password is required")
        user_payload["password"] = password

    elif password:
        # For LDAP/SAML/EXTERNAL users, password might still be accepted
        user_payload["password"] = password

    # Add idpId only for directory service users
    if user_type in ["LDAP", "SAML"]:
        if not directory_service:
            LOG.error(
                "Directory service is required for user type '{}'".format(user_type)
            )
            sys.exit(
                "Directory service is required for user type '{}'".format(user_type)
            )

        try:
            cache_data = Cache.get_entity_data(
                entity_type=CACHE.ENTITY.DIRECTORY_SERVICE, name=directory_service
            )
            if cache_data:
                idp_id = cache_data.get("uuid")
                if idp_id:
                    user_payload["idpId"] = idp_id
                else:
                    LOG.error(
                        "Directory service '{}' has no UUID in cache".format(
                            directory_service
                        )
                    )
                    sys.exit(
                        "Directory service '{}' has no UUID in cache".format(
                            directory_service
                        )
                    )
            else:
                LOG.error(
                    "Directory service '{}' not found in cache. "
                    "Please run 'calm update cache' to sync directory services.".format(
                        directory_service
                    )
                )
                sys.exit(
                    "Directory service '{}' not found in cache.".format(
                        directory_service
                    )
                )
        except Exception as e:
            LOG.error(
                "Directory service '{}' not found in cache"
                "Please run 'calm update cache' to sync directory services.".format(
                    directory_service
                )
            )
            sys.exit("Directory service '{}' not found in cache")

    LOG.info(
        "Creating user with payload (password hidden): {}".format(
            dict((k, "***" if k == "password" else v) for k, v in user_payload.items())
        )
    )
    res, err = client.user.create(user_payload)
    if err:
        LOG.error(err)
        sys.exit("user {} creation failed".format(name))

    res = res.json()

    user_data = res.get("data", {})
    user_ext_id = user_data.get("extId")

    if not user_ext_id:
        LOG.error("Failed to get user extId from response")
        LOG.debug(f"Response: {res}")
        sys.exit(-1)

    stdout_dict = {
        "name": name,
        "username": user_data.get("username"),
        "uuid": user_ext_id,
        "displayName": user_data.get("displayName"),
        "userType": user_data.get("userType"),
    }
    click.echo(json.dumps(stdout_dict, indent=4, separators=(",", ": ")))

    # Update users in cache
    LOG.info("Updating users cache ...")
    Cache.add_one(entity_type=CACHE.ENTITY.USER, uuid=user_ext_id)
    LOG.info("[Done]")


def delete_user(user_names):

    client = get_api_client()
    user_name_uuid_map = client.user.get_name_uuid_map(limit=1000)

    deleted_user_uuids = []
    for name in user_names:
        user_uuid = user_name_uuid_map.get(name, "")
        if not user_uuid:
            LOG.error("User {} doesn't exists".format(name))
            sys.exit(-1)

        res, err = client.user.delete(user_uuid)
        if err:
            LOG.exception("[{}] - {}".format(err["code"], err["error"]))
            sys.exit(-1)

        deleted_user_uuids.append(user_uuid)
        LOG.info("Polling on user deletion task")
        res = res.json()
        task_state = watch_task(
            res["status"]["execution_context"]["task_uuid"], poll_interval=5
        )
        if task_state in ERGON_TASK.FAILURE_STATES:
            LOG.exception("User deletion task went to {} state".format(task_state))
            sys.exit(-1)

    # Update users in cache
    if deleted_user_uuids:
        LOG.info("Updating users cache ...")
        for _user_uuid in deleted_user_uuids:
            Cache.delete_one(entity_type=CACHE.ENTITY.USER, uuid=_user_uuid)
        LOG.info("[Done]")


def deactivate_users(user_names=[]):
    """Deactivate users by setting their state to INACTIVE"""

    client = get_api_client()
    user_name_uuid_map = client.user.get_name_uuid_map(limit=1000)

    deactivated_user_uuids = []
    for name in user_names:
        # Get the user UUID (extId) - handle both list and string formats
        user_uuid = user_name_uuid_map.get(name, [])
        if not user_uuid:
            LOG.warning("User {} doesn't exist".format(name))
            continue

        user_uuid = user_uuid[0]

        LOG.info("Deactivating user: {}".format(name))

        # Call the IAM v4 API to update user state to INACTIVE
        res, err = client.user.update_state(user_uuid, USER.STATE.INACTIVE)

        if err:
            LOG.error("Failed to deactivate user: {}".format(name))
            sys.exit("Failed to deactivate user: {}".format(name))

        res = res.json()
        LOG.info(
            "User {} (UUID: {}) has been deactivated successfully".format(
                name, user_uuid
            )
        )

        deactivated_user_uuids.append(user_uuid)

    # Update users in cache
    Cache.sync_table(CACHE.ENTITY.USER)
    LOG.info("[Done]")

    return deactivated_user_uuids
