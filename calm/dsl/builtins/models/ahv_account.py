import sys
from .entity import EntityType, Entity

from calm.dsl.log import get_logging_handle
from .validator import PropertyValidator
from calm.dsl.constants import ENTITY, ACCOUNT
from calm.dsl.api.ncm_config_util import is_nc_enabled_by_config
from calm.dsl.store import Cache, Version
from calm.dsl.db.table_config import DomainsCache

from .utils import is_compile_secrets
from distutils.version import LooseVersion as LV
from calm.dsl.store.version import Version

LOG = get_logging_handle(__name__)

# AHV Account


class AhvAccountType(EntityType):
    __schema_name__ = "AhvAccount"
    __openapi_type__ = ENTITY.OPENAPI_TYPE.AHV

    def compile(cls):
        cdict = super().compile()

        # Adding this so that empty username is not in compiled account
        username = cdict.pop("username", "")
        if username:
            cdict["username"] = username

        # Handle password for basic_auth
        pswd = cdict.pop("password", "")
        if pswd:
            cdict["password"] = {
                "value": pswd if is_compile_secrets() else "",
                "attrs": {"is_secret_modified": True},
            }

        # Handle service_account for service_account auth
        service_account = cdict.pop("service_account", "")
        if service_account:
            cdict["service_account"] = {
                "value": service_account if is_compile_secrets() else "",
                "attrs": {"is_secret_modified": True},
            }

        # Set cred type if Calm version is >= 4.3.0
        calm_version = Version.get_version("Calm")
        if LV(calm_version) >= LV(ACCOUNT.SERVICE_ACCOUNT.FEATURE_MIN_VERSION):
            if service_account:
                cdict["cred_type"] = ACCOUNT.CRED_TYPE.SERVICE_ACCOUNT
            else:
                cdict["cred_type"] = ACCOUNT.CRED_TYPE.BASIC_AUTH

        if is_nc_enabled_by_config():
            domain_name = cdict.get("domain", None)
            if not domain_name:
                LOG.error("Domain name is required for NCM 2.0+")
                sys.exit("Domain name is required for NCM 2.0+")

            domain_cache_data = DomainsCache.get_entity_data(name=domain_name)
            if not domain_cache_data:
                raise Exception(
                    "Domain {} not found. Please run: calm update cache".format(
                        domain_name
                    )
                )

            cdict["pc_uuid"] = domain_cache_data.get("uuid", "")

        return cdict

    def post_compile(cls, cdict):
        cdict = super().post_compile(cdict)
        if not is_nc_enabled_by_config():
            cdict.pop("pc_uuid", None)

        # domain name is not required to pass in payload for on-prem and NCM setups.
        cdict.pop("domain", None)
        return cdict


class AhvAccountValidator(PropertyValidator, openapi_type=ENTITY.OPENAPI_TYPE.AHV):
    __default__ = None
    __kind__ = AhvAccountType


def ahv_account(**kwargs):
    name = kwargs.pop("name", None)
    bases = (Entity,)
    return AhvAccountType(name, bases, kwargs)


AhvAccountData = ahv_account()
