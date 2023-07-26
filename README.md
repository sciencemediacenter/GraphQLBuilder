<div id="header" align="center">
  <img src="https://media.sciencemediacenter.de/static/img/logos/smc/smc-logo-typo-bw-big.png" width="300"/>

  <div id="badges" style="padding-top: 20px">
    <a href="https://www.sciencemediacenter.de">
      <img src="https://img.shields.io/badge/Website-orange?style=plastic" alt="Website Science Media Center"/>
    </a>
    <a href="https://lab.sciencemediacenter.de">
      <img src="https://img.shields.io/badge/Website (SMC Lab)-grey?style=plastic" alt="Website Science Media Center Lab"/>
    </a>
    <a href="https://twitter.com/smc_germany_lab">
      <img src="https://img.shields.io/badge/Twitter-blue?style=plastic&logo=twitter&logoColor=white" alt="Twitter SMC Lab"/>
    </a>
  </div>
</div>

# GraphQLBuilder 

GraphQLBuilder is a package that can support the creation of GraphQL queries. It provides various methods for translating dicts or lists into mutation objects, which can then be used in a gql query. 

Attention! This package is optimized for using a hasura.io endpoint - not all GraphQL functions are supported. 

## Installation

```bash
$ pip install git+https://github.com/sciencemediacenter/GraphQLBuilder
```

## Usage


```python
import GraphQLBuilder

gq = GraphQLBuilder.GraphQLBuilder()

```
## Documentation

The documentation can be found [here](https://sciencemediacenter.github.io/GraphQLBuilder/)

## Contributing

Feel free to dive in! [Open an issue]() or submit PRs.

## License

`GraphQLBuilder` was created by Hendrik Adam and is licensed under the GPL-3.0.
