import click
import json
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle
from calm.dsl.constants import ROLE

from .utils import get_name_query, highlight_text


LOG = get_logging_handle(__name__)


def get_roles(name, filter_by, limit, offset, quiet, out):
    """Get the roles, optionally filtered by a string"""

    client = get_api_client()
    ContextObj = get_context()
    server_config = ContextObj.get_server_config()

    # TODO: Explore on ways to add filter by name and filter by status for v4 API

    res, err = client.role.list_all(select=ROLE.ALL_ATTRIBUTES, ignore_error=False)

    if err:
        pc_ip = server_config["pc_ip"]
        LOG.warning("Cannot fetch roles from {}".format(pc_ip))
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
        click.echo(highlight_text("No role found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            click.echo(highlight_text(_row["name"]))
        return

    table = PrettyTable()
    table.field_names = ["NAME", "UUID", "DESCRIPTION"]

    for _row in json_rows:

        table.add_row(
            [
                highlight_text(_row["displayName"]),
                highlight_text(_row.get("extId", "")),
                highlight_text(_row.get("description", "")),
            ]
        )

    click.echo(table)
