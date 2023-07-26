Usage
=====

Installation
------------

To use this helper, first install it using pip:

.. code-block:: console

   $ pip install git+https://github.com/sciencemediacenter/GraphQLBuilder


Initialization
----------------

To use the GraphQLBuilder in your project, you need to import it and initialize it with the following parameters:

.. code-block:: python

   import GraphQLBuilder

   gq = GraphQLBuilder.GraphQLBuilder()

The "TypeSchema"
----------------

If you use this helper in the framework with Hasura.io, you have to specify a "TypeSchema" for some functions. This determines the type of the corresponding GraphQL field. 

For more information, please refer to the documentation of `Hasura.io <https://hasura.io/docs/latest/schema/postgres/postgresql-types/#string>`_  and to the examples within this document.
