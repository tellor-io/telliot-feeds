from dataclasses import dataclass
from typing import Any
from typing import Optional

import requests
from eth_abi import encode_abi
from eth_abi import encode_single
from eth_utils import keccak
from eth_utils import to_hex
from telliot_core.apps.telliot_config import TelliotConfig

from telliot_feeds.datasource import DataSource
from telliot_feeds.dtypes.datapoint import datetime_now_utc
from telliot_feeds.dtypes.datapoint import OptionalDataPoint
from telliot_feeds.utils.log import get_logger


logger = get_logger(__name__)


@dataclass
class SnapshotVoteResultSource(DataSource[Any]):
    """datasource for snapshot retrieving a vote result"""

    proposalId: Optional[str] = None
    transactionsHash: Optional[str] = None
    moduleAddress: Optional[str] = None
    cfg: TelliotConfig = TelliotConfig()

    def get_response(self, proposalId: Optional[str]) -> Optional[bool]:
        url = "https://hub.snapshot.org/graphql"
        query = """
        query proposal($id: String!) {
          proposal(id: $id) {
            title
            state
            scores
            choices
            plugins
          }
        }
        """
        variables = {"id": proposalId}
        response = requests.post(url, json={"query": query, "variables": variables})
        data = response.json()

        if "errors" in data:
            print("Error fetching proposal data:", data["errors"])
            return None

        proposal = data.get("data", {}).get("proposal")
        real_query_id = self.get_query_id(proposal, proposalId)
        transactions_hash = self.hex_to_bytes(self.transactionsHash)
        query_data_args = encode_abi(
            ["string", "bytes32", "address"], [self.proposalId, transactions_hash, self.moduleAddress]
        )
        query_data = encode_abi(["string", "bytes"], ["Snapshot", query_data_args])
        query_id = keccak(query_data)
        if to_hex(query_id) != to_hex(real_query_id):
            logger.error("Query id does not match")
            return None
        if proposal:
            title = proposal.get("title")
            state = proposal.get("state")
            scores = proposal.get("scores")
            choices = proposal.get("choices")

            if not scores or not choices:
                logger.error("Unable to automatically handle vote result (check proposal at snapshot.org)")
                return None

            outcome = {
                "title": title,
                "state": state,
                "scores": scores,
                "choices": choices,
                "winner": choices[scores.index(max(scores))] if scores else None,
            }

            # log the outcome
            if outcome:
                logger.info(f"Proposal Title: {outcome['title']}")
                logger.info(f"State: {outcome['state']}")
                logger.info("Scores by choice:")
            for choice, score in zip(outcome["choices"], outcome["scores"]):
                logger.info(f"{choice}: {score}")
                logger.info(f"Winner: {outcome['winner']}")

            # return the outcome
            if outcome["winner"] == "For":
                logger.info("Vote result: For")
                return True
            elif outcome["winner"] == "Against":
                logger.info("Vote result: Against")
                return False
            else:
                logger.info("Is proposal structure 'For/Against'? (restart with -b to report manually)")
                return None

        else:
            logger.error("Proposal details not found. Please check proposal id.")
            return None

    def hex_to_bytes(self, hex_str: Optional[str]) -> Optional[bytes]:
        """Convert a hex string to bytes, handling optional '0x' prefix."""
        if hex_str is None:
            return None
        if hex_str.startswith("0x"):
            hex_str = hex_str[2:]
        return bytes.fromhex(hex_str)

    def get_single_transaction_hash(
        self, to_address: str, value: int, data: str, operation: int, nonce: int, chain_id: int, module_address: str
    ) -> str:
        DOMAIN_SEPARATOR_TYPEHASH = keccak(text="EIP712Domain(uint256 chainId,address verifyingContract)")
        TRANSACTION_TYPEHASH = keccak(
            text="Transaction(address to,uint256 value,bytes data,uint8 operation,uint256 nonce)"
        )
        domain_separator_bytes = encode_abi(
            ["bytes32", "uint256", "address"],
            [DOMAIN_SEPARATOR_TYPEHASH, int(chain_id), module_address],
        )
        domain_separator = keccak(domain_separator_bytes)
        tx_subhash_bytes = encode_abi(
            ["bytes32", "address", "uint256", "bytes32", "uint8", "uint256"],
            [TRANSACTION_TYPEHASH, to_address, int(value), keccak(hexstr=data), int(operation), int(nonce)],
        )
        tx_subhash = keccak(tx_subhash_bytes)
        tx_data = b"\x19" + b"\x01" + encode_single("bytes32", domain_separator) + encode_single("bytes32", tx_subhash)
        tx_hash = keccak(tx_data)
        return tx_hash

    def get_query_id(self, proposal_data: Optional[dict], proposal_id: Optional[str]) -> Optional[str]:
        plugins = proposal_data.get("plugins")
        if not plugins:
            return None
        safe_snap = plugins.get("safeSnap")
        if not safe_snap:
            return None
        safes = safe_snap.get("safes")
        if not safes:
            return None
        first_safe = safes[0]
        module_address = first_safe.get("tellorAddress")
        if not module_address:
            return None
        chain_id = int(first_safe.get("network"))
        if not chain_id:
            return None
        txs = first_safe.get("txs")
        if not txs:
            return None
        txs0 = txs[0]
        transactions = txs0.get("transactions")
        if not transactions:
            return None
        tx_hashes = []
        for tx in transactions:
            to_address = tx.get("to")
            value = tx.get("value")
            data = tx.get("data")
            operation = tx.get("operation")
            nonce = tx.get("nonce")
            tx_hash = self.get_single_transaction_hash(
                to_address, value, data, operation, nonce, chain_id, module_address
            )
            tx_hashes.append(tx_hash)
        tx_hashes_array_bytes = encode_abi(["bytes32[]"], [tx_hashes])
        tx_superhash = keccak(tx_hashes_array_bytes)
        query_data_args = encode_abi(["string", "bytes32", "address"], [proposal_id, tx_superhash, module_address])
        query_data = encode_abi(["string", "bytes"], ["Snapshot", query_data_args])
        query_id = keccak(query_data)
        return query_id

    async def fetch_new_datapoint(self) -> OptionalDataPoint[bool]:
        """Prepare Current time-stamped boolean result of vote."""
        try:
            vote_passed = self.get_response(self.proposalId)
            if vote_passed is True:
                return True, datetime_now_utc()
            elif vote_passed is False:
                return False, datetime_now_utc()
            else:
                return None, None

        except Exception as e:
            logger.info(f"Unable to fetch vote result. Error: {e}")
            return None, None


if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        proposalId = "0xe992735684706baf15e447b537acbaaac8ef74d8ce0033205456ceed58bffdf6"
        transactionsHash = "0xfd471b205457d8bac0d29a63292545f9f3189086a31a7794de341d55e9f50188"
        moduleAddress = "0xB1bB6479160317a41df61b15aDC2d894D71B63D9"
        source = SnapshotVoteResultSource(
            proposalId=proposalId, transactionsHash=transactionsHash, moduleAddress=moduleAddress
        )
        v, _ = await source.fetch_new_datapoint()
        print(v)

    asyncio.run(main())
