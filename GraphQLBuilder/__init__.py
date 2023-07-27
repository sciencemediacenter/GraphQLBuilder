import json
import logging
import os
import requests
from typing import Any, Union, List, Dict, Optional

class GraphQLBuilder:
    """This Class is used to build GraphQL Queries and Mutations. All functions are created to help access the GraphQL API of Hasura.io. 
    
    See https://hasura.io/docs/latest/graphql/core/index.html for more information. 

    The Class is also used to execute the queries and mutations. This is done via the execute_query function.
    """

    def get_path(self, path: List[str], source: Dict[Any, Any], fallback_return_value: Optional[Any] = None) -> Any:
        """Function the traverse a dict via a path and return the value of the last element in the path.

        Attention: This CAN ALSO work if a stage of the path is a dict nested in a list with length 1, since it will always return the first element of a list.

        Args:
            path (List[str]): Path of Knots as List
            source (Dict[Any, Any]): Source Dict
            fallback_return_value (Optional[Any]): Allows to specify a return value if no value in the path was found, default None

        Returns:
            Any: value of Knot or None

        Examples:
            >>> get_path(["a", "b", "c"], {"a": {"b": {"c": "d"}}})
            "d"

        """
        if len(path) == 0 or not isinstance(source, dict):
            return fallback_return_value
        tmp: Dict[Any, Any] = source
        for index, knot in enumerate(path):
            # Check if we got a list as an element, if so return the first item out of it.
            if isinstance(tmp, list):
                try:
                    tmp = tmp[0]
                except IndexError:
                    return fallback_return_value
            tmp = tmp.get(knot, None)
            if tmp == None:
                return fallback_return_value
            elif index == len(path) - 1:
                return tmp

    def build_graphQL_mutation_objects_from_list(
        self, source_data: List[Any], key: str, itemtype: str, return_as_list: Optional[bool] = False
    ) -> Union[str, List[Any]]:
        """Build Graph QL Mutation Objects from a List of Items

        Args:
            source_data (List[Any]): The List Containing the Items
            key (str): The Key (field) which the values in the list should be mapped to
            itemtype (str): Type of the Items in List (Int, Boolean, or String)
            return_as_list (bool, optional): If True, return the prepared items as a list instead of a final mutation string. Useful when using the Query Builder

        Returns:
            str: the created Mutation Objects
            or List[Any]: the created Mutation Objects as List

        """
        _items = []
        for v in source_data:
            if itemtype == "Int":
                _items.append("{%s: %d}" % (key, v))
            elif itemtype == "Boolean":
                _items.append(
                    '{%s: "%s"}' % (key, str(v).lower()),
                )
            else:
                try:
                    _items.append(
                        '{%s: "%s"}'
                        % (
                            key,
                            v.replace("\\", "\\\\")
                            .replace("\n", "\\n")
                            .replace("\r", "\\r")
                            .replace("\t", "\\t")
                            .replace('"', '\\"'),
                        ),
                    )
                except AttributeError:
                    logging.error("Encoding Error")
                    logging.error("Building GraphQL Mutation Object Failed")
                    return ""

        if return_as_list:
            return _items

        return "%s" % ", ".join(_items)

    def build_graphQL_mutation_objects_from_dict(
        self,
        source_data: dict,
        typeschema: dict,
        custom_mapping: Optional[Dict[str, Any]] = {},
        custom_mapping_append_other: Optional[bool] = False,
        custom_mapping_value_overwrite: Optional[Dict[str, Any]] = {},
        ignore_fields: Optional[List[str]] = [],
        append_if_missing_fields: Optional[Dict[str, Any]] = {},
    ) -> str:
        """Builds GraphQL Mutation Objects (=strings in a specfic format) from a source dictonary.

        For the correct use with hasuro.io endpoints, you need to provide a valide TypeSchema as a dict. See the docs for more information.
        
        This function also provides a mapping 'service', which allows you to map a source key to a target key in the TypeSchema. This is useful, when the source data is not in the correct format.
        Be aware, that if you use a custom_mapping, all other fields will be ignored. If you want to include them, set custom_mapping_append_other to True.
            
        You can also use point seperated strings for dicts like 'status.agreed' to map nested dicts.

        Args:
            source_data (dict): Source Data as Dict
            typeschema (dict): The TypeSchema as Dict
            custom_mapping (dict, optional): Custom field mapping. Defaults to {}.
            custom_mapping_append_other (bool, optional): Automatically map all Fields not mentioned in custom mapping. Defaults to False.
            custom_mapping_value_overwrite (dict, optional): Allows to overwrite specific values, when processing data. Can only be used, when using a custom mapping. This will also append fields. Defaults to {}.
            ignore_fields (list, optional): List of fields (=keys) to ignore when building the query objects. Defaults to [].
            append_if_missing_fields (dict, optional): Used to fix broken or incomplete datasets. If a field is missing, it will be added with the given value. Defaults to {}.

        Returns:
            str: returns all the items as a joined string, which can be used in a mutation query
 
        """
        _items = []

        # Check for Custom Mapping
        if not custom_mapping == {}:
            _tmp = {}

            # Merge both custom mapping dicts to get all fields
            custom_mapping.update(custom_mapping_value_overwrite)
            for k, v in custom_mapping.items():

                if k in custom_mapping_value_overwrite:
                    # if we just do "if v", then False values or '0'-values would be ignored.. :<
                    if v != None:
                        _tmp[k] = v
                else:
                    if isinstance(v, str) and "." in v:
                        v = v.split(".")
                        _tmp[k] = self.get_path(v, source_data)
                    elif isinstance(v, str):
                        # workaround to use get_path
                        v = [v]
                        _tmp[k] = self.get_path(v, source_data)

                    # Catch Missing Values
                    elif v == None:
                        continue

            # Check if we should append the other fields, if not, we just use the custom mapping as source data
            if not custom_mapping_append_other:
                source_data = _tmp
            else:
                source_data.update(_tmp)

        if append_if_missing_fields:
            for k, v in append_if_missing_fields.items():
                # If the Key is Missing or when the key is present but set to none.
                if not k in source_data.keys() or (
                    k in source_data.keys() and source_data[k] == None
                ):
                    logging.debug(
                        "Missing Field in Dataset. Adding %s with value %s" % (k, str(v)))
                    source_data[k] = v

        for k, v in source_data.items():
            if k not in ignore_fields:

                # If k is in custom_mapping_value_overwrite, all formatting should already be done. But just in Case, we check for Booleans..
                if k in custom_mapping_value_overwrite:
                    # Format Booleans
                    if isinstance(v, bool):
                        v = "true" if v else "false"
                    _items.append("%s: %s" % (k, v))
                else:
                    # check for NoneType, else just skip. Will be null in DB, if the field is nullable. If not, this will throw an error on insert
                    if v != None:
                        if typeschema.get(k) == "Int":
                            try:
                                _items.append("%s: %d" % (k, int(v)))
                            # Try to convert emptry strings to int - We just ignore it, since it then appears as null in data
                            except Exception as e:
                                logging.error(
                                    "Error - Failed converting Int %s" % str(e))
                                continue
                        elif typeschema.get(k) == "Boolean":
                            # Catch improper parsings of some input data. There can be a case where a Boolean Var is a empty string.
                            if not v == "":
                                # Format Booleans
                                if isinstance(v, bool):
                                    v = "true" if v else "false"
                                _items.append(
                                    "%s: %s" % (k, str(v).lower()),
                                )

                        # This is for all the cases in which the typeschema is null..
                        else:
                            # Check if we got a str, else do nothing.
                            if isinstance(v, str):
                                _items.append(
                                    '%s: "%s"'
                                    % (
                                        k,
                                        v.replace("\\", "\\\\")
                                        .replace("\n", "\\n")
                                        .replace("\r", "\\r")
                                        .replace("\t", "\\t")
                                        .replace("\x02", "")
                                        .replace('"', '\\"'),
                                    ),
                                )
                            elif isinstance(v, bool):
                                _items.append(
                                    '%s: "%s"' % (k, v),
                                )
                            elif isinstance(v, int) or isinstance(v, float):
                                _items.append("%s: %d" % (k, int(v)))

        return "{%s}" % ", ".join(_items)

    def build_search_qry(
        self, typename: str, qry_filter: str, returning_fields: List[str or Dict[str, Any]], limit: Optional[int] = 10
    ) -> str:
        """Builds a Search Query with optional filter and returns it

        Args:
            typename (str): Name of the Query Type
            qry_filter (str): Filter as String!! e.g {field: {_eq: "value"}} or {_and: {field_one: {_eq: "foo"}, field_two: {_eq: "bar"}}}
            returning_fields (List[Any]): List of fields which should be returned. Cannot be empty! For nested fields, use a dict. e.g. {"field": ["subfield_one", "subfield_two"]}
            limit (int): Amount of returned items, default 10

        Returns:
            str: Final Query ready for execution

        """

        def _prepare_dict(field_dict) -> str:
            """Prepares a dict to be used in a query"""
            _tmp = []

            # Check if the dict has only one key, since this is a representation of nested gql
            if len(field_dict.keys()) != 1:
                logging.error(
                    "Error in _prepare_dict: field_dict has more than one key!")
                raise Exception("Error in _prepare_dict: field_dict has more than one key!")
            
            # Set the values - The values contain a list of strings or dicts. We need to check for that
            for v in field_dict[list(field_dict.keys())[0]]:
                if isinstance(v, dict):
                    _tmp.append(_prepare_dict(v))
                else:
                    _tmp.append(v)

            return "%s { %s }" % (list(field_dict.keys())[0], " ".join(_tmp))

        if not returning_fields:
            logging.error(
                "_build_search_qry error: Returning Fields are empty!")
            return ""

        # Build returning fields
        _prepared_fields = []
        for field in returning_fields:
            # We have to check if the field is a dict, since we need to build the query differently
            # The dict should be fully translated into a string
            try:
                if isinstance(field, dict):
                    _prepared_fields.append(_prepare_dict(field))
                else:
                    _prepared_fields.append(field)
            except Exception as e:
                logging.error(f"Error in _build_search_qry: {e}")
                return ""


        _query = """
            query SearchQuery {
                %s(limit: %d) {
                        %s
                }
            }
        """
        _query_with_filter = """
            query SearchQuery {
                %s(limit: %d, where: %s) {
                        %s
                }
            }
        """
        if qry_filter:
            return _query_with_filter % (typename, limit, qry_filter, " ".join(_prepared_fields))
        else:
            return _query % (typename, limit, " ".join(_prepared_fields))

    def build_insert_mutation_qry(
        self,
        typename: str,
        data_objects: List[Any],
        returning_objects: List[Any],
        update_constraint: Optional[str] = None,
        update_field_list: Optional[List[str]] = [],
    ) -> str:
        """Builds a complete Mutation Query

        Args:
            typename (str): Name of the Type (without insert_)
            data_objects (List[Any]): List of the generated Mutation Objects (which should be strings by now!)
            returning_objects (List[Any]): List of fields to return. Strings, cannot be empty!
            update_constraint ([type], optional): Name of the update_constraint to check for. Defaults to None.
            update_field_list (list, optional): Fields to be updated, when constraint hits. Defaults to [].

        Returns:
            str: returnes the genrated query as string

        """
        _query = """
            mutation InsertInto {
                %s(
                    objects: [%s]
                ) {
                    returning {
                        %s
                    }
                }
            }
        """
        _query_with_constraint = """
            mutation InsertInto {
                %s(
                    objects: [%s], 
                    on_conflict: {
                        constraint: %s, update_columns: [%s]
                    }
                ) {
                    returning {
                        %s
                    }
                }
            }
        """

        if not update_constraint:
            return _query % (
                "insert_" + typename,
                ", ".join(data_objects),
                " ".join(returning_objects),
            )

        else:

            return _query_with_constraint % (
                "insert_" + typename,
                ", ".join(data_objects),
                update_constraint,
                ", ".join(update_field_list),
                " ".join(returning_objects),
            )

    def build_delete_qry(self, typename: str, qry_filter: Optional[str] = {}) -> str:
        """Builds a delete query

        Args:
            typename (str): Name of the Query Type
            qry_filter (str, optional): Filter als String!! e.g {journalName: {_eq: "Nature"}} or {_and: {contactMail: {_eq: ""}, journalName: {_eq: ""}}}

        Returns:
            str: Final Query ready for execution

        """
        _query = """
            mutation deleteMutation {
                delete_%s(where: %s) {
                    affected_rows
                }
            }
        """

        return _query % (typename, qry_filter)

    def execute_query(self, endpoint_url: str, qry: str, bearer_token: Optional[str] = "") -> Dict[str, Any]:
        """
        Executes a GraphQL Query and returns the result as a List of Dicts

        Args:
            endpoint_url (str): URL of the GraphQL Endpoint
            qry (str): Query to execute
            bearer_token (str, optional): Bearer Token for Auth. Defaults to "".

        Returns:
            List[Dict[str, Any]]: (JSON) Result of the Query 

        """

        _headers = {
            "content-type": "application/json",
        }

        if bearer_token != "":
            _headers["Authorization"] = f"{bearer_token}"

        try:
            ret = requests.post(
                endpoint_url,
                json={
                    "query": qry,
                },
                headers=_headers,
                verify=False,
            )
        except requests.exceptions.HTTPError as errh:
            logging.error("==> Http Error: %s" % errh)
            return
        except Exception as e:
            logging.error(f"==> {e}")
            return

        if ret.status_code == 200:
            if ret.json().get("errors") is not None:
                logging.error(json.dumps(ret.json(), ensure_ascii=False))
                return {}
            return ret.json()
        else:
            logging.error(f"   --- ERROR NOT 200 {ret.status_code}")
            return
