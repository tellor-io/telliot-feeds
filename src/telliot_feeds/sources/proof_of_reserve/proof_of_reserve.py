import json
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.apps.core import RPCEndpoint
from clamfig import deserialize

ethereum_address = "0x20157DBAbb84e3BBFE68C349d0d44E48AE7B5AD2"

FUNDED_STATUS = 1

def getAttestorGroupPublicKey(endpoint: RPCEndpoint, contract):
    try:
        attestorPubKey = contract.attestorGroupPubKey().call()
        return attestorPubKey
    except Exception as e:
        print(f"Unable to get attestor pubkey: {e}")


async def ProveProofOfReserves():
    cfg = TelliotConfig()
    ethereum_endpoint = cfg.endpoints.find(chain_id=1)[0]
    ethereum_endpoint.connect()

    with open("./contract_info/DLCBTC.json") as f:
        info_res = json.load(f)

    contract_info = deserialize(info_res)
    abi = contract_info['contract']['abi']

    eth_contract = ethereum_endpoint.web3.eth.contract(address=ethereum_address, abi=abi)
    getAllDLCsFunction = eth_contract.get_function_by_name("getAllDLCs")
    totalFetched = 0
    numToFetch = 50
    fundedVaults = []
    while True:
        try:
            fetchedVaults = await getAllDLCsFunction(totalFetched, numToFetch).call()
            for vault in fetchedVaults:
                if vault['status'] == FUNDED_STATUS:
                    fundedVaults.append(vault) 

            totalFetched += numToFetch
            if len(fetchedVaults) < numToFetch:
                break
        except Exception as e:
            print(f"Exception when getting DLCs: {e}")


    attestorGroupPubkey = getAttestorGroupPublicKey(ethereum_endpoint, eth_contract)
    
    

    







