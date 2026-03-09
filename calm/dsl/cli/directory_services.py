import click
import json
from prettytable import PrettyTable

from calm.dsl.api import get_api_client
from calm.dsl.config import get_context
from calm.dsl.log import get_logging_handle

from .utils import get_name_query, highlight_text


LOG = get_logging_handle(__name__)


def get_directory_services(name, filter_by, limit, offset, quiet, out):
    """Get the directory services, optionally filtered by a string"""

    client = get_api_client()

    # TODO: Add filter_by in future according to new v4 api structure

    res, err = client.directory_service.list()

    if err:
        context = get_context()
        server_config = context.get_server_config()
        pc_ip = server_config["pc_ip"]

        LOG.warning("Cannot fetch directory_services from {}".format(pc_ip))
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
        click.echo(highlight_text("No directory service found !!!\n"))
        return

    if quiet:
        for _row in json_rows:
            click.echo(highlight_text(_row["name"]))
        return

    table = PrettyTable()
    table.field_names = [
        "NAME",
        "DIRECTORY TYPE",
        "DOMAIN NAME",
        "URL",
        "UUID",
        "TENANT ID",
    ]

    for _row in json_rows:

        table.add_row(
            [
                highlight_text(_row["name"]),
                highlight_text(_row.get("directoryType", "")),
                highlight_text(_row.get("domainName", "")),
                highlight_text(_row.get("url", "")),
                highlight_text(_row.get("extId", "")),
                highlight_text(_row.get("tenantId", "")),
            ]
        )

    click.echo(table)
