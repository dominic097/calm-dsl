from calm.dsl.api.handle import ClientHandle
from calm.dsl.log.logger import get_logging_handle
from calm.dsl.constants import CACHE

LOG = get_logging_handle(__name__)


def get_idp_service_name(client: ClientHandle, idp_id: str) -> str:
    """
    Returns the name of the Identity Provider service given its ID.
    Uses DirectoryServiceCache database to avoid repeated API calls and rate limiting.

    Args:
        client (ClientHandle): The API client handle.
        idp_id (str): The ID of the Identity Provider.
    Returns:
        str: The name of the Identity Provider service.
    """
    if not idp_id:
        LOG.warning("IDP ID is not provided. Returning empty string.")
        return ""

    # Try to get from database cache first
    try:
        from calm.dsl.store import Cache

        cache_data = Cache.get_entity_data_using_uuid(
            entity_type=CACHE.ENTITY.DIRECTORY_SERVICE, uuid=idp_id
        )

        if cache_data:
            service_name = cache_data.get("name", "")
            LOG.debug(
                "Directory service found in cache for idp_id {}: {}".format(
                    idp_id, service_name
                )
            )
            return service_name

    except Exception as e:
        LOG.debug(
            "Failed to lookup directory service in cache for idp_id {}: {}".format(
                idp_id, e
            )
        )

    # Fallback to API call if not found in cache
    LOG.debug(
        "Directory service not found in cache for idp_id {}. Making API call...".format(
            idp_id
        )
    )
    directory_service, err = client.directory_service.get(idp_id)
    if err:
        LOG.warning(
            "Cannot fetch directory service with id {}. Error code: {}".format(
                idp_id, err.get("code")
            )
        )
        return ""

    return directory_service.get("name", "")


def get_user_from_response(client: ClientHandle, entity: dict) -> dict:
    """
    Returns user data from response json
    Args:
        entity (dict): user entity json response
    Returns:
        dict: user data with keys: name, uuid, display_name, directory
    """

    if not entity:
        LOG.error("No user data received")
        return {}

    name = entity.get("username")
    uuid = entity.get("extId")
    display_name = entity.get("displayName", "")
    idp_id = entity.get("idpId", "")
    user_type = entity.get("userType", "")

    if name is None or not uuid or display_name is None:
        LOG.error(
            "Invalid user data received: name={}, uuid={}, display_name={}".format(
                name, uuid, display_name
            )
        )
        return {}

    directory_service_name = get_idp_service_name(client, idp_id)

    return {
        "name": name,
        "uuid": uuid,
        "display_name": display_name,
        "directory": directory_service_name,
        "user_type": user_type,
    }


def get_user_group_from_response(client: ClientHandle, entity: dict) -> dict:
    """
    Returns user group data from response json
    Args:
        entity (dict): user group entity json response
    Returns:
        dict: user group data with keys: name, uuid, display_name, directory
    """
    distinguished_name = entity.get("distinguishedName")
    uuid = entity.get("extId")
    display_name = entity.get("name", "")
    idp_id = entity.get("idpId", "")

    if not uuid:
        LOG.error(
            "Invalid user group data received: distinguished_name={}, uuid={}, display_name={}".format(
                distinguished_name, uuid, display_name
            )
        )
        return {}

    directory_name = get_idp_service_name(client, idp_id)

    return {
        "name": distinguished_name,
        "uuid": uuid,
        "display_name": display_name,
        "directory": directory_name,
    }
