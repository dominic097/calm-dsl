import click
import sys
import traceback
from peewee import OperationalError, IntegrityError
from distutils.version import LooseVersion as LV

from calm.dsl.config import get_context
from .version import Version
from calm.dsl.db import get_db_handle, init_db_handle
from calm.dsl.log import get_logging_handle
from calm.dsl.api import get_client_handle_by_deployment
from calm.dsl.api.util import get_auth_info
from calm.dsl.db.table_config import AhvNetworkFunctionChain, DomainsCache
from calm.dsl.api.ncm_config_util import is_nc_enabled_by_config

LOG = get_logging_handle(__name__)


class Cache:
    """Cache class Implementation"""

    @classmethod
    def get_cache_tables(cls, sync_version=False):
        """returns tables used for cache purpose"""

        db = get_db_handle()
        db_tables = db.registered_tables

        # Get context
        context = get_context()

        # Get calm version from api only if necessary
        calm_version = Version.get_version("Calm")
        if sync_version or (not calm_version):
            server_config = context.get_server_config()
            api_key_location = server_config.get("api_key_location", None)
            cred = get_auth_info(api_key_location)
            username = cred.get("username")
            password = cred.get("password")

            nc_server_config = context.get_nc_server_config()
            nc_enabled = nc_server_config.get("enabled", False)
            nc_host = nc_server_config.get("host", None)
            nc_username = nc_server_config.get("username", None)
            nc_password = nc_server_config.get("password", None)

            ncm_server_config = context.get_ncm_server_config()
            ncm_enabled = ncm_server_config.get("ncm_enabled", False)
            ncm_host = ncm_server_config.get("host", None)
            ncm_port = ncm_server_config.get("port", None)

            client = get_client_handle_by_deployment(
                server_config["pc_ip"],
                server_config["pc_port"],
                auth=(username, password),
                nc_enabled=nc_enabled,
                nc_host=nc_host,
                nc_auth=(nc_username, nc_password),
                ncm_enabled=ncm_enabled,
                ncm_host=ncm_host,
                ncm_port=ncm_port,
            )
            res, err = client.version.get_calm_version()
            if err:
                LOG.error("Failed to get version")
                sys.exit(err["error"])
            calm_version = res.content.decode("utf-8")

        policy_config = context.get_policy_config()
        approval_policy_config = context.get_approval_policy_config()
        cache_tables = {}

        # For NC setup this table is not needed
        if is_nc_enabled_by_config() and AhvNetworkFunctionChain in db_tables:
            db_tables.remove(AhvNetworkFunctionChain)

        # For non NC setup this table is not needed
        if not is_nc_enabled_by_config() and DomainsCache in db_tables:
            db_tables.remove(DomainsCache)

        for table in db_tables:
            if hasattr(table, "__cache_type__") and (
                LV(calm_version) >= LV(table.feature_min_version)
            ):
                if table.is_approval_policy_required:
                    # if approval policy is required check policy and approval_policy status

                    policy_status = policy_config.get("policy_status", "False")
                    if isinstance(policy_status, str):
                        policy_status = eval(policy_status)

                    if (
                        policy_status == table.is_policy_required
                        and approval_policy_config.get(
                            "approval_policy_status", "False"
                        )
                        == "True"
                    ):
                        cache_tables[table.__cache_type__] = table

                elif table.is_policy_required:
                    if policy_config.get("policy_status", "False") == "True":
                        cache_tables[table.__cache_type__] = table
                else:
                    cache_tables[table.__cache_type__] = table
        return cache_tables

    @classmethod
    def get_entity_data(cls, entity_type, name, **kwargs):
        """returns entity data corresponding to supplied entry using entity name"""

        db_cls = cls.get_entity_db_table_object(entity_type)

        try:
            res = db_cls.get_entity_data(name=name, **kwargs)
        except OperationalError:
            formatted_exc = traceback.format_exc()
            LOG.debug("Exception Traceback:\n{}".format(formatted_exc))
            LOG.error(
                "Cache error occurred. Please update cache using 'calm update cache' command"
            )
            sys.exit(-1)

        if not res:
            kwargs["name"] = name
            LOG.debug(
                "Unsuccessful db query from {} table for following params {}".format(
                    entity_type, kwargs
                )
            )

        return res

    @classmethod
    def get_entity_data_using_uuid(cls, entity_type, uuid, *args, **kwargs):
        """returns entity data corresponding to supplied entry using entity uuid"""

        db_cls = cls.get_entity_db_table_object(entity_type)

        try:
            res = db_cls.get_entity_data_using_uuid(uuid=uuid, **kwargs)
        except OperationalError:
            formatted_exc = traceback.format_exc()
            LOG.debug("Exception Traceback:\n{}".format(formatted_exc))
            LOG.error(
                "Cache error occurred. Please update cache using 'calm update cache' command"
            )
            sys.exit(-1)

        if not res:
            kwargs["uuid"] = uuid
            LOG.debug(
                "Unsuccessful db query from {} table for following params {}".format(
                    entity_type, kwargs
                )
            )

        return res

    @classmethod
    def get_entity_db_table_object(cls, entity_type):
        """returns database entity table object corresponding to entity"""

        if not entity_type:
            LOG.error("No entity type for cache supplied")
            sys.exit(-1)

        cache_tables = cls.get_cache_tables()
        db_cls = cache_tables.get(entity_type, None)
        if not db_cls:
            LOG.error("Unknown entity type ({}) supplied".format(entity_type))
            sys.exit(-1)

        return db_cls

    @classmethod
    def add_one(cls, entity_type, uuid, **kwargs):
        """adds one entity to entity db object"""

        db_obj = cls.get_entity_db_table_object(entity_type)
        db_obj.add_one(uuid, **kwargs)

    @classmethod
    def delete_one(cls, entity_type, uuid, **kwargs):
        """adds one entity to entity db object"""

        db_obj = cls.get_entity_db_table_object(entity_type)
        db_obj.delete_one(uuid, **kwargs)

    @classmethod
    def update_one(cls, entity_type, uuid, **kwargs):
        """adds one entity to entity db object"""

        db_obj = cls.get_entity_db_table_object(entity_type)
        db_obj.update_one(uuid, **kwargs)

    @classmethod
    def sync(cls):
        """Sync cache by latest data"""

        def sync_tables(tables):
            for table in tables:
                try:
                    LOG.debug(
                        "Syncing cache for '{}' table".format(table.get_cache_type())
                    )
                    table.sync()
                except Exception as exp:
                    LOG.error(
                        "Cache sync failed for '{}' table".format(
                            table.get_cache_type()
                        )
                    )
                    LOG.error("Error occurred while syncing cache: {}".format(exp))
                click.echo(".", nl=False, err=True)

        cache_table_map = cls.get_cache_tables(sync_version=True)
        tables = list(cache_table_map.values())

        # Inserting version table at start
        tables.insert(0, Version)

        try:
            LOG.info("Updating cache", nl=False)
            sync_tables(tables)

        except (OperationalError, IntegrityError):
            click.echo(" [Fail]")
            # init db handle once (recreating db if some schema changes are there)
            LOG.info("Removing existing db and updating cache again")
            init_db_handle()
            LOG.info("Updating cache", nl=False)
            sync_tables(tables)
        click.echo(" [Done]", err=True)

    @classmethod
    def sync_table(cls, cache_type):
        """sync the cache table provided in cache_type list"""

        if not cache_type:
            return

        cache_type = [cache_type] if not isinstance(cache_type, list) else cache_type
        cache_table_map = cls.get_cache_tables()

        for _ct in cache_type:
            if _ct not in cache_table_map:
                LOG.warning("Invalid cache_type ('{}') provided".format(cache_type))
                continue

            cache_table = cache_table_map[_ct]
            cache_table.sync()
            click.echo(".", nl=False, err=True)
        click.echo("[Done]", err=True)

    @classmethod
    def clear_entities(cls):
        """Clear data present in the cache tables"""

        # For now clearing means erasing all data. So reinitialising whole database
        init_db_handle()

    @classmethod
    def show_data(cls):
        """Display data present in cache tables"""

        cache_tables = cls.get_cache_tables()
        for cache_type, table in cache_tables.items():
            click.echo("\n{}".format(cache_type.upper()))
            try:
                table.show_data()
            except OperationalError:
                formatted_exc = traceback.format_exc()
                LOG.debug("Exception Traceback:\n{}".format(formatted_exc))
                LOG.error(
                    "Cache error occurred. Please update cache using 'calm update cache' command"
                )
                sys.exit(-1)

    @classmethod
    def show_table(cls, cache_type):
        """sync the cache table provided in cache_type list"""

        if not cache_type:
            return

        cache_type = [cache_type] if not isinstance(cache_type, list) else cache_type
        cache_table_map = cls.get_cache_tables()

        for _ct in cache_type:
            if _ct not in cache_table_map:
                LOG.warning("Invalid cache_type ('{}') provided".format(cache_type))
                continue

            cache_table = cache_table_map[_ct]
            cache_table.show_data()
