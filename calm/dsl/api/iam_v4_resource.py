from calm.dsl.api.connection import REQUEST
from calm.dsl.api.resource import ResourceAPI
from calm.dsl.log.logger import get_logging_handle


LOG = get_logging_handle(__name__)


_LOWER_PAGE_LIMIT_BOUND = 1
_UPPER_PAGE_LIMIT_BOUND = 100


_PAGE_QUERY_PARAM = "$page"
_LIMIT_QUERY_PARAM = "$limit"
_FILTER_QUERY_PARAM = "$filter"
_ORDER_BY_QUERY_PARAM = "$orderby"
_SELECT_QUERY_PARAM = "$select"


class IAMV4ResourceAPI(ResourceAPI):
    """
    Resource API for IAM v4 resources.
    """

    def __init__(self, connection, resource_type):
        super().__init__(connection, resource_type)
        # IAM v4 API does not have a separate list endpoint
        self.list_path = self.api_base_path

    def get(self, id=None):
        """
        Returns the entity with the given ID.
        Args:
            id: The ID of the entity to retrieve.
        """
        if not id:
            raise ValueError("ID cannot be None or empty.")

        item_url = self.item_path.format(id)
        LOG.debug(f"Fetching entity for item url: {item_url}")
        response, err = self.connection._call(
            item_url, verify=False, method=REQUEST.METHOD.GET
        )

        if not err:
            return response.json().get("data", {}), None

        return None, err

    def list(
        self,
        page: int = 0,
        limit: int = 50,
        _filter: str = None,
        order_by: str = None,
        select: str = None,
        ignore_error=False,
    ):
        """
        Returns a list of entities of the resource type.
        Args:
            page: The page number to retrieve.
            limit: The number of items per page.
            filter: The filter to apply to the list.
            order_by: The field to order the results by.
            select: The fields to include in the response.
            NOTE: this parameter must conform to the OData V4.01 -> e.g $select=field1,field2
            ignore_error: Whether to ignore errors.
        """
        if page < 0:
            raise ValueError("Page number cannot be negative.")

        if limit < _LOWER_PAGE_LIMIT_BOUND or limit > _UPPER_PAGE_LIMIT_BOUND:
            raise ValueError(
                f"Limit must be between {_LOWER_PAGE_LIMIT_BOUND} and {_UPPER_PAGE_LIMIT_BOUND}."
            )
        list_url = self._extend_list_url_with_query_params(
            page, limit, _filter, order_by, select
        )
        LOG.debug(f"Fetching entities for list url: {list_url}")

        response, err = self.connection._call(
            list_url,
            verify=False,
            method=REQUEST.METHOD.GET,
            ignore_error=ignore_error,
            timeout=(5, 60),
        )
        if not err:
            response = response.json()
            return response.get("data", []), None

        if ignore_error:
            return None, err

        raise Exception(f"[{err['code']}] - {err['error']}")

    def list_all(
        self, api_limit=100, total_results=None, select=None, ignore_error=False
    ):
        """
        Returns all entities of the resource type.
        Args:
            api_limit: The maximum number of items to retrieve in a single API call.
            total_results: The total number of results to retrieve.
                          If specified, the method will stop fetching once this limit is reached.
            select: The fields to include in the response.
            ignore_error: Whether to ignore errors.
        Returns:
            A tuple of (list of all entities of the resource type, error).
        """
        all_entities = []
        page_no = 0
        total_entities = 0

        while True:
            LOG.debug(
                f"Fetching entities for resource type: {self.connection.host}, page: {page_no}, limit: {api_limit}"
            )
            entities, err = self.list(
                page=page_no,
                limit=api_limit,
                select=select,
                ignore_error=ignore_error,
            )
            if err:
                if ignore_error:
                    return None, err
                else:
                    raise Exception(f"[{err['code']}] - {err['error']}")

            # Not to exceed the total results limit if it is specified
            if total_results and (total_entities + len(entities)) > total_results:
                entities = entities[: total_results - total_entities]

            all_entities.extend(entities)
            page_no += 1
            total_entities += len(entities)

            if len(entities) < api_limit or (
                total_results and total_entities == total_results
            ):
                break

        return all_entities, None

    def get_name_uuid_map(self, name_field: str = "name", limit: int = None) -> dict:
        """
        Returns a map of entity names to their UUIDs.
        Args:
            name_field: Field to consider for the entity name.
                        Default is "name".
            limit: Optional limit on the number of entities to return.
            If provided, only the first 'limit' entities will be considered.
        Returns:
            A dictionary mapping entity names to their UUIDs.
            structure: {name: [uuid1, uuid2, ...]}
        """
        return self._get_name_uuid_map(name_field=name_field, limit=limit)

    def get_uuid_name_map(self, name_field: str = "name", limit: int = None) -> dict:
        """
        Returns a map of entity UUIDs to their names.
        Args:
            name_field: Field to consider for the entity name.
                        Default is "name".
            limit: Optional limit on the number of entities to return.
            If provided, only the first 'limit' entities will be considered.
        Returns:
            A dictionary mapping entity UUIDs to their names.
            structure: {uuid: name}
        """
        return self._get_uuid_name_map(name_field=name_field, limit=limit)

    def _get_name_uuid_map(self, name_field: str = "name", limit: int = None) -> dict:
        """
        Returns a map of entity names to their UUIDs.
        Args:
            name_field: Field to consider for the entity name.
            limit: Optional limit on the number of entities to return.
        Returns:
            A dictionary mapping entity names to their UUIDs.
            structure: {name: [uuid1, uuid2, ...]}
        """
        entities, _ = self.list_all(
            select=",".join([name_field, "extId"]), ignore_error=False
        )
        if limit is not None and limit > 0:
            entities = entities[:limit]

        name_uuid_map = {}

        for entity in entities:
            name = entity.get(name_field)
            if not name:
                LOG.debug(f"No name found in entity: {entity}")
                continue

            uuid = entity.get("extId")

            # TODO: are names unique depend on the attribute we use for name
            # if it is, we can use a simple map; TBD
            if name and uuid:
                if name in name_uuid_map:
                    name_uuid_map[name].append(uuid)
                else:
                    name_uuid_map[name] = [uuid]

        return name_uuid_map

    def _get_uuid_name_map(self, name_field: str = "name", limit: int = None) -> dict:
        """
        Returns a map of entity UUIDs to their names.
        Args:
            name_field: Field to consider for the entity name.
            limit: Optional limit on the number of entities to return.
        Returns:
            A dictionary mapping entity UUIDs to their names.
            structure: {uuid: name}
        """
        entities, _ = self.list_all(
            select=",".join([name_field, "extId"]), ignore_error=False
        )
        if limit is not None and limit > 0:
            entities = entities[:limit]

        uuid_name_map = {}

        for entity in entities:
            # Use the first available name field from the list
            name = entity.get(name_field)
            if not name:
                LOG.debug(f"No name found in entity: {entity}")
                continue

            uuid = entity.get("extId")

            if uuid and name:
                uuid_name_map[uuid] = name

        return uuid_name_map

    def _extend_list_url_with_query_params(
        self, page, limit, _filter, order_by, select
    ):
        """
        Extends the list URL with query parameters.
        """
        page_query_param = f"{_PAGE_QUERY_PARAM}={page}"
        limit_query_param = f"{_LIMIT_QUERY_PARAM}={limit}"
        filter_query_param = f"{_FILTER_QUERY_PARAM}={_filter}" if _filter else ""
        orderby_query_param = f"{_ORDER_BY_QUERY_PARAM}={order_by}" if order_by else ""
        select_query_param = f"{_SELECT_QUERY_PARAM}={select}" if select else ""

        query_params = [page_query_param, limit_query_param]
        if filter_query_param:
            query_params.append(filter_query_param)

        if orderby_query_param:
            query_params.append(orderby_query_param)

        if select_query_param:
            query_params.append(select_query_param)

        query_string = "&".join(query_params)

        return f"{self.api_base_path}?{query_string}"
