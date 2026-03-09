import click

from .marketplace_commands_main import (
    marketplace_get,
    marketplace_describe,
    marketplace_approve,
    marketplace_publish,
    marketplace_update,
    marketplace_delete,
    marketplace_reject,
    marketplace_run,
    publish,
)
from .marketplace import (
    get_marketplace_items,
    describe_marketplace_item,
    publish_runbook_as_new_marketplace_item,
    publish_runbook_as_existing_marketplace_item,
    approve_marketplace_item,
    publish_marketplace_item,
    update_marketplace_item,
    delete_marketplace_item,
    reject_marketplace_item,
    execute_marketplace_runbook,
)
from .constants import MARKETPLACE_ITEM

APP_STATES = [
    MARKETPLACE_ITEM.STATES.PENDING,
    MARKETPLACE_ITEM.STATES.ACCEPTED,
    MARKETPLACE_ITEM.STATES.REJECTED,
    MARKETPLACE_ITEM.STATES.PUBLISHED,
]
APP_SOURCES = [
    MARKETPLACE_ITEM.SOURCES.GLOBAL,
    MARKETPLACE_ITEM.SOURCES.LOCAL,
]


# TODO Add limit and offset
@marketplace_get.command("runbooks", feature_min_version="3.2.0")
@click.option("--name", "-n", default=None, help="Filter by name of NCM store runbooks")
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    default=False,
    help="Show only NCM store runbooks names",
)
@click.option(
    "--app_family",
    "-f",
    default="All",
    help="Filter by app family category of NCM store runbooks",
)
@click.option(
    "--app_state",
    "-a",
    "app_states",
    type=click.Choice(APP_STATES),
    multiple=True,
    help="filter by state of NCM store runbooks",
)
@click.option(
    "--filter",
    "filter_by",
    "-fb",
    default=None,
    help="Filter NCM store runbooks by this string",
)
def _get_marketplace_runbooks(name, quiet, app_family, app_states, filter_by):
    """Get NCM store manager runbooks"""

    get_marketplace_items(
        name=name,
        quiet=quiet,
        app_family=app_family,
        app_states=app_states,
        filter_by=filter_by,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )


@marketplace_describe.command("runbook", feature_min_version="3.2.0")
@click.argument("name")
@click.option(
    "--out",
    "-o",
    "out",
    type=click.Choice(["text", "json"]),
    default="text",
    help="output format.",
)
@click.option("--version", "-v", default=None, help="Version of NCM store runbooks")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of NCM store runbook",
)
@click.option(
    "--app_state",
    "-a",
    default=None,
    type=click.Choice(APP_STATES),
    help="State of NCM store runbook",
)
def _describe_marketplace_runbook(name, out, version, source, app_state):
    """Describe a NCM store manager runbook"""

    describe_marketplace_item(
        name=name, out=out, version=version, app_source=source, app_state=app_state
    )


@marketplace_approve.command("runbook", feature_min_version="3.2.0")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of NCM store runbook")
@click.option("--category", "-c", default=None, help="Category for NCM store runbook")
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Add projects to NCM store runbook",
)
@click.option(
    "--remove-project",
    "-rp",
    "remove_projects",
    multiple=True,
    help="Remove projects from NCM store runbook",
)
@click.option(
    "--all_projects",
    "-ap",
    is_flag=True,
    default=False,
    help="Approve runbook to all runbook",
)
def approve_runbook(
    name, version, category, all_projects, projects=[], remove_projects=[]
):
    """Approves a NCM store manager runbook"""

    approve_marketplace_item(
        name=name,
        version=version,
        projects=projects,
        category=category,
        all_projects=all_projects,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
        remove_projects=remove_projects,
    )


@marketplace_publish.command("runbook", feature_min_version="3.2.0")
@click.argument("name", nargs=1)
@click.option("--version", "-v", default=None, help="Version of NCM store runbook")
@click.option("--category", "-c", default=None, help="Category for NCM store runbook")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source for NCM store runbook",
)
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for NCM store runbook",
)
@click.option(
    "--all_projects",
    "-ap",
    is_flag=True,
    default=False,
    help="Approve runbook to all projects",
)
def _publish_marketplace_runbook(
    name, version, category, source, all_projects, projects=[]
):
    """Publish a NCM store manager runbook to NCM store"""

    publish_marketplace_item(
        name=name,
        version=version,
        projects=projects,
        category=category,
        app_source=source,
        all_projects=all_projects,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )


@marketplace_update.command("runbook", feature_min_version="3.2.0")
@click.argument("name", nargs=1)
@click.option(
    "--version", "-v", required=True, help="Version of NCM store runbook"
)  # Required to prevent unwanted update of published mpi
@click.option("--category", "-c", default=None, help="Category for NCM store runbook")
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for NCM store runbook",
)
@click.option("--description", "-d", help="Description for NCM store runbook")
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source for NCM store runbook",
)
@click.option(
    "--all_projects",
    "-ap",
    is_flag=True,
    default=False,
    help="Update NCM store runbook with all projects",
)
def _update_marketplace_runbook(
    name, version, category, projects, description, source, all_projects
):
    """Update a NCM store manager runbook"""

    update_marketplace_item(
        name=name,
        version=version,
        category=category,
        projects=projects,
        description=description,
        app_source=source,
        all_projects=all_projects,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )


@marketplace_delete.command("runbook", feature_min_version="3.2.0")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of NCM store runbook"
)  # Required to prevent unwanted delete of unknown mpi
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of NCM store runbook",
)
@click.option(
    "--app_state",
    "-a",
    default=None,
    type=click.Choice(APP_STATES),
    help="State of NCM store runbook",
)
def _delete_marketplace_runbook(name, version, source, app_state):
    """Deletes NCM store manager runbook"""

    delete_marketplace_item(
        name=name,
        version=version,
        app_source=source,
        app_state=app_state,
        type=MARKETPLACE_ITEM.TYPES.RUNBOOK,
    )


@marketplace_reject.command("runbook", feature_min_version="3.2.0")
@click.argument("name")
@click.option(
    "--version", "-v", required=True, help="Version of NCM store runbook"
)  # Required to prevent unwanted rejection of unknown mpi
def _reject_marketplace_runbook(name, version):
    """Reject NCM store manager runbook"""

    reject_marketplace_item(
        name=name, version=version, type=MARKETPLACE_ITEM.TYPES.RUNBOOK
    )


@publish.command("runbook", feature_min_version="3.2.0")
@click.argument("runbook_name")
@click.option("--version", "-v", required=True, help="Version of NCM store runbook")
@click.option("--name", "-n", default=None, help="Name of NCM store runbook")
@click.option(
    "--description", "-d", default="", help="Description for NCM store runbook"
)
@click.option(
    "--with_secrets",
    "-w",
    is_flag=True,
    default=False,
    help="Preserve secrets while publishing runbooks to NCM store",
)
@click.option(
    "--with_endpoints",
    "-w",
    is_flag=True,
    default=False,
    help="Preserve endpoints publishing runbooks to NCM store",
)
@click.option(
    "--existing_marketplace_runbook",
    "-e",
    is_flag=True,
    default=False,
    help="Publish as new version of existing NCM store runbook",
)
@click.option(
    "--publish_to_marketplace",
    "-pm",
    is_flag=True,
    default=False,
    help="Publish the runbook directly to NCM store skipping the steps to approve, etc.",
)
@click.option(
    "--auto_approve",
    "-aa",
    is_flag=True,
    default=False,
    help="Auto approves the runbook",
)
@click.option(
    "--project",
    "-p",
    "projects",
    multiple=True,
    help="Projects for NCM store runbook (used for approving runbook)",
)
@click.option(
    "--category",
    "-c",
    default=None,
    help="Category for NCM store runbook (used for approving runbook)",
)
@click.option(
    "--file",
    "-f",
    "icon_file",
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    help="Path of app icon image to be uploaded",
)
@click.option(
    "--icon_name", "-i", default=None, help="App icon name for NCM store runbook"
)
@click.option(
    "--all_projects",
    "-ap",
    is_flag=True,
    default=False,
    help="Publishes runbook to all projects",
)
def publish_runbook(
    runbook_name,
    name,
    version,
    description,
    with_secrets,
    with_endpoints,
    existing_marketplace_runbook,
    publish_to_marketplace,
    projects=[],
    category=None,
    auto_approve=False,
    icon_name=False,
    icon_file=None,
    all_projects=False,
):
    """Publish a runbook to NCM store manager"""

    if not name:
        # Using runbook name as the marketplace runbook name if no name provided
        name = runbook_name

    if not existing_marketplace_runbook:
        publish_runbook_as_new_marketplace_item(
            runbook_name=runbook_name,
            marketplace_item_name=name,
            version=version,
            description=description,
            with_secrets=with_secrets,
            with_endpoints=with_endpoints,
            publish_to_marketplace=publish_to_marketplace,
            projects=projects,
            category=category,
            auto_approve=auto_approve,
            icon_name=icon_name,
            icon_file=icon_file,
            all_projects=all_projects,
        )

    else:
        publish_runbook_as_existing_marketplace_item(
            runbook_name=runbook_name,
            marketplace_item_name=name,
            version=version,
            description=description,
            with_secrets=with_secrets,
            with_endpoints=with_endpoints,
            publish_to_marketplace=publish_to_marketplace,
            projects=projects,
            category=category,
            auto_approve=auto_approve,
            icon_name=icon_name,
            icon_file=icon_file,
            all_projects=all_projects,
        )


@marketplace_run.command("runbook", feature_min_version="3.2.0")
@click.argument("name")
@click.option("--version", "-v", default=None, help="Version of NCM store item")
@click.option("--project", "-pj", default=None, help="Project for the execution")
@click.option(
    "--ignore_runtime_variables",
    "-i",
    is_flag=True,
    default=False,
    help="Ignore runtime variables and use defaults for runbook execution",
)
@click.option(
    "--source",
    "-s",
    default=None,
    type=click.Choice(APP_SOURCES),
    help="App Source of NCM store item",
)
@click.option("--watch/--no-watch", "-w", default=False, help="Watch scrolling output")
def _run_marketplace_runbook(
    name, version, project, source, ignore_runtime_variables, watch
):
    """Execute a NCM store item of type runbook"""

    execute_marketplace_runbook(
        name=name,
        version=version,
        project_name=project,
        app_source=source,
        watch=watch,
        ignore_runtime_variables=ignore_runtime_variables,
    )
