import json

from calm.dsl.builtins import Account, AccountResources
from calm.dsl.constants import ACCOUNT
from calm.dsl.config import get_context

context = get_context()
SERVER_CONFIG = context.get_server_config()

USERNAME = "username"
PASSWORD = "password"
SYNC_INTERVAL_SECS = 3900
DOMAIN = "domain name"


class multipc_remote_ahv_account(Account):
    """This is a remote ahv account with domain attribute"""

    type = ACCOUNT.TYPE.AHV
    sync_interval = SYNC_INTERVAL_SECS
    resources = AccountResources.Ntnx(
        username=USERNAME, password=PASSWORD, domain=DOMAIN
    )
