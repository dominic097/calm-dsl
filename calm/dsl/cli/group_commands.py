import click

from .groups import get_groups, create_group, delete_group
from .main import get, create, delete


@get.command("groups")
@click.option("--name", "-n", default=None, help="Search for groups by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter groups by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option(
    "--quiet", "-q", is_flag=True, default=False, help="Show only group names"
)
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_groups(name, filter_by, limit, offset, quiet, out):
    """Get groups, optionally filtered by a string"""

    get_groups(name, filter_by, limit, offset, quiet, out)


@create.command("group")
@click.option("--name", "-n", required=True, help="Common name of the user group")
@click.option(
    "--directory",
    "-d",
    "directory_service",
    required=True,
    help="Name of the directory service",
)
@click.option(
    "--distinguished-name",
    "-dn",
    "distinguished_name",
    required=True,
    help="Distinguished name of the user group",
)
def _create_group(name, directory_service, distinguished_name):
    """Creates a user-group

    \b
    Example:
      calm create group -n "grp123" -d "MyDirectory" -dn "cn=Grp123,cn=users,dc=domain1,dc=com"
    """

    create_group(name, directory_service, distinguished_name)


@delete.command("group")
@click.argument("group_names", nargs=-1)
def _delete_group(group_names):
    """Deletes a group"""

    delete_group(group_names)
