Examples
========


Building a search query
-----------------------

Getting Data from an endpoint

.. code-block:: python

    import GraphQLBuilder

    gz = GraphQLBuilder.GraphQLBuilder()

    def get_data() -> List[Dict[str, Any]]:
        qry = gz.build_search_qry("some_data_endpoint", "", [
            'id, name, foo, bar,'], limit=20000)

        ret = gz.execute_query("https://example.com/v1/graphql", qry)

        return gz.getPath(['data', 'some_data_endpoint'], ret)

Building an insert query
------------------------

.. code-block:: python

    import GraphQLBuilder

    data = {
        "id": "some_id",
        "name": "some_name",
        "foo": "some_foo",
        "bar": "some_bar",
        "internal_stuff": "some_internal_stuff", 
    }

    gz = GraphQLBuilder.GraphQLBuilder()

    def post_data() -> List[Dict[str, Any]]:

        mutation_objects: List[Any] = []

        mutation_objects.append(gz.build_graphQL_mutation_objects_from_dict(
            data, 
            {
                "id": "Int",
                "name": "String",
                "foo": "String",
                "bar": "String",
                "stuff": "String",
            },
            custom_mapping={
                "internal_stuff": "stuff"
            },
            custom_mapping_append_other=True
        ))

        qry = gz.build_insert_qry("some_data_endpoint", mutation_objects, ['id', 'name', 'foo', 'bar', 'stuff']'])
        ret = gz.execute_query("https://example.com/v1/graphql", qry, bearer_token="some_token")

        return gz.getPath(['data', 'some_data_endpoint'], ret)
