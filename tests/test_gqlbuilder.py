import GraphQLBuilder as GraphQLBuilder
import requests
from requests_mock.mocker import Mocker

# Thanks - https://stackoverflow.com/questions/16474848/python-how-to-compare-strings-and-ignore-white-space-and-special-characters
def _cmp(a, b):
    return [c for c in a if c.isalpha()] == [c for c in b if c.isalpha()]


def test_creation_class_object():
    gz = GraphQLBuilder.GraphQLBuilder()
    assert gz != None

def test_get_path():
    gz = GraphQLBuilder.GraphQLBuilder()

    _mock_data = {
        "id": 1,
        "data": {
            "name": "test",
            "age": 42
        },
        "list_data": [{"first_element": "test"}]
    }

    # Test Working
    assert gz.get_path(["data", "name"], _mock_data) == "test"
    assert gz.get_path(["data", "age"], _mock_data) == 42
    assert gz.get_path(["list_data", "first_element"], _mock_data) == "test"
    
    # Test Fallbacks
    assert gz.get_path(["unknown"], _mock_data, fallback_return_value="fallback") == "fallback"
    assert gz.get_path(["data", "unknown"], _mock_data, fallback_return_value="fallback") == "fallback"
    assert gz.get_path([], "_mock_data", fallback_return_value="fallback") == "fallback"

    _mock_data["list_data"] = []
    assert gz.get_path(["list_data", "first_element"], _mock_data, fallback_return_value="fallback") == "fallback"


def test_build_graphQL_mutation_objects_from_list():
    gz = GraphQLBuilder.GraphQLBuilder()

    _mock_data = [1, 2, 3, 4, 5]
    mutation_objects: str = gz.build_graphQL_mutation_objects_from_list(_mock_data, "test", "Int")

    # Test working
    assert mutation_objects == '{test: 1}, {test: 2}, {test: 3}, {test: 4}, {test: 5}'

    # Test return as list
    mutation_objects: List[Any] = gz.build_graphQL_mutation_objects_from_list(_mock_data, "test", "Int", return_as_list=True)
    assert len(mutation_objects) == 5

    # Test boolean
    _mock_data = [True, False]
    mutation_objects: List[Any] = gz.build_graphQL_mutation_objects_from_list(_mock_data, "test", "Boolean", return_as_list=True)
    assert len(mutation_objects) == 2

    # Test wrong type
    _mock_data = ["Test", True, False]
    mutation_objects: List[Any] = gz.build_graphQL_mutation_objects_from_list(_mock_data, "test", "String", return_as_list=False)
    assert mutation_objects == ""

def test_build_graphQL_mutation_objects_from_dict():
    gz = GraphQLBuilder.GraphQLBuilder()

    _mock_data = {
        "id": 1,
        "data": {
            "name": "test",
            "age": 42
        },
        "job_description": "test",
        "has_bird": True,
        "amount_animals": 2,
    }

    _type_schema = {
        "id": "Int",
        "name": "String",
        "age": "Int",
        "job": "String",
        "has_dog": "Boolean",
        "has_cat": "Boolean",
        "has_bird": None,
        "amount_animals": None,
    }

    # Test working with custom mapping
    mutation_objects: str = gz.build_graphQL_mutation_objects_from_dict(
        _mock_data, 
        _type_schema, 
        custom_mapping={"name": "data.name", "age": "data.age", "job": "job_description", "unknown": None},
        custom_mapping_append_other=True,
        custom_mapping_value_overwrite={"id": 2, "age": 0, "has_cat": False},
        ignore_fields=["name", "job_description"],
        append_if_missing_fields={"append_field": "test", "has_dog": True},
    )
    assert mutation_objects == '{id: 2, has_bird: "True", amount_animals: 2, age: 0, job: "test", has_cat: false, append_field: "test", has_dog: true}'

    # Test working with custom mapping and append other false
    mutation_objects: str = gz.build_graphQL_mutation_objects_from_dict(
        _mock_data, 
        _type_schema, 
        custom_mapping={"name": "data.name", "age": "data.age", "job": "job_description", "unknown": None},
        custom_mapping_append_other=False,
        custom_mapping_value_overwrite={"id": 2, "age": 0},
        ignore_fields=["name", "job_description"],
        append_if_missing_fields={"append_field": "test", "has_dog": True},
    )
    assert mutation_objects == '{age: 0, job: "test", id: 2, append_field: "test", has_dog: true}'

    # Test working with custom mapping and append other false and broken type schema
    _type_schema["name"] = "Int"
    mutation_objects: str = gz.build_graphQL_mutation_objects_from_dict(
        _mock_data, 
        _type_schema,
        custom_mapping={"name": "data.name", "age": "data.age", "job": "job_description", "unknown": None},
        custom_mapping_append_other=False,
        custom_mapping_value_overwrite={"id": 2, "age": 0},
        ignore_fields=["job_description"],
        append_if_missing_fields={"append_field": "test", "has_dog": True},
    )
    assert mutation_objects == '{age: 0, job: "test", id: 2, append_field: "test", has_dog: true}'

def test_build_search_query():
    gz = GraphQLBuilder.GraphQLBuilder()

    # Test normal working query
    qry = gz.build_search_qry(
        "test_endpoint",
        "",
        ["id", "name", "age"],
        10,
    )
    assert _cmp(qry, "query SearchQuery { test_endpoint(limit 10) {id name age}}") == True

    # Test working query with where clause (=filter)
    qry = gz.build_search_qry(
        "test_endpoint",
        "{id: {_eq: 1}}",
        ["id", "name", "age"],
        10,
    )
    assert _cmp(qry, "query SearchQuery { test_endpoint(limit 10, where: {id: {_eq: 1}}) {id name age}}") == True

    # Test working query with where clause (=filter) and nested dict
    qry = gz.build_search_qry(
        "test_endpoint",
        "{id: {_eq: 1}}",
        ["id", {"name": {"firstname": "test", "lastname": "bar"}}, "age"],
        10,
    )
    assert _cmp(qry, "query SearchQuery { test_endpoint(limit 10, where: {id: {_eq: 1}}) {id name {firstname lastname } age}}") == True

    # Test a not working query, since the return fields are empty
    qry = gz.build_search_qry(
        "test_endpoint",
        "{id: {_eq: 1}}",
        [],
        10,
    )
    assert qry == ""

    # Test a working query, with nested return fields
    qry = gz.build_search_qry(
        "test_endpoint",
        "{id: {_eq: 1}}",
        ["id", {"name": ["firstname", "lastname"]}, "age"],
        10,
    )
    assert _cmp(qry, "query SearchQuery { test_endpoint(limit 10, where: {id: {_eq: 1}}) {id name {firstname lastname } age}}") == True

    # Test a working query, with double nested return fields
    qry = gz.build_search_qry(
        "test_endpoint",
        "{id: {_eq: 1}}",
        ["id", {"name": ["firstname", "lastname", {"animals": ["has_bird", "has_dog"]}]}, "age"],
        10,
    )
    assert _cmp(qry, "query SearchQuery { test_endpoint(limit 10, where: {id: {_eq: 1}}) {id name { firstname lastname } animals { has_bird has_dog } age}}") == True

    # Test a query, with a broken nested dict in the returned fields
    qry = gz.build_search_qry(
        "test_endpoint",
        "{id: {_eq: 1}}",
        ["id", {"name": ["firstname", "lastname"], "second_not_allowed_field": ""}, "age"],
        10,
    )
    assert qry == ""


def test_build_insert_mutation_query():
    gz = GraphQLBuilder.GraphQLBuilder()

    _mock_data = {
        "id": 1,
        "data": {
            "name": "test",
            "age": 42
        }
    }

    _type_schema = {
        "id": "Int",
        "name": "String",
        "age": "Int",
    }

    mutation_objects: str = gz.build_graphQL_mutation_objects_from_dict(
        _mock_data, 
        _type_schema, 
        custom_mapping={"name": "data.name", "age": "data.age"},
        custom_mapping_append_other=True
    )

    # Test a working query, with update columns
    qry = gz.build_insert_mutation_qry(
        "test_endpoint",
        [mutation_objects],
        ["id", "name", "age"],
        "id_primkey_contraint",
        ["name", "age"],
    )
    assert _cmp(qry, 'mutation InsertInto { insert_test_endpoint( objects: [{id: 1, name: "test", age: 42}], on_conflict: { constraint: id_primkey_contraint, update_columns: [name, age]}) {returning {id name age}}}') == True

    # Test a working query, without update columns
    qry = gz.build_insert_mutation_qry(
        "test_endpoint",
        [mutation_objects],
        ["id", "name", "age"],
    )
    assert _cmp(qry, 'mutation InsertInto { insert_test_endpoint( objects: [{id: 1, name: "test", age: 42}]) {returning {id name age}}}') == True


def test_build_delete_query():
    gz = GraphQLBuilder.GraphQLBuilder()

    qry = gz.build_delete_qry(
        "test_endpoint",
        "{id: {_eq: 1}}"
    )

    assert _cmp(qry, 'mutation deleteMutation { delete_test_endpoint(where: {id: {_eq: 1}}) {affected_rows}}') == True

def test_execute_query(requests_mock: Mocker):
    gz = GraphQLBuilder.GraphQLBuilder()

    _mock_data = {
        "id": 1,
        "data": {
            "name": "test",
            "age": 42
        }
    }

    _type_schema = {
        "id": "Int",
        "name": "String",
        "age": "Int",
    }

    mutation_objects: str = gz.build_graphQL_mutation_objects_from_dict(
        _mock_data, 
        _type_schema, 
        custom_mapping={"name": "data.name", "age": "data.age"},
        custom_mapping_append_other=True
    )

    qry = gz.build_insert_mutation_qry(
        "test_endpoint",
        [mutation_objects],
        ["id", "name", "age"],
        "id_primkey_contraint",
        ["name", "age"],
    )

    # Test a working request.
    requests_mock.post('https://test.com/v1/graphql', 
        json={"data": {"insert_test_endpoint": {"returning": [{"id": 1, "name": "test", "age": 42}]}}}
    )

    response = gz.execute_query(
        "https://test.com/v1/graphql",
        qry,
        bearer_token="test_token"
    )
    assert response == {"data": {"insert_test_endpoint": {"returning": [{"id": 1, "name": "test", "age": 42}]}}}

    # Test Connection Error
    requests_mock.post('https://test.com/v1/graphql', exc=requests.exceptions.HTTPError)
    response = gz.execute_query(
        "https://test.com/v1/graphql",
        qry,
        bearer_token="test_token"
    )
    assert response == None

    # Test Request Exception
    requests_mock.post('https://test.com/v1/graphql', exc="Test Exception")
    response = gz.execute_query(
        "https://test.com/v1/graphql",
        qry,
        bearer_token="test_token"
    )
    assert response == None

    # Test Status Code
    requests_mock.post('https://test.com/v1/graphql', status_code=404)
    response = gz.execute_query(
        "https://test.com/v1/graphql",
        qry,
        bearer_token="test_token"
    )
    assert response == None

    # Test Error in response
    requests_mock.post('https://test.com/v1/graphql', json={"errors": [{"message": "test_error"}]})
    response = gz.execute_query(
        "https://test.com/v1/graphql",
        qry,
        bearer_token="test_token"
    )
    assert response == []