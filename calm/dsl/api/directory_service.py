from calm.dsl.api.iam_v4_resource import IAMV4ResourceAPI


class DirectoryServiceAPI(IAMV4ResourceAPI):
    """
    Resource API for Directory Services."""

    def __init__(self, connection):
        super().__init__(connection, resource_type="directory-services")
