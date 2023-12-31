try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

import os

long_description = """
GraphQLBuilder is a package that can support the creation of GraphQL queries. It provides various methods for translating dicts or lists into mutation objects, which can then be used in a gql query. 

Attention! This package is optimized for using a hasura.io endpoint - not all GraphQL functions are supported. 
"""

setup(
    name='GraphQLBuilder',
    version='0.2.1',
    url='https://github.com/sciencemediacenter/GraphQLBuilder',
    license='GPLv3',
    author='Hendrik Adam',
    author_email='hendrik.adam@sciencemediacenter.de',
    install_requires=[
        'requests>=2.26.0',
        'types-requests>=2.26.0',
        ],
    packages=find_packages(),
    tests_require=['pytest'],
    description='GraphQL Query Builder with focus on hasura.io',
    long_description = long_description,
    platforms='any',
    keywords = "GraphQL, hasura.io, query builder",
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],

    )
