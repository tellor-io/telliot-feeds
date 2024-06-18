import json
from telliot_core.apps.telliot_config import TelliotConfig
from telliot_core.apps.core import RPCEndpoint
from clamfig import deserialize
from bitcoinlib import networks
from bitcoinlib import keys
from requests.adapters import HTTPAdapter
import requests

ethereum_address = "0x20157DBAbb84e3BBFE68C349d0d44E48AE7B5AD2"

FUNDED_STATUS = 1

def getAttestorGroupPublicKey(endpoint: RPCEndpoint, contract) -> str :
    try:
        attestorPubKey: str = contract.attestorGroupPubKey().call()
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


    attestorGroupPubkey = await getAttestorGroupPublicKey(ethereum_endpoint, eth_contract)
    bitcoinNetwork = networks.Network("bitcoin")
    attestorPublicKey = keys.addr_base58_to_pubkeyhash(bytes.fromhex(attestorGroupPubkey), True)

    for vault in fundedVaults:
        if vault.fundingTxId is None or vault.taprootPubKey is None or vault.valueLocked is None or vault.uuid is None:
            return False
        
        with requests.Session() as s:
            try:
                bitcoinExplorerTXURL = f'https://blockchain.info/rawtx/{vault.fundingTxId}'
                fundingTx = s.get(bitcoinExplorerTXURL)
                fundingTx = fundingTx.json()
                print(f'funding tx: {fundingTx}')
            except Exception as e:
                print(e)

            try: 
                latestBlock = s.get("https://blockchain.info/latestblock")
                latestBlock = latestBlock.json()
                print(f'Block height res: {latestBlock}')
            except Exception as e:
                print(e)
            
            if fundingTx["block_height"] is None:
                raise(f'NO block height found in tx object: {fundingTx}')
            
            confirmations = latestBlock["height"] - fundingTx["block_height"]
            if confirmations < 6:
                return False
            
            output_obj = None
            for obj in fundingTx["out"]:
                if obj["value"] == vault["valueLocked"]:
                    output_obj = obj

            if output_obj is None:
                print("no output object found in transaction that matches the value locked field of the vault")
                return False
            
            base58KeyCommittedToUUID = keys.base58encode(bytes.fromhex(vault["uuid"]))
            unspendandablePubKey = keys.addr_base58_to_pubkeyhash(base58KeyCommittedToUUID)
            tapRootPubKey = bytes.fromhex(vault["taprootPubKey"])





            


        


        

    
    

    







