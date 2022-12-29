# Add New Data Type (Custom Oracle Queries)
## Checklist
- Links to [dataSpecs](https://github.com/tellor-io/dataSpecs) issue & new query type file
- Add query type (subclass `AbiQuery`)
- Add sources (subclass `DataSource`)
- Add feed (instance of `DataFeed`)
- Add example instance of the query type to catalog
- Add support for building custom instances of the new query type (using the `--build-feed` flag)
- Tests for new query type, sources, feeds, & additions to the CLI
- Update docs for each addition
- Include example transactions from a block explorer of new query type submitted to Tellor using `telliot-feeds`

If the Tellor oracle doesn't have the on-chain data your smart contract needs, this section should
help you define a new query so that Tellor's decentralized network of reporters can get busy putting
your data securely on-chain.

## More Info on Query Design

Creating new Tellor query is pretty simple - there are only a few steps. Along the way, though,
there are some important considerations and decisions to make so that Tellor's oracle data serves
your project well. Here's how to get started.

_Step 1. Give the query a name_

Call it anything, really (within reason of course). `WeatherReport`, `GameScore`, `ElectionResult`,
`PropertyOwner`, or anything else you can imagine. We call this the _Query Type_. If you stick
with [CamelCase](https://en.wikipedia.org/wiki/Camel_case) names, it would really help us out, so
thanks in advance!

_Step 2. Choose query parameters (if you want to)_

A Query Type can also have _parameters_ that serve to customize the response. For
example, `PropertyOwner` might have a parameter called `address`. `GameScore` might have a few
_parameters_ such as `game_date`, `home_team`, or `away_team`. You get the idea. It helps if you
also define what values are allowed for each _parameter_. One last thing - we know it seems weird,
but we'd love it if you named your parameters
using [SnakeCase](https://en.wikipedia.org/wiki/Snake_case).

_Step 3. Choose the data type_

Tellor's reporters need to know how you'd like your data served (medium rare, a side of fries?).
When you think about it, reporters need to know the _data type_ used to respond, such as `float`
, `int`, `string`, bool`, raw bytes, etc. But don't stop there. Interesting queries can have complex
responses with structured data types that can hold data such as weather reports, addresses, GPS
locations, game statistics.

That's the great thing about Tellor, you
can [have it your way](https://www.youtube.com/watch?v=KJXzkUH72cY)!

_Step 4. You make the rules_

Since it's _your_ data used for _your_ smart contract, you get to make the rules!
With great power (to create arbitrary queries with arbitrary responses) comes great responsibility.
Rules about your data are mainly to encourage Tellor's reporters to provide the data with a
reasonable degree of confidence. Remember, reporters may lose their staked TRB if the network votes
the answer incorrect!

This is the part of Query Design that is more of an _art_. Be sure to carefully describe the
expected response, including the conditions that you would expect for the value to be disputed and
removed from the chain. Depending on your design, the _rules_ can have a great impact on the
security of your network.

_Step 5. Define data sources (if you want to)_

Another optional step here. Reporters will need to figure out how to get the requested data. If the
rules are clear, you can leave it up to them - that's totally cool.

Otherwise, you can point reporters in the right direction. Ideally there are multiple off-chain data
sources to increase the robustness and decentralization of the feed. Sometimes there are specific
API endpoints that have exactly the data that you're looking for. If endpoints are paid, you might
have to _tip_ reporters a bit more as an incentive for the feed.

_That's it!_

You've learned the art of Tellor Query design, including some important things to consider in the
process. Please reach out to the
[integrations team on discord](https://discord.com/channels/461602746336935936/794270931630948432)
for more help in getting started.

If you're a dev, you can continue reading for a detailed technical
guide for adding new queries to the tellor network.

## Detailed Guide

This section begins a detailed technical description of how to add a new query to the Tellor
network. The process of adding a new query to the Tellor network involves three steps:

1. [Define the new query][step-1-query-definition]
2. [Register the new query][step-2-query-registration]
3. [Create a data source to provide data for the new query][step-3-query-data-sources]

Technically speaking, the 3rd step above is not required, but it enables Tellor's existing
decentralized reporter network to automatically respond to the query. Without this step, customers
will be required to stand-up their own reporter network.

## Step 1: Query Definition

To define a new query, the first step is to specify its _Query Type_. If possible, it's easiest to
use one of the Query Types already defined for the Tellor network (
e.g. [`SpotPrice`][telliot_feeds.queries.price.spot_price.SpotPrice]). If none of the existing query
types work, you will need to [define a new query type][defining-new-query-types].

When using an existing Query Type, you'll need to specify the parameter values that correspond to
the data you would like put on-chain. For example, when using the `SpotPrice` query, you'll need to
specify the values for two parameters: `asset` and `currency`.

It is important to note the difference between defining a _Query Type_ and a defining a _query_.
Defining a new Query Type creates an entire new class of queries, whereas defining a new _query_
refers to an instance of a QueryType with the value of each parameter specified.

To formally add the query definition to Tellor network, you'll need
to [propose changes][propose-changes] to
the [Tellor Data Specification Repository](https://github.com/tellor-io/dataSpecs).

## Step 2: Query Registration

Registering the new query makes users aware of the query and lets reporters know how to respond. It
requires [proposing changes][propose-changes] to
the [`telliot-core` repository](https://github.com/tellor-io/telliot-core), and must include two
things.

First, it must include a unit test for the new query. Using the pytest framework, create a unit test
that creates an instance of the query and verify that the values query descriptor, query data, and
query ID are sensible.

Second, it must be registered with the Query [`Catalog`][telliot_feeds.queries.catalog.Catalog].

The [example below][example-adding-a-new-spotprice] demonstrates how to test a new query and
register it in the catalog.

## Step 3: Query Data Sources

A query [`DataSource`][telliot_feeds.datasource.DataSource] provides a method to fetch new data
points in response to a query. It provides an API that enables Tellor's existing decentralized
reporter network to automatically respond to the query.

Ideally, a [`DataSource`][telliot_feeds.datasource.DataSource] should provide additional
decentralization and robustness by fetching data from multiple sources and aggregating the result.

A new [`DataSource`][telliot_feeds.datasource.DataSource] is created
by [proposing changes][propose-changes] to
the [`telliot-feeds` repository](https://github.com/tellor-io/telliot-feeds).

## Defining New Query Types

If none of the existing Tellor Query Types works for your application, you can define a new _Query
Type_.

A new _Query Type_ definition specifies:

- The _name_ of the query type
- The data type or structure of the value expected query response (i.e.
  its [`ValueType`][telliot_feeds.dtypes.value_type.ValueType])
- Optionally, the name and data type of each query _parameter_
- Encoding method - the method used to encode the Query Type and parameter values into
  the [`query_data`][telliot_feeds.queries.query.OracleQuery.query_data] field used for Tellor
  contract interactions.

It is important to note the difference between defining a _Query Type_ and a defining a _query_.
Defining a new Query Type creates an entire new class of queries, whereas defining a new _query_
refers to an instance of a QueryType with the value of each parameter specified.

To define a new Query Type, [propose changes][propose-changes] to
the [`telliot-core` repository](https://github.com/tellor-io/telliot-core) defining a new subclass
of [`OracleQuery`][telliot_feeds.queries.query.OracleQuery] that implements all required methods and
properties.

New users may choose between subclassing [`JsonQuery`][telliot_feeds.queries.json_query.JsonQuery]
and the  
[`AbiQuery`][telliot_feeds.queries.abi_query.AbiQuery]. These queries are identical in every way
except for the coder/decoder that converts between the query name/parameters and the query data
field used in contract interfaces. The latter format is recommended if on-chain read/write access to
parameter values is required.

You'll also need to create a [test file](https://github.com/tellor-io/telliot-core/blob/main/tests/test_query_snapshot.py) for your new _Query Type_.

To get the [`query_data`][telliot_feeds.queries.query.OracleQuery.query_data] and [`query_id`][telliot_feeds.queries.query.OracleQuery.query_id] in hex format, open up a Python shell and enter the following. We'll be using the [`Snapshot`] query as an example.

```python
from telliot_feeds.queries.snapshot import Snapshot

q = Snapshot(proposal_id="QmbZ6cYVvfoKvkDX14jRcN86z6bfV135npUfhxmENjHnQ1")
q.query_data
q.query_id.hex()
```

## Propose changes

To propose changes to a Tellor repository, perform the following steps:

1. Fork the tellor repository to your github account.
2. Follow our [developer's guide](https://tellor-io.github.io/telliot-core/contributing/) and make the proposed changes in your forked repository.
3. Submit a pull-request to incorporate the changes from your fork into the main tellor repository.

Alternately, standalone changes can be proposed in a separate repository, but it is the user's
responsibility to ensure compatibility with
the [`telliot-core`](https://github.com/tellor-io/telliot-core) framework.

## Example: Adding a new `SpotPrice`

In this example, a new [`SpotPrice`][telliot_feeds.queries.price.spot_price.SpotPrice] query is
defined for the price of BTC in USD.

To add a new spot price, use the
existing [`SpotPrice`][telliot_feeds.queries.price.spot_price.SpotPrice]
Query Type and simply define a new `asset`/`currency` pair.

_Example: Create and test the SpotPrice query for BTC/USD._

```python
from telliot_feeds.queries.price.spot_price import SpotPrice


def test_new_query():
    q = SpotPrice(asset="BTC", currency="USD")
    assert q.descriptor == '{"type":"SpotPrice","asset":"btc","currency":"usd"}'
    assert q.query_data == b'{"type":"SpotPrice","asset":"btc","currency":"usd"}'
    assert q.query_id.hex() == "d66b36afdec822c56014e56f468dee7c7b082ed873aba0f7663ec7c6f25d2c0a"
```

_Example: Add the query to the Query [`Catalog`][telliot_feeds.queries.catalog.Catalog]_

Add the following statements to `telliot_feeds.queries.query_catalog.py`.

```python
query_catalog.add_entry(
    tag="btc-usd-spot", title="BTC/USD spot price", q=SpotPrice(asset="BTC", currency="USD")
)

```
