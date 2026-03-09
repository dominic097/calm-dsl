import click

from calm.dsl.api.ncm_config_util import is_nc_enabled_by_config
from calm.dsl.log import get_logging_handle
from .users import get_users, create_user, delete_user, deactivate_users
from .main import get, create, delete, deactivate

LOG = get_logging_handle(__name__)


@get.command("users")
@click.option("--name", "-n", default=None, help="Search for users by name")
@click.option(
    "--filter", "filter_by", "-f", default=None, help="Filter users by this string"
)
@click.option("--limit", "-l", default=20, help="Number of results to return")
@click.option(
    "--offset", "-s", default=0, help="Offset results by the specified amount"
)
@click.option("--quiet", "-q", is_flag=True, default=False, help="Show only user names")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format",
)
def _get_users(name, filter_by, limit, offset, quiet, out):
    """Get users, optionally filtered by a string"""

    get_users(name, filter_by, limit, offset, quiet, out)


@create.command("user")
@click.option("--name", "-n", required=True, help="Username (user principal name)")
@click.option("--first-name", "-f", required=True, help="User's first name")
@click.option("--last-name", "-l", required=True, help="User's last name")
@click.option(
    "--display-name", "-dn", "display_name", default="", help="User's display name"
)
@click.option(
    "--password",
    "-p",
    default=None,
    help="User's password",
    prompt=False,
    hide_input=True,
)
@click.option(
    "--directory",
    "-d",
    "directory_service",
    default=None,
    help="Directory Service name (required for LDAP/SAML users)",
)
@click.option(
    "--user-type",
    "-t",
    default="LOCAL",
    type=click.Choice(["LOCAL", "LDAP", "SAML", "SERVICE_ACCOUNT", "EXTERNAL"]),
    help="User type (default: LOCAL)",
)
def _create_user(
    name,
    first_name,
    last_name,
    display_name="",
    password=None,
    directory_service=None,
    user_type="LOCAL",
):
    """Creates a user using IAM v4 API

    Required parameters:
    - name: Username/user principal name
    - first-name: User's first name
    - last-name: User's last name
    - password: User's password

    Optional parameters:
    - directory: Directory service (required for LDAP/SAML users)
    - user-type: Type of user (LOCAL, LDAP, SAML, SERVICE_ACCOUNT, EXTERNAL)
    - display-name: User's display name
    """
    create_user(
        name,
        first_name,
        last_name,
        display_name=display_name,
        password=password,
        directory_service=directory_service,
        user_type=user_type,
    )


@delete.command("user")
@click.argument("user_names", nargs=-1)
def _delete_user(user_names):
    """Deletes a user"""

    # delete user is same as deactivate user (UI behaves similarly)
    deactivate_users(user_names)


@deactivate.command("user")
@click.argument("user_names", nargs=-1)
def _deactivate_user(user_names):
    """Deactivates a user"""

    deactivate_users(user_names)
