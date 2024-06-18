const {
    p2tr,
    p2tr_ns,
} =  require('@scure/btc-signer');
const { BIP32Factory } = require('bip32');
const { Network } = require('bitcoinjs-lib');
const ellipticCurveCryptography = require('tiny-secp256k1');
const axios = require('axios');
const ethers = require('ethers');
const decimal = require('decimal.js')
const bip32 = new BIP32Factory(ellipticCurveCryptography);
const { hex } = require('@scure/base');
let contract_info = require('./contract_info/DLCManager.json')
const bitcoin = {
    messagePrefix: '\x18Bitcoin Signed Message:\n',
    bech32: 'bc',
    bip32: {
      public: 0x0488b21e,

      private: 0x0488ade4,
    },
    pubKeyHash: 0x00,
    scriptHash: 0x05,
    wif: 0x80,
}

const TAPROOT_UNSPENDABLE_KEY_HEX = '0250929b74c1a04954b78b4b6035e97a5e078a5a0f28ec96d547bfee9ace803ac0';

async function getDerivedPublicKey(extendedPublicKey) {
    return bip32.fromBase58(extendedPublicKey, bitcoin).derivePath('0/0').publicKey;
}

function getXOnlyPublicKey(publicKey) {
    // console.log("length of publickey: ", publicKey.length)
    // console.log("REgular pubkey: ", publicKey)
    // console.log("shortend pubkey: ", publicKey.slice(1))
    return publicKey.length === 32 ? publicKey : publicKey.subarray(1);
}

function createTaprootMultisigPayment(
    unspendableDerivedPublicKey,
    publicKeyA,
    publicKeyB,
) {
    //console.log(`UnspendableDerivedKey: ${unspendableDerivedPublicKey}, publickeyA: ${publicKeyA}, publicKeyB: ${publicKeyB}`)
    const unspendableDerivedPublicKeyFormatted = getXOnlyPublicKey(unspendableDerivedPublicKey);
  
    const publicKeys = [getXOnlyPublicKey(publicKeyA), getXOnlyPublicKey(publicKeyB)];
    const sortedArray = publicKeys.sort((a, b) => (a.toString('hex') > b.toString('hex') ? 1 : -1));
  
    const taprootMultiLeafWallet = p2tr_ns(2, sortedArray);
  
    return p2tr(unspendableDerivedPublicKeyFormatted, taprootMultiLeafWallet, bitcoin);
}

async function getDefaultProvider(nodeURL) {
    try {
        const provider = new ethers.getDefaultProvider(nodeURL);
        const dlcManagerContract = new ethers.Contract(
            "0x20157DBAbb84e3BBFE68C349d0d44E48AE7B5AD2",
            contract_info.contract.abi,
            provider
        );

        return dlcManagerContract;
    } catch (error) {
        throw(`Could not get Default Provider: ${error}}`);
    }
}

async function getAttestorGroupPublicKey(nodeURL) {
    try {
      const dlcManagerContract = await getDefaultProvider(nodeURL);
      const attestorGroupPubKey = await dlcManagerContract.attestorGroupPubKey();
      return attestorGroupPubKey;
    } catch (error) {
      throw(`Could not fetch Attestor Public Key: ${error}`);
    }
}
   
async function getAllFundedVaults(nodeURL) {
    const FUNDED_STATUS = 1;
    try {
      const dlcManagerContract = await getDefaultProvider(nodeURL);
      const numToFetch = 50;
      let totalFetched = 0;
      const fundedVaults = [];
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const fetchedVaults = await dlcManagerContract.getAllDLCs(
          totalFetched,
          totalFetched + numToFetch
        );
        fetchedVaults.map(vault => {
            if (vault.length == 12) {
                if (Number(vault[5]) == FUNDED_STATUS) {
                    let cleanVault = {
                        uuid: vault[0],
                        protocolContract: vault[1],
                        timestamp: vault[2],
                        valueLocked: vault[3],
                        creator: vault[4],
                        status: vault[5],
                        fundingTxId: vault[6],
                        closingTxId: vault[7],
                        btcFeeRecipient: vault[8],
                        btcMintFeeBasisPoints: vault[9],
                        btcRedeemFeeBasisPoints: vault[10],
                        taprootPubKey: vault[11]
                    }
                    fundedVaults.push(cleanVault)
                }
            }
        });
        console.log("FUnded vaults length: ", fundedVaults.length)
        totalFetched += numToFetch;
        if (fetchedVaults.length !== numToFetch) break;
      }
      return fundedVaults;
    } catch (error) {
      throw(`Could not fetch Funded Vaults: ${error}`);
    }
}

function customShiftValue(value, shift, unshift) {
    const decimalPoweredShift = new decimal.Decimal(10 ** shift);
    const decimalValue = new decimal.Decimal(Number(value));
    console.log("Decimal: ", decimalValue.div(decimalPoweredShift))
    const decimalShiftedValue = unshift ? decimalValue.div(decimalPoweredShift) : decimalValue.mul(decimalPoweredShift);
    return decimalShiftedValue
}

function matchScripts(multisigScripts, outputScript) {
    return multisigScripts.some(
      multisigScript =>
        outputScript.length === multisigScript.length &&
        outputScript.every((value, index) => value === multisigScript[index])
    );
}

function getUnspendableKeyCommittedToUUID(vaultUUID) {
    const publicKeyBuffer = Buffer.from(TAPROOT_UNSPENDABLE_KEY_HEX, 'hex');
    const chainCodeBuffer = Buffer.from(vaultUUID.slice(2), 'hex');
    
    const unspendablePublicKey = bip32
      .fromPublicKey(publicKeyBuffer, chainCodeBuffer, bitcoin)
      .toBase58();
  
    return unspendablePublicKey;
}
  

async function verifyVaultDeposit(vault, attestorPublicKey) {

    if (!vault.fundingTxId || !vault.taprootPubKey || !vault.valueLocked || !vault.uuid) {
      return false;
    }
 
    try {
        // Fetch the Funding Transaction by its ID
        const fundingTransaction = await axios.get(`https://blockchain.info/rawtx/${vault.fundingTxId}`);
        //console.log("funding transaction: ", fundingTransaction)
 
          // Fetch the current Bitcoin Block Height
        const latestBlock = await axios.get("https://blockchain.info/latestblock");
        //("latest block result: ", latestBlock.data.height)
        const bitcoinBlockHeight = latestBlock.height;

 
        // Check the number of Confirmations for the Funding Transaction
        if (fundingTransaction.data.block_height == null) {
            throw(`NO block height found in tx object: ${fundingTransaction}`)
        }
        let confirmations = bitcoinBlockHeight - fundingTransaction.data.block_height;
        if (confirmations < 6) {
            return False
        }
        
        // Get the Closing Transaction Input from the Funding Transaction by the locked Bitcoin value
        let closingTxInput;
        //console.log("length of tx output: ", fundingTransaction.data.out.length)
        //console.log("first output tx obj: ", fundingTransaction.data.out[0])
        for (let i = 0; i < fundingTransaction.data.out.length; i++) {
            console.log(`On ${i} of output tx obj`)
            if (Number(fundingTransaction.data.out[i].value) == Number(vault.valueLocked)) {
                closingTxInput = fundingTransaction.data.out[i]
                //console.log(`Found the right tx that matches the value locked: ${fundingTransaction.data.out[i]} for this much locked: ${vault.valueLocked}`)
            }
        }
 
        const unspendableKeyCommittedToUUID = await getDerivedPublicKey(
            getUnspendableKeyCommittedToUUID(vault.uuid)
        );
        //console.log("got unspendable pubkey from uuid")
 
        const multisigTransaction = createTaprootMultisigPayment(
            unspendableKeyCommittedToUUID,
            attestorPublicKey,
            Buffer.from(vault.taprootPubKey, 'hex')
        );
        //console.log('created taproot tx"')

        // Verify that the Funding Transaction's Output Script matches the expected MultiSig Script
        const acceptedScript = matchScripts(
            [multisigTransaction.script],
            hex.decode(closingTxInput.script)
        );
        console.log(`Matched scripts with result of ${acceptedScript}`)

        if (!acceptedScript) {
            return false;
        }

        return true;
    } catch (error) {
        throw new Error(`Error verifying Vault Deposit: ${error}`);
    }
}



async function calculateProofOfReserve(nodeURL) {
    const allFundedVaults = await (getAllFundedVaults(nodeURL)).then(vaultsArrays => vaultsArrays.flat());

    // Get the Attestor Public Key from the Attestor Group
    const attestorPublicKey = await getDerivedPublicKey(
      await getAttestorGroupPublicKey(nodeURL)
    );
    //console.log("attestor key: ", attestorPublicKey)
    let sum = 0;

    const results = await Promise.all(
      allFundedVaults.map(async vault => {
        try {
          if (await verifyVaultDeposit(vault, attestorPublicKey)) {
            console.log(`Verified a funded vault adding ${Number(vault.valueLocked)} to the current sum of ${sum} to get a new total of ${sum + Number(vault.valueLocked)}`);
            sum += Number(vault.valueLocked)
            return
          }
        } catch (error) {
          // eslint-disable-next-line no-console
          console.error('Error while verifying Deposit for Vault:', vault.uuid, error);
        }
        return 0;
      })
    );

    //const currentProofOfReserve = results.reduce((sum, collateral) => sum + collateral, 0);

    return customShiftValue(sum, 8, true);
}

(async () => {
    const nodeURL = "https://arbitrum-mainnet.infura.io/v3/94b56175a11646878f53e87f5777c2c7"
    let res = await calculateProofOfReserve(nodeURL)
    console.log("Got all funded vaults: ", res)
    // for(let i = 0; i < res.length; i++) {
    //     console.log(res[i])
    // }
})()
