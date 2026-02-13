from .main import (
    get,
    describe,
    launch,
    publish,
    approve,
    update,
    delete,
    reject,
    unpublish,
    decompile,
    run,
)
from .utils import FeatureFlagGroup


# Marketplace Commands


@get.group("marketplace", cls=FeatureFlagGroup)
def marketplace_get():
    """Get NCM store entities"""
    pass


@describe.group("marketplace", cls=FeatureFlagGroup)
def marketplace_describe():
    """Describe NCM store entities"""
    pass


@launch.group("marketplace", cls=FeatureFlagGroup)
def marketplace_launch():
    """Launch NCM store entities"""
    pass


@decompile.group("marketplace", cls=FeatureFlagGroup)
def marketplace_decompile():
    """Decompile NCM store entities"""
    pass


@approve.group("marketplace", cls=FeatureFlagGroup)
def marketplace_approve():
    """Approve NCM store entities"""
    pass


@publish.group("marketplace", cls=FeatureFlagGroup)
def marketplace_publish():
    """Publish NCM store entities"""
    pass


@update.group("marketplace", cls=FeatureFlagGroup)
def marketplace_update():
    """Update NCM store entities"""
    pass


@delete.group("marketplace", cls=FeatureFlagGroup)
def marketplace_delete():
    """Delete NCM store entities"""
    pass


@reject.group("marketplace", cls=FeatureFlagGroup)
def marketplace_reject():
    """Reject NCM store entities"""
    pass


@unpublish.group("marketplace", cls=FeatureFlagGroup)
def marketplace_unpublish():
    """Unpublish NCM store entities"""
    pass


@run.group("marketplace", cls=FeatureFlagGroup)
def marketplace_run():
    """Run NCM store entities"""
    pass
