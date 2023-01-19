# Add New Data Type (Custom Oracle Query)

### Steps
1. Your new data type, or query, should be defined in the [dataSpecs](https:://github.com/tellor-io/dataSpecs) repo. If not, [create the spec there](https://github.com/tellor-io/dataSpecs/issues/new?assignees=&labels=&template=new_query_type.yaml&title=%5BNew+Query+Type%5D%3A+) first. Once that's done, follow the steps below.
2. Create a subclass of `AbiQuery` in `src/telliot_feeds/queries/`. For example, if you wanted to implement the [Snapshot query type](https://github.com/tellor-io/dataSpecs/blob/main/types/Snapshot.md), it would look like this:
```python
import logging
from dataclasses import dataclass
from typing import Optional

from telliot_feeds.dtypes.value_type import ValueType
from telliot_feeds.queries.abi_query import AbiQuery

logger = logging.getLogger(__name__)


@dataclass
class Snapshot(AbiQuery):
    """Returns the proposal result for a given proposal id (an IPFS hash for a certain proposal) coming from Snapshot.
       A boolean value indicating whether a proposal succeeded (True) or failed (False) should be returned.

    Attributes:
        proposal_id:
            Specifies the requested data a of a valid proposal on Snapshot.

    See https://snapshot.org/ for proposal results.
    See the data spec for more info about this query type:
    https://github.com/tellor-io/dataSpecs/blob/main/types/Snapshot.md
    """

    proposalId: Optional[str]

    #: ABI used for encoding/decoding parameters
    abi = [{"name": "proposalId", "type": "string"}]

    @property
    def value_type(self) -> ValueType:
        """Data type returned for a Snapshot query.

        - `bool`: a boolean value true or false equivalent to uint8 restricted to the values 0 and 1
        - `packed`: false
        """

        return ValueType(abi_type="bool", packed=False)
```
3. Next you'll need to add a data source for your query type in `src/telliot_feeds/sources/`. For an example of an automated data source, see `src/telliot_feeds/sources/etherscan_gas.py`. For an example of a data source that requires manual entry, see `src/telliot_feeds/sources/manual/snapshot.py`.
4. Create an instance of the `DataFeed` class in `src/telliot_feeds/feeds/`. For example, if you had implemented the `SpotPrice` query type and added sources for `MATIC/USD`, the `DataFeed` subclass would look like this (`src/telliot_feeds/feeds/matic_usd_feed.py`):
```python
from telliot_feeds.datafeed import DataFeed
from telliot_feeds.queries.price.spot_price import SpotPrice
from telliot_feeds.sources.price.spot.binance import BinanceSpotPriceSource
from telliot_feeds.sources.price.spot.bittrex import BittrexSpotPriceSource
from telliot_feeds.sources.price.spot.coinbase import CoinbaseSpotPriceSource
from telliot_feeds.sources.price.spot.coingecko import CoinGeckoSpotPriceSource
from telliot_feeds.sources.price.spot.gemini import GeminiSpotPriceSource
from telliot_feeds.sources.price.spot.kraken import KrakenSpotPriceSource
from telliot_feeds.sources.price_aggregator import PriceAggregator

matic_usd_median_feed = DataFeed(
    query=SpotPrice(asset="MATIC", currency="USD"),
    source=PriceAggregator(
        asset="matic",
        currency="usd",
        algorithm="median",
        sources=[
            CoinGeckoSpotPriceSource(asset="matic", currency="usd"),
            BittrexSpotPriceSource(asset="matic", currency="usd"),
            BinanceSpotPriceSource(asset="matic", currency="usdt"),
            CoinbaseSpotPriceSource(asset="matic", currency="usd"),
            GeminiSpotPriceSource(asset="matic", currency="usd"),
            KrakenSpotPriceSource(asset="matic", currency="usd"),
        ],
    ),
)
```
5. Add example instance of the query type to catalog. For example, if you wanted an example `Snapshot` query instance in the catalog, edit `src/telliot_feeds/queries/query_catalog.py` to include:
```python
query_catalog.add_entry(
    tag="snapshot-proposal-example",
    title="Snapshot proposal example",
    q=Snapshot(proposalId="cce9760adea906176940ae5fd05bc007cc9252b524832065800635484cb5cb57"),
)
```
7. Make sure you've added tests for your new query type, data sources, data feed, & changes to the CLI.
8. Submit a PR to the `telliot-feeds` repo. Included an example `submitValue` transaction for your new query type in the PR description. For example [this PR]().

Telliot-core/telliot-feed-examples (implementation)
Make query type & tests in telliot-core (e.g. https://github.com/tellor-io/telliot-core/blob/main/src/telliot_core/queries/morphware.py & https://github.com/tellor-io/telliot-core/blob/main/tests/test_query_morphware.py)
Query type class file (i recommend copying and pasting morphware and using it as a template. Replace the Morphware specs with your new specs!)
Name class after the new query type
In docstring:
Header should read “Returns the result for a given <your new query type name> query.”
Link to:
The .md file in the dataSpecs repo that matches this query type
Additional resources about the new data type (ex: educational resources that answer: what is a gas price? What is eip1559?)
Copy from your new query type’s dataSpecs .md file the “abi” field in the JSON response(copy from open bracket to closed bracket)
Attributes
Replace “version” with the new query parameters (include python Typing)
Paste into the “abi” attribute of your new query type class in the python file
In “value_type” docstring:
Header should read “Data type returned for a <your new query type> query.”
Return the abi_type parameter that matches the response type from your new query type’s dataSpecs .md file 
Note: if the abi type is “ufixed256x18”, use the UnsignedFloatType class instead of “ValueType”
Query type tests (I also recommend copying and pasting the morphware test file and using it as a template, replacing the Morphware details with your new query type’s specs)
Name file “test_query_<name of your query type>.py”
In the file docstring, Replace “Morphware” with “<your new query type>”
Replace the Morphware import with your new Query Type class
In the “test_query_constructor()” test...
 In the docstring, replace “Morphware” with “<your new query type>”
Change constructor in test from “Morphware” to “<name of class of your new query type>”
Replace the Morphware parameters with test values of your query type’s query parameters
Replace the Morphware “exp_query_data” value with the expected value for your query type and query parameters. You can generate it this way:
Generate the queryData here https://queryidbuilder.herokuapp.com/custom
Format the queryData from hex to bytes https://stackoverflow.com/questions/6624453/whats-the-correct-way-to-convert-bytes-to-a-hex-string-in-python-3
Replace the Morphware queryData with your output
Test the decoding of the query data
Assert the decoded query type is correct
Assert the decoded query parameters are correct
Assert the queryId is the same as what you generate here https://queryidbuilder.herokuapp.com/custom
In the “test_encode_decode_reported_val()” test…
Replace Morphware constructor with constructor of your new query type
Replace Morphware query parameters with your query type’s query parameters
Replace link to Morphware dataSpecs with link to your dataSpecs markdown file
Remove example Morphware data source comment block
Set data variable to some dummy data in the response type format you specified on the dataSpecs of your query type
Encode “data” and assert that it became bytes (python data type)
Decode the encoded “data” and assert that returns to its original data type
Make PR
Make data source and feed for your query type in telliot-feed-examples (e.g. https://github.com/tellor-io/telliot-feed-examples/blob/main/src/telliot_feed_examples/sources/morphware.py & https://github.com/tellor-io/telliot-feed-examples/blob/main/src/telliot_feed_examples/feeds/morphware.py). And their corresponding tests (e.g. https://github.com/tellor-io/telliot-feed-examples/blob/main/tests/feeds/test_morphware_feeds.py & https://github.com/tellor-io/telliot-feed-examples/blob/main/tests/sources/test_morphwarev1_sources.py)
Find an API that matches your dataSpec
DataSource Implementation (use Morphware DataSource as a template/reference)
Create new file in “sources” directory
Name file “<name of your query type in lowercase with underscores between words>.py
Name DataSource class as <”new query type name”Source> (e.g. GasPriceOracleSource)
Adjust class docstring to match your querySpec
In “get_metadata()” function… (helper function for requesting from the data endpoint)
Rename function to describe the type of data you’re requesting 
Add your query parameters (with types) as arguments to the function
In docstring: describe what type of data is fetched, and which API it’s fetched from
Change to “get” request if necessary
Mount to “https” instead of “http” if necessary
Set “json_data” (these are the API’s arguments) to the query parameter arguments of the function
Post request to your query type’s API’s url
Rename logger message to match your query type’s name
In the “fetch_new_datapoint()” function…
In docstring, Describe what type of data you’re requesting, and where it’s sourced from
Save helper function call above to “rsp” variable
Change logger message to match your query type’s name
Save json of the helper function’s response to a variable
Adjust data types
Save datapoint and current time in a tuple
Store the datapoint
Replace Morphware references in logger messages with name of your query type 
Testing (use Morphware DataSource tests as a template)
Replace Morphware Import with your DataSource
Assert “fetch_new_datapoint” does nor return nothing (check logs if the test fails on this assertion)
Assert that “fetch_new_datapoint” returns the data type you expect for your new query type
DataFeed implementation
Create new file in “feeds” directory
Name file “<name of your query type>_feed.py”
In file header docstring…
describe the example query of your query type, and describe any example query parameters used in the example DataFeed
Link to the new query dataSpec .md file for “more info”
Import…
“DataFeed”
Your query type class
Your DataSource class
Set example query parameters if your query type requires them (and describe them with additional comments if necessary
Save to a variable a DataFeed object, where…
“query” is an instance of your query type class
“source” is an instance of your DataSource class
Pass in query parameters here as class attributes
DataFeed testing
Create new test file in “tests/feeds” directory
Name test “test_<name of your query type>_feed.py”
Test “fetch_new_datapoint” function call from your query type data feed
Note: the function can be called from the source attribute of the data feed
The assertions of the test should be the same as those of your DataSource tests
Add an instance of your new query type to the catalog in telliot-core (e.g. https://github.com/tellor-io/telliot-core/pull/267). 
Link the query tag to the DataFeed you've created in telliot-feed-examples (e.g. https://github.com/tellor-io/telliot-feed-examples/pull/168)
